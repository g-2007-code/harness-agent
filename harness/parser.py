import json
import re
from harness.models import Action


class ParseError(Exception):
    pass


def parse(response: str) -> Action:
    match = re.search(r'\{.*\}', response, re.DOTALL)
    if not match:
        raise ParseError("No JSON found in response")

    json_str = match.group()
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ParseError(f"Invalid JSON: {e}")

    tool = data.get("tool")
    if not tool:
        raise ParseError("Missing 'tool' field in JSON")

    args = data.get("args", {})
    return Action(tool=tool, args=args, raw=response)
