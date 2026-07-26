# Phase 2: Feedback Loop Deepening Design

## Overview

Deepen the feedback loop from a single reactive PASS/FAIL check to a multi-stage pipeline with structured feedback, post-action checks, pattern analysis, and enhanced feedback injection that drives LLM self-correction.

## Motivation

Current feedback (`harness/feedback.py`) is 10 lines — just `result.success → PASS/FAIL`. The LLM sees only a flat summary string. No auto-lint, no auto-test, no pattern detection, no structured feedback.

## Architecture

```
Action → dispatch → ActionResult
                        ↓
              Feedback Pipeline:
                Stage 1: Basic check (success/exit_code → PASS/FAIL)
                Stage 2: Syntax check (if write_file .py, run py_compile)
                Stage 3: Test check (if write_file test_*.py, run pytest)
                Stage 4: Pattern analysis (compare with last N feedbacks)
                        ↓
              Enriched Feedback (with checks[], suggested_next_action)
                        ↓
              Memory: stores structured feedback, LLM sees enriched summary
                        ↓
              Loop: injects hint to LLM → LLM self-corrects in next turn
```

**Key clarification on "self-correction":** The harness CANNOT fix syntax errors itself — that requires LLM intelligence. What the harness does is:
1. Detect the failure (via py_compile / pytest)
2. Inject a detailed, structured hint to the LLM context
3. The LLM sees the hint in the next turn and rewrites the file

This is "enhanced feedback that drives LLM self-correction", not "harness auto-fixes". The `_try_auto_fix` concept from the previous draft was wrong and has been removed.

## Data Model Changes

### `harness/models.py`

```python
@dataclass
class CheckResult:
    """Result of a single feedback pipeline check."""
    name: str       # "syntax", "test", "pattern"
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
    metadata: dict = field(default_factory=dict)  # NEW: stores path, tool name, etc.
```

## Feedback Pipeline (`harness/feedback.py`)

```python
def collect(result: ActionResult, tool: str = "", turn_number: int = 0,
            history: list = None) -> Feedback:
    # Stage 1: Basic check
    passed = result.success
    summary = _build_summary(passed, tool, result)

    # Stage 2: Syntax check (only for write_file on .py files)
    checks = []
    if tool == "write_file" and result.success:
        path = result.metadata.get("path", "")
        if path.endswith(".py"):
            check = _check_syntax(path)
            checks.append(check)
            if not check.passed:
                passed = False
                summary += f" | Syntax check FAILED: {check.detail}"

    # Stage 3: Test check (only for write_file on test_*.py files)
    if tool == "write_file" and result.success and path.endswith("test_*.py"):
        check = _check_tests(path)
        checks.append(check)
        if not check.passed:
            passed = False
            summary += f" | Test check FAILED: {check.detail}"

    # Stage 4: Pattern analysis
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
    import py_compile
    try:
        py_compile.compile(path, doraise=True)
        return CheckResult(name="syntax", passed=True, detail="Syntax OK")
    except py_compile.PyCompileError as e:
        return CheckResult(name="syntax", passed=False, detail=str(e))
```

### Stage 3: Test Check

```python
def _check_tests(path: str) -> CheckResult:
    """Run pytest on the test file to check if tests pass."""
    import subprocess
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", path, "--tb=short", "-q"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return CheckResult(name="test", passed=True, detail="All tests passed")
        else:
            return CheckResult(name="test", passed=False,
                             detail=result.stdout[-500:] + result.stderr[-500:])
    except subprocess.TimeoutExpired:
        return CheckResult(name="test", passed=False, detail="Test timed out after 30s")
    except Exception as e:
        return CheckResult(name="test", passed=False, detail=str(e))
```

### Stage 4: Pattern Analysis

```python
def _analyze_patterns(history: list) -> str:
    """Detect recurring failure patterns in recent history.
    
    history is a list of (Action, Feedback) tuples.
    Uses action.tool (not feedback metadata) to identify the tool.
    """
    recent = history[-5:]  # last 5 (Action, Feedback) pairs
    failures = [(action, fb) for action, fb in recent if not fb.passed]
    if len(failures) >= 3:
        tools = [action.tool for action, _ in failures]  # FIXED: use action.tool
        if all(t == "write_file" for t in tools):
            return "Hint: 3 consecutive write failures. Check syntax and file permissions before retrying."
        if all(t == "run_shell" for t in tools):
            return "Hint: 3 consecutive shell failures. Try a different command or approach."
    return ""
```

