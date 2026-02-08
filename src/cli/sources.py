"""Source ingestion commands: YouTube, Wikipedia, ArXiv, PubMed, Gutenberg, GitHub, web crawl."""

from typing import Optional

import typer

from src.cli.api_client import CLIClient, CLIError
from src.cli.display import console, show_error, show_success, show_table

app = typer.Typer(help="Ingest content from external sources")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _show_single_result(data: dict) -> None:
    """Display a single ingestion result (document_id, title, status, chunk_count)."""
    console.print(f"  Title:       [bold]{data.get('title', '')}[/bold]")
    console.print(f"  Document ID: {data.get('document_id', '')}")
    console.print(f"  Status:      {data.get('status', '')}")
    console.print(f"  Chunks:      {data.get('chunk_count', 0)}")


def _show_multi_results(data: dict) -> None:
    """Display multi-document ingestion results as a Rich table."""
    documents = data.get("documents", [])
    show_success(f"Ingested {len(documents)} document(s)!")
    if not documents:
        console.print("[dim]No documents returned.[/dim]")
        return
    rows = []
    for doc in documents:
        rows.append([
            doc.get("document_id", "")[:12] + "...",
            doc.get("title", "")[:50],
            doc.get("status", ""),
            str(doc.get("chunk_count", 0)),
        ])
    show_table("Ingested Documents", ["ID", "Title", "Status", "Chunks"], rows)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command("youtube")
def ingest_youtube(
    video_id: str = typer.Argument(..., help="YouTube video ID or URL"),
    subject: Optional[str] = typer.Option(None, "--subject", "-s", help="Subject area"),
    grade_level: Optional[str] = typer.Option(None, "--grade-level", "-g", help="Grade level"),
) -> None:
    """Ingest a YouTube video transcript into the knowledge base."""
    client = CLIClient()
    body: dict = {"video_id": video_id}
    if subject:
        body["subject"] = subject
    if grade_level:
        body["grade_level"] = grade_level

    with console.status("Fetching YouTube transcript..."):
        try:
            resp = client.post("/content/ingest/youtube", json=body)
        except CLIError as exc:
            show_error(str(exc))
            raise typer.Exit(1)

    data = resp.json()
    show_success("YouTube transcript ingested!")
    _show_single_result(data)


@app.command("wikipedia")
def ingest_wikipedia(
    query: str = typer.Argument(..., help="Wikipedia search query or article title"),
    lang: str = typer.Option("en", "--lang", "-l", help="Wikipedia language code"),
    subject: Optional[str] = typer.Option(None, "--subject", "-s", help="Subject area"),
    grade_level: Optional[str] = typer.Option(None, "--grade-level", "-g", help="Grade level"),
) -> None:
    """Ingest a Wikipedia article into the knowledge base."""
    client = CLIClient()
    body: dict = {"query": query, "lang": lang}
    if subject:
        body["subject"] = subject
    if grade_level:
        body["grade_level"] = grade_level

    with console.status(f"Fetching Wikipedia article for '{query}'..."):
        try:
            resp = client.post("/content/ingest/wikipedia", json=body)
        except CLIError as exc:
            show_error(str(exc))
            raise typer.Exit(1)

    data = resp.json()
    show_success("Wikipedia article ingested!")
    _show_single_result(data)


@app.command("arxiv")
def ingest_arxiv(
    query: str = typer.Argument(..., help="ArXiv search query"),
    max_results: int = typer.Option(3, "--max-results", "-n", help="Maximum number of papers to ingest"),
    subject: Optional[str] = typer.Option(None, "--subject", "-s", help="Subject area"),
    grade_level: Optional[str] = typer.Option(None, "--grade-level", "-g", help="Grade level"),
) -> None:
    """Ingest papers from ArXiv into the knowledge base."""
    client = CLIClient()
    body: dict = {"query": query, "max_results": max_results}
    if subject:
        body["subject"] = subject
    if grade_level:
        body["grade_level"] = grade_level

    with console.status(f"Searching ArXiv for '{query}'..."):
        try:
            resp = client.post("/content/ingest/arxiv", json=body)
        except CLIError as exc:
            show_error(str(exc))
            raise typer.Exit(1)

    data = resp.json()
    _show_multi_results(data)


