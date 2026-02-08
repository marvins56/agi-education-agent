"""Document management commands: upload, list, search, info, delete."""

import mimetypes
import os
from typing import Optional

import httpx
import typer
from rich.panel import Panel
from rich.prompt import Confirm

from src.cli.api_client import CLIClient, CLIError
from src.cli.config import get_api_url, load_credentials
from src.cli.display import console, show_error, show_success, show_table

app = typer.Typer(help="Document management commands")


@app.command("list")
def list_docs(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    page_size: int = typer.Option(20, "--size", "-s", help="Page size"),
) -> None:
    """List uploaded documents."""
    client = CLIClient()
    with console.status("Fetching documents..."):
        try:
            resp = client.get("/content/documents", params={"page": page, "page_size": page_size})
        except CLIError as exc:
            show_error(str(exc))
            raise typer.Exit(1)

    data = resp.json()
    items = data.get("items", [])
    total = data.get("total", 0)

    if not items:
        console.print("[dim]No documents found.[/dim]")
        return

    rows = []
    for doc in items:
        doc_id = doc.get("id", "")[:12] + "..."
        title = doc.get("title", "")[:40]
        file_type = doc.get("file_type", "")
        subject = doc.get("subject", "") or "-"
        status = doc.get("status", "")
        chunks = str(doc.get("chunk_count", 0))
        created = (doc.get("created_at", "") or "")[:10]
        rows.append([doc_id, title, file_type, subject, status, chunks, created])

    show_table(
        f"Documents ({total} total)",
        ["ID", "Title", "Type", "Subject", "Status", "Chunks", "Date"],
        rows,
    )


@app.command("search")
def search_docs(
    query: str = typer.Argument(..., help="Search query"),
    subject: Optional[str] = typer.Option(None, "--subject", help="Filter by subject"),
    limit: int = typer.Option(5, "--limit", "-l", help="Max results"),
) -> None:
    """Search the knowledge base."""
    client = CLIClient()
    params: dict = {"q": query, "limit": limit}
    if subject:
        params["subject"] = subject

    with console.status("Searching..."):
        try:
            resp = client.get("/content/search", params=params)
        except CLIError as exc:
            show_error(str(exc))
            raise typer.Exit(1)

    data = resp.json()
    results = data.get("results", [])
    total = data.get("total", 0)

    if not results:
        console.print(f"[dim]No results for '{query}'.[/dim]")
        return

    console.print(f"[bold]Found {total} result(s) for:[/bold] {query}\n")

    for i, r in enumerate(results, 1):
        preview = r.get("content_preview", "")[:300]
        distance = r.get("distance", 0.0)
        relevance = max(0.0, (1.0 - distance) * 100)
        meta = r.get("metadata", {})
        citation = r.get("citation", {})

        meta_parts = []
        if meta.get("subject"):
            meta_parts.append(f"Subject: {meta['subject']}")
        if meta.get("title"):
            meta_parts.append(f"Source: {meta['title']}")
        if citation.get("page"):
            meta_parts.append(f"Page: {citation['page']}")

        subtitle = f"Relevance: {relevance:.0f}%"
        if meta_parts:
            subtitle += " | " + " | ".join(meta_parts)

        console.print(Panel(
            preview,
            title=f"Result {i}",
            subtitle=subtitle,
            border_style="cyan",
            padding=(0, 1),
        ))


