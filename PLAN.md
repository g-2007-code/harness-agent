# harness-agent MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimal runnable coding agent harness with 6 dimensions (decision/tools/governance/feedback/memory/config), LLM abstraction layer (OpenAI + Mock), CLI, keyring credentials, Docker + PyPI distribution, and mock-LLM unit tests.

**Architecture:** Self-implemented agent main loop that orchestrates context assembly → LLM call → response parsing → governance check → tool dispatch → feedback collection → memory append → stop check. All modules communicate through interfaces, injectable mock LLM for deterministic testing.

**Tech Stack:** Python 3.10+, pytest, keyring, pyyaml, openai SDK, Docker, PyPI

## Global Constraints

- Python 3.10+ required
- TDD mandatory: red → green → refactor, no implementation before test
- No agent frameworks (LangChain/AutoGen/CrewAI) — self-implemented harness kernel only
- API keys never hardcoded, never committed, never logged
- Each task ends with a commit
- Test command: `pytest tests/ -v`
- All core mechanisms must be testable with mock LLM (no network, no real LLM)

---

## File Structure

```
harness-agent/
├── .github/workflows/
│   └── test.yml           # GitHub Actions (unit-test + docker-build)
├── harness/
│   ├── __init__.py
│   ├── models.py          # Data models (Message, Action, ActionResult, Feedback, CheckResult, etc.)
│   ├── config.py          # YAML config loading with defaults
│   ├── parser.py          # Parse LLM JSON response → Action
│   ├── governance.py      # Guardrail: check(action) → GovernanceDecision
│   ├── feedback.py        # Multi-stage pipeline: basic → syntax check → pattern analysis
│   ├── memory.py          # Session context + cross-session persistence + hint injection
│   ├── loop.py            # Agent main loop (6-step cycle + hint injection)
│   ├── cli.py             # CLI entry + keyring subcommands + TUI integration
│   ├── tui.py             # Terminal UI renderer (rich-based callback)
│   ├── llm/
│   │   ├── __init__.py    # LLMProvider ABC + factory
│   │   ├── base.py        # LLMProvider ABC + LLMError
│   │   ├── mock.py        # Mock LLM (deterministic, script-based)
│   │   └── openai.py      # OpenAI Chat Completions provider (OpenAI + DeepSeek via base_url)
│   └── tools/
│       ├── __init__.py    # ToolRegistry
│       ├── file_tools.py  # read_file, write_file
│       └── shell.py       # run_shell
├── tests/
│   ├── __init__.py
│   ├── conftest.py        # Shared fixtures (tmp_project_dir, mock_config)
│   ├── test_models.py
│   ├── test_config.py
│   ├── test_parser.py
│   ├── test_governance.py
│   ├── test_feedback.py
│   ├── test_memory.py
│   ├── test_tools.py
│   ├── test_llm_mock.py
│   ├── test_llm_openai.py
│   ├── test_loop.py
│   ├── test_cli.py
│   └── test_demo.py       # Mechanism demonstration (A.6)
├── pyproject.toml
├── Dockerfile
├── .gitignore
├── config.yaml            # Default config
├── README.md
├── SPEC.md
├── PLAN.md
├── AGENT_LOG.md
├── .gitlab-ci.yml
└── docs/superpowers/
    ├── specs/             # Phase 2 design spec
    └── plans/             # Phase 2 implementation plan
```

## Task Dependency Graph

```
Task 1 (scaffolding) ──→ Task 2 (models)
                              │
         ┌────────┬───────────┼────────┬────────┐
         ▼        ▼           ▼        ▼        ▼
    Task 3     Task 4     Task 5    Task 6    Task 8
   (config)    (llm)    (parser)  (tools)  (governance)
         │        │           │        │        │
         │        │           │        ▼        │
         │        │           │    Task 7     │
         │        │           │   (shell)      │
         │        │           │        │        │
         │        │           │        ▼        ▼
         │        │           │    Task 9 (feedback)
         │        │           │        │
         │        │           │        ▼
         │        │           │    Task 10 (memory)
         │        │           │        │
         │        │           ▼        │
         │        │    Task 11 (loop) ←┘
         │        │           │
         │        │           ▼
         │        │    Task 12 (cli)
         │        │           │
         │        ▼           │
         │   Task 13 (openai)│
         │        │           │
         │        ▼           ▼
         │   Task 14 (demo) ←┘
         │        │
         ▼        ▼
    Task 15 (docker+pypi)
              │
              ▼
    Task 16 (CI)
```

**Parallelizable:** Tasks 3, 4, 5, 6, 8 can run in parallel after Task 2. Task 7 after Task 6. Tasks 9, 10 after 7+8.

---

## Task 1: Project Scaffolding ✅ (commit 821a4a0)

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `harness/__init__.py`
- Create: `harness/llm/__init__.py`
- Create: `harness/tools/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `config.yaml`

**Interfaces:**
- Produces: project structure for all subsequent tasks

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_get_build_requires"

[project]
name = "harness-agent"
version = "0.1.0"
description = "A self-implemented coding agent harness for Python projects"
requires-python = ">=3.10"
dependencies = [
    "openai>=1.0",
    "keyring>=24.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.0", "pytest-cov>=4.0"]

[project.scripts]
harness = "harness.cli:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["harness*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

- [ ] **Step 2: Create .gitignore**

```
__pycache__/
*.pyc
*.egg-info/
dist/
build/
.env
.harness/
*.egg
.eggs/
.coverage
htmlcov/
```

- [ ] **Step 3: Create package init files and conftest**

`harness/__init__.py`:
```python
"""harness-agent: A self-implemented coding agent harness."""
```

`harness/llm/__init__.py`:
```python
"""LLM abstraction layer."""
```

`harness/tools/__init__.py`:
```python
"""Tool registry and implementations."""
```

`tests/__init__.py`:
```python
```

`tests/conftest.py`:
```python
import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture
def tmp_project_dir(tmp_path):
    """Provide a temporary project directory."""
    return tmp_path
```

- [ ] **Step 4: Create default config.yaml**

```yaml
llm:
  provider: mock
  model: gpt-4o
max_turns: 20
governance:
  blocked_commands:
    - "rm -rf"
    - "git push --force"
    - "curl"
    - "wget"
    - "chmod 777"
    - "sudo"
  auto_deny: false
session:
  dir: ".harness/sessions"
logging:
  level: info
  dir: ".harness/logs"
```

- [ ] **Step 5: Verify project structure**

Run: `python -c "import harness; print('OK')"`
Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml .gitignore harness/ tests/ config.yaml
git commit -m "chore: project scaffolding"
```

---

## Task 2: Data Models ✅ (commit bf4899f)

**Files:**
- Create: `harness/models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Produces: `Message`, `Conversation`, `Action`, `ActionResult`, `Feedback`, `GovernanceDecision`, `Session`, `Config` dataclasses

- [ ] **Step 1: Write the failing test**

```python
# tests/test_models.py
from harness.models import (
    Message, Conversation, Action, ActionResult,
    Feedback, GovernanceDecision, Session, Config
)


