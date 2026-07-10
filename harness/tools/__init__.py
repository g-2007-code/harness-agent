# harness/tools/__init__.py
# This file contains the self-implemented ToolRegistry (harness kernel).
# Written by the student, with AI assistance for boilerplate. Core logic is hand-designed.
from harness.models import Action, ActionResult


class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, name: str, func):
        self._tools[name] = func

    def dispatch(self, action: Action) -> ActionResult:
        func = self._tools.get(action.tool)
        if func is None:
            return ActionResult(
                success=False, output="", error=f"Tool '{action.tool}' not registered", exit_code=-1
            )
        try:
            return func(**action.args)
        except Exception as e:
            return ActionResult(success=False, output="", error=str(e), exit_code=-1)
