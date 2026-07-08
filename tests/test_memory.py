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
