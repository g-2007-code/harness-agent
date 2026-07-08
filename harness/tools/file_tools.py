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
