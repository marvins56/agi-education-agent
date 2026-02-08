"""EduAGI CLI entry point."""

import typer

from src.cli import auth, chat, docs, models, sources

app = typer.Typer(
    name="eduagi",
    help="EduAGI - AI-powered educational assistant CLI",
    no_args_is_help=True,
)

# Register auth commands directly on the app (login, logout)
app.command("login")(auth.login)
app.command("logout")(auth.logout)

# Register chat as a command (not a group)
app.command("chat")(chat.start)

# Register models as a sub-group
app.add_typer(models.app, name="models")

# Register docs as a sub-group
app.add_typer(docs.app, name="docs")

# Register sources as a sub-group
app.add_typer(sources.app, name="sources")


if __name__ == "__main__":
    app()
