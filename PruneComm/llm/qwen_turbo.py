from system.registry import PRUNE_COMM_REGISTRY
from llm.openai_chat_base import OpenAIChatBase


@PRUNE_COMM_REGISTRY.register('qwen-turbo')
class QwenTurboChat(OpenAIChatBase):
    def __init__(self, model_name: str = 'qwen-turbo'):
        super().__init__(model_name)