@app.command("upload")
def upload_file(
    filepath: str = typer.Argument(..., help="Path to file (PDF, DOCX, PPTX, XLSX, CSV, EPUB, HTML, TXT, MD)"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Document title"),
    subject: Optional[str] = typer.Option(None, "--subject", "-s", help="Subject area"),
    grade_level: Optional[str] = typer.Option(None, "--grade-level", "-g", help="Grade level"),
) -> None:
    """Upload a file to the knowledge base."""
    filepath = os.path.expanduser(filepath)
    if not os.path.isfile(filepath):
        show_error(f"File not found: {filepath}")
        raise typer.Exit(1)

    filename = os.path.basename(filepath)
    content_type, _ = mimetypes.guess_type(filepath)
    if not content_type:
        content_type = "application/octet-stream"

    creds = load_credentials()
    if not creds or not creds.get("access_token"):
        show_error("Not logged in. Run: eduagi login")
        raise typer.Exit(1)

    base_url = get_api_url()
    url = f"{base_url}/content/upload"
    headers = {"Authorization": f"Bearer {creds['access_token']}"}

    params: dict[str, str] = {}
    if title:
        params["title"] = title
    if subject:
        params["subject"] = subject
    if grade_level:
        params["grade_level"] = grade_level

    with console.status(f"Uploading {filename}..."):
        try:
            with open(filepath, "rb") as f:
                files = {"file": (filename, f, content_type)}
                resp = httpx.post(url, files=files, params=params, headers=headers, timeout=120.0)
        except httpx.ConnectError:
            show_error(f"Cannot connect to the EduAGI server at {base_url}")
            raise typer.Exit(1)
        except httpx.HTTPError as exc:
            show_error(f"Network error: {exc}")
            raise typer.Exit(1)

    if resp.status_code == 401:
        show_error("Session expired. Please log in again with: eduagi login")
        raise typer.Exit(1)
    if resp.status_code == 403:
        show_error("Permission denied. Only teachers and admins can upload documents.")
        raise typer.Exit(1)
    if resp.status_code >= 400:
        detail = ""
        try:
            detail = resp.json().get("detail", "")
        except Exception:
            pass
        show_error(detail or f"Upload failed with status {resp.status_code}")
        raise typer.Exit(1)

    data = resp.json()
    show_success("Upload successful!")
    console.print(f"  Document ID: [bold]{data.get('document_id', '')}[/bold]")
    console.print(f"  Status:      {data.get('status', '')}")
    console.print(f"  Chunks:      {data.get('chunk_count', 0)}")
    console.print(f"  Filename:    {data.get('filename', '')}")


@app.command("upload-url")
def upload_url(
    url: str = typer.Argument(..., help="URL to ingest"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Document title"),
    subject: Optional[str] = typer.Option(None, "--subject", "-s", help="Subject area"),
    grade_level: Optional[str] = typer.Option(None, "--grade-level", "-g", help="Grade level"),
) -> None:
    """Ingest content from a URL into the knowledge base."""
    client = CLIClient()
    body: dict = {"url": url}
    if title:
        body["title"] = title
    if subject:
        body["subject"] = subject
    if grade_level:
        body["grade_level"] = grade_level

    with console.status(f"Processing URL: {url}..."):
        try:
            resp = client.post("/content/upload-url", json=body)
        except CLIError as exc:
            show_error(str(exc))
            raise typer.Exit(1)

    data = resp.json()
    show_success("URL processed successfully!")
    console.print(f"  Document ID: [bold]{data.get('document_id', '')}[/bold]")
    console.print(f"  Status:      {data.get('status', '')}")
    console.print(f"  Chunks:      {data.get('chunk_count', 0)}")


@app.command("info")
def doc_info(
    doc_id: str = typer.Argument(..., help="Document ID"),
) -> None:
    """Show details of a specific document."""
    client = CLIClient()
    with console.status("Fetching document..."):
        try:
            resp = client.get(f"/content/documents/{doc_id}")
        except CLIError as exc:
            show_error(str(exc))
            raise typer.Exit(1)

    d = resp.json()
    lines = [
        f"[bold]Title:[/bold]      {d.get('title', '')}",
        f"[bold]ID:[/bold]         {d.get('id', '')}",
        f"[bold]Type:[/bold]       {d.get('file_type', '')}",
        f"[bold]Subject:[/bold]    {d.get('subject', '') or '-'}",
        f"[bold]Grade:[/bold]      {d.get('grade_level', '') or '-'}",
        f"[bold]Status:[/bold]     {d.get('status', '')}",
        f"[bold]Chunks:[/bold]     {d.get('chunk_count', 0)}",
        f"[bold]File Size:[/bold]  {d.get('file_size', 0) or 0} bytes",
        f"[bold]Filename:[/bold]   {d.get('original_filename', '')}",
        f"[bold]Created:[/bold]    {d.get('created_at', '') or '-'}",
        f"[bold]Processed:[/bold]  {d.get('processed_at', '') or '-'}",
    ]
    meta = d.get("metadata", {})
    if meta:
        lines.append(f"[bold]Metadata:[/bold]   {meta}")

    console.print(Panel(
        "\n".join(lines),
        title="Document Details",
        border_style="blue",
        padding=(1, 2),
    ))


@app.command("delete")
def delete_doc(
    doc_id: str = typer.Argument(..., help="Document ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Delete a document from the knowledge base."""
    if not yes:
        if not Confirm.ask(f"Delete document [bold]{doc_id}[/bold]?"):
            console.print("[dim]Cancelled.[/dim]")
            return

    client = CLIClient()
    with console.status("Deleting document..."):
        try:
            resp = client.delete(f"/content/documents/{doc_id}")
        except CLIError as exc:
            show_error(str(exc))
            raise typer.Exit(1)

    data = resp.json()
    show_success(f"Document {data.get('document_id', doc_id)} deleted.")
