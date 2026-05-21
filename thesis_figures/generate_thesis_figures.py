import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle, FancyArrowPatch
import numpy as np


OUT_DIR = Path(__file__).parent


def set_style():
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = [
        "SimSun",
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 120


def draw_box(ax, x, y, w, h, text, fc="#ffffff", ec="#334155", lw=1.2, fs=10, weight="normal", ha="center"):
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.02",
        linewidth=lw,
        edgecolor=ec,
        facecolor=fc,
    )
    ax.add_patch(box)
    ax.text(x + w / 2 if ha == "center" else x + 0.02, y + h / 2, text, ha=ha, va="center", fontsize=fs, weight=weight, color="#0f172a")
    return box


def fig1_indicator_system():
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Root
    draw_box(ax, 0.40, 0.90, 0.20, 0.07, "课题评价指标体系", fc="#e2e8f0", ec="#1e293b", lw=2.0, fs=13, weight="bold")

    # Branch heads
    heads = [
        (0.08, 0.70, 0.24, 0.08, "准确率\n（核心性能指标）", "#dbeafe"),
        (0.38, 0.70, 0.24, 0.08, "Token 消耗\n（核心成本指标）", "#dcfce7"),
        (0.68, 0.70, 0.24, 0.08, "通信结构特征\n（辅助分析指标）", "#fef3c7"),
    ]

    for x, y, w, h, label, color in heads:
        draw_box(ax, x, y, w, h, label, fc=color, ec="#334155", lw=2.0, fs=11, weight="bold")

    # Thick root lines
    root_bottom = (0.50, 0.90)
    for x, y, w, h, _, _ in heads:
        ax.plot([root_bottom[0], x + w / 2], [root_bottom[1], y + h], color="#475569", linewidth=2.2)

    # Sub-nodes for accuracy
    acc_nodes = [
        (0.05, 0.49, 0.30, 0.08, "独立作答准确率\n（第一轮预测正确数 / 总样本数）"),
        (0.05, 0.37, 0.30, 0.08, "参考重答准确率\n（第二轮预测正确数 / 总样本数）"),
        (0.05, 0.25, 0.30, 0.08, "准确率提升幅度\n= 参考重答准确率 - 独立作答准确率"),
    ]
    for x, y, w, h, label in acc_nodes:
        draw_box(ax, x, y, w, h, label, fc="#eff6ff", ec="#3b82f6", lw=1.0, fs=9)
        ax.plot([0.20, x + w / 2], [0.70, y + h], color="#60a5fa", linewidth=1.2)

    # Sub-nodes for token
    tok_nodes = [
        (0.35, 0.49, 0.30, 0.08, "单智能体推理 Token 消耗\n（各 Agent 第一轮+第二轮）"),
        (0.35, 0.37, 0.30, 0.08, "通信过程 Token 消耗\n（参考信息拼接与交互带来的增量）"),
        (0.35, 0.25, 0.30, 0.08, "系统总 Token 消耗\n= 全部智能体总和"),
    ]
    for x, y, w, h, label in tok_nodes:
        draw_box(ax, x, y, w, h, label, fc="#f0fdf4", ec="#22c55e", lw=1.0, fs=9)
        ax.plot([0.50, x + w / 2], [0.70, y + h], color="#4ade80", linewidth=1.2)

    # Sub-nodes for communication
    comm_nodes = [
        (0.65, 0.49, 0.30, 0.08, "通信链路数量\n（每轮参考映射形成的边数）"),
        (0.65, 0.37, 0.30, 0.08, "冗余通信比例\n= 冗余通信 Token 量 / 总通信 Token 量"),
        (0.65, 0.25, 0.30, 0.08, "参考映射合理性\n（映射与策略目标一致程度）"),
    ]
    for x, y, w, h, label in comm_nodes:
        draw_box(ax, x, y, w, h, label, fc="#fffbeb", ec="#f59e0b", lw=1.0, fs=9)
        ax.plot([0.80, x + w / 2], [0.70, y + h], color="#fbbf24", linewidth=1.2)

    fig.suptitle("图 1 课题评价指标体系示意图", fontsize=16, weight="bold", y=0.98)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "图1_课题评价指标体系示意图.png", dpi=320)
    plt.close(fig)


