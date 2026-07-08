from abc import ABC, abstractmethod
from typing import List
from harness.models import Message


class LLMError(Exception):
    pass


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, messages: List[Message]) -> str:
        pass
