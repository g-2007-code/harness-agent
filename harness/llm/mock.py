from typing import List
from harness.llm.base import LLMProvider
from harness.models import Message


class MockLLM(LLMProvider):
    def __init__(self, responses: List[str]):
        self._responses = list(responses)
        self._index = 0

    def complete(self, messages: List[Message]) -> str:
        if self._index >= len(self._responses):
            raise IndexError("Script exhausted: no more mock responses")
        response = self._responses[self._index]
        self._index += 1
        return response
