from harness.llm.base import LLMProvider
from harness.llm.mock import MockLLM
from harness.models import Message


def test_mock_llm_returns_scripted_response():
    responses = ['{"tool": "read_file", "args": {"path": "foo.py"}}']
    llm = MockLLM(responses)
    messages = [Message(role="user", content="read foo.py")]
    result = llm.complete(messages)
    assert result == responses[0]


def test_mock_llm_returns_sequential_responses():
    responses = [
        '{"tool": "read_file", "args": {"path": "foo.py"}}',
        '{"tool": "write_file", "args": {"path": "foo.py", "content": "print(1)"}}',
        '{"tool": "task_complete", "args": {"summary": "done"}}',
    ]
    llm = MockLLM(responses)
    messages = [Message(role="user", content="fix foo.py")]
    assert llm.complete(messages) == responses[0]
    assert llm.complete(messages) == responses[1]
    assert llm.complete(messages) == responses[2]


def test_mock_llm_raises_when_script_exhausted():
    import pytest
    llm = MockLLM(["only one response"])
    llm.complete([Message(role="user", content="task")])
    with pytest.raises(IndexError, match="Script exhausted"):
        llm.complete([Message(role="user", content="task")])


def test_mock_llm_is_llm_provider():
    llm = MockLLM(["response"])
    assert isinstance(llm, LLMProvider)
