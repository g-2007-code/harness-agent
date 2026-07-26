# harness/loop.py
# This file contains the self-implemented agent main loop (harness kernel).
# Written by the student, with AI assistance for boilerplate. Core logic is hand-designed.
import logging
import time
from harness.llm.base import LLMProvider, LLMError
from harness.tools import ToolRegistry
from harness.governance import Governance
from harness.feedback import collect
from harness.memory import Memory
from harness.parser import parse, ParseError
from harness.models import Action, ActionResult, Feedback

logger = logging.getLogger("harness")

LLM_MAX_RETRIES = 3


class AgentLoop:
    def __init__(self, llm: LLMProvider, registry: ToolRegistry,
                 governance: Governance, memory: Memory, max_turns: int = 20,
                 callback=None):
        self._llm = llm
        self._registry = registry
        self._governance = governance
        self._memory = memory
        self._max_turns = max_turns
        self._cb = callback

    def run(self, task: str) -> str:
        if self._cb:
            self._cb.on_start(task)

        turn = 0
        parse_failures = 0

        while turn < self._max_turns:
            turn += 1
            if self._cb:
                self._cb.on_turn(turn, self._max_turns)

            context = self._memory.build_context()

            response = None
            for attempt in range(LLM_MAX_RETRIES + 1):
                try:
                    response = self._llm.complete(context)
                    break
                except LLMError as e:
                    logger.warning(
                        f"[turn {turn}] LLM error (attempt {attempt + 1}/"
                        f"{LLM_MAX_RETRIES + 1}): {e}"
                    )
                    if self._cb:
                        self._cb.on_llm_error(str(e), attempt + 1, LLM_MAX_RETRIES + 1)
                    if attempt < LLM_MAX_RETRIES:
                        time.sleep(2 ** attempt)
                        continue
                    if self._cb:
                        self._cb.on_stop(f"LLM call failed after {LLM_MAX_RETRIES} retries")
                    return f"Stopped: LLM call failed after {LLM_MAX_RETRIES} retries"

            logger.info(f"[turn {turn}] LLM response: {response[:100]}")
            if self._cb:
                self._cb.on_llm_response(response)

            try:
                action = parse(response)
                parse_failures = 0
            except ParseError as e:
                parse_failures += 1
                logger.warning(f"[turn {turn}] Parse error: {e}")
                if self._cb:
                    self._cb.on_parse_error(str(e), parse_failures, 3)
                if parse_failures >= 3:
                    if self._cb:
                        self._cb.on_stop("Parse failed 3 times consecutively")
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
                if self._cb:
                    self._cb.on_complete(summary)
                return summary

            decision = self._governance.check(action)
            if self._cb:
                self._cb.on_action(action.tool, action.args)
                self._cb.on_governance(decision.allow, decision.confirm, decision.reason)

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

            feedback = collect(result, action.tool, turn, self._memory.get_history())
            logger.info(f"[turn {turn}] {feedback.summary}")
            if self._cb:
                self._cb.on_result(feedback.passed, feedback.summary)

            # Inject pattern suggestion if detected
            if feedback.suggested_next_action:
                self._memory.append_hint(feedback.suggested_next_action)
                logger.info(f"[turn {turn}] Injected hint: {feedback.suggested_next_action}")

            # Inject detailed hint for failed checks (syntax errors, etc.)
            if not feedback.passed and feedback.checks:
                failed_checks = [c for c in feedback.checks if not c.passed]
                if failed_checks:
                    hint = f"Your last action failed checks: {failed_checks[0].detail[:300]}. Please fix and retry."
                    self._memory.append_hint(hint)
                    logger.info(f"[turn {turn}] Injected check hint: {hint[:100]}")

            self._memory.append(action, feedback)

        if self._cb:
            self._cb.on_stop(f"Reached max turns ({self._max_turns})")
        return f"Stopped: reached max turns ({self._max_turns})"
