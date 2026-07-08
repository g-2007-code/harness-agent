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
