from harness.models import ActionResult, Feedback, CheckResult


def _check_syntax(path: str) -> CheckResult:
    """Run py_compile on a .py file to check syntax."""
    import py_compile
    try:
        py_compile.compile(path, doraise=True)
        return CheckResult(name="syntax", passed=True, detail="Syntax OK")
    except py_compile.PyCompileError as e:
        return CheckResult(name="syntax", passed=False, detail=str(e))


def _analyze_patterns(history: list) -> str:
    """Detect recurring failure patterns in recent history.

    history is a list of (Action, Feedback) tuples.
    Returns a suggestion string, or empty string if no pattern detected.
    """
    recent = history[-5:]
    failures = [(action, fb) for action, fb in recent if not fb.passed]
    if len(failures) >= 3:
        tools = [action.tool for action, _ in failures]
        if all(t == "write_file" for t in tools):
            return "Hint: 3 consecutive write failures. Check syntax and file permissions before retrying."
        if all(t == "run_shell" for t in tools):
            return "Hint: 3 consecutive shell failures. Try a different command or approach."
    return ""


def collect(result: ActionResult, tool: str = "") -> Feedback:
    if result.success:
        summary = f"[PASS] {tool}: {result.output[:200]}"
    else:
        summary = f"[FAIL] {tool} (exit_code={result.exit_code}): {result.error[:200]}"
    return Feedback(passed=result.success, summary=summary, raw_result=result)
