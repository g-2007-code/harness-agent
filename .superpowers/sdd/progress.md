# Progress Ledger

## Completed Tasks
- Task 1: scaffolding (commit 821a4a0)
- Task 2: data models (commit bf4899f)
- Task 3: config loading (commit dc6fb20)
- Task 4: LLM abstraction + mock (commit f93e962)
- Task 5: parser (commit 715711c)
- Task 6: tool registry + file tools (commit 82e5f6d)
- Task 7: shell tool (commit f0cb0af) — fixed Windows quote compat
- Task 8: governance (commit 9e246af)
- Task 9: feedback (commit 91b7739)
- Task 10: memory (commit 869423c)
- Task 11: agent main loop (commit 14744ce)
- Task 12: CLI + keyring (commit 35d05c5) — fixed logging order bug
- Task 13: OpenAI provider (commit d4f7f2b)
- Task 14: mechanism demonstration (commit 23b4708)
- Task 15: Docker + PyPI (commit 6015f02) — fixed pyproject.toml build-backend
- Task 16: CI config (commit 63be0bb)

## Test Results
- 57/57 tests passing
- Full suite: pytest tests/ -v

## Issues Found & Fixed During Implementation
1. Task 7: Windows cmd.exe doesn't support single quotes in `python -c '...'` — changed to double quotes
2. Task 7: Test assertion "timeout" didn't match implementation "timed out" — aligned assertion to implementation
3. Task 12: logging.basicConfig with FileHandler called before os.makedirs — moved makedirs first
4. Task 15: pyproject.toml build-backend was invalid — changed to setuptools.build_meta
