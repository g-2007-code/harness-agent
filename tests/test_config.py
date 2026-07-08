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
