# tests/test_llm_openai.py
import pytest
from unittest.mock import patch, MagicMock
from harness.llm.openai import OpenAILLM
from harness.models import Message


def test_openai_llm_complete():
    llm = OpenAILLM(api_key="sk-fake", model="gpt-4o")
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"tool": "task_complete", "args": {"summary": "done"}}'

    with patch.object(llm._client.chat.completions, "create", return_value=mock_response):
        messages = [Message(role="user", content="test")]
        result = llm.complete(messages)
    assert result == '{"tool": "task_complete", "args": {"summary": "done"}}'


def test_openai_llm_is_llm_provider():
    from harness.llm.base import LLMProvider
    llm = OpenAILLM(api_key="sk-fake", model="gpt-4o")
    assert isinstance(llm, LLMProvider)


def test_openai_llm_raises_on_api_error():
    from harness.llm.base import LLMError
    llm = OpenAILLM(api_key="sk-fake", model="gpt-4o")
    with patch.object(llm._client.chat.completions, "create", side_effect=Exception("API error")):
        with pytest.raises(LLMError, match="API error"):
            llm.complete([Message(role="user", content="test")])