def fig2_parameter_ui():
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Header
    draw_box(ax, 0.03, 0.92, 0.94, 0.06, "系统参数配置界面", fc="#e2e8f0", ec="#1e293b", lw=1.8, fs=14, weight="bold")

    # Four modules
    modules = [
        (0.05, 0.56, 0.42, 0.30, "智能体配置模块"),
        (0.53, 0.56, 0.42, 0.30, "通信策略配置模块"),
        (0.05, 0.18, 0.42, 0.30, "任务配置模块"),
        (0.53, 0.18, 0.42, 0.30, "操作按钮模块"),
    ]
    for x, y, w, h, title in modules:
        draw_box(ax, x, y, w, h, title, fc="#f8fafc", ec="#334155", lw=1.3, fs=11, weight="bold")

    def input_row(x, y, label, value):
        ax.text(x, y, label, ha="left", va="center", fontsize=9.5, color="#334155")
        draw_box(ax, x + 0.20, y - 0.025, 0.18, 0.05, value, fc="#ffffff", ec="#94a3b8", lw=1.0, fs=9)

    # Agent config content
    input_row(0.08, 0.75, "智能体数量（1-10）", "4")
    input_row(0.08, 0.67, "智能体模型选择", "qwen-plus / GPT-3.5 / Llama2")

    # Comm config content
    input_row(0.56, 0.75, "通信策略选择", "反相似 / 相似 / 随机")
    input_row(0.56, 0.67, "冗余阈值", "0.85")
    input_row(0.56, 0.61, "剪枝频率", "每轮一次")

    # Task config content
    input_row(0.08, 0.37, "数据集选择", "教育类/常识类多选问答")
    input_row(0.08, 0.29, "实验轮次", "10")

    # Buttons
    draw_box(ax, 0.58, 0.34, 0.12, 0.07, "确认配置", fc="#dbeafe", ec="#3b82f6", lw=1.2, fs=10, weight="bold")
    draw_box(ax, 0.73, 0.34, 0.12, 0.07, "重置参数", fc="#fef3c7", ec="#f59e0b", lw=1.2, fs=10, weight="bold")
    draw_box(ax, 0.66, 0.24, 0.16, 0.07, "启动实验", fc="#dcfce7", ec="#16a34a", lw=1.4, fs=11, weight="bold")

    fig.suptitle("图 2 系统参数配置界面示意图", fontsize=16, weight="bold", y=0.98)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "图2_系统参数配置界面示意图.png", dpi=320)
    plt.close(fig)