## Loop Enhanced Feedback Injection (`harness/loop.py`)

```python
# After feedback collection
feedback = collect(result, action.tool, turn, self._memory.get_history())

# Inject structured hint to LLM context (drives LLM self-correction)
if feedback.suggested_next_action:
    self._memory.append_hint(feedback.suggested_next_action)

# If syntax/test check failed, inject detailed error to help LLM fix it
if not feedback.passed and feedback.checks:
    failed_checks = [c for c in feedback.checks if not c.passed]
    if failed_checks:
        hint = f"Your last action failed checks: {failed_checks[0].detail}. Please fix and retry."
        self._memory.append_hint(hint)
```

**What this does:** When the LLM writes a file with syntax errors, the next turn's context includes:
1. `[Tool Result] [FAIL] write_file | Syntax check FAILED: SyntaxError: invalid syntax...`
2. `[Hint] Your last action failed checks: SyntaxError: invalid syntax... Please fix and retry.`

The LLM sees both the failure and the specific error, enabling it to self-correct.

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
| `harness/feedback.py` | Multi-stage pipeline: basic → syntax check → test check → pattern analysis |
| `harness/loop.py` | Enhanced feedback injection: hint injection for failed checks, pattern suggestions |
| `harness/memory.py` | `append_hint()`, `get_history()` |
| `harness/tools/file_tools.py` | Add `metadata` to `ActionResult` return |
| `harness/tools/shell.py` | Add `metadata` to `ActionResult` return |
| `SPEC.md` | Update §3.6 (反馈模块) and §11.6 (重点维度) to reflect Phase 2 implementation |

## Scope vs SPEC.md §11.6

SPEC.md §11.6 promised these for Phase 2:

| SPEC promise | This design | Status |
|--------------|------------|--------|
| 多阶段校验管道 | syntax + test checks | ✅ Partial (no typecheck/coverage) |
| 失败分类（语法/类型/逻辑/风格） | syntax check classifies syntax errors | ✅ Partial |
| 多轮自我修正循环 | hint injection drives LLM self-correction | ✅ Aligned |
| 治理深化（HITL 状态机） | — | ❌ Out of scope (YAGNI) |
| 记忆深化（项目约定学习） | — | ❌ Out of scope (YAGNI) |

**Rationale for scope cuts:** HITL state machine and project convention learning add complexity without proportional value for a course project. The core contribution — multi-stage feedback pipeline + self-correction via hint injection — is where the depth lies. SPEC.md will be updated to reflect this scope.

## Test Strategy

### New/Modified Tests

| Test | File | Type | Description |
|------|------|------|-------------|
| `test_check_syntax_pass` | `test_feedback.py` | Unit | Valid .py file passes syntax check |
| `test_check_syntax_fail` | `test_feedback.py` | Unit | Invalid .py file fails syntax check |
| `test_pipeline_with_syntax_check` | `test_feedback.py` | Unit | write_file .py triggers syntax check |
| `test_pipeline_skips_non_py` | `test_feedback.py` | Unit | write_file .txt skips syntax check |
| `test_pattern_analysis_3_failures` | `test_feedback.py` | Unit | 3 consecutive failures → suggestion |
| `test_pattern_analysis_no_pattern` | `test_feedback.py` | Unit | No pattern → empty suggestion |
| `test_loop_injects_hint_on_fail` | `test_loop.py` | Integration | Syntax fail → hint appears in context |
| `test_loop_injects_suggestion` | `test_loop.py` | Integration | Pattern suggestion appears in context |
| `test_demo_updated` | `test_demo.py` | Demo | Updated A.6 demo with pipeline |

### Backward Compatibility

- `ActionResult.metadata` defaults to `field(default_factory=dict)` — existing code creating `ActionResult` without metadata still works
- `Feedback.checks` defaults to `field(default_factory=list)` — existing code creating `Feedback` without checks still works
- `collect()` signature: new params `turn_number` and `history` have defaults — existing calls still work

### 61 existing tests must still pass (no regressions)

## Test Command

```bash
pytest tests/ -v
```

Expected: 61 existing + 9 new = 70 tests pass.

## Edge Cases

- Syntax check on non-.py write_file: skipped (no false positive)
- Test check on non-test .py file: skipped (only runs on test_*.py)
- Pattern analysis with < 3 turns: returns empty (no false suggestion)
- metadata backward compatibility: existing tool calls without metadata get empty dict
- py_compile creates __pycache__ — tests use tmp_path so no pollution
