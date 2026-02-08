"""Source loader endpoints for ingesting content from external sources."""

import json
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
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
        doc.processed_at = datetime.utcnow()
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


# ---------- SSE streaming helpers ----------

def _sse_event(step: str, progress: int, message: str, result: dict | None = None) -> str:
    """Format a Server-Sent Event line."""
    payload: dict = {"step": step, "progress": progress, "message": message}
    if result is not None:
        payload["result"] = result
    return f"data: {json.dumps(payload)}\n\n"


def _sse_response(generator):
    """Wrap an async generator as an SSE StreamingResponse."""
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _ingest_single_sse(
    text: str,
    title: str,
    source_type: str,
    source_metadata: dict,
    subject: str | None,
    grade_level: str | None,
    user: User,
    db: AsyncSession,
    retriever: KnowledgeRetriever,
):
    """Ingest a single document, yielding SSE progress events."""
    yield _sse_event("creating_record", 20, "Creating document record...")

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
        chunker = SemanticChunker()
        enricher = ContentEnricher()
        document_id = str(uuid.uuid4())
        meta = {
            "subject": subject or "",
            "grade_level": grade_level or "",
            "title": title,
            "source_type": source_type,
            "document_id": document_id,
        }
        meta.update(source_metadata)

        yield _sse_event("enriching", 35, "Enriching metadata...")
        enriched_meta = await enricher.enrich(text, meta)

        yield _sse_event("chunking", 55, "Splitting text into chunks...")
        chunks = chunker.chunk(text, enriched_meta)

        yield _sse_event("storing", 75, f"Storing {len(chunks)} chunks in vector database...")
        collection = retriever._get_collection()
        if collection is not None:
            ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
            documents_list = [c["content"] for c in chunks]
            metadatas = [DocumentProcessor._clean_metadata(c["metadata"]) for c in chunks]
            collection.add(documents=documents_list, metadatas=metadatas, ids=ids)

        doc.chunk_count = len(chunks)
        doc.status = "completed"
        doc.processed_at = datetime.utcnow()
        doc.metadata_ = enriched_meta

        result = {
            "document_id": str(doc.id),
            "status": doc.status,
            "chunk_count": doc.chunk_count,
            "title": doc.title,
        }
        yield _sse_event("complete", 100, "Ingestion complete!", result)
    except Exception as exc:
        logger.error("SSE ingest failed for %s '%s': %s", source_type, title, exc)
        doc.status = "failed"
        doc.metadata_ = {"error": str(exc)}
        yield _sse_event("error", 0, f"Ingestion failed: {exc}")


async def _ingest_multiple_sse(
    items: list[dict],
    source_type: str,
    subject: str | None,
    grade_level: str | None,
    user: User,
    db: AsyncSession,
    retriever: KnowledgeRetriever,
):
    """Ingest multiple documents, yielding SSE progress events."""
    total = len(items)
    results = []
    chunker = SemanticChunker()
    enricher = ContentEnricher()

    for idx, item in enumerate(items):
        doc_num = idx + 1
        base = int((idx / total) * 85) + 10  # 10–95% range

        yield _sse_event("processing", base, f"Processing document {doc_num}/{total}: '{item['title']}'...")

        doc = Document(
            title=item["title"],
            subject=subject,
            grade_level=grade_level,
            original_filename=f"{source_type}:{item['title']}",
            file_type=source_type,
            status="processing",
            uploaded_by=user.id,
        )
        db.add(doc)
        await db.flush()

        try:
            document_id = str(uuid.uuid4())
            meta = {
                "subject": subject or "",
                "grade_level": grade_level or "",
                "title": item["title"],
                "source_type": source_type,
                "document_id": document_id,
            }
            meta.update(item.get("metadata", {}))

            enriched_meta = await enricher.enrich(item["text"], meta)
            chunks = chunker.chunk(item["text"], enriched_meta)

            store_progress = base + int(50 / total)
            yield _sse_event("storing", store_progress, f"Storing {len(chunks)} chunks from '{item['title']}'...")

            collection = retriever._get_collection()
            if collection is not None:
                ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
                documents_list = [c["content"] for c in chunks]
                metadatas = [DocumentProcessor._clean_metadata(c["metadata"]) for c in chunks]
                collection.add(documents=documents_list, metadatas=metadatas, ids=ids)

            doc.chunk_count = len(chunks)
            doc.status = "completed"
            doc.processed_at = datetime.utcnow()
            doc.metadata_ = enriched_meta

            results.append({
                "document_id": str(doc.id),
                "status": "completed",
                "chunk_count": len(chunks),
                "title": item["title"],
            })
        except Exception as exc:
            logger.error("SSE ingest failed for %s '%s': %s", source_type, item["title"], exc)
            doc.status = "failed"
            doc.metadata_ = {"error": str(exc)}
            results.append({
                "document_id": str(doc.id),
                "status": "failed",
                "chunk_count": 0,
                "title": item["title"],
            })
            yield _sse_event("warning", base + int(60 / total), f"Failed: '{item['title']}' — {exc}")

    ok_count = len([r for r in results if r["status"] == "completed"])
    total_chunks = sum(r["chunk_count"] for r in results)
    yield _sse_event(
        "complete", 100,
        f"Ingested {ok_count}/{total} documents ({total_chunks} total chunks)",
        {"documents": results},
    )


