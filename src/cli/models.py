"""Model management commands."""

import typer

from src.cli.api_client import CLIClient, CLIError
from src.cli.display import console, show_error, show_table

app = typer.Typer(help="Model management commands")


@app.command("list")
def list_models(
    current: bool = typer.Option(False, "-c", "--current", help="Show only the current default model"),
) -> None:
    """List available LLM providers and models."""
    client = CLIClient()

    if current:
        with console.status("Fetching current model..."):
            try:
                resp = client.get("/models/current")
            except CLIError as exc:
                show_error(str(exc))
                raise typer.Exit(1)

        data = resp.json()
        console.print(f"[bold]Current default:[/bold] {data['provider']}/{data['model']}")
        return

    with console.status("Fetching models..."):
        try:
            resp = client.get("/models")
        except CLIError as exc:
            show_error(str(exc))
            raise typer.Exit(1)

    providers = resp.json()
    rows: list[list[str]] = []
    for p in providers:
        available = "[green]yes[/green]" if p.get("available") else "[red]no[/red]"
        models_str = ", ".join(p.get("models", [])) or "[dim]none[/dim]"
        rows.append([p["provider"], available, models_str])

    show_table(
        "Available Models",
        ["Provider", "Available", "Models"],
        rows,
    )
