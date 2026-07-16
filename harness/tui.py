# harness/tui.py
# Terminal UI renderer using rich. Provides callback interface for AgentLoop.
from rich.console import Console
from rich.panel import Panel
from rich.markup import escape


class TUI:
    """Terminal UI callback for AgentLoop. Renders agent actions in real-time."""

    def __init__(self):
        self.console = Console()

    def on_start(self, task: str):
        self.console.print()
        self.console.print(Panel(task, title="Task", border_style="cyan"))

    def on_turn(self, turn: int, max_turns: int):
        self.console.print(f"\n[bold blue]── Turn {turn}/{max_turns} ──[/bold blue]")

    def on_llm_response(self, response: str):
        display = response[:150] + "..." if len(response) > 150 else response
        self.console.print(f"  [dim]LLM:[/dim] {escape(display)}")

    def on_action(self, tool: str, args: dict):
        color = "green" if tool in ("read_file", "write_file") else "yellow"
        args_display = dict(args)
        if "content" in args_display:
            args_display["content"] = args_display["content"][:50] + "..."
        self.console.print(f"  [{color}]Action:[/{color}] {tool}({args_display})")

    def on_governance(self, allow: bool, confirm: bool, reason: str):
        if not allow and not confirm:
            self.console.print(f"  [red]BLOCKED:[/red] {reason}")
        elif confirm:
            self.console.print(f"  [yellow]CONFIRM:[/yellow] {reason}")

    def on_result(self, passed: bool, summary: str):
        if passed:
            self.console.print(f"  [green]PASS[/green] {summary[:120]}")
        else:
            self.console.print(f"  [red]FAIL[/red] {summary[:120]}")

    def on_parse_error(self, error: str, retries: int, max_retries: int):
        self.console.print(f"  [red]PARSE ERROR[/red] ({retries}/{max_retries}): {error}")

    def on_llm_error(self, error: str, attempt: int, max_attempts: int):
        self.console.print(f"  [red]LLM ERROR[/red] ({attempt}/{max_attempts}): {error[:100]}")

    def on_complete(self, summary: str):
        self.console.print()
        self.console.print(Panel(summary, title="Complete", border_style="green"))

    def on_stop(self, reason: str):
        self.console.print()
        self.console.print(Panel(reason, title="Stopped", border_style="yellow"))