def fig3_statistics_dashboard():
    # Example data consistent with requested chart semantics
    strategies = ["反相似", "相似", "随机"]
    acc_values = [78.6, 73.2, 69.8]

    rounds = np.arange(1, 11)
    token_dissim = np.array([7600, 7800, 8050, 8200, 8450, 8600, 8850, 9000, 9200, 9450])
    token_sim = np.array([7350, 7520, 7700, 7850, 8000, 8140, 8280, 8420, 8560, 8700])
    token_rand = np.array([7100, 7300, 7490, 7700, 7910, 8100, 8290, 8500, 8690, 8880])

    pie_vals = [68, 32]
    pie_labels = ["有效通信链路占比", "冗余通信链路占比"]

    scatter_x = np.array([7100, 7300, 7490, 7700, 7910, 8100, 8290, 8500, 8690, 8880,
                          7350, 7520, 7700, 7850, 8000, 8140, 8280, 8420, 8560, 8700,
                          7600, 7800, 8050, 8200, 8450, 8600, 8850, 9000, 9200, 9450])
    scatter_y = np.array([67.5, 68.0, 68.4, 68.9, 69.1, 69.4, 69.6, 69.9, 70.1, 70.3,
                          70.4, 70.7, 71.0, 71.3, 71.5, 71.8, 72.0, 72.3, 72.5, 72.8,
                          73.0, 73.4, 73.8, 74.2, 74.7, 75.2, 75.6, 76.1, 76.8, 77.4])

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("图 3 实验统计图表示例", fontsize=16, weight="bold", y=0.98)

    # 3-1 bar
    ax = axes[0, 0]
    bars = ax.bar(strategies, acc_values, color=["#60a5fa", "#34d399", "#fbbf24"], edgecolor="#334155")
    ax.set_title("图 3-1 不同通信策略准确率对比图")
    ax.set_ylabel("准确率（%）")
    ax.set_ylim(0, 100)
    ax.grid(axis="y", alpha=0.25)
    for bar, val in zip(bars, acc_values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 1.2, f"{val:.1f}%", ha="center", va="bottom", fontsize=9)

    # 3-2 line
    ax = axes[0, 1]
    ax.plot(rounds, token_dissim, marker="o", linewidth=2.0, color="#ef4444", label="反相似")
    ax.plot(rounds, token_sim, marker="o", linewidth=2.0, color="#3b82f6", label="相似")
    ax.plot(rounds, token_rand, marker="o", linewidth=2.0, color="#10b981", label="随机")
    ax.set_title("图 3-2 不同通信策略 Token 消耗趋势图")
    ax.set_xlabel("实验轮次（1-10 轮）")
    ax.set_ylabel("Token 消耗总量")
    ax.grid(alpha=0.25)
    ax.legend(frameon=True)

    # 3-3 pie
    ax = axes[1, 0]
    colors = ["#22c55e", "#f97316"]
    wedges, texts, autotexts = ax.pie(
        pie_vals,
        labels=pie_labels,
        autopct="%.1f%%",
        startangle=90,
        colors=colors,
        textprops={"fontsize": 9},
    )
    for t in autotexts:
        t.set_color("#0f172a")
        t.set_weight("bold")
    ax.set_title("图 3-3 通信结构特征分析图")

    # 3-4 scatter
    ax = axes[1, 1]
    ax.scatter(scatter_x, scatter_y, color="#8b5cf6", alpha=0.75, edgecolor="white", linewidth=0.4)
    coef = np.polyfit(scatter_x, scatter_y, 1)
    fit_x = np.linspace(scatter_x.min(), scatter_x.max(), 120)
    fit_y = coef[0] * fit_x + coef[1]
    ax.plot(fit_x, fit_y, color="#1f2937", linewidth=1.8, linestyle="--", label="趋势线")
    ax.set_title("图 3-4 准确率与 Token 消耗相关性图")
    ax.set_xlabel("Token 消耗总量")
    ax.set_ylabel("参考重答准确率（%）")
    ax.grid(alpha=0.25)
    ax.legend()

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(OUT_DIR / "图3_实验统计图表示例.png", dpi=320)
    plt.close(fig)


