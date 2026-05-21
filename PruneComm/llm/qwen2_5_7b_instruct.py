from system.registry import PRUNE_COMM_REGISTRY
from llm.openai_chat_base import OpenAIChatBase


@PRUNE_COMM_REGISTRY.register('qwen2.5-7b-instruct')
class Qwen2_5_7BInstructChat(OpenAIChatBase):
    def __init__(self, model_name: str = 'qwen2.5-7b-instruct'):
        super().__init__(model_name)
