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
