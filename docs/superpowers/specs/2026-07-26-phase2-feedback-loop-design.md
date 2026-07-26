# Phase 2: Feedback Loop Deepening Design

## Overview

Deepen the feedback loop from a single reactive PASS/FAIL check to a multi-stage pipeline with structured feedback, post-action hooks, pattern analysis, and self-correction.

## Motivation

Current feedback (`harness/feedback.py`) is 10 lines — just `result.success → PASS/FAIL`. The LLM sees only a flat summary string. No auto-lint, no auto-test, no pattern detection, no self-correction.

## Architecture

```
Action → dispatch → ActionResult
                        ↓
              Feedback Pipeline:
                Stage 1: Basic check (success/exit_code → PASS/FAIL)
                Stage 2: Syntax check (if write_file .py, run py_compile)
                Stage 3: Pattern analysis (compare with last N feedbacks)
                        ↓
              Enriched Feedback (with checks[], suggested_next_action)
                        ↓
              Memory: stores structured feedback, LLM sees enriched summary
                        ↓
              Loop: auto-retry on syntax errors, inject hints for patterns
```

## Data Model Changes

### `harness/models.py`

```python
@dataclass
class CheckResult:
    """Result of a single feedback pipeline check."""
    name: str       # "syntax", "test", "blacklist"
    passed: bool
    detail: str

@dataclass
class Feedback:
    passed: bool
    summary: str
    raw_result: ActionResult
    checks: List[CheckResult] = field(default_factory=list)
    suggested_next_action: str = ""
    turn_number: int = 0
```

### `harness/models.py` — ActionResult metadata

```python
@dataclass
class ActionResult:
    success: bool
    output: str
    error: str
    exit_code: int
    metadata: dict = field(default_factory=dict)  # NEW
```

## Feedback Pipeline (`harness/feedback.py`)

```python
def collect(result: ActionResult, tool: str = "", turn_number: int = 0,
            history: list = None) -> Feedback:
    # Stage 1: Basic check
    passed = result.success
    summary = _build_summary(passed, tool, result)

    # Stage 2: Syntax check
    checks = []
    if tool == "write_file" and result.success:
        path = result.metadata.get("path", "")
        if path.endswith(".py"):
            check = _check_syntax(path)
            checks.append(check)
            if not check.passed:
                passed = False

    # Stage 3: Pattern analysis
    suggestion = ""
    if history:
        suggestion = _analyze_patterns(history)

    return Feedback(passed=passed, summary=summary, raw_result=result,
                    checks=checks, suggested_next_action=suggestion,
                    turn_number=turn_number)
```

### Stage 2: Syntax Check

```python
def _check_syntax(path: str) -> CheckResult:
    """Run py_compile on a .py file to check syntax."""
    import py_compile, sys
    try:
        py_compile.compile(path, doraise=True)
        return CheckResult(name="syntax", passed=True, detail="Syntax OK")
    except py_compile.PyCompileError as e:
        return CheckResult(name="syntax", passed=False, detail=str(e))
```

### Stage 3: Pattern Analysis

```python
def _analyze_patterns(history: list) -> str:
    """Detect recurring failure patterns in recent history."""
    recent = [fb for _, fb in history[-5:]]
    failures = [fb for fb in recent if not fb.passed]
    if len(failures) >= 3:
        tools = [fb.raw_result.metadata.get("tool", "") for fb in failures]
        if all(t == "write_file" for t in tools):
            return "Suggestion: 3 consecutive write failures. Check file permissions and syntax."
        if all(t == "run_shell" for t in tools):
            return "Suggestion: 3 consecutive shell failures. Try a different approach."
    return ""
```

## Loop Self-Correction (`harness/loop.py`)

```python
# After feedback collection
feedback = collect(result, action.tool, turn, self._memory.get_history())

# Inject suggestion into context
if feedback.suggested_next_action:
    self._memory.append_hint(feedback.suggested_next_action)

# Auto-retry: syntax error → auto-fix and re-run
if not feedback.passed and feedback.checks:
    auto_fix = self._try_auto_fix(action, feedback)
    if auto_fix:
        result = auto_fix
        feedback = collect(result, action.tool, turn, ...)
```

### Auto-fix Strategies

- **Syntax error in write_file**: Re-run `py_compile` after the fix, or suggest the LLM re-attempt
- **Governance blocked**: Generate safe alternative command
- **Parse error**: Re-prompt with simpler format requirement

## Memory Changes (`harness/memory.py`)

```python
def append_hint(self, hint: str):
    """Inject a hint message visible to the LLM."""
    self._messages.append(Message(role="user", content=f"[Hint] {hint}"))

def get_history(self) -> list:
    """Return recent (Action, Feedback) pairs for pattern analysis."""
    return self._history[-10:]
```

## Tool Changes (`harness/tools/`)

- `write_file` returns `ActionResult` with `metadata={"path": path, "tool": "write_file"}`
- `run_shell` returns `ActionResult` with `metadata={"tool": "run_shell", "command": command}`

## Files Modified

| File | Change |
|------|--------|
| `harness/models.py` | Add `CheckResult`, extend `Feedback` with `checks`/`suggested_next_action`/`turn_number`, add `metadata` to `ActionResult` |
| `harness/feedback.py` | Multi-stage pipeline: basic → syntax check → pattern analysis |
| `harness/loop.py` | Self-correction: auto-retry, hint injection, suggestion handling |
| `harness/memory.py` | `append_hint()`, `get_history()` |
| `harness/tools/file_tools.py` | Add `metadata` to `ActionResult` return |
| `harness/tools/shell.py` | Add `metadata` to `ActionResult` return |

## Test Strategy

### New/Modified Tests

| Test | File | Type | Description |
|------|------|------|-------------|
| `test_check_syntax_pass` | `test_feedback.py` | Unit | Valid .py file passes syntax check |
| `test_check_syntax_fail` | `test_feedback.py` | Unit | Invalid .py file fails syntax check |
| `test_pipeline_with_syntax_check` | `test_feedback.py` | Unit | write_file .py triggers syntax check |
| `test_pattern_analysis_3_failures` | `test_feedback.py` | Unit | 3 consecutive failures → suggestion |
| `test_pattern_analysis_no_pattern` | `test_feedback.py` | Unit | No pattern → empty suggestion |
| `test_loop_auto_retry_syntax_error` | `test_loop.py` | Integration | Mock LLM writes bad syntax → auto-retry |
| `test_loop_injects_suggestion` | `test_loop.py` | Integration | Suggestion appears in context |
| `test_demo_updated` | `test_demo.py` | Demo | Updated A.6 demo with pipeline |

### 61 existing tests must still pass (no regressions)

## Test Command

```bash
pytest tests/ -v
```

Expected: 61 existing + 8 new = 69 tests pass.

## Edge Cases

- Syntax check on non-.py write_file: skipped (no false positive)
- Pattern analysis with < 3 turns: returns empty (no false suggestion)
- Auto-retry on governance block: not attempted (governance is final)
- metadata backward compatibility: existing tool calls without metadata get empty dict