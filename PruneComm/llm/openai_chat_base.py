from typing import List, Union, Optional, Dict

from tenacity import retry, wait_random_exponential, stop_after_attempt
from dotenv import load_dotenv
import os
from openai import AsyncOpenAI

from llm.llm import LLM

load_dotenv(dotenv_path="model.env")

MINE_BASE_URL = os.getenv("BASE_URL")
MINE_API_KEY = os.getenv("API_KEY")


def _normalize_content(content) -> str:
    """Normalize model output content into a non-empty plain string."""
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
    num_comps: int,
):
    client = AsyncOpenAI(base_url=MINE_BASE_URL, api_key=MINE_API_KEY)
    chat_completion = await client.chat.completions.create(
        messages=msg,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        n=num_comps,
        extra_body={"enable_thinking": False},
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
        model="text-embedding-v2",
    )
    embedding = resp.data[0].embedding
    total_tokens = resp.usage.total_tokens
    return embedding, total_tokens


class OpenAIChatBase(LLM):
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
            messages = [{"role": "user", "content": messages}]

        return await achat(
            self.model_name,
            messages,
            max_tokens,
            temperature,
            num_comps,
        )

    async def gen(
        self,
        messages: Union[str, List[Dict]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        num_comps: Optional[int] = None,
    ):
        answer, chat_tokens = await self.agen(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            num_comps=num_comps,
        )

        hidden_states, embed_tokens = await aembedding(answer)
        total_tokens = chat_tokens + embed_tokens

        return answer, hidden_states, total_tokens