@app.command("pubmed")
def ingest_pubmed(
    query: str = typer.Argument(..., help="PubMed search query"),
    max_results: int = typer.Option(3, "--max-results", "-n", help="Maximum number of articles to ingest"),
    subject: Optional[str] = typer.Option(None, "--subject", "-s", help="Subject area"),
    grade_level: Optional[str] = typer.Option(None, "--grade-level", "-g", help="Grade level"),
) -> None:
    """Ingest articles from PubMed into the knowledge base."""
    client = CLIClient()
    body: dict = {"query": query, "max_results": max_results}
    if subject:
        body["subject"] = subject
    if grade_level:
        body["grade_level"] = grade_level

    with console.status(f"Searching PubMed for '{query}'..."):
        try:
            resp = client.post("/content/ingest/pubmed", json=body)
        except CLIError as exc:
            show_error(str(exc))
            raise typer.Exit(1)

    data = resp.json()
    _show_multi_results(data)


@app.command("gutenberg")
def ingest_gutenberg(
    query: str = typer.Argument(..., help="Project Gutenberg search query"),
    max_results: int = typer.Option(1, "--max-results", "-n", help="Maximum number of books to ingest"),
    subject: Optional[str] = typer.Option(None, "--subject", "-s", help="Subject area"),
    grade_level: Optional[str] = typer.Option(None, "--grade-level", "-g", help="Grade level"),
) -> None:
    """Ingest books from Project Gutenberg into the knowledge base."""
    client = CLIClient()
    body: dict = {"query": query, "max_results": max_results}
    if subject:
        body["subject"] = subject
    if grade_level:
        body["grade_level"] = grade_level

    with console.status(f"Searching Project Gutenberg for '{query}'..."):
        try:
            resp = client.post("/content/ingest/gutenberg", json=body)
        except CLIError as exc:
            show_error(str(exc))
            raise typer.Exit(1)

    data = resp.json()
    _show_multi_results(data)


@app.command("github")
def ingest_github(
    repo: str = typer.Argument(..., help="GitHub repository (e.g. owner/repo)"),
    file_path: Optional[str] = typer.Option(None, "--file-path", "-f", help="Specific file path within the repo"),
    branch: str = typer.Option("main", "--branch", "-b", help="Branch name"),
    subject: Optional[str] = typer.Option(None, "--subject", "-s", help="Subject area"),
    grade_level: Optional[str] = typer.Option(None, "--grade-level", "-g", help="Grade level"),
) -> None:
    """Ingest a file or repository from GitHub into the knowledge base."""
    client = CLIClient()
    body: dict = {"repo": repo, "branch": branch}
    if file_path:
        body["file_path"] = file_path
    if subject:
        body["subject"] = subject
    if grade_level:
        body["grade_level"] = grade_level

    target = f"{repo}/{file_path}" if file_path else repo
    with console.status(f"Fetching from GitHub: {target}..."):
        try:
            resp = client.post("/content/ingest/github", json=body)
        except CLIError as exc:
            show_error(str(exc))
            raise typer.Exit(1)

    data = resp.json()
    show_success("GitHub content ingested!")
    _show_single_result(data)


@app.command("crawl")
def ingest_crawl(
    url: str = typer.Argument(..., help="URL to crawl"),
    max_depth: int = typer.Option(2, "--max-depth", "-d", help="Maximum crawl depth"),
    max_pages: int = typer.Option(20, "--max-pages", "-n", help="Maximum number of pages to crawl"),
    subject: Optional[str] = typer.Option(None, "--subject", "-s", help="Subject area"),
    grade_level: Optional[str] = typer.Option(None, "--grade-level", "-g", help="Grade level"),
) -> None:
    """Crawl a website and ingest pages into the knowledge base."""
    client = CLIClient()
    body: dict = {"url": url, "max_depth": max_depth, "max_pages": max_pages}
    if subject:
        body["subject"] = subject
    if grade_level:
        body["grade_level"] = grade_level

    with console.status(f"Crawling {url} (depth={max_depth}, max_pages={max_pages})..."):
        try:
            resp = client.post("/content/ingest/crawl", json=body)
        except CLIError as exc:
            show_error(str(exc))
            raise typer.Exit(1)

    data = resp.json()
    _show_multi_results(data)


@app.command("list")
def list_sources() -> None:
    """Show available source types for ingestion."""
    client = CLIClient()
    with console.status("Fetching available sources..."):
        try:
            resp = client.get("/content/sources/available")
        except CLIError as exc:
            show_error(str(exc))
            raise typer.Exit(1)

    data = resp.json()
    sources = data if isinstance(data, list) else data.get("sources", [])

    if not sources:
        console.print("[dim]No sources available.[/dim]")
        return

    rows = []
    for src in sources:
        if isinstance(src, str):
            rows.append([src, "-", "-"])
        elif isinstance(src, dict):
            rows.append([
                src.get("name", ""),
                src.get("description", "-"),
                src.get("status", "-"),
            ])
    show_table("Available Sources", ["Source", "Description", "Status"], rows)
