# tests/test_loop.py
import pytest
from harness.loop import AgentLoop
from harness.llm.base import LLMProvider, LLMError
from harness.llm.mock import MockLLM
from harness.tools import ToolRegistry
from harness.tools.file_tools import read_file, write_file
from harness.tools.shell import run_shell
from harness.governance import Governance
from harness.feedback import collect
from harness.memory import Memory
from harness.config import load_config


class FlakyLLM(LLMProvider):
    """LLM that raises LLMError for the first ``fail_count`` calls then succeeds."""

    def __init__(self, response: str, fail_count: int):
        self._response = response
        self._fail_count = fail_count
        self.calls = 0

    def complete(self, messages):
        self.calls += 1
        if self.calls <= self._fail_count:
            raise LLMError(f"transient error {self.calls}")
        return self._response


class AlwaysFailingLLM(LLMProvider):
    """LLM that always raises LLMError."""

    def __init__(self):
        self.calls = 0

    def complete(self, messages):
        self.calls += 1
        raise LLMError("persistent error")


def test_loop_completes_task_with_mock(tmp_path):
    file_path = tmp_path / "foo.py"
    file_path.write_text("print(1)")

    responses = [
        f'{{"tool": "read_file", "args": {{"path": "{file_path}"}}}}',
        '{"tool": "task_complete", "args": {"summary": "done"}}',
    ]
    llm = MockLLM(responses)
    registry = ToolRegistry()
    registry.register("read_file", read_file)
    registry.register("write_file", write_file)
    registry.register("run_shell", run_shell)

    loop = AgentLoop(
        llm=llm,
        registry=registry,
        governance=Governance(blocked_commands=["rm -rf"], auto_deny=True, project_dir=str(tmp_path)),
        memory=Memory(task="read foo.py", session_dir=str(tmp_path / "sessions")),
        max_turns=10,
    )
    result = loop.run("read foo.py")
    assert "done" in result.lower()


def test_loop_stops_on_max_turns():
    responses = ['{"tool": "read_file", "args": {"path": "x.py"}}'] * 100
    llm = MockLLM(responses)
    registry = ToolRegistry()
    registry.register("read_file", lambda path: __import__("harness.models", fromlist=["ActionResult"]).ActionResult(
        success=False, output="", error="not found", exit_code=-1
    ))

    loop = AgentLoop(
        llm=llm,
        registry=registry,
        governance=Governance(blocked_commands=[], auto_deny=True),
        memory=Memory(task="test", session_dir="."),
        max_turns=3,
    )
    result = loop.run("test")
    assert "max" in result.lower() or "3" in result


def test_loop_handles_parse_error_retry():
    responses = [
        "not json at all",
        '{"tool": "task_complete", "args": {"summary": "done"}}',
    ]
    llm = MockLLM(responses)
    registry = ToolRegistry()

    loop = AgentLoop(
        llm=llm,
        registry=registry,
        governance=Governance(blocked_commands=[], auto_deny=True),
        memory=Memory(task="test", session_dir="."),
        max_turns=10,
    )
    result = loop.run("test")
    assert "done" in result.lower()


def test_loop_governance_blocks_dangerous_command():
    responses = [
        '{"tool": "run_shell", "args": {"command": "rm -rf /"}}',
        '{"tool": "task_complete", "args": {"summary": "done"}}',
    ]
    llm = MockLLM(responses)
    registry = ToolRegistry()
    registry.register("run_shell", run_shell)

    loop = AgentLoop(
        llm=llm,
        registry=registry,
        governance=Governance(blocked_commands=["rm -rf"], auto_deny=True),
        memory=Memory(task="test", session_dir="."),
        max_turns=10,
    )
    result = loop.run("test")
    assert "done" in result.lower()


def test_loop_retries_llm_error_then_succeeds(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _: None)

    llm = FlakyLLM(
        response='{"tool": "task_complete", "args": {"summary": "done"}}',
        fail_count=2,
    )
    loop = AgentLoop(
        llm=llm,
        registry=ToolRegistry(),
        governance=Governance(blocked_commands=[], auto_deny=True),
        memory=Memory(task="test", session_dir="."),
        max_turns=10,
    )
    result = loop.run("test")
    assert "done" in result.lower()
    assert llm.calls == 3


def test_loop_stops_after_max_llm_retries(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _: None)

    llm = AlwaysFailingLLM()
    loop = AgentLoop(
        llm=llm,
        registry=ToolRegistry(),
        governance=Governance(blocked_commands=[], auto_deny=True),
        memory=Memory(task="test", session_dir="."),
        max_turns=10,
    )
    result = loop.run("test")
    assert "stopped" in result.lower()
    assert "3" in result
    assert llm.calls == 4
