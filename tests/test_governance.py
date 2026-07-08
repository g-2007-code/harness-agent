from harness.governance import Governance
from harness.models import Action, GovernanceDecision


def test_check_allows_safe_read():
    gov = Governance(blocked_commands=["rm -rf", "sudo"], auto_deny=False)
    action = Action(tool="read_file", args={"path": "foo.py"}, raw="")
    decision = gov.check(action)
    assert decision.allow is True
    assert decision.confirm is False


def test_check_denies_blacklisted_command():
    gov = Governance(blocked_commands=["rm -rf"], auto_deny=False)
    action = Action(tool="run_shell", args={"command": "rm -rf /"}, raw="")
    decision = gov.check(action)
    assert decision.allow is False
    assert decision.confirm is False
    assert "rm -rf" in decision.reason


def test_check_confirms_substring_match():
    gov = Governance(blocked_commands=["rm -rf"], auto_deny=False)
    action = Action(tool="run_shell", args={"command": "rm -rf ./build"}, raw="")
    decision = gov.check(action)
    assert decision.allow is False
    assert decision.confirm is True


def test_auto_deny_converts_confirm_to_deny():
    gov = Governance(blocked_commands=["rm -rf"], auto_deny=True)
    action = Action(tool="run_shell", args={"command": "rm -rf ./build"}, raw="")
    decision = gov.check(action)
    assert decision.allow is False
    assert decision.confirm is False


def test_check_denies_write_outside_project(tmp_path):
    import os
    gov = Governance(blocked_commands=[], auto_deny=False, project_dir=str(tmp_path))
    action = Action(tool="write_file", args={"path": "/etc/passwd", "content": "hacked"}, raw="")
    decision = gov.check(action)
    assert decision.allow is False
    assert "outside" in decision.reason.lower()


def test_check_allows_write_inside_project(tmp_path):
    gov = Governance(blocked_commands=[], auto_deny=False, project_dir=str(tmp_path))
    action = Action(tool="write_file", args={"path": str(tmp_path / "foo.py"), "content": "print(1)"}, raw="")
    decision = gov.check(action)
    assert decision.allow is True
