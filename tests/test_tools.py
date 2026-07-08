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


def test_run_shell_success():
    from harness.tools.shell import run_shell
    result = run_shell(command="echo hello")
    assert result.success is True
    assert "hello" in result.output
    assert result.exit_code == 0


def test_run_shell_failure():
    from harness.tools.shell import run_shell
    result = run_shell(command='python -c "import sys; sys.exit(1)"')
    assert result.success is False
    assert result.exit_code == 1


def test_run_shell_timeout():
    from harness.tools.shell import run_shell
    result = run_shell(command='python -c "import time; time.sleep(10)"', timeout=1)
    assert result.success is False
    assert "timed out" in result.error.lower()
