import asyncio
# 注意：在异步环境中，通常不再需要手动设置 policy，由启动器（uvicorn）决定
# asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from typing import List, Union, Optional, Dict, Any
from tenacity import retry, wait_random_exponential, stop_after_attempt
from dotenv import load_dotenv
import os
from openai import AsyncOpenAI
from system.registry import PRUNE_COMM_REGISTRY
from llm.llm import LLM

load_dotenv(dotenv_path="model.env")

MINE_BASE_URL = os.getenv("BASE_URL")
MINE_API_KEY = os.getenv("API_KEY")


def _normalize_content(content) -> str:
    if content is None:
        return "[EMPTY_RESPONSE]"

    if isinstance(content, str):
        text = content.strip()
        return text if text else "[EMPTY_RESPONSE]"

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") or ""
                if text:
                    parts.append(str(text).strip())
            else:
                parts.append(str(item).strip())
        merged = " ".join([p for p in parts if p])
        return merged if merged else "[EMPTY_RESPONSE]"

    text = str(content).strip()
    return text if text else "[EMPTY_RESPONSE]"

@retry(wait=wait_random_exponential(max=300), stop=stop_after_attempt(3))
async def achat(
    model: str,
    msg: List[Dict],
    max_tokens: int,
    temperature: float,
    num_comps: int
):
    client = AsyncOpenAI(base_url=MINE_BASE_URL, api_key=MINE_API_KEY)
    chat_completion = await client.chat.completions.create(
        messages=msg,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        n=num_comps,
        extra_body={"enable_thinking": False}
    )
    answer = _normalize_content(chat_completion.choices[0].message.content)
    total_tokens = chat_completion.usage.total_tokens
    return answer, total_tokens

@retry(wait=wait_random_exponential(max=300), stop=stop_after_attempt(3))
async def aembedding(text: str):
    safe_text = _normalize_content(text)
    client = AsyncOpenAI(base_url=MINE_BASE_URL, api_key=MINE_API_KEY)
    resp = await client.embeddings.create(
        input=safe_text,
        model="text-embedding-v2"
    )
    embedding = resp.data[0].embedding
    total_tokens = resp.usage.total_tokens
    return embedding, total_tokens

@PRUNE_COMM_REGISTRY.register('qwen-plus')
class QwenChat(LLM):
    def __init__(self, model_name: str):
        super().__init__(model_name)

    async def agen(
        self,
        messages: Union[str, List[Dict]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        num_comps: Optional[int] = None,
    ):
        max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS
        temperature = temperature or self.DEFAULT_TEMPERATURE
        num_comps = num_comps or self.DEFAULT_NUM_COMPLETIONS

        if isinstance(messages, str):
            messages = [{'role': 'user', 'content': messages}]

        return await achat(
            self.model_name,
            messages,
            max_tokens,
            temperature,
            num_comps
        )

    # 核心修改：将 gen 变为异步函数，打通调用链
    async def gen(
        self,
        messages: Union[str, List[Dict]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        num_comps: Optional[int] = None,
    ):
        # 1. 直接 await 聊天接口，不再使用 loop.run_until_complete
        answer, chat_tokens = await self.agen(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            num_comps=num_comps
        )
        
        # 2. 直接 await Embedding 接口
        # 移除 asyncio.run(...)，因为它会尝试开启一个新循环导致冲突
        hidden_states, embed_tokens = await aembedding(answer)
        
        total_tokens = chat_tokens + embed_tokens
        
        return answer, hidden_states, total_tokens
