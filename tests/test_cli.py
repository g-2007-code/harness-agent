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