# ---------- Endpoints ----------

@router.post("/ingest/youtube")
async def ingest_youtube(
    body: YouTubeIngestRequest,
    stream: bool = Query(False),
    user: User = Depends(require_role(Role.teacher, Role.admin)),
    db: AsyncSession = Depends(get_db),
    retriever: KnowledgeRetriever = Depends(get_retriever),
):
    """Ingest a YouTube video transcript into the knowledge base."""
    if stream:
        async def generate():
            yield _sse_event("fetching", 5, "Fetching YouTube transcript...")
            loader = YouTubeLoader()
            try:
                data = await loader.load(video_id=body.video_id)
            except Exception as exc:
                yield _sse_event("error", 0, str(exc))
                return
            title = body.title or data["title"]
            yield _sse_event("fetched", 12, f"Fetched: '{title}'")
            async for event in _ingest_single_sse(
                text=data["text"], title=title, source_type="youtube",
                source_metadata=data.get("metadata", {}),
                subject=body.subject, grade_level=body.grade_level,
                user=user, db=db, retriever=retriever,
            ):
                yield event
        return _sse_response(generate())

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
    stream: bool = Query(False),
    user: User = Depends(require_role(Role.teacher, Role.admin)),
    db: AsyncSession = Depends(get_db),
    retriever: KnowledgeRetriever = Depends(get_retriever),
):
    """Ingest a Wikipedia article into the knowledge base."""
    if stream:
        async def generate():
            yield _sse_event("fetching", 5, "Fetching Wikipedia article...")
            loader = WikipediaLoader()
            try:
                data = await loader.load(query=body.query, lang=body.lang or "en")
            except Exception as exc:
                yield _sse_event("error", 0, str(exc))
                return
            title = body.title or data["title"]
            yield _sse_event("fetched", 12, f"Fetched: '{title}'")
            async for event in _ingest_single_sse(
                text=data["text"], title=title, source_type="wikipedia",
                source_metadata=data.get("metadata", {}),
                subject=body.subject, grade_level=body.grade_level,
                user=user, db=db, retriever=retriever,
            ):
                yield event
        return _sse_response(generate())

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
    stream: bool = Query(False),
    user: User = Depends(require_role(Role.teacher, Role.admin)),
    db: AsyncSession = Depends(get_db),
    retriever: KnowledgeRetriever = Depends(get_retriever),
):
    """Ingest ArXiv research papers into the knowledge base."""
    if stream:
        async def generate():
            yield _sse_event("fetching", 5, f"Searching ArXiv for up to {body.max_results or 1} papers...")
            loader = ArxivLoader()
            try:
                items = await loader.load(query=body.query, max_results=body.max_results or 1)
            except Exception as exc:
                yield _sse_event("error", 0, str(exc))
                return
            yield _sse_event("fetched", 10, f"Found {len(items)} papers")
            async for event in _ingest_multiple_sse(
                items=items, source_type="arxiv",
                subject=body.subject, grade_level=body.grade_level,
                user=user, db=db, retriever=retriever,
            ):
                yield event
        return _sse_response(generate())

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
    stream: bool = Query(False),
    user: User = Depends(require_role(Role.teacher, Role.admin)),
    db: AsyncSession = Depends(get_db),
    retriever: KnowledgeRetriever = Depends(get_retriever),
):
    """Ingest PubMed biomedical articles into the knowledge base."""
    if stream:
        async def generate():
            yield _sse_event("fetching", 5, f"Searching PubMed for up to {body.max_results or 3} articles...")
            loader = PubMedLoader()
            try:
                items = await loader.load(query=body.query, max_results=body.max_results or 3)
            except Exception as exc:
                yield _sse_event("error", 0, str(exc))
                return
            yield _sse_event("fetched", 10, f"Found {len(items)} articles")
            async for event in _ingest_multiple_sse(
                items=items, source_type="pubmed",
                subject=body.subject, grade_level=body.grade_level,
                user=user, db=db, retriever=retriever,
            ):
                yield event
        return _sse_response(generate())

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
    stream: bool = Query(False),
    user: User = Depends(require_role(Role.teacher, Role.admin)),
    db: AsyncSession = Depends(get_db),
    retriever: KnowledgeRetriever = Depends(get_retriever),
):
    """Ingest Project Gutenberg books into the knowledge base."""
    if stream:
        async def generate():
            yield _sse_event("fetching", 5, f"Searching Project Gutenberg for up to {body.max_results or 1} books...")
            loader = GutenbergLoader()
            try:
                items = await loader.load(query=body.query, max_results=body.max_results or 1)
            except Exception as exc:
                yield _sse_event("error", 0, str(exc))
                return
            yield _sse_event("fetched", 10, f"Found {len(items)} books")
            async for event in _ingest_multiple_sse(
                items=items, source_type="gutenberg",
                subject=body.subject, grade_level=body.grade_level,
                user=user, db=db, retriever=retriever,
            ):
                yield event
        return _sse_response(generate())

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
    stream: bool = Query(False),
    user: User = Depends(require_role(Role.teacher, Role.admin)),
    db: AsyncSession = Depends(get_db),
    retriever: KnowledgeRetriever = Depends(get_retriever),
):
    """Ingest files from a public GitHub repository into the knowledge base."""
    if stream:
        async def generate():
            yield _sse_event("fetching", 5, f"Fetching from GitHub: {body.repo}...")
            loader = GitHubLoader()
            try:
                data = await loader.load(
                    repo=body.repo, file_path=body.file_path,
                    branch=body.branch or "main",
                )
            except Exception as exc:
                yield _sse_event("error", 0, str(exc))
                return
            if isinstance(data, list):
                yield _sse_event("fetched", 10, f"Fetched {len(data)} files")
                async for event in _ingest_multiple_sse(
                    items=data, source_type="github",
                    subject=body.subject, grade_level=body.grade_level,
                    user=user, db=db, retriever=retriever,
                ):
                    yield event
            else:
                title = data["title"]
                yield _sse_event("fetched", 12, f"Fetched: '{title}'")
                async for event in _ingest_single_sse(
                    text=data["text"], title=title, source_type="github",
                    source_metadata=data.get("metadata", {}),
                    subject=body.subject, grade_level=body.grade_level,
                    user=user, db=db, retriever=retriever,
                ):
                    yield event
        return _sse_response(generate())

    loader = GitHubLoader()
    try:
        data = await loader.load(
            repo=body.repo,
            file_path=body.file_path,
            branch=body.branch or "main",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

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
    stream: bool = Query(False),
    user: User = Depends(require_role(Role.teacher, Role.admin)),
    db: AsyncSession = Depends(get_db),
    retriever: KnowledgeRetriever = Depends(get_retriever),
):
    """Crawl a website recursively and ingest all pages into the knowledge base."""
    if stream:
        async def generate():
            yield _sse_event("fetching", 5, f"Crawling {body.url} (depth {body.max_depth or 2}, max {body.max_pages or 20} pages)...")
            loader = RecursiveURLLoader()
            try:
                items = await loader.load(
                    url=body.url, max_depth=body.max_depth or 2,
                    max_pages=body.max_pages or 20,
                )
            except Exception as exc:
                yield _sse_event("error", 0, str(exc))
                return
            yield _sse_event("fetched", 10, f"Crawled {len(items)} pages")
            async for event in _ingest_multiple_sse(
                items=items, source_type="web_crawl",
                subject=body.subject, grade_level=body.grade_level,
                user=user, db=db, retriever=retriever,
            ):
                yield event
        return _sse_response(generate())

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
