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
