from system.registry import PRUNE_COMM_REGISTRY
import os

@PRUNE_COMM_REGISTRY.register('agents')
class AgentCls:
    def __init__(self, agent_name: str, model_name: str = None):
        self.agent_name = agent_name
        self.model_name = model_name

        try:
            AgentCls = PRUNE_COMM_REGISTRY.get_class(self.model_name)
        except KeyError:
            AgentCls = PRUNE_COMM_REGISTRY.get_class('qwen-plus')
            self.model_name = "qwen-plus"

        self.llm = AgentCls(self.model_name)

    async def answer(self, question):
        prompt = question["task"] if isinstance(question, dict) else question
        
        answer, hidden_states, token_count = await self.llm.gen(prompt)
        
        print(f"[{self.agent_name}] 回答已生成 (model={self.model_name})")
        print(f"[{self.agent_name}] 向量片段: {hidden_states[:5]}...")
        print(f"[{self.agent_name}] Token 消耗: {token_count}")
        
        return answer, hidden_states, token_count