# harness-agent

A self-implemented coding agent harness for Python projects. Built from scratch (no LangChain/AutoGen) with 6 dimensions: decision loop, tools, governance, feedback, memory, and config.

## Features

- **Self-implemented agent main loop**: context assembly → LLM call → response parsing → governance check → tool dispatch → feedback collection → memory append → stop check
- **Multi-stage feedback pipeline** (Phase 2): basic check → syntax check (py_compile) → pattern analysis (consecutive failure detection) → hint injection drives LLM self-correction
- **Pluggable LLM abstraction**: OpenAI, DeepSeek, Mock (for testing)
- **Code-level governance guardrails**: blacklist blocking, path restriction, HITL confirmation
- **Terminal UI (TUI)**: rich-based real-time display of Task/Turn/Action/Result/Complete panels
- **Cross-session memory**: conversation history + JSON persistence + hint injection
- **Credential security**: OS keyring storage, never hardcoded/committed/logged
- **Docker + PyPI distribution**: one command install/run

## Quick Start

### 1. Install

```bash
# From source (development)
git clone <repo-url>
cd harness-agent
pip install -e ".[dev]"

# Or from PyPI (when published)
pip install harness-agent
```

### 2. Configure API Key

```bash
# Store API key in OS keyring (recommended)
# Input is hidden when typing — this is a security feature (getpass)
# Just type/paste your key and press Enter
harness keyring setup
# → Select provider (e.g., 2 for deepseek)
# → Enter API key (hidden input)
# → "API key for deepseek stored."

# Verify (never displays the key itself)
harness keyring status
# → deepseek: 已配置

# Update key (run setup again, overwrites)
harness keyring setup

# Clear key
harness keyring clear --provider deepseek
# Or clear all
harness keyring clear
```

### 3. Create config.yaml

```yaml
llm:
  provider: deepseek              # openai / deepseek / mock
  model: deepseek-chat            # deepseek-chat / gpt-4o / etc.
  base_url: "https://api.deepseek.com"  # omit for OpenAI, required for DeepSeek
max_turns: 20
governance:
  blocked_commands:
    - "rm -rf"
    - "git push --force"
    - "curl"
    - "wget"
    - "chmod 777"
    - "sudo"
  auto_deny: false                 # true = auto-reject confirmations (CI mode)
session:
  dir: ".harness/sessions"
logging:
  level: info                     # debug / info / warning / error
  dir: ".harness/logs"
```

### 4. Run

```bash
# Run in current directory
harness run "fix the syntax error in foo.py" --config config.yaml

# Run without --config (defaults to ./config.yaml)
harness run "add a test for the add function in math_utils.py"
```

## Usage Examples

### Fix a bug

```bash
# Create a file with a bug
echo "def add(a, b)\n    return a + b" > bug.py

# Ask the agent to fix it
harness run "读取 bug.py，找出语法错误并修复，然后运行验证" --config config.yaml
```

Agent workflow:
1. Reads `bug.py` → sees missing colon
2. Runs `python bug.py` → gets `SyntaxError`
3. Writes fixed file
4. Runs `python bug.py` → success
5. Returns `task_complete`

### Use in another directory

```bash
# harness is globally installed after `pip install -e .`
# Just create a config.yaml in any directory and run:

cd /path/to/another/project
cp /path/to/harness-agent/config.yaml .
harness run "explain what main.py does" --config config.yaml
```

### Docker

```bash
# Build
docker build -t harness-agent .

# Run (mount your project, pass key via env var)
docker run -it --rm \
  -e DEEPSEEK_API_KEY=sk-xxx \
  -v $(pwd):/workspace \
  -w /workspace \
  harness-agent run "fix bug in foo.py"
```

> **Security note**: Environment variables are visible to the process environment. Use keyring on the host for better security. Docker env var is a fallback for containerized environments.

## CLI Commands

```
harness run "task description" [--config config.yaml]
    Run the agent on a task.

harness keyring setup
    Interactively store an API key (hidden input via getpass).
    If key already exists, it will be overwritten (update).

harness keyring status
    Show which providers have keys configured.
    Never displays the actual key value.

harness keyring clear [--provider openai]
    Clear a specific provider's key, or all keys if no --provider specified.
```

## Testing

```bash
# Run all tests (88 tests, no network needed)
pytest tests/ -v

# Run mechanism demonstrations (A.6)
pytest tests/test_demo.py -v

# Run with coverage
pytest tests/ --cov=harness
```

## CI Status

GitHub Actions runs on every push. Latest status:
- **unit-test**: 88 tests, all pass
- **docker-build**: Docker image builds successfully

