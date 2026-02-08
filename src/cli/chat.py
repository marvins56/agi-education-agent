"""Interactive chat REPL for the EduAGI tutor."""

from typing import Optional

import typer
from rich.prompt import Prompt

from src.cli.api_client import CLIClient, CLIError
from src.cli.config import load_credentials
from src.cli.display import console, show_ai_response, show_error

app = typer.Typer(help="Chat commands")


@app.command()
def start(
    subject: Optional[str] = typer.Option(None, "-s", "--subject", help="Subject for the session"),
    topic: Optional[str] = typer.Option(None, "-t", "--topic", help="Topic for the session"),
    model: Optional[str] = typer.Option(None, "-m", "--model", help="Model override (provider/model, e.g. ollama/llama3)"),
) -> None:
    """Start an interactive chat session with the AI tutor."""
    creds = load_credentials()
    if not creds:
        show_error("Not logged in. Run: eduagi login")
        raise typer.Exit(1)

    client = CLIClient()

    # Parse provider/model from -m flag
    provider: str | None = None
    model_name: str | None = None
    if model:
        if "/" in model:
            provider, model_name = model.split("/", 1)
        else:
            model_name = model

    # Create session
    session_body: dict = {}
    if subject:
        session_body["subject"] = subject
    if topic:
        session_body["topic"] = topic

    with console.status("Creating session..."):
        try:
            resp = client.post("/chat/sessions", json=session_body)
        except CLIError as exc:
            show_error(str(exc))
            raise typer.Exit(1)

    session = resp.json()
    session_id = session["session_id"]

    console.print(f"[dim]Session: {session_id}[/dim]")
    if subject or topic:
        parts = []
        if subject:
            parts.append(f"Subject: {subject}")
        if topic:
            parts.append(f"Topic: {topic}")
        console.print(f"[dim]{' | '.join(parts)}[/dim]")
    console.print("[dim]Type 'exit' or 'quit' to end. Ctrl+C / Ctrl+D also work.[/dim]\n")

    # REPL loop
    while True:
        try:
            user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Session ended.[/dim]")
            break

        if user_input.strip().lower() in ("exit", "quit"):
            console.print("[dim]Session ended.[/dim]")
            break

        if not user_input.strip():
            continue

        msg_body: dict = {
            "content": user_input,
            "session_id": session_id,
        }
        if subject:
            msg_body["subject"] = subject
        if topic:
            msg_body["topic"] = topic
        if provider:
            msg_body["provider"] = provider
        if model_name:
            msg_body["model"] = model_name

        with console.status("Thinking..."):
            try:
                resp = client.post("/chat/message", json=msg_body)
            except CLIError as exc:
                show_error(str(exc))
                continue

        data = resp.json()
        show_ai_response(data.get("text", ""))

        # Show sources if any
        sources = data.get("sources", [])
        if sources:
            console.print(f"[dim]Sources: {len(sources)} referenced[/dim]")

        # Show suggested actions if any
        actions = data.get("suggested_actions", [])
        if actions:
            console.print("[dim]Suggestions: " + " | ".join(actions) + "[/dim]")

        console.print()