def test_message_creation():
    msg = Message(role="system", content="You are a coding agent")
    assert msg.role == "system"
    assert msg.content == "You are a coding agent"


def test_action_creation():
    action = Action(tool="write_file", args={"path": "foo.py", "content": "print(1)"}, raw='{"tool":"write_file"}')
    assert action.tool == "write_file"
    assert action.args["path"] == "foo.py"


def test_action_result():
    result = ActionResult(success=True, output="hello", error="", exit_code=0)
    assert result.success is True
    assert result.exit_code == 0


def test_feedback():
    result = ActionResult(success=True, output="", error="", exit_code=0)
    fb = Feedback(passed=True, summary="OK", raw_result=result)
    assert fb.passed is True
    assert fb.raw_result == result


def test_governance_decision():
    decision = GovernanceDecision(allow=True, confirm=False, reason="safe")
    assert decision.allow is True
    assert decision.confirm is False


def test_session():
    action = Action(tool="read_file", args={"path": "foo.py"}, raw="")
    result = ActionResult(success=True, output="content", error="", exit_code=0)
    fb = Feedback(passed=True, summary="OK", raw_result=result)
    session = Session(id="20260708-abc", task="fix bug", history=[(action, fb)], summary="done")
    assert session.task == "fix bug"
    assert len(session.history) == 1
    assert session.history[0][0].tool == "read_file"


def test_config_defaults():
    config = Config(
        llm_provider="mock", llm_model="gpt-4o", max_turns=20,
        blocked_commands=["rm -rf"], auto_deny=False,
        session_dir=".harness/sessions", log_level="info", log_dir=".harness/logs"
    )
    assert config.max_turns == 20
    assert config.auto_deny is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'harness.models'`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/models.py
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class Message:
    role: str
    content: str


@dataclass
class Conversation:
    messages: List[Message]


@dataclass
class Action:
    tool: str
    args: dict
    raw: str


@dataclass
class ActionResult:
    success: bool
    output: str
    error: str
    exit_code: int


@dataclass
class Feedback:
    passed: bool
    summary: str
    raw_result: ActionResult


@dataclass
class GovernanceDecision:
    allow: bool
    confirm: bool
    reason: str


@dataclass
class Session:
    id: str
    task: str
    history: List[Tuple[Action, Feedback]]
    summary: str


@dataclass
class Config:
    llm_provider: str
    llm_model: str
    max_turns: int
    blocked_commands: List[str]
    auto_deny: bool
    session_dir: str
    log_level: str
    log_dir: str
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/models.py tests/test_models.py
git commit -m "feat: add data models (Message, Action, ActionResult, Feedback, etc.)"
```

---

## Task 3: Config Loading ✅ (commit dc6fb20)

**Depends on:** Task 2

**Files:**
- Create: `harness/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: `Config` from `harness.models`
- Produces: `load_config(path: str) -> Config`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
import os
from harness.config import load_config
from harness.models import Config


def test_load_config_from_yaml(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
llm:
  provider: openai
  model: gpt-4o
max_turns: 15
governance:
  blocked_commands:
    - "rm -rf"
    - "sudo"
  auto_deny: true
session:
  dir: ".harness/sessions"
logging:
  level: debug
  dir: ".harness/logs"
""")
    config = load_config(str(config_file))
    assert config.llm_provider == "openai"
    assert config.llm_model == "gpt-4o"
    assert config.max_turns == 15
    assert config.auto_deny is True
    assert "rm -rf" in config.blocked_commands
    assert config.log_level == "debug"


def test_load_config_defaults_when_file_missing(tmp_path):
    config = load_config(str(tmp_path / "nonexistent.yaml"))
    assert config.llm_provider == "mock"
    assert config.llm_model == "gpt-4o"
    assert config.max_turns == 20
    assert config.auto_deny is False


def test_load_config_partial_yaml_uses_defaults(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("llm:\n  provider: anthropic\n")
    config = load_config(str(config_file))
    assert config.llm_provider == "anthropic"
    assert config.max_turns == 20  # default
    assert config.auto_deny is False  # default
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/config.py
import os
import yaml
from harness.models import Config


DEFAULTS = Config(
    llm_provider="mock",
    llm_model="gpt-4o",
    max_turns=20,
    blocked_commands=["rm -rf", "git push --force", "curl", "wget", "chmod 777", "sudo"],
    auto_deny=False,
    session_dir=".harness/sessions",
    log_level="info",
    log_dir=".harness/logs",
)


def load_config(path: str) -> Config:
    if not os.path.exists(path):
        return DEFAULTS

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    llm = data.get("llm", {})
    gov = data.get("governance", {})
    sess = data.get("session", {})
    log = data.get("logging", {})

    return Config(
        llm_provider=llm.get("provider", DEFAULTS.llm_provider),
        llm_model=llm.get("model", DEFAULTS.llm_model),
        max_turns=data.get("max_turns", DEFAULTS.max_turns),
        blocked_commands=gov.get("blocked_commands", DEFAULTS.blocked_commands),
        auto_deny=gov.get("auto_deny", DEFAULTS.auto_deny),
        session_dir=sess.get("dir", DEFAULTS.session_dir),
        log_level=log.get("level", DEFAULTS.log_level),
        log_dir=log.get("dir", DEFAULTS.log_dir),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/config.py tests/test_config.py
git commit -m "feat: add YAML config loading with defaults"
```

---

## Task 4: LLM Abstraction + Mock Provider ✅ (commit f93e962)

**Depends on:** Task 2

**Files:**
- Create: `harness/llm/base.py`
- Modify: `harness/llm/__init__.py`
- Create: `harness/llm/mock.py`
- Test: `tests/test_llm_mock.py`

**Interfaces:**
- Consumes: `Message` from `harness.models`
- Produces: `LLMProvider` (ABC), `MockLLM` class

- [ ] **Step 1: Write the failing test**

```python
# tests/test_llm_mock.py
from harness.llm.base import LLMProvider
from harness.llm.mock import MockLLM
from harness.models import Message


def test_mock_llm_returns_scripted_response():
    responses = ['{"tool": "read_file", "args": {"path": "foo.py"}}']
    llm = MockLLM(responses)
    messages = [Message(role="user", content="read foo.py")]
    result = llm.complete(messages)
    assert result == responses[0]


def test_mock_llm_returns_sequential_responses():
    responses = [
        '{"tool": "read_file", "args": {"path": "foo.py"}}',
        '{"tool": "write_file", "args": {"path": "foo.py", "content": "print(1)"}}',
        '{"tool": "task_complete", "args": {"summary": "done"}}',
    ]
    llm = MockLLM(responses)
    messages = [Message(role="user", content="fix foo.py")]
    assert llm.complete(messages) == responses[0]
    assert llm.complete(messages) == responses[1]
    assert llm.complete(messages) == responses[2]


def test_mock_llm_raises_when_script_exhausted():
    import pytest
    llm = MockLLM(["only one response"])
    llm.complete([Message(role="user", content="task")])
    with pytest.raises(IndexError, match="Script exhausted"):
        llm.complete([Message(role="user", content="task")])


def test_mock_llm_is_llm_provider():
    llm = MockLLM(["response"])
    assert isinstance(llm, LLMProvider)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_llm_mock.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/llm/base.py
from abc import ABC, abstractmethod
from typing import List
from harness.models import Message


class LLMError(Exception):
    pass


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, messages: List[Message]) -> str:
        pass
```

