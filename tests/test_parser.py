import pytest
from harness.parser import parse, ParseError
from harness.models import Action


def test_parse_tool_action():
    response = '{"tool": "write_file", "args": {"path": "foo.py", "content": "print(1)"}}'
    action = parse(response)
    assert action.tool == "write_file"
    assert action.args["path"] == "foo.py"
    assert action.args["content"] == "print(1)"
    assert action.raw == response


def test_parse_task_complete():
    response = '{"tool": "task_complete", "args": {"summary": "done"}}'
    action = parse(response)
    assert action.tool == "task_complete"
    assert action.args["summary"] == "done"


def test_parse_with_surrounding_text():
    response = 'I will read the file now.\n{"tool": "read_file", "args": {"path": "foo.py"}}\nLet me check.'
    action = parse(response)
    assert action.tool == "read_file"
    assert action.args["path"] == "foo.py"


def test_parse_invalid_json_raises():
    with pytest.raises(ParseError, match="No JSON found"):
        parse("this is not json at all")


def test_parse_empty_response_raises():
    with pytest.raises(ParseError, match="No JSON found"):
        parse("")
