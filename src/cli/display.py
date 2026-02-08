"""Rich display helpers for the EduAGI CLI."""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

console = Console()
err_console = Console(stderr=True)


def show_ai_response(text: str) -> None:
    """Render AI response as Rich Markdown inside a panel."""
    md = Markdown(text)
    console.print(Panel(md, title="EduAGI", border_style="blue", padding=(1, 2)))


def show_error(msg: str) -> None:
    """Display an error message in a red panel."""
    err_console.print(Panel(msg, title="Error", border_style="red"))


def show_success(msg: str) -> None:
    """Display a success message in green."""
    console.print(f"[green]{msg}[/green]")


def show_table(title: str, columns: list[str], rows: list[list[str]]) -> None:
    """Render a Rich table."""
    table = Table(title=title, show_header=True, header_style="bold cyan")
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*row)
    console.print(table)
