import asyncio
import os
import sys
import json
import re
import numpy as np
from datetime import datetime
from pathlib import Path
from collections import Counter
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

sys.path.append(str(Path(__file__).parent.parent))

from data.dataset.mmlu_dataset import MMLUDataset
from system.registry import PRUNE_COMM_REGISTRY
import agent.agent
import llm.qwen_chat
import memory.sys_memory

load_dotenv()

@PRUNE_COMM_REGISTRY.register('workflow')
class Workflow:
    def __init__(self, nums_agents=None):
        self.llm_name = os.getenv("LLM_NAME", "qwen-plus")
        self.nums_agents = nums_agents or int(os.getenv("NUMS_AGENTS", 3))
        self.result_dir = Path("exp/result")
        self.result_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.result_file = self.result_dir / f"AgentExp{self.nums_agents}_{timestamp}.txt"
        
        with open(self.result_file, "w", encoding="utf-8") as f:
            f.write(f"实验开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

    def extract_option(self, text):
        if not text: return ""
        match = re.search(r'\b([A-D])\b', text.upper())
        if match:
            return match.group(1)
        clean_text = re.sub(r'[^A-D]', '', text.upper())
        return clean_text[0] if clean_text else text.strip()[:1].upper()

    def save_round_result(self, idx, question, ref_agent_dict, final_answers, 
                          vote_result, system_answer, correct_answer, current_acc,
                          token_usage):
        with open(self.result_file, "a", encoding="utf-8") as f:
            f.write(f"【第 {idx+1} 轮结果】\n")
            f.write(f"1. 题目：{question['task']}\n")  
            f.write("2. 每个Agent参考的记忆对象：\n")
            for agent_name, ref_agent in ref_agent_dict.items():
                f.write(f"   - {agent_name} → 参考 {ref_agent}\n")
            f.write("3. 每个Agent Token消耗详情：\n")
            for agent_name, token_info in token_usage.items():
                f.write(f"   - {agent_name}：首次回答 {token_info['first']} | 最终回答 {token_info['final']} | 总计 {token_info['first'] + token_info['final']}\n")
            f.write(f"4. 所有智能体最终答案：{final_answers}\n")
            f.write(f"5. 投票结果(标准化)：{dict(vote_result)}\n")
            f.write(f"6. 系统最终输出：{system_answer}\n")
            f.write(f"7. 正确答案：{correct_answer}\n")
            f.write(f"8. 当前准确率：{current_acc:.2%}\n")
            f.write("\n" + "=" * 80 + "\n\n")

    async def run(self):
        val_dataset = MMLUDataset(split='val')
        print(f"验证集总量: {len(val_dataset)}")
        
        AgentCls = PRUNE_COMM_REGISTRY.get_class('agents')
        SysMemoryCls = PRUNE_COMM_REGISTRY.get_class('sys_memory')

        agents = [AgentCls(f"Agent_{i+1}") for i in range(self.nums_agents)]
        agents_names = [a.agent_name for a in agents]
        sys_memory = SysMemoryCls()
        sys_memory.build_momory_space(agents_names)

        total_correct = 0

        for idx, record in enumerate(val_dataset):
            question = MMLUDataset.record_to_input(record)
            correct_answer = self.extract_option(MMLUDataset.record_to_target_answer(record))
            
            step_data = {
                "idx": idx,
                "question": question['task'],
                "logs": [],
                "matrix": [],
                "accuracy": 0,
                "sys_ans": "",
                "correct_ans": correct_answer,
                "token_usage": {},
                "vote_details": {},
                "stats": ""
            }

            agent_results = {}
            token_usage = {}

            for agent in agents:
                ans, hidden, tokens = await agent.answer(question)
                agent_results[agent.agent_name] = (ans, hidden)
                sys_memory.add_memory(agent.agent_name, f"回答：{ans}")
                token_usage[agent.agent_name] = {"first": tokens, "final": 0}
                
                step_data["logs"].append({
                    "agent": agent.agent_name,
                    "round": 1,
                    "content": ans
                })

            hiddens_list = [np.array(agent_results[name][1]).flatten() for name in agents_names]
            hiddens_np = np.array(hiddens_list)
            norm = np.linalg.norm(hiddens_np, axis=1, keepdims=True)
            norm[norm == 0] = 1e-8
            sim_matrix = cosine_similarity(hiddens_np / norm)
            step_data["matrix"] = sim_matrix.tolist()

            most_irrelevant_map = {}
            match_stats = "最不相关匹配结果：\n"
            for i, name_i in enumerate(agents_names):
                sims = sim_matrix[i]
                mask = np.ones(len(sims), dtype=bool)
                mask[i] = False
                min_idx = np.where(sims == np.min(sims[mask]))[0][0]
                most_irrelevant_map[name_i] = agents_names[min_idx]
                match_stats += f"  {name_i} → {agents_names[min_idx]} (Sim: {sims[min_idx]:.4f})\n"

            # --- Round 2 ---
            final_answers_raw = []
            for agent in agents:
                other = most_irrelevant_map[agent.agent_name]
                other_mem = sys_memory.read_memory(other)
                ref_prompt = {
                    "task": f"原始问题：{question['task']}\n"
                            f"你需要参考【异议者 {other} 的回答】：\n{other_mem}\n"
                            f"请给出最终答案选项。"
                }
                final_ans, _, tokens = await agent.answer(ref_prompt)
                final_answers_raw.append(final_ans.strip())
                token_usage[agent.agent_name]["final"] = tokens
                
                step_data["logs"].append({
                    "agent": agent.agent_name,
                    "round": 2,
                    "content": f"参考 {other} 后回答：{final_ans}"
                })

            standardized_answers = [self.extract_option(a) for a in final_answers_raw]
            vote = Counter(standardized_answers)
            sys_ans = vote.most_common(1)[0][0]
            
            if sys_ans == correct_answer:
                total_correct += 1
            current_acc = total_correct / (idx + 1)
            
            stats_text = (
                f"{match_stats}"
                f"投票统计: {dict(vote)}\n"
                f"Token 消耗:\n" + 
                "\n".join([f"  {k}: R1({v['first']}) + R2({v['final']}) = {v['first']+v['final']}" 
                          for k,v in token_usage.items()])
            )

            step_data["accuracy"] = current_acc
            step_data["sys_ans"] = sys_ans
            step_data["token_usage"] = token_usage
            step_data["vote_details"] = dict(vote)
            step_data["stats"] = stats_text
            step_data["ref_agent_dict"] = most_irrelevant_map

            print(f"\n[Round {idx+1}] 结果：")
            print(f"标准化答案流: {standardized_answers}")
            print(f"系统预测: {sys_ans} | 正确答案: {correct_answer}")
            print(f"当前准确率: {current_acc:.2%}")

            self.save_round_result(
                idx=idx, question=question, ref_agent_dict=most_irrelevant_map,
                final_answers=final_answers_raw, vote_result=vote,
                system_answer=sys_ans, correct_answer=correct_answer,
                current_acc=current_acc, token_usage=token_usage
            )

            for name in agents_names: sys_memory.clear_memory(name)
            yield step_data

