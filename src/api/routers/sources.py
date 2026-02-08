"""Source loader endpoints for ingesting content from external sources."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_db, get_retriever
from src.auth.rbac import Role, require_role
from src.documents.chunker import SemanticChunker
from src.documents.enricher import ContentEnricher
from src.documents.processor import DocumentProcessor
from src.models.document import Document
from src.models.user import User
from src.rag.retriever import KnowledgeRetriever

from src.documents.loaders.youtube import YouTubeLoader
from src.documents.loaders.wikipedia_loader import WikipediaLoader
from src.documents.loaders.arxiv_loader import ArxivLoader
from src.documents.loaders.pubmed_loader import PubMedLoader
from src.documents.loaders.gutenberg_loader import GutenbergLoader
from src.documents.loaders.github_loader import GitHubLoader
from src.documents.loaders.recursive_url_loader import RecursiveURLLoader

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------- Request schemas ----------

class YouTubeIngestRequest(BaseModel):
    video_id: str
    title: str | None = None
    subject: str | None = None
    grade_level: str | None = None


class WikipediaIngestRequest(BaseModel):
    query: str
    lang: str | None = "en"
    title: str | None = None
    subject: str | None = None
    grade_level: str | None = None


class ArxivIngestRequest(BaseModel):
    query: str
    max_results: int | None = 1
    subject: str | None = None
    grade_level: str | None = None


class PubMedIngestRequest(BaseModel):
    query: str
    max_results: int | None = 3
    subject: str | None = None
    grade_level: str | None = None


class GutenbergIngestRequest(BaseModel):
    query: str
    max_results: int | None = 1
    subject: str | None = None
    grade_level: str | None = None


class GitHubIngestRequest(BaseModel):
    repo: str
    file_path: str | None = None
    branch: str | None = "main"
    subject: str | None = None
    grade_level: str | None = None


class CrawlIngestRequest(BaseModel):
    url: str
    max_depth: int | None = 2
    max_pages: int | None = 20
    subject: str | None = None
    grade_level: str | None = None


# ---------- Helpers ----------

def _build_processor(retriever: KnowledgeRetriever) -> DocumentProcessor:
    """Create a DocumentProcessor wired to the given retriever."""
    return DocumentProcessor(
        chunker=SemanticChunker(),
        enricher=ContentEnricher(),
        retriever=retriever,
    )


async def _ingest_single(
    text: str,
    title: str,
    source_type: str,
    source_metadata: dict,
    subject: str | None,
    grade_level: str | None,
    user: User,
    db: AsyncSession,
    retriever: KnowledgeRetriever,
) -> dict:
    """Create a Document record, process text through the pipeline, and return the result."""
    doc = Document(
        title=title,
        subject=subject,
        grade_level=grade_level,
        original_filename=f"{source_type}:{title}",
        file_type=source_type,
        status="processing",
        uploaded_by=user.id,
    )
    db.add(doc)
    await db.flush()

    try:
        processor = _build_processor(retriever)
        meta = {
            "subject": subject or "",
            "grade_level": grade_level or "",
            "title": title,
            "source_type": source_type,
        }
        meta.update(source_metadata)
        result = await processor._process_text(text, meta)
        doc.chunk_count = result["chunk_count"]
        doc.status = "completed"
        doc.processed_at = datetime.now(timezone.utc)
        doc.metadata_ = result.get("metadata", {})
    except Exception as exc:
        logger.error("Ingest failed for %s '%s': %s", source_type, title, exc)
        doc.status = "failed"
        doc.metadata_ = {"error": str(exc)}

    return {
        "document_id": str(doc.id),
        "status": doc.status,
        "chunk_count": doc.chunk_count,
        "title": doc.title,
    }


async def _ingest_multiple(
    items: list[dict],
    source_type: str,
    subject: str | None,
    grade_level: str | None,
    user: User,
    db: AsyncSession,
    retriever: KnowledgeRetriever,
) -> dict:
    """Ingest a list of loader results, each having text/title/metadata."""
    documents = []
    for item in items:
        result = await _ingest_single(
            text=item["text"],
            title=item["title"],
            source_type=source_type,
            source_metadata=item.get("metadata", {}),
            subject=subject,
            grade_level=grade_level,
            user=user,
            db=db,
            retriever=retriever,
        )
        documents.append(result)
    return {"documents": documents}


# ---------- Endpoints ----------

@router.post("/ingest/youtube")
async def ingest_youtube(
    body: YouTubeIngestRequest,
    user: User = Depends(require_role(Role.teacher, Role.admin)),
    db: AsyncSession = Depends(get_db),
    retriever: KnowledgeRetriever = Depends(get_retriever),
):
    """Ingest a YouTube video transcript into the knowledge base."""
    loader = YouTubeLoader()
    try:
        data = await loader.load(video_id=body.video_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    title = body.title or data["title"]
    return await _ingest_single(
        text=data["text"],
        title=title,
        source_type="youtube",
        source_metadata=data.get("metadata", {}),
        subject=body.subject,
        grade_level=body.grade_level,
        user=user,
        db=db,
        retriever=retriever,
    )


@router.post("/ingest/wikipedia")
async def ingest_wikipedia(
    body: WikipediaIngestRequest,
    user: User = Depends(require_role(Role.teacher, Role.admin)),
    db: AsyncSession = Depends(get_db),
    retriever: KnowledgeRetriever = Depends(get_retriever),
):
    """Ingest a Wikipedia article into the knowledge base."""
    loader = WikipediaLoader()
    try:
        data = await loader.load(query=body.query, lang=body.lang or "en")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    title = body.title or data["title"]
    return await _ingest_single(
        text=data["text"],
        title=title,
        source_type="wikipedia",
        source_metadata=data.get("metadata", {}),
        subject=body.subject,
        grade_level=body.grade_level,
        user=user,
        db=db,
        retriever=retriever,
    )


@router.post("/ingest/arxiv")
async def ingest_arxiv(
    body: ArxivIngestRequest,
    user: User = Depends(require_role(Role.teacher, Role.admin)),
    db: AsyncSession = Depends(get_db),
    retriever: KnowledgeRetriever = Depends(get_retriever),
):
    """Ingest ArXiv research papers into the knowledge base."""
    loader = ArxivLoader()
    try:
        items = await loader.load(query=body.query, max_results=body.max_results or 1)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return await _ingest_multiple(
        items=items,
        source_type="arxiv",
        subject=body.subject,
        grade_level=body.grade_level,
        user=user,
        db=db,
        retriever=retriever,
    )


@router.post("/ingest/pubmed")
async def ingest_pubmed(
    body: PubMedIngestRequest,
    user: User = Depends(require_role(Role.teacher, Role.admin)),
    db: AsyncSession = Depends(get_db),
    retriever: KnowledgeRetriever = Depends(get_retriever),
):
    """Ingest PubMed biomedical articles into the knowledge base."""
    loader = PubMedLoader()
    try:
        items = await loader.load(query=body.query, max_results=body.max_results or 3)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return await _ingest_multiple(
        items=items,
        source_type="pubmed",
        subject=body.subject,
        grade_level=body.grade_level,
        user=user,
        db=db,
        retriever=retriever,
    )


@router.post("/ingest/gutenberg")
async def ingest_gutenberg(
    body: GutenbergIngestRequest,
    user: User = Depends(require_role(Role.teacher, Role.admin)),
    db: AsyncSession = Depends(get_db),
    retriever: KnowledgeRetriever = Depends(get_retriever),
):
    """Ingest Project Gutenberg books into the knowledge base."""
    loader = GutenbergLoader()
    try:
        items = await loader.load(query=body.query, max_results=body.max_results or 1)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return await _ingest_multiple(
        items=items,
        source_type="gutenberg",
        subject=body.subject,
        grade_level=body.grade_level,
        user=user,
        db=db,
        retriever=retriever,
    )


@router.post("/ingest/github")
async def ingest_github(
    body: GitHubIngestRequest,
    user: User = Depends(require_role(Role.teacher, Role.admin)),
    db: AsyncSession = Depends(get_db),
    retriever: KnowledgeRetriever = Depends(get_retriever),
):
    """Ingest files from a public GitHub repository into the knowledge base."""
    loader = GitHubLoader()
    try:
        data = await loader.load(
            repo=body.repo,
            file_path=body.file_path,
            branch=body.branch or "main",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # GitHubLoader.load returns a single dict (or list for future expansion)
    if isinstance(data, list):
        return await _ingest_multiple(
            items=data,
            source_type="github",
            subject=body.subject,
            grade_level=body.grade_level,
            user=user,
            db=db,
            retriever=retriever,
        )

    title = data["title"]
    return await _ingest_single(
        text=data["text"],
        title=title,
        source_type="github",
        source_metadata=data.get("metadata", {}),
        subject=body.subject,
        grade_level=body.grade_level,
        user=user,
        db=db,
        retriever=retriever,
    )


@router.post("/ingest/crawl")
async def ingest_crawl(
    body: CrawlIngestRequest,
    user: User = Depends(require_role(Role.teacher, Role.admin)),
    db: AsyncSession = Depends(get_db),
    retriever: KnowledgeRetriever = Depends(get_retriever),
):
    """Crawl a website recursively and ingest all pages into the knowledge base."""
    loader = RecursiveURLLoader()
    try:
        items = await loader.load(
            url=body.url,
            max_depth=body.max_depth or 2,
            max_pages=body.max_pages or 20,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return await _ingest_multiple(
        items=items,
        source_type="web_crawl",
        subject=body.subject,
        grade_level=body.grade_level,
        user=user,
        db=db,
        retriever=retriever,
    )


@router.get("/sources/available")
async def list_available_sources(
    user: User = Depends(get_current_user),
):
    """Return the list of available external source types for ingestion."""
    return {
        "sources": [
            {
                "type": "youtube",
                "name": "YouTube",
                "description": "Ingest video transcripts from YouTube",
                "endpoint": "/ingest/youtube",
            },
            {
                "type": "wikipedia",
                "name": "Wikipedia",
                "description": "Ingest articles from Wikipedia",
                "endpoint": "/ingest/wikipedia",
            },
            {
                "type": "arxiv",
                "name": "ArXiv",
                "description": "Ingest research papers from ArXiv",
                "endpoint": "/ingest/arxiv",
            },
            {
                "type": "pubmed",
                "name": "PubMed",
                "description": "Ingest biomedical literature from PubMed",
                "endpoint": "/ingest/pubmed",
            },
            {
                "type": "gutenberg",
                "name": "Project Gutenberg",
                "description": "Ingest public domain books from Project Gutenberg",
                "endpoint": "/ingest/gutenberg",
            },
            {
                "type": "github",
                "name": "GitHub",
                "description": "Ingest files from public GitHub repositories",
                "endpoint": "/ingest/github",
            },
            {
                "type": "web_crawl",
                "name": "Web Crawler",
                "description": "Recursively crawl and ingest website pages",
                "endpoint": "/ingest/crawl",
            },
        ]
    }
