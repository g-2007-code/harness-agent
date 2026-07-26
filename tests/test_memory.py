# tests/test_memory.py
import json
import os
from harness.memory import Memory
from harness.models import Message, Action, ActionResult, Feedback


def test_build_context_initial():
    mem = Memory(task="fix bug in foo.py")
    ctx = mem.build_context()
    assert len(ctx) >= 2
    assert ctx[0].role == "system"
    assert ctx[1].role == "user"
    assert "fix bug in foo.py" in ctx[1].content


def test_append_and_build_context():
    mem = Memory(task="fix bug")
    action = Action(tool="read_file", args={"path": "foo.py"}, raw="")
    result = ActionResult(success=True, output="content", error="", exit_code=0)
    fb = Feedback(passed=True, summary="[PASS] read_file: content", raw_result=result)
    mem.append(action, fb)
    ctx = mem.build_context()
    assert len(ctx) >= 4  # system + user + assistant + tool result
    assert any("read_file" in m.content for m in ctx)


def test_save_and_load_session(tmp_path):
    mem = Memory(task="fix bug", session_dir=str(tmp_path))
    action = Action(tool="read_file", args={"path": "foo.py"}, raw="")
    result = ActionResult(success=True, output="content", error="", exit_code=0)
    fb = Feedback(passed=True, summary="OK", raw_result=result)
    mem.append(action, fb)
    session = mem.save_session()
    assert os.path.exists(os.path.join(str(tmp_path), f"{session.id}.json"))

    mem2 = Memory(task="fix bug", session_dir=str(tmp_path))
    loaded = mem2.load_session(session.id)
    assert loaded is not None
    assert loaded.task == "fix bug"
    assert len(loaded.history) == 1


def test_load_nonexistent_session(tmp_path):
    mem = Memory(task="test", session_dir=str(tmp_path))
    result = mem.load_session("nonexistent-id")
    assert result is None


def test_append_hint():
    from harness.memory import Memory
    mem = Memory(task="test", session_dir=".")
    mem.append_hint("Check syntax before retrying")
    ctx = mem.build_context()
    assert any("[Hint]" in m.content for m in ctx)
    assert any("Check syntax" in m.content for m in ctx)


def test_get_history_empty():
    from harness.memory import Memory
    mem = Memory(task="test", session_dir=".")
    assert mem.get_history() == []


def test_get_history_returns_recent():
    from harness.memory import Memory
    from harness.models import Action, ActionResult, Feedback
    mem = Memory(task="test", session_dir=".")
    for i in range(5):
        action = Action(tool="read_file", args={}, raw="")
        result = ActionResult(success=True, output="ok", error="", exit_code=0)
        fb = Feedback(passed=True, summary="[PASS]", raw_result=result)
        mem.append(action, fb)
    history = mem.get_history()
    assert len(history) == 5
    assert all(isinstance(h, tuple) for h in history)


def test_get_history_caps_at_10():
    from harness.memory import Memory
    from harness.models import Action, ActionResult, Feedback
    mem = Memory(task="test", session_dir=".")
    for i in range(15):
        action = Action(tool="read_file", args={}, raw="")
        result = ActionResult(success=True, output="ok", error="", exit_code=0)
        fb = Feedback(passed=True, summary="[PASS]", raw_result=result)
        mem.append(action, fb)
    history = mem.get_history()
    assert len(history) == 10
