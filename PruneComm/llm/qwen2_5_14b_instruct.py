from system.registry import PRUNE_COMM_REGISTRY
from llm.openai_chat_base import OpenAIChatBase


@PRUNE_COMM_REGISTRY.register('qwen2.5-14b-instruct')
class Qwen2_5_14BInstructChat(OpenAIChatBase):
    def __init__(self, model_name: str = 'qwen2.5-14b-instruct'):
        super().__init__(model_name)
