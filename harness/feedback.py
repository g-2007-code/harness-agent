from harness.models import ActionResult, Feedback, CheckResult


def _check_syntax(path: str) -> CheckResult:
    """Run py_compile on a .py file to check syntax."""
    import py_compile
    try:
        py_compile.compile(path, doraise=True)
        return CheckResult(name="syntax", passed=True, detail="Syntax OK")
    except py_compile.PyCompileError as e:
        return CheckResult(name="syntax", passed=False, detail=str(e))


def collect(result: ActionResult, tool: str = "") -> Feedback:
    if result.success:
        summary = f"[PASS] {tool}: {result.output[:200]}"
    else:
        summary = f"[FAIL] {tool} (exit_code={result.exit_code}): {result.error[:200]}"
    return Feedback(passed=result.success, summary=summary, raw_result=result)
