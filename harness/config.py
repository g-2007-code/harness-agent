# harness/config.py
import os
import yaml
from harness.models import Config


DEFAULTS = Config(
    llm_provider="mock",
    llm_model="gpt-4o",
    max_turns=20,
    blocked_commands=["rm -rf", "git push --force", "curl", "wget", "chmod 777", "sudo"],
    auto_deny=False,
    session_dir=".harness/sessions",
    log_level="info",
    log_dir=".harness/logs",
)


def load_config(path: str) -> Config:
    if not os.path.exists(path):
        return DEFAULTS

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    llm = data.get("llm", {})
    gov = data.get("governance", {})
    sess = data.get("session", {})
    log = data.get("logging", {})

    return Config(
        llm_provider=llm.get("provider", DEFAULTS.llm_provider),
        llm_model=llm.get("model", DEFAULTS.llm_model),
        max_turns=data.get("max_turns", DEFAULTS.max_turns),
        blocked_commands=gov.get("blocked_commands", DEFAULTS.blocked_commands),
        auto_deny=gov.get("auto_deny", DEFAULTS.auto_deny),
        session_dir=sess.get("dir", DEFAULTS.session_dir),
        log_level=log.get("level", DEFAULTS.log_level),
        log_dir=log.get("dir", DEFAULTS.log_dir),
    )