def fig4_realtime_ui():
    fig, ax = plt.subplots(figsize=(14, 8.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Top header
    draw_box(ax, 0.02, 0.92, 0.96, 0.065, "多智能体协同推理实时可视化界面", fc="#e2e8f0", ec="#1e293b", lw=1.8, fs=14, weight="bold")
    ax.text(0.03, 0.895, "当前轮次：Round 6/10", fontsize=10, color="#334155")
    ax.text(0.82, 0.895, "实时时间：14:32:18", fontsize=10, color="#334155")

    # Layout regions
    draw_box(ax, 0.02, 0.08, 0.30, 0.80, "智能体状态区", fc="#f8fafc", ec="#334155", lw=1.2, fs=11, weight="bold")
    draw_box(ax, 0.34, 0.08, 0.38, 0.80, "通信动态区", fc="#f8fafc", ec="#334155", lw=1.2, fs=11, weight="bold")
    draw_box(ax, 0.74, 0.08, 0.24, 0.80, "数据监控区", fc="#f8fafc", ec="#334155", lw=1.2, fs=11, weight="bold")

    # Left cards (1-6 sample)
    states = [
        ("Agent 1", "独立作答中", "1260", "A", "-", "#fde68a"),
        ("Agent 2", "参考重答中", "1420", "C", "C", "#fef08a"),
        ("Agent 3", "完成", "1508", "B", "C", "#bbf7d0"),
        ("Agent 4", "完成", "1481", "C", "C", "#bbf7d0"),
        ("Agent 5", "参考重答中", "1372", "D", "C", "#fef08a"),
        ("Agent 6", "完成", "1536", "C", "C", "#bbf7d0"),
    ]

    y0 = 0.81
    for i, (aid, st, tok, pre, fin, col) in enumerate(states):
        y = y0 - i * 0.12
        draw_box(ax, 0.035, y - 0.08, 0.27, 0.09, "", fc=col, ec="#94a3b8", lw=0.9)
        ax.text(0.045, y - 0.03, f"{aid} | 状态: {st}", fontsize=8.7, color="#0f172a")
        ax.text(0.045, y - 0.06, f"Token: {tok} | 初步答案: {pre} | 最终答案: {fin}", fontsize=8.2, color="#334155")

    # Middle node-link graph
    center_points = {
        "1": (0.44, 0.72),
        "2": (0.58, 0.75),
        "3": (0.66, 0.62),
        "4": (0.61, 0.44),
        "5": (0.47, 0.40),
        "6": (0.39, 0.55),
    }

    # Strategy color legend
    ax.text(0.36, 0.84, "链路颜色：红=反相似，蓝=相似", fontsize=9, color="#334155")

    edges = [
        ("1", "4", "#ef4444"),
        ("2", "3", "#3b82f6"),
        ("3", "2", "#ef4444"),
        ("4", "5", "#3b82f6"),
        ("5", "3", "#ef4444"),
        ("6", "4", "#3b82f6"),
    ]

    for s, t, c in edges:
        x1, y1 = center_points[s]
        x2, y2 = center_points[t]
        arr = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="->", mutation_scale=12, linewidth=1.7, color=c, alpha=0.9)
        ax.add_patch(arr)

    for nid, (x, y) in center_points.items():
        circ = Circle((x, y), 0.025, facecolor="#dbeafe", edgecolor="#1d4ed8", linewidth=1.3)
        ax.add_patch(circ)
        ax.text(x, y, nid, ha="center", va="center", fontsize=10, weight="bold", color="#1e3a8a")

    # Right monitoring data
    draw_box(ax, 0.765, 0.76, 0.19, 0.10, "当前准确率\n74.5%", fc="#ecfeff", ec="#06b6d4", lw=1.1, fs=11, weight="bold")
    draw_box(ax, 0.765, 0.62, 0.19, 0.10, "累计 Token 消耗\n96,420", fc="#fff7ed", ec="#f97316", lw=1.1, fs=11, weight="bold")
    draw_box(ax, 0.765, 0.48, 0.19, 0.10, "冗余通信比例\n31.2%", fc="#fef2f2", ec="#ef4444", lw=1.1, fs=11, weight="bold")

    # Progress bars and mini line
    ax.text(0.765, 0.41, "准确率进度", fontsize=9.5, color="#334155")
    ax.add_patch(Rectangle((0.765, 0.385), 0.19, 0.018, facecolor="#e2e8f0", edgecolor="#cbd5e1"))
    ax.add_patch(Rectangle((0.765, 0.385), 0.1415, 0.018, facecolor="#22c55e", edgecolor="#16a34a"))

    ax.text(0.765, 0.34, "Token 增长小折线", fontsize=9.5, color="#334155")
    x0, y0 = 0.77, 0.24
    mini_x = np.linspace(x0, x0 + 0.175, 10)
    mini_y = np.array([0.00, 0.01, 0.025, 0.03, 0.045, 0.05, 0.06, 0.07, 0.075, 0.09]) + y0
    ax.plot(mini_x, mini_y, color="#f59e0b", linewidth=1.8)
    ax.scatter(mini_x, mini_y, color="#f59e0b", s=10)
    ax.add_patch(Rectangle((0.765, 0.225), 0.19, 0.12, fill=False, edgecolor="#cbd5e1", linewidth=0.9))

    fig.suptitle("图 4 系统实时可视化界面示意图", fontsize=16, weight="bold", y=0.985)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "图4_系统实时可视化界面示意图.png", dpi=320)
    plt.close(fig)


def main():
    set_style()
    fig1_indicator_system()
    fig2_parameter_ui()
    fig3_statistics_dashboard()
    fig4_realtime_ui()
    print("Generated 4 figures in:", OUT_DIR)


if __name__ == "__main__":
    main()
