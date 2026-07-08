# harness/loop.py
import logging
from harness.llm.base import LLMProvider
from harness.tools import ToolRegistry
from harness.governance import Governance
from harness.feedback import collect
from harness.memory import Memory
from harness.parser import parse, ParseError
from harness.models import Action, ActionResult, Feedback

logger = logging.getLogger("harness")


class AgentLoop:
    def __init__(self, llm: LLMProvider, registry: ToolRegistry,
                 governance: Governance, memory: Memory, max_turns: int = 20):
        self._llm = llm
        self._registry = registry
        self._governance = governance
        self._memory = memory
        self._max_turns = max_turns

    def run(self, task: str) -> str:
        turn = 0
        parse_failures = 0

        while turn < self._max_turns:
            turn += 1
            context = self._memory.build_context()
            response = self._llm.complete(context)
            logger.info(f"[turn {turn}] LLM response: {response[:100]}")

            try:
                action = parse(response)
                parse_failures = 0
            except ParseError as e:
                parse_failures += 1
                logger.warning(f"[turn {turn}] Parse error: {e}")
                if parse_failures >= 3:
                    return f"Stopped: parse failed 3 times consecutively"
                self._memory.append(
                    Action(tool="parse_error", args={}, raw=response),
                    Feedback(passed=False, summary=f"Parse error: {e}. Please return valid JSON.",
                             raw_result=ActionResult(success=False, output="", error=str(e), exit_code=-1))
                )
                continue

            if action.tool == "task_complete":
                summary = action.args.get("summary", "Task complete")
                logger.info(f"[turn {turn}] Task complete: {summary}")
                return summary

            decision = self._governance.check(action)
            if not decision.allow and not decision.confirm:
                logger.warning(f"[turn {turn}] Blocked: {decision.reason}")
                result = ActionResult(success=False, output="", error=f"Blocked: {decision.reason}", exit_code=-1)
            elif decision.confirm:
                user_input = input(f"Confirm action: {action.tool}({action.args})? [y/N] ")
                if user_input.lower() == "y":
                    result = self._registry.dispatch(action)
                else:
                    result = ActionResult(success=False, output="", error="User declined", exit_code=-1)
            else:
                result = self._registry.dispatch(action)

            feedback = collect(result, action.tool)
            logger.info(f"[turn {turn}] {feedback.summary}")
            self._memory.append(action, feedback)

        return f"Stopped: reached max turns ({self._max_turns})"
