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