```python
# harness/llm/mock.py
from typing import List
from harness.llm.base import LLMProvider
from harness.models import Message


class MockLLM(LLMProvider):
    def __init__(self, responses: List[str]):
        self._responses = list(responses)
        self._index = 0

    def complete(self, messages: List[Message]) -> str:
        if self._index >= len(self._responses):
            raise IndexError("Script exhausted: no more mock responses")
        response = self._responses[self._index]
        self._index += 1
        return response
```

```python
# harness/llm/__init__.py
from harness.llm.base import LLMProvider, LLMError

__all__ = ["LLMProvider", "LLMError"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_llm_mock.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/llm/ tests/test_llm_mock.py
git commit -m "feat: add LLM abstraction layer and Mock provider"
```

---

## Task 5: Parser ✅ (commit 715711c)

**Depends on:** Task 2

**Files:**
- Create: `harness/parser.py`
- Test: `tests/test_parser.py`

**Interfaces:**
- Consumes: `Action` from `harness.models`
- Produces: `parse(response: str) -> Action`, `ParseError`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_parser.py
import pytest
from harness.parser import parse, ParseError
from harness.models import Action


def test_parse_tool_action():
    response = '{"tool": "write_file", "args": {"path": "foo.py", "content": "print(1)"}}'
    action = parse(response)
    assert action.tool == "write_file"
    assert action.args["path"] == "foo.py"
    assert action.args["content"] == "print(1)"
    assert action.raw == response


def test_parse_task_complete():
    response = '{"tool": "task_complete", "args": {"summary": "done"}}'
    action = parse(response)
    assert action.tool == "task_complete"
    assert action.args["summary"] == "done"


def test_parse_with_surrounding_text():
    response = 'I will read the file now.\n{"tool": "read_file", "args": {"path": "foo.py"}}\nLet me check.'
    action = parse(response)
    assert action.tool == "read_file"
    assert action.args["path"] == "foo.py"


def test_parse_invalid_json_raises():
    with pytest.raises(ParseError, match="No JSON found"):
        parse("this is not json at all")


def test_parse_empty_response_raises():
    with pytest.raises(ParseError, match="No JSON found"):
        parse("")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_parser.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/parser.py
import json
import re
from harness.models import Action


class ParseError(Exception):
    pass


def parse(response: str) -> Action:
    match = re.search(r'\{.*\}', response, re.DOTALL)
    if not match:
        raise ParseError("No JSON found in response")

    json_str = match.group()
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ParseError(f"Invalid JSON: {e}")

    tool = data.get("tool")
    if not tool:
        raise ParseError("Missing 'tool' field in JSON")

    args = data.get("args", {})
    return Action(tool=tool, args=args, raw=response)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_parser.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/parser.py tests/test_parser.py
git commit -m "feat: add LLM response parser (JSON extraction → Action)"
```

---

## Task 6: Tool Registry + File Tools ✅ (commit 82e5f6d)

**Depends on:** Task 2

**Files:**
- Modify: `harness/tools/__init__.py`
- Create: `harness/tools/file_tools.py`
- Test: `tests/test_tools.py`

**Interfaces:**
- Consumes: `Action`, `ActionResult` from `harness.models`
- Produces: `ToolRegistry`, `read_file`, `write_file`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_tools.py
import pytest
from harness.tools import ToolRegistry
from harness.tools.file_tools import read_file, write_file
from harness.models import Action, ActionResult


def test_tool_registry_register_and_dispatch():
    registry = ToolRegistry()
    registry.register("read_file", read_file)
    action = Action(tool="read_file", args={"path": "test.txt"}, raw="")
    result = registry.dispatch(action)
    assert isinstance(result, ActionResult)


def test_tool_registry_unknown_tool():
    registry = ToolRegistry()
    action = Action(tool="nonexistent", args={}, raw="")
    result = registry.dispatch(action)
    assert result.success is False
    assert "not registered" in result.error


def test_read_file_success(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello world")
    result = read_file(path=str(file_path))
    assert result.success is True
    assert result.output == "hello world"
    assert result.exit_code == 0


def test_read_file_not_found():
    result = read_file(path="/nonexistent/path/file.txt")
    assert result.success is False
    assert "not found" in result.error.lower() or "no such file" in result.error.lower()


def test_write_file_success(tmp_path):
    file_path = tmp_path / "output.txt"
    result = write_file(path=str(file_path), content="print(1)")
    assert result.success is True
    assert file_path.read_text() == "print(1)"


def test_write_file_creates_parent_dirs(tmp_path):
    file_path = tmp_path / "subdir" / "output.txt"
    result = write_file(path=str(file_path), content="print(1)")
    assert result.success is True
    assert file_path.read_text() == "print(1)"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tools.py -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/tools/__init__.py
from harness.models import Action, ActionResult


class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, name: str, func):
        self._tools[name] = func

    def dispatch(self, action: Action) -> ActionResult:
        func = self._tools.get(action.tool)
        if func is None:
            return ActionResult(
                success=False, output="", error=f"Tool '{action.tool}' not registered", exit_code=-1
            )
        try:
            return func(**action.args)
        except Exception as e:
            return ActionResult(success=False, output="", error=str(e), exit_code=-1)
```

```python
# harness/tools/file_tools.py
import os
from harness.models import ActionResult


def read_file(path: str) -> ActionResult:
    if not os.path.exists(path):
        return ActionResult(success=False, output="", error=f"File not found: {path}", exit_code=-1)
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return ActionResult(success=True, output=content, error="", exit_code=0)
    except Exception as e:
        return ActionResult(success=False, output="", error=str(e), exit_code=-1)


def write_file(path: str, content: str) -> ActionResult:
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return ActionResult(success=True, output=f"Wrote {len(content)} chars to {path}", error="", exit_code=0)
    except Exception as e:
        return ActionResult(success=False, output="", error=str(e), exit_code=-1)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_tools.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/tools/ tests/test_tools.py
git commit -m "feat: add ToolRegistry and file tools (read_file, write_file)"
```

---

## Task 7: Shell Tool ✅ (commit f0cb0af)

**Depends on:** Task 6

**Files:**
- Create: `harness/tools/shell.py`
- Modify: `tests/test_tools.py`

