# tests/test_demo.py
"""
A.6 Mechanism Demonstration: 3 deterministic behaviors under mock LLM.

① Governance guardrail blocks a dangerous action
② Injected failure feedback causes agent to change next action
③ Feedback loop deterministic behavior (pass/fail judgment)
"""
from harness.loop import AgentLoop
from harness.llm.mock import MockLLM
from harness.tools import ToolRegistry
from harness.tools.file_tools import read_file, write_file
from harness.tools.shell import run_shell
from harness.governance import Governance
from harness.feedback import collect
from harness.memory import Memory
from harness.models import ActionResult, Feedback


def test_demo_1_governance_blocks_dangerous_command():
    """① 治理护栏拦截一个危险动作"""
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
        memory=Memory(task="dangerous task", session_dir="."),
        max_turns=5,
    )
    result = loop.run("dangerous task")
    # Agent should complete after governance blocked the dangerous command
    assert "done" in result.lower()
    # Verify the blocked feedback was recorded in memory
    ctx = loop._memory.build_context()
    assert any("Blocked" in m.content or "blocked" in m.content.lower() for m in ctx)


def test_demo_2_failure_feedback_changes_next_action():
    """② 注入一次失败，反馈闭环使 agent 收到反馈并据此改变下一步动作"""
    responses = [
        '{"tool": "read_file", "args": {"path": "/nonexistent/file.py"}}',
        '{"tool": "task_complete", "args": {"summary": "file not found, giving up"}}',
    ]
    llm = MockLLM(responses)
    registry = ToolRegistry()
    registry.register("read_file", read_file)

    loop = AgentLoop(
        llm=llm,
        registry=registry,
        governance=Governance(blocked_commands=[], auto_deny=True),
        memory=Memory(task="read a file", session_dir="."),
        max_turns=5,
    )
    result = loop.run("read a file")
    assert "not found" in result.lower() or "giving up" in result.lower()
    # Verify failure feedback was in context for second LLM call
    ctx = loop._memory.build_context()
    assert any("FAIL" in m.content or "not found" in m.content.lower() for m in ctx)


def test_demo_3_feedback_deterministic_judgment():
    """③ 反馈闭环确定性行为：exit_code 客观判定"""
    # Pass case
    pass_result = ActionResult(success=True, output="OK", error="", exit_code=0)
    pass_fb = collect(pass_result, tool="run_shell")
    assert pass_fb.passed is True
    assert "[PASS]" in pass_fb.summary

    # Fail case
    fail_result = ActionResult(success=False, output="", error="SyntaxError", exit_code=1)
    fail_fb = collect(fail_result, tool="run_shell")
    assert fail_fb.passed is False
    assert "[FAIL]" in fail_fb.summary
    assert "1" in fail_fb.summary  # exit_code
    assert "SyntaxError" in fail_fb.summary
