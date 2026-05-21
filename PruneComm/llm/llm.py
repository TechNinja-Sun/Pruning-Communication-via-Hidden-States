from typing import List, Union, Optional, Dict, Any
from tenacity import retry, wait_random_exponential, stop_after_attempt
from dotenv import load_dotenv
import os
from openai import AsyncOpenAI
from system.registry import PRUNE_COMM_REGISTRY
from abc import abstractmethod

load_dotenv(dotenv_path="model.env")

DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", 1024))
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", 0.1))
DEFAULT_NUM_COMPLETIONS = int(os.getenv("DEFAULT_NUM_COMPLETIONS", 1))

@PRUNE_COMM_REGISTRY.register('llm')
class LLM:
    DEFAULT_MAX_TOKENS = DEFAULT_MAX_TOKENS
    DEFAULT_TEMPERATURE = DEFAULT_TEMPERATURE
    DEFAULT_NUM_COMPLETIONS = DEFAULT_NUM_COMPLETIONS

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.DEFAULT_MAX_TOKENS = DEFAULT_MAX_TOKENS
        self.DEFAULT_TEMPERATURE = DEFAULT_TEMPERATURE 
        self.DEFAULT_NUM_COMPLETIONS = DEFAULT_NUM_COMPLETIONS

    @abstractmethod
    async def agen(self, **kwargs):
        pass

    @abstractmethod
    def gen(self, **kwargs):
        pass