"""Authentication commands: login and logout."""

import typer
from rich.prompt import Prompt

from src.cli.api_client import CLIClient, CLIError
from src.cli.config import clear_credentials, load_credentials, save_credentials
from src.cli.display import console, show_error, show_success

app = typer.Typer(help="Authentication commands")


@app.command()
def login() -> None:
    """Log in to the EduAGI server."""
    email = Prompt.ask("[bold]Email[/bold]")
    password = Prompt.ask("[bold]Password[/bold]", password=True)

    client = CLIClient()
    with console.status("Logging in..."):
        try:
            resp = client.post(
                "/auth/login",
                json={"email": email, "password": password},
                authenticated=False,
            )
        except CLIError as exc:
            show_error(str(exc))
            raise typer.Exit(1)

    data = resp.json()
    save_credentials(
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        email=email,
    )
    show_success(f"Logged in as {email}")


@app.command()
def logout() -> None:
    """Log out and clear stored credentials."""
    creds = load_credentials()
    if not creds:
        show_error("Not logged in.")
        raise typer.Exit(1)

    client = CLIClient()
    try:
        client.post("/auth/logout")
    except CLIError:
        pass  # Best-effort server-side logout

    clear_credentials()
    show_success("Logged out.")
