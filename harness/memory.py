# harness/memory.py
import json
import os
import platform
import time
import random
from harness.models import Message, Action, ActionResult, Feedback, Session


def _build_system_prompt() -> str:
    return f"""You are a Python coding agent running on {platform.system()} ({platform.release()}).
Current working directory: {os.getcwd()}
Use platform-appropriate shell commands (e.g., Windows: cmd/PowerShell; Linux/macOS: bash).

You must respond with exactly one JSON action. No explanations, no markdown — just the JSON.
Available tools:
- read_file: args={{"path": str}}
- write_file: args={{"path": str, "content": str}}
- run_shell: args={{"command": str}}
To complete the task, respond with: {{"tool": "task_complete", "args": {{"summary": str}}}}

Important: JSON strings must be properly escaped. Use \\\\n for newlines, \\\\" for quotes inside strings."""


class Memory:
    def __init__(self, task: str, session_dir: str = ".harness/sessions"):
        self._task = task
        self._session_dir = session_dir
        self._messages: list[Message] = [
            Message(role="system", content=_build_system_prompt()),
            Message(role="user", content=task),
        ]
        self._history: list[tuple[Action, Feedback]] = []

    def build_context(self) -> list[Message]:
        return list(self._messages)

    def append(self, action: Action, feedback: Feedback):
        self._history.append((action, feedback))
        self._messages.append(Message(role="assistant", content=action.raw))
        self._messages.append(Message(role="user", content=f"[Tool Result] {feedback.summary}"))

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