Two historical PRs: [#1 Phase 2: Feedback Loop Deepening](https://github.com/g-2007-code/harness-agent/pull/1) → [#2 Docs sync](https://github.com/g-2007-code/harness-agent/pull/2)

## Directory Structure

```
harness-agent/
├── harness/
│   ├── __init__.py
│   ├── models.py          # Data models (Message, Action, ActionResult, Feedback, etc.)
│   ├── config.py          # YAML config loading with defaults
│   ├── parser.py          # Parse LLM JSON response → Action
│   ├── governance.py      # Guardrails: blacklist, path restriction, auto_deny
│   ├── feedback.py        # Multi-stage pipeline: basic → syntax check → pattern analysis
│   ├── memory.py          # Session context + cross-session JSON persistence + hint injection
│   ├── loop.py            # Agent main loop (6-step cycle + hint injection)
│   ├── cli.py             # CLI entry + keyring subcommands + TUI integration
│   ├── tui.py             # Terminal UI renderer (rich-based callback)
│   ├── llm/
│   │   ├── __init__.py    # Exports LLMProvider, LLMError
│   │   ├── base.py        # LLMProvider ABC + LLMError
│   │   ├── mock.py        # MockLLM (deterministic, script-based, for testing)
│   │   └── openai.py      # OpenAILLM (OpenAI + DeepSeek via base_url)
│   └── tools/
│       ├── __init__.py    # ToolRegistry (register + dispatch)
│       ├── file_tools.py  # read_file, write_file
│       └── shell.py       # run_shell (with timeout)
├── tests/
│   ├── conftest.py        # Shared fixtures
│   ├── test_models.py     # 12 tests
│   ├── test_config.py     # 4 tests
│   ├── test_parser.py     # 5 tests
│   ├── test_governance.py # 7 tests
│   ├── test_feedback.py   # 18 tests (pipeline stages)
│   ├── test_memory.py     # 8 tests
│   ├── test_tools.py      # 11 tests
│   ├── test_llm_mock.py   # 4 tests
│   ├── test_llm_openai.py # 3 tests
│   ├── test_loop.py       # 8 tests (incl. hint injection)
│   ├── test_cli.py        # 4 tests
│   └── test_demo.py       # 4 mechanism demonstrations (A.6)
├── config.yaml            # Default config (DeepSeek)
├── Dockerfile             # Docker image
├── pyproject.toml         # Package config
├── .github/workflows/test.yml  # GitHub Actions CI
├── .gitlab-ci.yml         # CI (unit-test + docker-build)
├── SPEC.md                # Design specification
├── PLAN.md                # Implementation plan (16 TDD tasks)
├── SPEC_PROCESS.md        # Brainstorming + cold-start verification
├── AGENT_LOG.md           # Implementation process log
├── REFLECTION.md          # Reflection report
└── FOR_FRESHMEN.md        # Project explanation for beginners
```

## Security

- **API keys** stored in OS keyring (Windows Credential Manager / macOS Keychain / Linux Secret Service)
- Keys **never** hardcoded in source, committed to Git, or written to logs
- **Governance guardrails** block dangerous commands (`rm -rf`, `git push --force`, `curl`, `wget`, `chmod 777`, `sudo`)
- **Path restriction**: `write_file` limited to current working directory and subdirectories
- **HITL confirmation**: dangerous commands (substring match) prompt for user approval (`auto_deny: false`)
- **CI mode**: set `auto_deny: true` to auto-reject all confirmations (non-interactive)
- `.gitignore` excludes `.env`, `.harness/`, `__pycache__/`

## Supported LLM Providers

| Provider | Config `provider` | Config `base_url` | Keyring name |
|----------|-------------------|-------------------|--------------|
| OpenAI | `openai` | (omit) | `openai` |
| DeepSeek | `deepseek` | `https://api.deepseek.com` | `deepseek` |
| Mock (testing) | `mock` | (omit) | (none) |

To add a new OpenAI-compatible provider, just set `provider`, `model`, and `base_url` in config.yaml.

## Known Limitations

- Python 3.10+ required
- Feedback pipeline covers syntax check (py_compile) and pattern analysis; typecheck (mypy) and coverage are future work
- No sandboxing for shell commands (governance blacklist only)
- Cross-session memory is file-based (JSON), not vector-indexed
- System prompt includes platform info (Windows/Linux) to avoid cross-platform command issues
- LLM response must be valid JSON (parser extracts last `{...}` block via regex)

## Mechanism Demonstration (A.6)

Four deterministic demonstrations under mock LLM:

```bash
pytest tests/test_demo.py -v
```

1. **Governance guardrail blocks dangerous action**: agent tries `rm -rf /` → blocked → agent changes approach
2. **Failure feedback changes next action**: agent reads nonexistent file → failure feedback → agent reports "file not found"
3. **Deterministic pass/fail judgment**: `exit_code=0` → `[PASS]`, `exit_code=1` → `[FAIL]` with error details
4. **Feedback pipeline syntax check**: agent writes file with syntax error → py_compile detects it → hint injected → agent rewrites with correct syntax → verified

## License

MIT (see LICENSE file if applicable). Third-party dependencies retain their licenses:
- [openai](https://github.com/openai/openai-python) (Apache 2.0)
- [keyring](https://github.com/jaraco/keyring) (MIT)
- [pyyaml](https://github.com/yaml/pyyaml) (MIT)
- [pytest](https://github.com/pytest-dev/pytest) (MIT)
