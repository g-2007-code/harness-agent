# harness/governance.py
# This file contains the self-implemented governance guardrail mechanism (harness kernel).
# Written by the student, with AI assistance for boilerplate. Core logic is hand-designed.
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
            try:
                inside = os.path.commonpath([abs_path, self._project_dir]) == self._project_dir
            except ValueError:
                inside = False
            if not inside:
                return GovernanceDecision(allow=False, confirm=False, reason=f"Blocked: path outside project directory")
            return GovernanceDecision(allow=True, confirm=False, reason="safe")

        return GovernanceDecision(allow=True, confirm=False, reason="safe")
