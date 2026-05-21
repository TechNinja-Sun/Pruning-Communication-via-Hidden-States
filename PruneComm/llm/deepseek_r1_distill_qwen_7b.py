from system.registry import PRUNE_COMM_REGISTRY
from llm.openai_chat_base import OpenAIChatBase


@PRUNE_COMM_REGISTRY.register('deepseek-r1-distill-qwen-7b')
class DeepSeekR1DistillQwen7BChat(OpenAIChatBase):
    def __init__(self, model_name: str = 'deepseek-r1-distill-qwen-7b'):
        super().__init__(model_name)