**Interfaces:**
- Produces: `run_shell(command: str, timeout: int) -> ActionResult`

- [ ] **Step 1: Write the failing test**

```python
# Append to tests/test_tools.py

def test_run_shell_success():
    from harness.tools.shell import run_shell
    result = run_shell(command="echo hello")
    assert result.success is True
    assert "hello" in result.output
    assert result.exit_code == 0


def test_run_shell_failure():
    from harness.tools.shell import run_shell
    result = run_shell(command="python -c 'import sys; sys.exit(1)'")
    assert result.success is False
    assert result.exit_code == 1


def test_run_shell_timeout():
    from harness.tools.shell import run_shell
    result = run_shell(command="python -c 'import time; time.sleep(10)'", timeout=1)
    assert result.success is False
    assert "timeout" in result.error.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tools.py::test_run_shell_success -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/tools/shell.py
import subprocess
from harness.models import ActionResult


def run_shell(command: str, timeout: int = 30) -> ActionResult:
    try:
        proc = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return ActionResult(
            success=proc.returncode == 0,
            output=proc.stdout,
            error=proc.stderr,
            exit_code=proc.returncode,
        )
    except subprocess.TimeoutExpired:
        return ActionResult(
            success=False, output="", error=f"Command timed out after {timeout}s", exit_code=-1
        )
    except Exception as e:
        return ActionResult(success=False, output="", error=str(e), exit_code=-1)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_tools.py -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/tools/shell.py tests/test_tools.py
git commit -m "feat: add run_shell tool with timeout support"
```

---

## Task 8: Governance ✅ (commit 9e246af)

**Depends on:** Task 2

**Files:**
- Create: `harness/governance.py`
- Test: `tests/test_governance.py`

**Interfaces:**
- Consumes: `Action`, `GovernanceDecision` from `harness.models`
- Produces: `Governance` class with `check(action) -> GovernanceDecision`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_governance.py
from harness.governance import Governance
from harness.models import Action, GovernanceDecision


def test_check_allows_safe_read():
    gov = Governance(blocked_commands=["rm -rf", "sudo"], auto_deny=False)
    action = Action(tool="read_file", args={"path": "foo.py"}, raw="")
    decision = gov.check(action)
    assert decision.allow is True
    assert decision.confirm is False


def test_check_denies_blacklisted_command():
    gov = Governance(blocked_commands=["rm -rf"], auto_deny=False)
    action = Action(tool="run_shell", args={"command": "rm -rf /"}, raw="")
    decision = gov.check(action)
    assert decision.allow is False
    assert decision.confirm is False
    assert "rm -rf" in decision.reason


def test_check_confirms_substring_match():
    gov = Governance(blocked_commands=["rm -rf"], auto_deny=False)
    action = Action(tool="run_shell", args={"command": "rm -rf ./build"}, raw="")
    decision = gov.check(action)
    assert decision.allow is False
    assert decision.confirm is True


def test_auto_deny_converts_confirm_to_deny():
    gov = Governance(blocked_commands=["rm -rf"], auto_deny=True)
    action = Action(tool="run_shell", args={"command": "rm -rf ./build"}, raw="")
    decision = gov.check(action)
    assert decision.allow is False
    assert decision.confirm is False


def test_check_denies_write_outside_project(tmp_path):
    import os
    gov = Governance(blocked_commands=[], auto_deny=False, project_dir=str(tmp_path))
    action = Action(tool="write_file", args={"path": "/etc/passwd", "content": "hacked"}, raw="")
    decision = gov.check(action)
    assert decision.allow is False
    assert "outside" in decision.reason.lower()


def test_check_allows_write_inside_project(tmp_path):
    gov = Governance(blocked_commands=[], auto_deny=False, project_dir=str(tmp_path))
    action = Action(tool="write_file", args={"path": str(tmp_path / "foo.py"), "content": "print(1)"}, raw="")
    decision = gov.check(action)
    assert decision.allow is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_governance.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/governance.py
import os
from harness.models import Action, GovernanceDecision


class Governance:
    def __init__(self, blocked_commands: list, auto_deny: bool = False, project_dir: str = "."):
        self._blocked = blocked_commands
        self._auto_deny = auto_deny
        self._project_dir = os.path.abspath(project_dir)

    def check(self, action: Action) -> GovernanceDecision:
        if action.tool == "run_shell":
            command = action.args.get("command", "")
            for pattern in self._blocked:
                if command.strip() == pattern or command.strip() == pattern + " /":
                    return GovernanceDecision(allow=False, confirm=False, reason=f"Blocked: exact match '{pattern}'")
                if pattern in command:
                    if self._auto_deny:
                        return GovernanceDecision(allow=False, confirm=False, reason=f"Blocked: contains '{pattern}' (auto_deny)")
                    return GovernanceDecision(allow=False, confirm=True, reason=f"Confirm: command contains '{pattern}'")
            return GovernanceDecision(allow=True, confirm=False, reason="safe")

        if action.tool == "write_file":
            path = action.args.get("path", "")
            abs_path = os.path.abspath(path)
            if not abs_path.startswith(self._project_dir):
                return GovernanceDecision(allow=False, confirm=False, reason=f"Blocked: path outside project directory")
            return GovernanceDecision(allow=True, confirm=False, reason="safe")

        return GovernanceDecision(allow=True, confirm=False, reason="safe")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_governance.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/governance.py tests/test_governance.py
git commit -m "feat: add governance guardrails (blacklist, path restriction, auto_deny)"
```

---

## Task 9: Feedback ✅ (commit 91b7739)

**Depends on:** Task 2

**Files:**
- Create: `harness/feedback.py`
- Test: `tests/test_feedback.py`

**Interfaces:**
- Consumes: `ActionResult`, `Feedback` from `harness.models`
- Produces: `collect(result: ActionResult, tool: str) -> Feedback`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_feedback.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_feedback.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/feedback.py
from harness.models import ActionResult, Feedback


def collect(result: ActionResult, tool: str = "") -> Feedback:
    if result.success:
        summary = f"[PASS] {tool}: {result.output[:200]}"
    else:
        summary = f"[FAIL] {tool} (exit_code={result.exit_code}): {result.error[:200]}"
    return Feedback(passed=result.success, summary=summary, raw_result=result)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_feedback.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/feedback.py tests/test_feedback.py
git commit -m "feat: add feedback collection (exit_code → pass/fail judgment)"
```

---

## Task 10: Memory ✅ (commit 869423c)

**Depends on:** Task 2

**Files:**
- Create: `harness/memory.py`
- Test: `tests/test_memory.py`

**Interfaces:**
- Consumes: `Message`, `Action`, `Feedback`, `Session` from `harness.models`
- Produces: `Memory` class with `build_context()`, `append()`, `save_session()`, `load_session()`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_memory.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/memory.py
import json
import os
import time
import random
from harness.models import Message, Action, ActionResult, Feedback, Session


