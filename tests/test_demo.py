# tests/test_demo.py
"""
A.6 Mechanism Demonstration: 4 deterministic behaviors under mock LLM.

① Governance guardrail blocks a dangerous action
② Injected failure feedback causes agent to change next action
③ Feedback loop deterministic behavior (pass/fail judgment)
④ Feedback pipeline: syntax check → hint injection → LLM self-correction
"""
import json
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


def test_demo_4_feedback_pipeline_syntax_check(tmp_path):
    """④ 反馈流水线：写文件后自动语法检查，失败时注入 hint 驱动 LLM 自修正"""
    bad_file = tmp_path / "bad.py"
    responses = [
        f'{{"tool": "write_file", "args": {{"path": {json.dumps(str(bad_file))}, "content": "def broken(\\n"}}}}',
        f'{{"tool": "write_file", "args": {{"path": {json.dumps(str(bad_file))}, "content": "def fixed():\\n    pass\\n"}}}}',
        '{"tool": "task_complete", "args": {"summary": "fixed syntax error"}}',
    ]
    llm = MockLLM(responses)
    registry = ToolRegistry()
    registry.register("write_file", write_file)
    registry.register("read_file", read_file)
    registry.register("run_shell", run_shell)

    loop = AgentLoop(
        llm=llm,
        registry=registry,
        governance=Governance(blocked_commands=[], auto_deny=True, project_dir=str(tmp_path)),
        memory=Memory(task="fix syntax", session_dir=str(tmp_path / "sessions")),
        max_turns=10,
    )
    result = loop.run("fix syntax")
    assert "fixed" in result.lower()

    # Verify the pipeline ran a syntax check on the first write
    ctx = loop._memory.build_context()
    # First write should have failed syntax check
    assert any("Syntax" in m.content or "syntax" in m.content.lower() for m in ctx)
    # A hint should have been injected
    assert any("[Hint]" in m.content for m in ctx)
    # The file should eventually be valid
    import py_compile
    py_compile.compile(str(bad_file), doraise=True)
