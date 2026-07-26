from harness.feedback import collect
from harness.models import ActionResult, Feedback


def test_collect_pass_for_success():
    result = ActionResult(success=True, output="hello", error="", exit_code=0)
    fb = collect(result, tool="run_shell")
    assert fb.passed is True
    assert "hello" in fb.summary
    assert fb.raw_result == result


def test_collect_fail_for_nonzero_exit():
    result = ActionResult(success=False, output="", error="SyntaxError", exit_code=1)
    fb = collect(result, tool="run_shell")
    assert fb.passed is False
    assert "SyntaxError" in fb.summary
    assert fb.raw_result.exit_code == 1


def test_collect_pass_for_read_file_success():
    result = ActionResult(success=True, output="file content", error="", exit_code=0)
    fb = collect(result, tool="read_file")
    assert fb.passed is True


def test_collect_fail_for_read_file_failure():
    result = ActionResult(success=False, output="", error="File not found", exit_code=-1)
    fb = collect(result, tool="read_file")
    assert fb.passed is False
    assert "File not found" in fb.summary


def test_collect_summary_includes_exit_code():
    result = ActionResult(success=False, output="", error="error", exit_code=42)
    fb = collect(result, tool="run_shell")
    assert "42" in fb.summary


def test_check_syntax_pass(tmp_path):
    from harness.feedback import _check_syntax
    file_path = tmp_path / "valid.py"
    file_path.write_text("x = 1\n")
    check = _check_syntax(str(file_path))
    assert check.name == "syntax"
    assert check.passed is True
    assert "OK" in check.detail


def test_check_syntax_fail(tmp_path):
    from harness.feedback import _check_syntax
    file_path = tmp_path / "invalid.py"
    file_path.write_text("def broken(\n")
    check = _check_syntax(str(file_path))
    assert check.name == "syntax"
    assert check.passed is False
    assert "SyntaxError" in check.detail or "syntax" in check.detail.lower()


def test_pattern_analysis_3_write_failures():
    from harness.feedback import _analyze_patterns
    from harness.models import Action, ActionResult
    history = []
    for i in range(3):
        action = Action(tool="write_file", args={"path": f"f{i}.py"}, raw="")
        result = ActionResult(success=False, output="", error="error", exit_code=1)
        fb = Feedback(passed=False, summary="[FAIL]", raw_result=result)
        history.append((action, fb))
    suggestion = _analyze_patterns(history)
    assert "write" in suggestion.lower()
    assert "3" in suggestion


def test_pattern_analysis_3_shell_failures():
    from harness.feedback import _analyze_patterns
    from harness.models import Action, ActionResult
    history = []
    for i in range(3):
        action = Action(tool="run_shell", args={"command": "bad"}, raw="")
        result = ActionResult(success=False, output="", error="error", exit_code=1)
        fb = Feedback(passed=False, summary="[FAIL]", raw_result=result)
        history.append((action, fb))
    suggestion = _analyze_patterns(history)
    assert "shell" in suggestion.lower()


def test_pattern_analysis_no_pattern():
    from harness.feedback import _analyze_patterns
    history = []
    suggestion = _analyze_patterns(history)
    assert suggestion == ""


def test_pattern_analysis_mixed_no_suggestion():
    from harness.feedback import _analyze_patterns
    from harness.models import Action, ActionResult
    history = []
    tools = ["write_file", "run_shell", "read_file"]
    for t in tools:
        action = Action(tool=t, args={}, raw="")
        result = ActionResult(success=False, output="", error="e", exit_code=1)
        fb = Feedback(passed=False, summary="[FAIL]", raw_result=result)
        history.append((action, fb))
    suggestion = _analyze_patterns(history)
    assert suggestion == ""


def test_pipeline_with_syntax_check_pass(tmp_path):
    from harness.feedback import collect
    file_path = tmp_path / "valid.py"
    file_path.write_text("x = 1\n")
    result = ActionResult(
        success=True, output="Wrote 10 chars", error="", exit_code=0,
        metadata={"path": str(file_path), "tool": "write_file"}
    )
    fb = collect(result, tool="write_file", turn_number=1)
    assert fb.passed is True
    assert len(fb.checks) == 1
    assert fb.checks[0].name == "syntax"
    assert fb.checks[0].passed is True
    assert fb.turn_number == 1


def test_pipeline_with_syntax_check_fail(tmp_path):
    from harness.feedback import collect
    file_path = tmp_path / "invalid.py"
    file_path.write_text("def broken(\n")
    result = ActionResult(
        success=True, output="Wrote 10 chars", error="", exit_code=0,
        metadata={"path": str(file_path), "tool": "write_file"}
    )
    fb = collect(result, tool="write_file", turn_number=1)
    assert fb.passed is False
    assert len(fb.checks) == 1
    assert fb.checks[0].passed is False
    assert "Syntax" in fb.summary or "syntax" in fb.summary.lower()


def test_pipeline_skips_non_py(tmp_path):
    from harness.feedback import collect
    result = ActionResult(
        success=True, output="Wrote 10 chars", error="", exit_code=0,
        metadata={"path": "readme.txt", "tool": "write_file"}
    )
    fb = collect(result, tool="write_file", turn_number=1)
    assert fb.passed is True
    assert len(fb.checks) == 0


def test_pipeline_skips_read_file():
    from harness.feedback import collect
    result = ActionResult(success=True, output="content", error="", exit_code=0)
    fb = collect(result, tool="read_file", turn_number=1)
    assert fb.passed is True
    assert len(fb.checks) == 0


def test_pipeline_with_pattern_suggestion():
    from harness.feedback import collect
    from harness.models import Action
    history = []
    for i in range(3):
        action = Action(tool="write_file", args={}, raw="")
        result = ActionResult(success=False, output="", error="e", exit_code=1)
        fb = Feedback(passed=False, summary="[FAIL]", raw_result=result)
        history.append((action, fb))
    result = ActionResult(success=True, output="ok", error="", exit_code=0)
    fb = collect(result, tool="read_file", turn_number=4, history=history)
    assert "write" in fb.suggested_next_action.lower()


def test_pipeline_backward_compat_no_new_args():
    """Existing calls to collect() without new args must still work."""
    from harness.feedback import collect
    result = ActionResult(success=True, output="ok", error="", exit_code=0)
    fb = collect(result, tool="run_shell")
    assert fb.passed is True
    assert fb.checks == []
    assert fb.suggested_next_action == ""
    assert fb.turn_number == 0
