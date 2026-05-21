from system.registry import PRUNE_COMM_REGISTRY
from llm.openai_chat_base import OpenAIChatBase


@PRUNE_COMM_REGISTRY.register('qwen1.5-14b-chat')
class Qwen1_5_14BChat(OpenAIChatBase):
    def __init__(self, model_name: str = 'qwen1.5-14b-chat'):
        super().__init__(model_name)
