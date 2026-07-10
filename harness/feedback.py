# harness/feedback.py
# This file contains the self-implemented feedback collection mechanism (harness kernel).
# Written by the student, with AI assistance for boilerplate. Core logic is hand-designed.
from harness.models import ActionResult, Feedback


def collect(result: ActionResult, tool: str = "") -> Feedback:
    if result.success:
        summary = f"[PASS] {tool}: {result.output[:200]}"
    else:
        summary = f"[FAIL] {tool} (exit_code={result.exit_code}): {result.error[:200]}"
    return Feedback(passed=result.success, summary=summary, raw_result=result)
