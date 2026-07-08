from harness.models import (
    Message, Conversation, Action, ActionResult,
    Feedback, GovernanceDecision, Session, Config
)


def test_message_creation():
    msg = Message(role="system", content="You are a coding agent")
    assert msg.role == "system"
    assert msg.content == "You are a coding agent"


def test_action_creation():
    action = Action(tool="write_file", args={"path": "foo.py", "content": "print(1)"}, raw='{"tool":"write_file"}')
    assert action.tool == "write_file"
    assert action.args["path"] == "foo.py"


def test_action_result():
    result = ActionResult(success=True, output="hello", error="", exit_code=0)
    assert result.success is True
    assert result.exit_code == 0


def test_feedback():
    result = ActionResult(success=True, output="", error="", exit_code=0)
    fb = Feedback(passed=True, summary="OK", raw_result=result)
    assert fb.passed is True
    assert fb.raw_result == result


def test_governance_decision():
    decision = GovernanceDecision(allow=True, confirm=False, reason="safe")
    assert decision.allow is True
    assert decision.confirm is False


def test_session():
    action = Action(tool="read_file", args={"path": "foo.py"}, raw="")
    result = ActionResult(success=True, output="content", error="", exit_code=0)
    fb = Feedback(passed=True, summary="OK", raw_result=result)
    session = Session(id="20260708-abc", task="fix bug", history=[(action, fb)], summary="done")
    assert session.task == "fix bug"
    assert len(session.history) == 1
    assert session.history[0][0].tool == "read_file"


def test_config_defaults():
    config = Config(
        llm_provider="mock", llm_model="gpt-4o", max_turns=20,
        blocked_commands=["rm -rf"], auto_deny=False,
        session_dir=".harness/sessions", log_level="info", log_dir=".harness/logs"
    )
    assert config.max_turns == 20
    assert config.auto_deny is False
