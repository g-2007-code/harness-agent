from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class Message:
    role: str
    content: str


@dataclass
class Conversation:
    messages: List[Message]


@dataclass
class Action:
    tool: str
    args: dict
    raw: str


@dataclass
class ActionResult:
    success: bool
    output: str
    error: str
    exit_code: int
    metadata: dict = field(default_factory=dict)


@dataclass
class CheckResult:
    """Result of a single feedback pipeline check."""
    name: str
    passed: bool
    detail: str


@dataclass
class Feedback:
    passed: bool
    summary: str
    raw_result: ActionResult
    checks: List[CheckResult] = field(default_factory=list)
    suggested_next_action: str = ""
    turn_number: int = 0


@dataclass
class GovernanceDecision:
    allow: bool
    confirm: bool
    reason: str


@dataclass
class Session:
    id: str
    task: str
    history: List[Tuple[Action, Feedback]]
    summary: str


@dataclass
class Config:
    llm_provider: str
    llm_model: str
    llm_base_url: str
    max_turns: int
    blocked_commands: List[str]
    auto_deny: bool
    session_dir: str
    log_level: str
    log_dir: str
