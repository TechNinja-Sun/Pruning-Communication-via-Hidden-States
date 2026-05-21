import asyncio
import os
import sys
import re
import json
import csv
import numpy as np
from datetime import datetime
from pathlib import Path
from collections import Counter
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm
import random
from openai import AsyncOpenAI

import matplotlib.pyplot as plt
import networkx as nx
import seaborn as sns

# 关闭窗口弹出，后台绘图
plt.switch_backend('Agg')
sns.set(style="whitegrid")

sys.path.append(str(Path(__file__).parent.parent))

from data.dataset.mmlu_dataset import MMLUDataset
from system.registry import PRUNE_COMM_REGISTRY
import agent.agent
import llm
import memory.sys_memory

load_dotenv()

MINE_BASE_URL = os.getenv("BASE_URL")
MINE_API_KEY = os.getenv("API_KEY")


@PRUNE_COMM_REGISTRY.register('workflow')
class Workflow:

    def __init__(self, nums_agents=None, max_rounds=None):
        self.nums_agents = nums_agents or int(os.getenv("NUMS_AGENTS", 4))
        raw_model_list = os.getenv("LLM_NAME_LIST", os.getenv("AGENT_MODELS", "qwen-plus"))
        self.model_list = [name.strip() for name in raw_model_list.split(",") if name.strip()]
        self.comm_mode = os.getenv("COMM_MODE", "dissimilar")
        self.max_rounds = max_rounds or int(os.getenv("MAX_ROUNDS", 10))
        self.high_consensus_th = float(os.getenv("HIGH_CONSENSUS_TH", 0.75))
        self.mid_consensus_th = float(os.getenv("MID_CONSENSUS_TH", 0.50))
        self.correct_tendency_th = float(os.getenv("CORRECT_TENDENCY_TH", 0.50))
        self.core_ratio = float(os.getenv("CORE_RATIO", 0.60))
        self.consensus_history_window = int(os.getenv("CONSENSUS_HISTORY_WINDOW", 30))

        self.exp_dir = Path(f"exp/result_{datetime.now().strftime('%Y%m%d_%H%M%S')}/{self.comm_mode}")
        self.exp_dir.mkdir(parents=True, exist_ok=True)

        self.round_json_dir = self.exp_dir / "round_json"
        self.round_json_dir.mkdir(parents=True, exist_ok=True)

        self.metric_dir = self.exp_dir / "metrics"
        self.metric_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.log_file = self.exp_dir / f"log_{timestamp}.txt"
        self.trace_file = self.exp_dir / f"trace_{timestamp}.json"

        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write(f"Experiment Start: {datetime.now()}\n\n")
            f.write(f"Max Rounds: {self.max_rounds}\n\n")

        self.acc_history = []
        self.sim_history = []
        self.token_history = []
        self.answer_change_history = []
        self.correction_history = []
        self.wrong_change_history = []
        self.two_round_same_history = []
        self.global_trace = []
        self.round_comparisons = []
        self.round_strategy_history = []
        self.agent_stability = {}
        self.agent_model_map = {}
        self.agent_prior_strength = {}
        self.consensus_ratio_history = []

    async def _is_model_callable(self, client: AsyncOpenAI, model: str) -> bool:
        try:
            await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "A/B/C/D only"}],
                max_tokens=1,
                temperature=0,
                n=1,
                extra_body={"enable_thinking": False},
            )
            return True
        except Exception:
            return False

    def _registered_model_names(self):
        reserved = {"llm", "agents", "workflow", "sys_memory"}
        return [name for name in PRUNE_COMM_REGISTRY._registry.keys() if name not in reserved]

    async def validate_model_list(self):
        """Keep a unique, callable model list and supplement replacements without duplicates."""
        candidate_models = list(dict.fromkeys(self.model_list))
        if not candidate_models:
            self.model_list = ["qwen-plus"]
            return

        registered = set(PRUNE_COMM_REGISTRY._registry.keys())
        registered_models = [m for m in candidate_models if m in registered]
        unregistered = [m for m in candidate_models if m not in registered]

        if unregistered:
            print("[WARN] 未注册模型将被忽略:", unregistered)

        if not registered_models:
            print("[WARN] 没有可用注册模型，回退到 qwen-plus")
            self.model_list = ["qwen-plus"]
            return

        client = AsyncOpenAI(base_url=MINE_BASE_URL, api_key=MINE_API_KEY)
        validated = []
        unavailable = []

        for model in registered_models:
            if await self._is_model_callable(client, model):
                validated.append(model)
            else:
                try:
                    await client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": "A/B/C/D only"}],
                        max_tokens=1,
                        temperature=0,
                        n=1,
                    )
                except Exception as e:
                    unavailable.append(f"{model} -> {type(e).__name__}: {e}")

        if unavailable:
            print("[WARN] 以下模型当前不可调用，已自动过滤:")
            for item in unavailable:
                print("  -", item)

        if len(validated) < self.nums_agents:
            print("[INFO] 可用模型不足，开始从其余注册模型中补位（不重复）...")
            for model in self._registered_model_names():
                if model in validated:
                    continue
                if await self._is_model_callable(client, model):
                    validated.append(model)
                    print(f"  + 补位模型: {model}")
                if len(validated) >= self.nums_agents:
                    break

        if not validated:
            print("[WARN] 所有候选模型均不可调用，回退到 qwen-plus")
            validated = ["qwen-plus"]

        if len(validated) < self.nums_agents:
            raise RuntimeError(
                f"唯一可调用模型不足: 需要 {self.nums_agents} 个，当前仅 {len(validated)} 个。"
                "请减少 NUMS_AGENTS 或提供更多可调用模型。"
            )

        self.model_list = validated

    def extract_option(self, text):
        if not text:
            return "A"

        text = text.upper()
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        keyword_pattern = re.compile(
            r"\b(?:FINAL\s+ANSWER|ANSWER|OPTION|CHOICE)\b\s*[:：-]?\s*(?:\*\*)?([ABCD])(?:\*\*)?"
        )
        line_pattern = re.compile(
            r"^(?:[\(\[]?([ABCD])[\)\]]?(?:[\.:：\-]\s*|\s*$)|(?:[\*\-]\s*)?([ABCD])\s*$)"
        )
        bare_pattern = re.compile(r"\b([ABCD])\b")

        for line in lines:
            keyword_match = keyword_pattern.search(line)
            if keyword_match:
                return keyword_match.group(1)

        for line in lines:
            line_match = line_pattern.match(line)
            if line_match:
                return line_match.group(1) or line_match.group(2)

        for line in lines:
            bare_match = bare_pattern.search(line)
            if bare_match:
                return bare_match.group(1)

        return "A"

    def ring_fallback(self, i, agent_list, candidate_indices=None):
        if candidate_indices:
            valid = [idx for idx in candidate_indices if idx != i]
            if valid:
                return agent_list[valid[0]]
        return agent_list[(i + 1) % len(agent_list)]

    def select_agent_by_mode(self, i, agent_list, sim_matrix, mode, candidate_indices=None):
        indices = list(range(len(agent_list))) if candidate_indices is None else list(candidate_indices)
        indices = [idx for idx in indices if idx != i]

        if not indices:
            return self.ring_fallback(i, agent_list)

        target_idx = None

        if mode == "dissimilar":
            best = 1.0
            for j in indices:
                if sim_matrix[i][j] < best:
                    best = sim_matrix[i][j]
                    target_idx = j
        elif mode == "similar":
            best = -1.0
            for j in indices:
                if sim_matrix[i][j] > best:
                    best = sim_matrix[i][j]
                    target_idx = j
        elif mode == "random":
            target_idx = random.choice(indices)

        if target_idx is None:
            return self.ring_fallback(i, agent_list, candidate_indices=indices)
        return agent_list[target_idx]

    def get_adaptive_consensus_thresholds(self, current_ratio):
        history = self.consensus_ratio_history[-self.consensus_history_window:]
        series = history + [current_ratio]

        if len(series) < 5:
            high_th = self.high_consensus_th
            mid_th = self.mid_consensus_th
        else:
            arr = np.array(series, dtype=np.float32)
            q_high = float(np.quantile(arr, 0.70))
            q_mid = float(np.quantile(arr, 0.40))

            high_th = (self.high_consensus_th + q_high) / 2.0
            high_th = max(0.55, min(0.90, high_th))

            mid_th = (self.mid_consensus_th + q_mid) / 2.0
            mid_th = max(0.35, min(high_th - 0.05, mid_th))

        return high_th, mid_th

    def decide_hybrid_strategy(self, first_round_answers, correct):
        options = [first_round_answers[name]["option"] for name in first_round_answers.keys()]
        vote = Counter(options)
        top_option, top_count = vote.most_common(1)[0]
        consensus_ratio = top_count / len(options)
        high_th, mid_th = self.get_adaptive_consensus_thresholds(consensus_ratio)

        correct_tendency = top_option == correct and consensus_ratio >= self.correct_tendency_th

        if correct_tendency or consensus_ratio >= high_th:
            strategy = "similar"
        elif consensus_ratio >= mid_th:
            strategy = "mixed"
        else:
            strategy = "dissimilar_then_similar"

        return {
            "strategy": strategy,
            "consensus_option": top_option,
            "consensus_ratio": consensus_ratio,
            "high_threshold": high_th,
            "mid_threshold": mid_th,
            "correct_tendency": correct_tendency,
            "vote": dict(vote),
        }

    def update_agent_stability(self, names, first_round_answers, correct):
        for name in names:
            if name not in self.agent_stability:
                self.agent_stability[name] = {"correct": 0, "total": 0}
            self.agent_stability[name]["total"] += 1
            if first_round_answers[name]["option"] == correct:
                self.agent_stability[name]["correct"] += 1

    def estimate_model_strength(self, model_name):
        name = model_name.lower()

        score = 0.0

        for val, w in [
            (0.5, 0.5), (0.6, 0.6), (1.5, 1.2), (1.7, 1.3),
            (3, 2.0), (4, 2.4), (7, 3.2), (8, 3.4),
            (14, 4.2), (27, 4.8), (32, 5.0), (35, 5.2),
            (57, 5.8), (72, 6.2), (80, 6.4), (110, 7.2),
            (122, 7.4), (235, 8.5), (397, 9.2), (480, 9.8),
        ]:
            if f"-{val}b" in name or f"-{int(val)}b" in name:
                score = max(score, w)

        # Product-tier hints.
        if "max" in name or "plus" in name:
            score += 1.0
        if "thinking" in name:
            score += 0.7
        if "flash" in name:
            score -= 0.3
        if "turbo" in name:
            score -= 0.2

        return score

    def split_core_edge_agents(self, names):
        scored = []
        for name in names:
            info = self.agent_stability.get(name, {"correct": 0, "total": 0})
            total = info["total"]
            correct = info["correct"]
            prior = self.agent_prior_strength.get(name, 0.0)

            # Smooth by prior so early rounds do not get dominated by env ordering.
            alpha = 3.0
            smoothed_score = (correct + alpha * prior) / (total + alpha)
            scored.append((name, smoothed_score, total, prior))

        scored.sort(key=lambda x: (x[1], x[2], x[3]), reverse=True)
        core_size = max(2, int(round(len(names) * self.core_ratio)))
        core_size = min(core_size, len(names) - 1) if len(names) > 2 else len(names)

        core_agents = [name for name, _, _, _ in scored[:core_size]]
        edge_agents = [name for name, _, _, _ in scored[core_size:]]
        return core_agents, edge_agents

    def get_agent_smoothed_score(self, agent_name, alpha=3.0):
        info = self.agent_stability.get(agent_name, {"correct": 0, "total": 0})
        total = info["total"]
        correct = info["correct"]
        prior = self.agent_prior_strength.get(agent_name, 0.0)
        return (correct + alpha * prior) / (total + alpha)

    def build_ref_maps(self, agent_list, sim_matrix, strategy):
        idx_of = {name: i for i, name in enumerate(agent_list)}
        primary_ref_map = {}
        secondary_ref_map = {}
        core_agents = []
        edge_agents = []

        if strategy in {"similar", "dissimilar", "random"}:
            for i, a in enumerate(agent_list):
                primary_ref_map[a] = self.select_agent_by_mode(i, agent_list, sim_matrix, strategy)
            return primary_ref_map, secondary_ref_map, core_agents, edge_agents

        if strategy == "mixed":
            core_agents, edge_agents = self.split_core_edge_agents(agent_list)
            core_indices = [idx_of[name] for name in core_agents if name in idx_of]

            for i, a in enumerate(agent_list):
                if a in core_agents:
                    primary_ref_map[a] = self.select_agent_by_mode(i, agent_list, sim_matrix, "similar", candidate_indices=core_indices)
                else:
                    primary_ref_map[a] = self.select_agent_by_mode(i, agent_list, sim_matrix, "dissimilar", candidate_indices=core_indices)
            return primary_ref_map, secondary_ref_map, core_agents, edge_agents

        if strategy == "dissimilar_then_similar":
            core_agents, edge_agents = self.split_core_edge_agents(agent_list)
            for i, a in enumerate(agent_list):
                if a in core_agents:
                    # Strong/core agents keep explore+converge dual references.
                    primary_ref_map[a] = self.select_agent_by_mode(i, agent_list, sim_matrix, "dissimilar")
                    secondary_ref_map[a] = self.select_agent_by_mode(i, agent_list, sim_matrix, "similar")
                else:
                    # Weak/edge agents use single similar reference to reduce prompt noise.
                    primary_ref_map[a] = self.select_agent_by_mode(i, agent_list, sim_matrix, "similar")
            return primary_ref_map, secondary_ref_map, core_agents, edge_agents

        for i, a in enumerate(agent_list):
            primary_ref_map[a] = self.select_agent_by_mode(i, agent_list, sim_matrix, "similar")
        return primary_ref_map, secondary_ref_map, core_agents, edge_agents

    def save_comm_graph(self, ref_map, save_dir):
        G = nx.DiGraph()
        for k, v in ref_map.items():
            G.add_edge(k, v)

        plt.figure(figsize=(6, 6))
        pos = nx.spring_layout(G, seed=42)
        nx.draw(G, pos, with_labels=True, node_size=2000, arrows=True)
        plt.title("Communication Graph")
        plt.savefig(save_dir / "comm_graph.png", dpi=300, bbox_inches='tight')
        plt.close()

    def save_heatmap(self, sim_matrix, agent_list, save_dir):
        plt.figure(figsize=(6, 5))
        sns.heatmap(sim_matrix,
                    xticklabels=agent_list,
                    yticklabels=agent_list,
                    cmap="coolwarm",
                    annot=True)
        plt.title("Similarity Heatmap")
        plt.savefig(save_dir / "sim_heatmap.png", dpi=300, bbox_inches='tight')
        plt.close()

    def plot_acc_curve(self):
        """ACC 折线图"""
        rounds = list(range(1, len(self.acc_history) + 1))
        if not rounds:
            return

        bg = "#f8fafc"
        grid = "#e2e8f0"
        values = [value * 100.0 for value in self.acc_history]

        fig, ax = plt.subplots(figsize=(11, 5.8), facecolor=bg)
        ax.set_facecolor(bg)

        ax.fill_between(rounds, values, [0] * len(rounds), color="#8ecae6", alpha=0.25, zorder=1)
        ax.plot(rounds, values, color="#0ea5e9", linewidth=2.8, zorder=3)
        ax.scatter(rounds, values, color="#0284c7", s=16, alpha=0.85, zorder=4)

        avg_acc = sum(values) / len(values)
        ax.axhline(avg_acc, color="#1f4e79", linestyle="--", linewidth=2.0, label=f"Average: {avg_acc:.2f}%")

        final_round = rounds[-1]
        final_acc = values[-1]
        ax.scatter([final_round], [final_acc], color="#0369a1", s=42, zorder=5)
        ax.annotate(
            f"Final: {final_acc:.2f}%",
            xy=(final_round, final_acc),
            xytext=(-85, 18),
            textcoords="offset points",
            fontsize=10,
            color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#bae6fd", alpha=0.95),
            arrowprops=dict(arrowstyle="->", color="#0ea5e9", lw=1.2),
        )

        ax.set_title("Accuracy Curve", fontsize=15, fontweight="bold", color="#0f172a", pad=10)
        ax.set_xlabel("Round", fontsize=11)
        ax.set_ylabel("Accuracy (%)", fontsize=11)
        ax.set_ylim(0, 102)
        ax.set_xticks(rounds)
        ax.grid(color=grid, linewidth=0.9, alpha=0.75)
        for spine in ax.spines.values():
            spine.set_color("#cbd5e1")
        ax.legend(loc="lower right", frameon=True, framealpha=0.92)

        fig.tight_layout()
        fig.savefig(self.metric_dir / "acc_curve.png", dpi=320)
        plt.close(fig)

    def plot_rate_curve(self, history, title, ylabel, filename, color):
        rounds = list(range(1, len(history) + 1))
        if not rounds:
            return

        bg = "#f8fafc"
        grid = "#e2e8f0"
        values = [v * 100.0 for v in history]
        fig, ax = plt.subplots(figsize=(11, 5.8), facecolor=bg)
        ax.set_facecolor(bg)

        ax.fill_between(rounds, values, [0] * len(rounds), color=color, alpha=0.18, zorder=1)
        ax.plot(rounds, values, color=color, linewidth=2.8, zorder=3)
        ax.scatter(rounds, values, color=color, s=16, alpha=0.85, zorder=4)

        avg_value = sum(values) / len(values)
        ax.axhline(avg_value, color="#374151", linestyle="--", linewidth=2.0, label=f"Average: {avg_value:.2f}%")

        final_round = rounds[-1]
        final_value = values[-1]
        ax.scatter([final_round], [final_value], color="#111827", s=42, zorder=5)
        ax.annotate(
            f"Final: {final_value:.2f}%",
            xy=(final_round, final_value),
            xytext=(-85, 18),
            textcoords="offset points",
            fontsize=10,
            color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#d1d5db", alpha=0.95),
            arrowprops=dict(arrowstyle="->", color=color, lw=1.2),
        )

        ax.set_xlabel("Round", fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_title(title, fontsize=15, fontweight="bold", color="#0f172a", pad=10)
        ax.set_xticks(rounds)
        ax.set_ylim(0, 105)
        ax.grid(color=grid, linewidth=0.9, alpha=0.75)
        for spine in ax.spines.values():
            spine.set_color("#cbd5e1")
        ax.legend(loc="lower right", frameon=True, framealpha=0.92)

        fig.tight_layout()
        fig.savefig(self.metric_dir / filename, dpi=320)
        plt.close(fig)

    def plot_strategy_ratio_curve(self):
        rounds = list(range(1, len(self.round_strategy_history) + 1))
        if not rounds:
            return

        bg = "#f8fafc"
        grid = "#e2e8f0"

        target_strategies = ["similar", "mixed", "dissimilar_then_similar"]
        cumulative_counts = {k: 0 for k in target_strategies}
        ratio_history = {k: [] for k in target_strategies}

        for idx, item in enumerate(self.round_strategy_history, start=1):
            strategy = item.get("strategy", "")
            if strategy in cumulative_counts:
                cumulative_counts[strategy] += 1

            for key in target_strategies:
                ratio_history[key].append(cumulative_counts[key] / idx * 100.0)

        fig, ax = plt.subplots(figsize=(11, 5.8), facecolor=bg)
        ax.set_facecolor(bg)

        style_map = {
            "similar": {"color": "#0ea5e9", "fill": "#8ecae6", "label": "similar"},
            "mixed": {"color": "#16a34a", "fill": "#86efac", "label": "mixed"},
            "dissimilar_then_similar": {"color": "#f97316", "fill": "#fdba74", "label": "dissimilar_then_similar"},
        }

        for key in target_strategies:
            values = ratio_history[key]
            style = style_map[key]
            ax.fill_between(rounds, values, [0] * len(rounds), color=style["fill"], alpha=0.12, zorder=1)
            ax.plot(rounds, values, color=style["color"], linewidth=2.4, label=style["label"], zorder=3)
            ax.scatter(rounds, values, color=style["color"], s=12, alpha=0.80, zorder=4)

            final_value = values[-1]
            ax.annotate(
                f"{style['label']}: {final_value:.1f}%",
                xy=(rounds[-1], final_value),
                xytext=(-110, 16 - 14 * target_strategies.index(key)),
                textcoords="offset points",
                fontsize=9,
                color="#0f172a",
                bbox=dict(boxstyle="round,pad=0.22", fc="white", ec=style["fill"], alpha=0.95),
                arrowprops=dict(arrowstyle="->", color=style["color"], lw=1.0),
            )

        ax.set_title("Strategy Ratio Over Rounds", fontsize=15, fontweight="bold", color="#0f172a", pad=10)
        ax.set_xlabel("Round", fontsize=11)
        ax.set_ylabel("Cumulative Ratio (%)", fontsize=11)
        ax.set_xticks(rounds)
        ax.set_ylim(0, 102)
        ax.grid(color=grid, linewidth=0.9, alpha=0.75)
        for spine in ax.spines.values():
            spine.set_color("#cbd5e1")
        ax.legend(loc="center right", frameon=True, framealpha=0.92)

        fig.tight_layout()
        fig.savefig(self.metric_dir / "strategy_ratio_curve.png", dpi=320)
        plt.close(fig)

    def plot_token_combined(self):
        """
        Token 组合图：
        - 柱状图：当前轮消耗 Token
        - 折线图：累计 Token（双Y轴）
        - 柱子顶部显示数值
        """
        rounds = list(range(1, len(self.token_history) + 1))
        total_rounds = len(rounds)
        if total_rounds == 0:
            return

        bg = "#f8fafc"
        grid = "#e2e8f0"

        # 计算每轮token & 累计token
        token_per_round = [self.token_history[0]]
        for i in range(1, len(self.token_history)):
            token_per_round.append(self.token_history[i] - self.token_history[i-1])
        token_cumulative = self.token_history

        # 创建画布 + 双Y轴
        fig, ax1 = plt.subplots(figsize=(11, 5.8), facecolor=bg)
        ax1.set_facecolor(bg)

        # 左Y轴：柱状图（当前轮）
        color_bar = '#fb7185'
        fill_bar = '#fda4af'
        bars = ax1.bar(rounds, token_per_round, color=fill_bar, edgecolor=color_bar, linewidth=0.5, alpha=0.55, label='Token per Round', zorder=2)
        ax1.set_xlabel("Round", fontsize=12)
        ax1.set_ylabel("Token per Round", color=color_bar, fontsize=12)
        ax1.tick_params(axis='y', labelcolor=color_bar)
        ax1.set_xticks(rounds)
        ax1.grid(color=grid, linewidth=0.9, alpha=0.75)

        # 柱子顶部显示数字
        for idx, bar in enumerate(bars):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2., height + max(token_per_round) * 0.01,
                     f'{int(height)}', ha='center', va='bottom', fontsize=9, fontweight='bold')

        # 右Y轴：折线图（累计）
        ax2 = ax1.twinx()
        color_line = '#f59e0b'
        ax2.fill_between(rounds, token_cumulative, [0] * len(rounds), color='#fde68a', alpha=0.25, zorder=1)
        ax2.plot(rounds, token_cumulative, color=color_line, marker='D', linewidth=2.5, markersize=6, label='Cumulative Token', zorder=5)
        ax2.set_ylabel("Cumulative Token", color=color_line, fontsize=12)
        ax2.tick_params(axis='y', labelcolor=color_line)

        total_token = token_cumulative[-1]
        ax2.annotate(
            f"Total: {total_token:,}",
            xy=(rounds[-1], token_cumulative[-1]),
            xytext=(-95, 16),
            textcoords="offset points",
            fontsize=10,
            color="#451a03",
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#fcd34d", alpha=0.95),
            arrowprops=dict(arrowstyle="->", color="#f59e0b", lw=1.2),
        )

        # 标题 + 网格
        plt.title("Token Consumption (Bar) + Cumulative (Line)", fontsize=15, fontweight="bold", color="#0f172a", pad=10)
        for spine in ax1.spines.values():
            spine.set_color("#cbd5e1")
        for spine in ax2.spines.values():
            spine.set_color("#cbd5e1")

        handles1, labels1 = ax1.get_legend_handles_labels()
        handles2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(handles1 + handles2, labels1 + labels2, loc="upper left", frameon=True, framealpha=0.92)

        # 保存
        plt.tight_layout()
        plt.savefig(self.metric_dir / "token_combined.png", dpi=320, bbox_inches='tight')
        plt.close()

    async def run(self):
        dataset = MMLUDataset(split='val')

        await self.validate_model_list()

        AgentCls = PRUNE_COMM_REGISTRY.get_class('agents')
        SysMemoryCls = PRUNE_COMM_REGISTRY.get_class('sys_memory')

        agents = []
        for i in range(self.nums_agents):
            model_name = self.model_list[i]
            agents.append(AgentCls(f"Agent_{i+1}", model_name=model_name))

        print("Agent 模型分配:")
        for agent in agents:
            print(f"  - {agent.agent_name}: {agent.model_name}")

        names = [a.agent_name for a in agents]
        self.agent_stability = {name: {"correct": 0, "total": 0} for name in names}
        self.agent_model_map = {a.agent_name: a.model_name for a in agents}
        self.agent_prior_strength = {
            name: self.estimate_model_strength(model)
            for name, model in self.agent_model_map.items()
        }

        sys_memory = SysMemoryCls()
        sys_memory.build_momory_space(names)

        total_correct = 0
        total_tokens = 0

        for idx, record in enumerate(tqdm(dataset)):
            current_round = idx + 1
            if current_round > self.max_rounds:
                break

            round_dir = self.exp_dir / f"round_{current_round}"
            round_dir.mkdir(parents=True, exist_ok=True)

            question = MMLUDataset.record_to_input(record)
            gt = MMLUDataset.record_to_target_answer(record)
            correct = self.extract_option(gt)

            tasks = [a.answer(question) for a in agents]
            results = await asyncio.gather(*tasks)

            agent_results = {}
            token_usage = {}
            first_round_answers = {}

            for a, (ans, hidden, tok) in zip(agents, results):
                agent_results[a.agent_name] = (ans, hidden)
                sys_memory.add_memory(a.agent_name, ans)
                token_usage[a.agent_name] = {"first": tok, "final": 0}
                total_tokens += tok
                first_round_answers[a.agent_name] = {
                    "model": a.model_name,
                    "answer": ans,
                    "option": self.extract_option(ans),
                    "token_count": tok,
                }

            # Update agent stability right after first-round answers,
            # so core-edge partition in hybrid mode can evolve over rounds.
            self.update_agent_stability(names, first_round_answers, correct)

            hiddens = []
            agent_list = list(agent_results.keys())

            for n in agent_list:
                vec = np.array(agent_results[n][1], dtype=np.float32)
                vec = vec / (np.linalg.norm(vec) + 1e-8)
                hiddens.append(vec)

            sim_matrix = cosine_similarity(np.array(hiddens))
            avg_sim = sim_matrix[np.triu_indices(len(sim_matrix), 1)].mean()
            self.sim_history.append(avg_sim)

            hybrid_info = self.decide_hybrid_strategy(first_round_answers, correct)
            self.consensus_ratio_history.append(hybrid_info["consensus_ratio"])

            if self.comm_mode == "hybrid":
                active_strategy = hybrid_info["strategy"]
            elif self.comm_mode in {"similar", "dissimilar", "random"}:
                active_strategy = self.comm_mode
            else:
                active_strategy = "similar"

            ref_map, secondary_ref_map, core_agents, edge_agents = self.build_ref_maps(agent_list, sim_matrix, active_strategy)

            self.round_strategy_history.append({
                "round": current_round,
                "strategy": active_strategy,
                "consensus_option": hybrid_info["consensus_option"],
                "consensus_ratio": hybrid_info["consensus_ratio"],
                "high_threshold": hybrid_info["high_threshold"],
                "mid_threshold": hybrid_info["mid_threshold"],
                "correct_tendency": hybrid_info["correct_tendency"],
                "vote": hybrid_info["vote"],
                "core_agents": core_agents,
                "edge_agents": edge_agents,
            })

            tasks = []
            for a in agents:
                ref = ref_map[a.agent_name]
                mem = sys_memory.read_memory(ref)
                secondary_ref = secondary_ref_map.get(a.agent_name)
                secondary_mem = sys_memory.read_memory(secondary_ref) if secondary_ref else ""

                if secondary_ref:
                    prompt_text = f"""
                            Question: {question['task']}
                            Primary reference from {ref}:
                            {mem}

                            Secondary reference from {secondary_ref}:
                            {secondary_mem}

                            Answer ONLY A/B/C/D
                            """
                else:
                    prompt_text = f"""
                            Question: {question['task']}
                            Reference from {ref}:
                            {mem}

                            Answer ONLY A/B/C/D
                            """

                prompt = {
                    "task": prompt_text
                }
                tasks.append(a.answer(prompt))

            results = await asyncio.gather(*tasks)

            raw, std = [], []
            second_round_answers = {}
            for a, (ans, _, tok) in zip(agents, results):
                raw.append(ans)
                std.append(self.extract_option(ans))
                token_usage[a.agent_name]["final"] = tok
                total_tokens += tok
                second_round_answers[a.agent_name] = {
                    "model": a.model_name,
                    "answer": ans,
                    "option": self.extract_option(ans),
                    "token_count": tok,
                }

            vote = Counter(std)
            pred = vote.most_common(1)[0][0]

            comparison_rows = []
            changed_count = 0
            corrected_count = 0
            wrong_changed_count = 0
            same_count = 0

            for agent_name in names:
                first_option = first_round_answers[agent_name]["option"]
                second_option = second_round_answers[agent_name]["option"]
                changed = first_option != second_option
                correct_after_change = changed and second_option == correct
                wrong_after_change = changed and second_option != correct
                same = not changed

                changed_count += int(changed)
                corrected_count += int(correct_after_change)
                wrong_changed_count += int(wrong_after_change)
                same_count += int(same)

                comparison_rows.append({
                    "round": current_round,
                    "agent": agent_name,
                    "model": first_round_answers[agent_name]["model"],
                    "first_answer": first_round_answers[agent_name]["answer"],
                    "first_option": first_option,
                    "second_answer": second_round_answers[agent_name]["answer"],
                    "second_option": second_option,
                    "changed": int(changed),
                    "correct_after_change": int(correct_after_change),
                    "wrong_after_change": int(wrong_after_change),
                    "same": int(same),
                    "gt": correct,
                })

            total_agents = len(names)
            change_rate = changed_count / total_agents if total_agents else 0.0
            correction_rate = corrected_count / total_agents if total_agents else 0.0
            wrong_rate = wrong_changed_count / total_agents if total_agents else 0.0
            low_efficiency_rate = same_count / total_agents if total_agents else 0.0

            self.answer_change_history.append(change_rate)
            self.correction_history.append(correction_rate)
            self.wrong_change_history.append(wrong_rate)
            self.two_round_same_history.append(low_efficiency_rate)

            two_round_metrics = {
                "answer_change_rate": change_rate,
                "correction_rate": correction_rate,
                "wrong_change_rate": wrong_rate,
                "two_round_same_rate": low_efficiency_rate,
                "changed_count": changed_count,
                "corrected_count": corrected_count,
                "wrong_changed_count": wrong_changed_count,
                "same_count": same_count,
                "total_agents": total_agents,
            }

            self.round_comparisons.extend(comparison_rows)

            if pred == correct:
                total_correct += 1

            acc = total_correct / current_round
            self.acc_history.append(acc)
            self.token_history.append(total_tokens)

            print(f"\n================ ROUND {current_round}/{self.max_rounds} =================")
            print("--------------- FIRST ROUND CHOICE ---------------")
            print(f"FIRST STD : {[first_round_answers[name]['option'] for name in names]}")
            for agent_name in names:
                info = first_round_answers[agent_name]
                print(f"{agent_name} ({info['model']}): {info['option']}")
            print("--------------- SECOND ROUND INFO ----------------")
            print(f"STRATEGY : {active_strategy}")
            print(f"CONSENSUS: {hybrid_info['consensus_option']} ({hybrid_info['consensus_ratio']:.2%})")
            print(f"THRESHOLDS: high={hybrid_info['high_threshold']:.2%}, mid={hybrid_info['mid_threshold']:.2%}")
            if core_agents:
                print(f"CORE AGENTS: {core_agents}")
                print(f"EDGE AGENTS: {edge_agents}")
                core_details = []
                for name in core_agents:
                    model_name = self.agent_model_map.get(name, "unknown")
                    score = self.get_agent_smoothed_score(name)
                    core_details.append(f"{name}({model_name}): {score:.3f}")
                print("CORE SCORES:")
                for item in core_details:
                    print(f"  - {item}")
            print(f"PRED : {pred}")
            print(f"SECOND RAW : {raw}")
            print(f"SECOND STD : {std}")
            print("--------------- TWO-ROUND METRICS ---------------")
            print(f"答案修改率: {change_rate:.2%}")
            print(f"改正率: {correction_rate:.2%}")
            print(f"改错率: {wrong_rate:.2%}")
            print(f"二轮低效率: {low_efficiency_rate:.2%}")
            print(f"GT   : {correct}")
            print(f"ACC  : {acc:.2%}")
            print("===============================================================\n")

            round_trace = {
                "idx": idx,
                "round": current_round,
                "max_rounds": self.max_rounds,
                "question": question["task"],
                "gt": correct,
                "pred": pred,
                "raw": raw,
                "std": std,
                "first_round_answers": first_round_answers,
                "second_round_answers": second_round_answers,
                "two_round_metrics": two_round_metrics,
                "acc": acc,
                "tokens": token_usage,
                "graph": ref_map,
                "secondary_graph": secondary_ref_map,
                "sim_matrix": sim_matrix.tolist(),
                "hybrid_strategy": {
                    "active_strategy": active_strategy,
                    "consensus_option": hybrid_info["consensus_option"],
                    "consensus_ratio": hybrid_info["consensus_ratio"],
                    "high_threshold": hybrid_info["high_threshold"],
                    "mid_threshold": hybrid_info["mid_threshold"],
                    "correct_tendency": hybrid_info["correct_tendency"],
                    "vote": hybrid_info["vote"],
                    "core_agents": core_agents,
                    "edge_agents": edge_agents,
                },
            }

            with open(self.round_json_dir / f"round_{current_round}.json", "w") as f:
                json.dump(round_trace, f, indent=2)

            self.global_trace.append(round_trace)
            self.save_comm_graph(ref_map, round_dir)
            self.save_heatmap(sim_matrix, agent_list, round_dir)

            for n in names:
                sys_memory.clear_memory(n)

        with open(self.trace_file, "w") as f:
            json.dump(self.global_trace, f, indent=2)

        summary_metrics = {
            "total_questions": len(self.global_trace),
            "total_agent_comparisons": len(self.round_comparisons),
            "strategy_distribution": dict(Counter([item["strategy"] for item in self.round_strategy_history])),
            "answer_change_rate": (
                sum(item["changed"] for item in self.round_comparisons) / len(self.round_comparisons)
                if self.round_comparisons else 0.0
            ),
            "correction_rate": (
                sum(item["correct_after_change"] for item in self.round_comparisons) / len(self.round_comparisons)
                if self.round_comparisons else 0.0
            ),
            "wrong_change_rate": (
                sum(item["wrong_after_change"] for item in self.round_comparisons) / len(self.round_comparisons)
                if self.round_comparisons else 0.0
            ),
            "two_round_same_rate": (
                sum(item["same"] for item in self.round_comparisons) / len(self.round_comparisons)
                if self.round_comparisons else 0.0
            ),
        }

        with open(self.metric_dir / "first_second_round_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary_metrics, f, indent=2, ensure_ascii=False)

        with open(self.metric_dir / "first_second_round_comparison.csv", "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "round",
                "agent",
                "model",
                "first_answer",
                "first_option",
                "second_answer",
                "second_option",
                "changed",
                "correct_after_change",
                "wrong_after_change",
                "same",
                "gt",
            ])
            writer.writeheader()
            writer.writerows(self.round_comparisons)

        # 绘图
        self.plot_acc_curve()
        self.plot_token_combined()
        self.plot_rate_curve(self.answer_change_history, "Answer Change Rate Curve", "Change Rate (%)", "answer_change_curve.png", "#7c3aed")
        self.plot_rate_curve(self.correction_history, "Correction Rate Curve", "Correction Rate (%)", "correction_rate_curve.png", "#059669")
        self.plot_rate_curve(self.wrong_change_history, "Wrong Change Rate Curve", "Wrong Rate (%)", "wrong_change_curve.png", "#dc2626")
        self.plot_rate_curve(self.two_round_same_history, "Two-Round Same Rate Curve", "Same Rate (%)", "two_round_same_curve.png", "#d97706")
        self.plot_strategy_ratio_curve()

        print("\n=========== FINAL RESULT ==========")
        print(f"Total Rounds Run: {len(self.acc_history)} / {self.max_rounds}")
        print(f"Final Accuracy  : {total_correct / len(self.acc_history):.2%}" if len(self.acc_history) > 0 else "Accuracy: N/A")
        print(f"Total Tokens    : {total_tokens}")
        print(f"答案修改率      : {summary_metrics['answer_change_rate']:.2%}")
        print(f"改正率          : {summary_metrics['correction_rate']:.2%}")
        print(f"改错率          : {summary_metrics['wrong_change_rate']:.2%}")
        print(f"二轮低效率      : {summary_metrics['two_round_same_rate']:.2%}")
        print(f"Charts saved to : {self.metric_dir}")
        print("===================================")

if __name__ == "__main__":
    wf = Workflow()
    asyncio.run(wf.run())