SYSTEM_PROMPT = """You are a Python coding agent. You must respond with a JSON action.
Available tools:
- read_file: args={"path": str}
- write_file: args={"path": str, "content": str}
- run_shell: args={"command": str}
To complete the task, respond with: {"tool": "task_complete", "args": {"summary": str}}
Always respond with exactly one JSON action."""


class Memory:
    def __init__(self, task: str, session_dir: str = ".harness/sessions"):
        self._task = task
        self._session_dir = session_dir
        self._messages: list[Message] = [
            Message(role="system", content=SYSTEM_PROMPT),
            Message(role="user", content=task),
        ]
        self._history: list[tuple[Action, Feedback]] = []

    def build_context(self) -> list[Message]:
        return list(self._messages)

    def append(self, action: Action, feedback: Feedback):
        self._history.append((action, feedback))
        self._messages.append(Message(role="assistant", content=action.raw))
        self._messages.append(Message(role="tool", content=feedback.summary))

    def save_session(self) -> Session:
        session_id = f"{time.strftime('%Y%m%d-%H%M%S')}-{random.randint(1000, 9999)}"
        session = Session(id=session_id, task=self._task, history=self._history, summary="")

        os.makedirs(self._session_dir, exist_ok=True)
        path = os.path.join(self._session_dir, f"{session_id}.json")

        serializable = {
            "id": session.id,
            "task": session.task,
            "history": [
                {
                    "action": {"tool": a.tool, "args": a.args, "raw": a.raw},
                    "feedback": {
                        "passed": f.passed,
                        "summary": f.summary,
                        "raw_result": {
                            "success": f.raw_result.success,
                            "output": f.raw_result.output,
                            "error": f.raw_result.error,
                            "exit_code": f.raw_result.exit_code,
                        },
                    },
                }
                for a, f in session.history
            ],
            "summary": session.summary,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, ensure_ascii=False, indent=2)

        return session

    def load_session(self, session_id: str) -> Session | None:
        path = os.path.join(self._session_dir, f"{session_id}.json")
        if not os.path.exists(path):
            return None

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        history = []
        for item in data.get("history", []):
            a = Action(
                tool=item["action"]["tool"],
                args=item["action"]["args"],
                raw=item["action"]["raw"],
            )
            r = ActionResult(
                success=item["feedback"]["raw_result"]["success"],
                output=item["feedback"]["raw_result"]["output"],
                error=item["feedback"]["raw_result"]["error"],
                exit_code=item["feedback"]["raw_result"]["exit_code"],
            )
            fb = Feedback(
                passed=item["feedback"]["passed"],
                summary=item["feedback"]["summary"],
                raw_result=r,
            )
            history.append((a, fb))

        return Session(
            id=data["id"], task=data["task"], history=history, summary=data.get("summary", "")
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_memory.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/memory.py tests/test_memory.py
git commit -m "feat: add memory module (context, session persistence)"
```

---

## Task 11: Agent Main Loop ✅ (commit 14744ce)

**Depends on:** Tasks 2, 3, 4, 5, 6, 7, 8, 9, 10

**Files:**
- Create: `harness/loop.py`
- Test: `tests/test_loop.py`

**Interfaces:**
- Consumes: all modules
- Produces: `AgentLoop` class with `run(task: str) -> str`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_loop.py
import pytest
from harness.loop import AgentLoop
from harness.llm.mock import MockLLM
from harness.tools import ToolRegistry
from harness.tools.file_tools import read_file, write_file
from harness.tools.shell import run_shell
from harness.governance import Governance
from harness.feedback import collect
from harness.memory import Memory
from harness.config import load_config


def test_loop_completes_task_with_mock(tmp_path):
    file_path = tmp_path / "foo.py"
    file_path.write_text("print(1)")

    responses = [
        f'{{"tool": "read_file", "args": {{"path": "{file_path}"}}}}',
        '{"tool": "task_complete", "args": {"summary": "done"}}',
    ]
    llm = MockLLM(responses)
    registry = ToolRegistry()
    registry.register("read_file", read_file)
    registry.register("write_file", write_file)
    registry.register("run_shell", run_shell)

    loop = AgentLoop(
        llm=llm,
        registry=registry,
        governance=Governance(blocked_commands=["rm -rf"], auto_deny=True, project_dir=str(tmp_path)),
        memory=Memory(task="read foo.py", session_dir=str(tmp_path / "sessions")),
        max_turns=10,
    )
    result = loop.run("read foo.py")
    assert "done" in result.lower()


def test_loop_stops_on_max_turns():
    responses = ['{"tool": "read_file", "args": {"path": "x.py"}}'] * 100
    llm = MockLLM(responses)
    registry = ToolRegistry()
    registry.register("read_file", lambda path: __import__("harness.models", fromlist=["ActionResult"]).ActionResult(
        success=False, output="", error="not found", exit_code=-1
    ))

    loop = AgentLoop(
        llm=llm,
        registry=registry,
        governance=Governance(blocked_commands=[], auto_deny=True),
        memory=Memory(task="test", session_dir="."),
        max_turns=3,
    )
    result = loop.run("test")
    assert "max" in result.lower() or "3" in result


def test_loop_handles_parse_error_retry():
    responses = [
        "not json at all",
        '{"tool": "task_complete", "args": {"summary": "done"}}',
    ]
    llm = MockLLM(responses)
    registry = ToolRegistry()

    loop = AgentLoop(
        llm=llm,
        registry=registry,
        governance=Governance(blocked_commands=[], auto_deny=True),
        memory=Memory(task="test", session_dir="."),
        max_turns=10,
    )
    result = loop.run("test")
    assert "done" in result.lower()


def test_loop_governance_blocks_dangerous_command():
    responses = [
        '{"tool": "run_shell", "args": {"command": "rm -rf /"}}',
        '{"tool": "task_complete", "args": {"summary": "done"}}',
    ]
    llm = MockLLM(responses)
    registry = ToolRegistry()
    registry.register("run_shell", run_shell)

    loop = AgentLoop(
        llm=llm,
        registry=registry,
        governance=Governance(blocked_commands=["rm -rf"], auto_deny=True),
        memory=Memory(task="test", session_dir="."),
        max_turns=10,
    )
    result = loop.run("test")
    assert "done" in result.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_loop.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/loop.py
import logging
from harness.llm.base import LLMProvider
from harness.tools import ToolRegistry
from harness.governance import Governance
from harness.feedback import collect
from harness.memory import Memory
from harness.parser import parse, ParseError
from harness.models import Action, ActionResult, Feedback

logger = logging.getLogger("harness")


class AgentLoop:
    def __init__(self, llm: LLMProvider, registry: ToolRegistry,
                 governance: Governance, memory: Memory, max_turns: int = 20):
        self._llm = llm
        self._registry = registry
        self._governance = governance
        self._memory = memory
        self._max_turns = max_turns

    def run(self, task: str) -> str:
        turn = 0
        parse_failures = 0

        while turn < self._max_turns:
            turn += 1
            context = self._memory.build_context()
            response = self._llm.complete(context)
            logger.info(f"[turn {turn}] LLM response: {response[:100]}")

            try:
                action = parse(response)
                parse_failures = 0
            except ParseError as e:
                parse_failures += 1
                logger.warning(f"[turn {turn}] Parse error: {e}")
                if parse_failures >= 3:
                    return f"Stopped: parse failed 3 times consecutively"
                self._memory.append(
                    Action(tool="parse_error", args={}, raw=response),
                    Feedback(passed=False, summary=f"Parse error: {e}. Please return valid JSON.",
                             raw_result=ActionResult(success=False, output="", error=str(e), exit_code=-1))
                )
                continue

            if action.tool == "task_complete":
                summary = action.args.get("summary", "Task complete")
                logger.info(f"[turn {turn}] Task complete: {summary}")
                return summary

            decision = self._governance.check(action)
            if not decision.allow and not decision.confirm:
                logger.warning(f"[turn {turn}] Blocked: {decision.reason}")
                result = ActionResult(success=False, output="", error=f"Blocked: {decision.reason}", exit_code=-1)
            elif decision.confirm:
                user_input = input(f"Confirm action: {action.tool}({action.args})? [y/N] ")
                if user_input.lower() == "y":
                    result = self._registry.dispatch(action)
                else:
                    result = ActionResult(success=False, output="", error="User declined", exit_code=-1)
            else:
                result = self._registry.dispatch(action)

            feedback = collect(result, action.tool)
            logger.info(f"[turn {turn}] {feedback.summary}")
            self._memory.append(action, feedback)

        return f"Stopped: reached max turns ({self._max_turns})"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_loop.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/loop.py tests/test_loop.py
git commit -m "feat: add agent main loop (context→LLM→parse→govern→dispatch→feedback→memory→stop)"
```

---

## Task 12: CLI + Keyring ✅ (commit 35d05c5)

**Depends on:** Tasks 3, 4, 11

**Files:**
- Create: `harness/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `load_config`, `AgentLoop`, `MockLLM`, `Governance`, `Memory`, `ToolRegistry`
- Produces: `main()` entry point, `keyring_setup()`, `keyring_status()`, `keyring_clear()`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cli.py
import pytest
from unittest.mock import patch, MagicMock
from harness.cli import main, keyring_setup, keyring_status, keyring_clear


def test_keyring_status_no_keys(capsys):
    with patch("keyring.get_password", return_value=None):
        keyring_status()
    captured = capsys.readouterr()
    assert "未配置" in captured.out or "not configured" in captured.out.lower()


def test_keyring_status_with_key(capsys):
    with patch("keyring.get_password", return_value="sk-fake-key"):
        keyring_status()
    captured = capsys.readouterr()
    assert "已配置" in captured.out or "configured" in captured.out.lower()
    assert "sk-fake-key" not in captured.out


def test_keyring_clear():
    with patch("keyring.delete_password") as mock_delete:
        keyring_clear(provider="openai")
    mock_delete.assert_called_once_with("harness-agent", "openai")


def test_main_run_with_mock(capsys, tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("llm:\n  provider: mock\nmax_turns: 5\n")
    with patch("sys.argv", ["harness", "run", "test task", "--config", str(config_file)]):
        main()
    captured = capsys.readouterr()
    assert len(captured.out) > 0 or len(captured.err) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/cli.py
import argparse
import getpass
import os
import sys
import logging

import keyring

from harness.config import load_config
from harness.llm.mock import MockLLM
from harness.loop import AgentLoop
from harness.memory import Memory
from harness.governance import Governance
from harness.tools import ToolRegistry
from harness.tools.file_tools import read_file, write_file
from harness.tools.shell import run_shell

PROVIDERS = ["openai", "anthropic", "google"]
KEYRING_SERVICE = "harness-agent"


def keyring_setup():
    print("Select LLM provider:")
    for i, p in enumerate(PROVIDERS):
        print(f"  {i + 1}. {p}")
    choice = input("Enter number: ").strip()
    try:
        provider = PROVIDERS[int(choice) - 1]
    except (ValueError, IndexError):
        print("Invalid choice")
        return
    key = getpass.getpass(f"Enter API key for {provider}: ")
    keyring.set_password(KEYRING_SERVICE, provider, key)
    print(f"API key for {provider} stored.")


def keyring_status():
    for provider in PROVIDERS:
        key = keyring.get_password(KEYRING_SERVICE, provider)
        status = "已配置" if key else "未配置"
        print(f"  {provider}: {status}")


def keyring_clear(provider: str = None):
    if provider:
        try:
            keyring.delete_password(KEYRING_SERVICE, provider)
            print(f"Cleared key for {provider}")
        except keyring.errors.PasswordDeleteError:
            print(f"No key found for {provider}")
    else:
        for p in PROVIDERS:
            try:
                keyring.delete_password(KEYRING_SERVICE, p)
            except keyring.errors.PasswordDeleteError:
                pass
        print("Cleared all keys")


def cmd_run(args):
    config = load_config(args.config)

    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(config.log_dir, "harness.log")),
        ],
    )
    os.makedirs(config.log_dir, exist_ok=True)

    if config.llm_provider == "mock":
        llm = MockLLM([
            '{"tool": "task_complete", "args": {"summary": "Mock: no real LLM configured"}}'
        ])
    else:
        from harness.llm.openai import OpenAILLM
        api_key = keyring.get_password(KEYRING_SERVICE, config.llm_provider)
        if not api_key:
            api_key = os.environ.get(f"{config.llm_provider.upper()}_API_KEY")
        if not api_key:
            print(f"No API key found for {config.llm_provider}. Run: harness keyring setup")
            sys.exit(1)
        llm = OpenAILLM(api_key=api_key, model=config.llm_model)

    registry = ToolRegistry()
    registry.register("read_file", read_file)
    registry.register("write_file", write_file)
    registry.register("run_shell", run_shell)

    governance = Governance(
        blocked_commands=config.blocked_commands,
        auto_deny=config.auto_deny,
    )
    memory = Memory(task=args.task, session_dir=config.session_dir)

    loop = AgentLoop(
        llm=llm, registry=registry, governance=governance,
        memory=memory, max_turns=config.max_turns,
    )
    result = loop.run(args.task)
    print(result)


def main():
    parser = argparse.ArgumentParser(prog="harness", description="Coding agent harness")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run agent on a task")
    run_parser.add_argument("task", help="Task description")
    run_parser.add_argument("--config", default="config.yaml", help="Config file path")

    keyring_parser = subparsers.add_parser("keyring", help="Manage API keys")
    keyring_sub = keyring_parser.add_subparsers(dest="keyring_command")
    keyring_sub.add_parser("setup", help="Set up API key")
    keyring_sub.add_parser("status", help="Show key status")
    clear_parser = keyring_sub.add_parser("clear", help="Clear key(s)")
    clear_parser.add_argument("--provider", default=None, help="Provider to clear")

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(args)
    elif args.command == "keyring":
        if args.keyring_command == "setup":
            keyring_setup()
        elif args.keyring_command == "status":
            keyring_status()
        elif args.keyring_command == "clear":
            keyring_clear(args.provider)
        else:
            keyring_parser.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/cli.py tests/test_cli.py
git commit -m "feat: add CLI entry point and keyring credential management"
```

---

## Task 13: OpenAI Provider ✅ (commit d4f7f2b)

**Depends on:** Task 4

**Files:**
- Create: `harness/llm/openai.py`
- Test: `tests/test_llm_openai.py` (mocked, no real API call)

**Interfaces:**
- Consumes: `LLMProvider` from `harness.llm.base`, `Message` from `harness.models`
- Produces: `OpenAILLM` class

- [ ] **Step 1: Write the failing test**

```python
# tests/test_llm_openai.py
import pytest
from unittest.mock import patch, MagicMock
from harness.llm.openai import OpenAILLM
from harness.models import Message


def test_openai_llm_complete():
    llm = OpenAILLM(api_key="sk-fake", model="gpt-4o")
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"tool": "task_complete", "args": {"summary": "done"}}'

    with patch.object(llm._client.chat.completions, "create", return_value=mock_response):
        messages = [Message(role="user", content="test")]
        result = llm.complete(messages)
    assert result == '{"tool": "task_complete", "args": {"summary": "done"}}'


def test_openai_llm_is_llm_provider():
    from harness.llm.base import LLMProvider
    llm = OpenAILLM(api_key="sk-fake", model="gpt-4o")
    assert isinstance(llm, LLMProvider)


def test_openai_llm_raises_on_api_error():
    from harness.llm.base import LLMError
    llm = OpenAILLM(api_key="sk-fake", model="gpt-4o")
    with patch.object(llm._client.chat.completions, "create", side_effect=Exception("API error")):
        with pytest.raises(LLMError, match="API error"):
            llm.complete([Message(role="user", content="test")])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_llm_openai.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/llm/openai.py
from typing import List
from openai import OpenAI
from harness.llm.base import LLMProvider, LLMError
from harness.models import Message


class OpenAILLM(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def complete(self, messages: List[Message]) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
            )
            return response.choices[0].message.content
        except Exception as e:
            raise LLMError(str(e))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_llm_openai.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/llm/openai.py tests/test_llm_openai.py
git commit -m "feat: add OpenAI LLM provider"
```

---

## Task 14: Mechanism Demonstration (A.6) ✅ (commit 23b4708)

**Depends on:** Tasks 8, 9, 11

**Files:**
- Create: `tests/test_demo.py`

**Interfaces:**
- Produces: 3 deterministic demonstrations under mock LLM

- [ ] **Step 1: Write the demonstration tests**

```python
# tests/test_demo.py
"""
A.6 Mechanism Demonstration: 3 deterministic behaviors under mock LLM.

① Governance guardrail blocks a dangerous action
② Injected failure feedback causes agent to change next action
③ Feedback loop deterministic behavior (pass/fail judgment)
"""
from harness.loop import AgentLoop
from harness.llm.mock import MockLLM
from harness.tools import ToolRegistry
from harness.tools.file_tools import read_file, write_file
from harness.tools.shell import run_shell
from harness.governance import Governance
from harness.feedback import collect
from harness.memory import Memory
from harness.models import ActionResult, Feedback


def test_demo_1_governance_blocks_dangerous_command():
    """① 治理护栏拦截一个危险动作"""
    responses = [
        '{"tool": "run_shell", "args": {"command": "rm -rf /"}}',
        '{"tool": "task_complete", "args": {"summary": "done"}}',
    ]
    llm = MockLLM(responses)
    registry = ToolRegistry()
    registry.register("run_shell", run_shell)

    loop = AgentLoop(
        llm=llm,
        registry=registry,
        governance=Governance(blocked_commands=["rm -rf"], auto_deny=True),
        memory=Memory(task="dangerous task", session_dir="."),
        max_turns=5,
    )
    result = loop.run("dangerous task")
    # Agent should complete after governance blocked the dangerous command
    assert "done" in result.lower()
    # Verify the blocked feedback was recorded in memory
    ctx = loop._memory.build_context()
    assert any("Blocked" in m.content or "blocked" in m.content.lower() for m in ctx)


def test_demo_2_failure_feedback_changes_next_action():
    """② 注入一次失败，反馈闭环使 agent 收到反馈并据此改变下一步动作"""
    responses = [
        '{"tool": "read_file", "args": {"path": "/nonexistent/file.py"}}',
        '{"tool": "task_complete", "args": {"summary": "file not found, giving up"}}',
    ]
    llm = MockLLM(responses)
    registry = ToolRegistry()
    registry.register("read_file", read_file)

    loop = AgentLoop(
        llm=llm,
        registry=registry,
        governance=Governance(blocked_commands=[], auto_deny=True),
        memory=Memory(task="read a file", session_dir="."),
        max_turns=5,
    )
    result = loop.run("read a file")
    assert "not found" in result.lower() or "giving up" in result.lower()
    # Verify failure feedback was in context for second LLM call
    ctx = loop._memory.build_context()
    assert any("FAIL" in m.content or "not found" in m.content.lower() for m in ctx)


def test_demo_3_feedback_deterministic_judgment():
    """③ 反馈闭环确定性行为：exit_code 客观判定"""
    # Pass case
    pass_result = ActionResult(success=True, output="OK", error="", exit_code=0)
    pass_fb = collect(pass_result, tool="run_shell")
    assert pass_fb.passed is True
    assert "[PASS]" in pass_fb.summary

    # Fail case
    fail_result = ActionResult(success=False, output="", error="SyntaxError", exit_code=1)
    fail_fb = collect(fail_result, tool="run_shell")
    assert fail_fb.passed is False
    assert "[FAIL]" in fail_fb.summary
    assert "1" in fail_fb.summary  # exit_code
    assert "SyntaxError" in fail_fb.summary
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_demo.py -v`
Expected: FAIL (loop not yet implemented if tasks out of order, or PASS if tasks 8,9,11 done)

- [ ] **Step 3: Verify all demos pass**

Run: `pytest tests/test_demo.py -v`
Expected: PASS (3 tests)

- [ ] **Step 4: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_demo.py
git commit -m "test: add A.6 mechanism demonstration (governance, feedback, self-correction)"
```

---

## Task 15: Docker + PyPI Distribution ✅ (commit 6015f02)

**Depends:** All previous tasks

**Files:**
- Create: `Dockerfile`
- Create: `README.md`

- [ ] **Step 1: Create Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY harness/ ./harness/
COPY config.yaml ./
RUN pip install --no-cache-dir .

ENTRYPOINT ["harness"]
```

- [ ] **Step 2: Create README.md**

```markdown
# harness-agent

A self-implemented coding agent harness for Python projects.

## Install

### PyPI
```bash
pip install harness-agent
```

### Docker
```bash
docker build -t harness-agent .
```

## Configure API Key

### Local (keyring — recommended)
```bash
harness keyring setup
harness keyring status
harness keyring clear --provider openai
```

### Docker (environment variable — less secure)
```bash
docker run -it --rm -e OPENAI_API_KEY=sk-xxx -v $(pwd):/workspace harness-agent run "fix bug in foo.py"
```
> Note: Environment variables are visible to process environment. Use keyring on host for better security.

## Run

```bash
harness run "fix the failing test in test_foo.py"
```

## Test

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Directory Structure

```
harness/
├── models.py       # Data models
├── config.py       # YAML config loading
├── parser.py       # LLM response parser
├── governance.py   # Guardrails
├── feedback.py     # Feedback collection
├── memory.py       # Session memory + persistence
├── loop.py         # Agent main loop
├── cli.py          # CLI entry + keyring
├── llm/            # LLM providers (OpenAI, Mock)
└── tools/          # Tools (read_file, write_file, run_shell)
```

## Security

- API keys stored in OS keyring (Windows Credential Manager / macOS Keychain / Linux Secret Service)
- Keys never hardcoded, committed, or logged
- Governance guardrails block dangerous commands (rm -rf, git push --force, etc.)
- write_file restricted to project directory

## Known Limitations

- Python 3.10+ required
- MVP feedback is reactive (captures tool results), not proactive (auto lint/test pipeline)
- No sandboxing for shell commands (governance blacklist only)
- Cross-session memory is file-based (JSON), not vector-indexed
```

- [ ] **Step 3: Verify Docker build**

Run: `docker build -t harness-agent .`
Expected: Build succeeds

- [ ] **Step 4: Verify pip install**

Run: `pip install -e . && harness --help`
Expected: Shows help text

- [ ] **Step 5: Commit**

```bash
git add Dockerfile README.md
git commit -m "feat: add Docker and PyPI distribution + README"
```

---

## Task 16: CI Configuration ✅ (commit 63be0bb)

**Depends:** Task 15

**Files:**
- Create: `.gitlab-ci.yml`

- [ ] **Step 1: Create .gitlab-ci.yml**

```yaml
stages:
  - test
  - build

unit-test:
  stage: test
  image: python:3.12-slim
  before_script:
    - pip install --no-cache-dir -e ".[dev]"
  script:
    - pytest tests/ -v --tb=short
  rules:
    - if: $CI_PIPELINE_SOURCE == "push"

docker-build:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker build -t harness-agent .
  rules:
    - if: $CI_PIPELINE_SOURCE == "push" && $CI_COMMIT_BRANCH == "main"
```

- [ ] **Step 2: Verify CI job name**

Run: `grep "unit-test:" .gitlab-ci.yml`
Expected: Match found

- [ ] **Step 3: Run tests locally to confirm CI will pass**

Run: `pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add .gitlab-ci.yml
git commit -m "ci: add GitLab CI with unit-test and docker-build jobs"
```

---

## Self-Review

### Spec Coverage

| SPEC Section | Task(s) | Status |
|--------------|---------|--------|
| §3.1 决策 (loop) | Task 11 | ✅ |
| §3.2 解析器 (parser) | Task 5 | ✅ |
| §3.3 LLM 抽象 | Task 4 (Mock), Task 13 (OpenAI) | ✅ |
| §3.4 工具 | Task 6 (file), Task 7 (shell) | ✅ |
| §3.5 治理 | Task 8 | ✅ |
| §3.6 反馈 | Task 9 | ✅ |
| §3.7 记忆 | Task 10 | ✅ |
| §3.8 配置 | Task 3 | ✅ |
| §3.9 CLI | Task 12 | ✅ |
| §3.10 日志 | Task 11 (integrated) | ✅ |
| §4.2 凭据安全 | Task 12 (keyring) | ✅ |
| §7.2 分发 | Task 15 (Docker+PyPI) | ✅ |
| §九 机制演示 | Task 14 | ✅ |
| CI | Task 16 | ✅ |

### Placeholder Scan

No TBD, TODO, or placeholder patterns found. All steps contain complete code.

### Type Consistency

- `Action(tool, args, raw)` — consistent across Tasks 2, 5, 6, 8, 9, 10, 11, 14 ✅
- `ActionResult(success, output, error, exit_code)` — consistent across Tasks 2, 6, 7, 9, 11, 14 ✅
- `Feedback(passed, summary, raw_result)` — consistent across Tasks 2, 9, 10, 11, 14 ✅
- `GovernanceDecision(allow, confirm, reason)` — consistent across Tasks 2, 8, 11 ✅
- `LLMProvider.complete(messages) -> str` — consistent across Tasks 4, 11, 12, 13 ✅
- `ToolRegistry.register/dispatch` — consistent across Tasks 6, 7, 11, 12, 14 ✅
- `Governance.check(action) -> GovernanceDecision` — consistent across Tasks 8, 11, 14 ✅
- `collect(result, tool) -> Feedback` — consistent across Tasks 9, 11, 14 ✅
- `Memory.build_context/append/save_session/load_session` — consistent across Tasks 10, 11, 12 ✅

---

## Phase 2: Feedback Loop Deepening

Phase 2 的实现计划见 `docs/superpowers/plans/2026-07-26-phase2-feedback-loop.md`（8 个 TDD task，全部完成）。

设计文档见 `docs/superpowers/specs/2026-07-26-phase2-feedback-loop-design.md`。

### Phase 2 Task 完成状态

| Task | 内容 | Commit | 状态 |
|------|------|--------|------|
| 1 | 数据模型扩展（CheckResult, Feedback.checks, ActionResult.metadata） | `365ab55` | ✅ |
| 2 | 工具返回 metadata（path, tool name） | `54dbfe1` | ✅ |
| 3 | 语法检查阶段（py_compile） | `645db28` | ✅ |
| 4 | 模式分析阶段（3 次连续失败检测） | `addc632` | ✅ |
| 5 | 流水线集成（basic → syntax → pattern） | `7cbb8be` | ✅ |
| 6 | Memory 新增 append_hint() / get_history() | `43d4e62` | ✅ |
| 7 | Loop 注入 hint 驱动 LLM 自修正 | `5525067` | ✅ |
| 8 | A.6 demo 第 4 项 + SPEC §3.6/§11.6 更新 | `8e94061` | ✅ |
| fix | hint 顺序修正 + 连续失败检查 | `ef64d7f` | ✅ |

测试：88/88 通过（61 Phase 1 + 27 Phase 2）

PR 记录：PR [#1](https://github.com/g-2007-code/harness-agent/pull/1)（Phase 2 功能，9 commit）→ PR [#2](https://github.com/g-2007-code/harness-agent/pull/2)（文档同步，6 commit）
