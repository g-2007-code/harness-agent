# harness/llm/openai.py
from typing import List
from openai import OpenAI
from harness.llm.base import LLMProvider, LLMError
from harness.models import Message


class OpenAILLM(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str = ""):
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = OpenAI(**kwargs)
        self._model = model

    def complete(self, messages: List[Message]) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
            )
            return response.choices[0].message.content
        except Exception as e:
            raise LLMError(str(e))
