"""Content upload, document management, and search endpoints."""

import json
import logging
import os
import re
import time
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_db, get_retriever
from src.auth.rbac import Role, require_role
from src.documents.chunker import SemanticChunker
from src.documents.enricher import ContentEnricher
from src.documents.processor import DocumentProcessor
from src.models.document import Document
from src.models.user import User
from src.rag.retriever import KnowledgeRetriever

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "uploads")
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".pptx", ".xlsx", ".xls", ".csv", ".epub", ".html", ".htm", ".json"}

# Magic byte signatures for allowed file types
_MAGIC_BYTES: dict[str, list[bytes]] = {
    ".pdf": [b"%PDF"],
    ".docx": [b"PK\x03\x04"],  # ZIP-based format
    ".pptx": [b"PK\x03\x04"],
    ".xlsx": [b"PK\x03\x04"],
    ".epub": [b"PK\x03\x04"],
}
# .xls, .csv, .html, .htm, .txt, .md have no magic bytes -- text formats


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


def _sanitize_filename(filename: str) -> str:
    """Sanitize a filename to prevent path traversal."""
    # Strip directory components and dangerous patterns
    name = os.path.basename(filename)
    name = name.replace("..", "").replace("/", "").replace("\\", "")
    # Remove non-alphanumeric chars except . - _
    name = re.sub(r"[^\w.\-]", "_", name)
    return name or "unnamed"


class UploadUrlRequest(BaseModel):
    url: HttpUrl
    title: str | None = None
    subject: str | None = None
    grade_level: str | None = None


class DocumentResponse(BaseModel):
    id: str
    title: str
    subject: str | None = None
    grade_level: str | None = None
    file_type: str
    file_size: int | None = None
    chunk_count: int
    status: str
    original_filename: str
    created_at: datetime | None = None
    processed_at: datetime | None = None


class SearchResult(BaseModel):
    content_preview: str
    metadata: dict = {}
    distance: float = 0.0
    citation: dict = {}


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int


@router.post("/upload")
async def upload_content(
    file: UploadFile = File(...),
    title: str | None = Query(None),
    subject: str | None = Query(None),
    grade_level: str | None = Query(None),
    stream: bool = Query(False),
    user: User = Depends(require_role(Role.teacher, Role.admin)),
    db: AsyncSession = Depends(get_db),
    retriever: KnowledgeRetriever = Depends(get_retriever),
):
    """Upload a file for processing and ingestion into the knowledge base."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read file content and check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds maximum size of 500MB")

    # Validate magic bytes for binary file types
    expected_magic = _MAGIC_BYTES.get(ext)
    if expected_magic:
        if not any(content.startswith(sig) for sig in expected_magic):
            raise HTTPException(
                status_code=400,
                detail=f"File content does not match expected format for {ext}",
            )

    # Sanitize and save file
    safe_name = _sanitize_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    if stream:
        async def generate():
            yield _sse_event("saving", 50, f"Saving file ({len(content) / (1024*1024):.1f}MB)...")
            with open(file_path, "wb") as f:
                f.write(content)

            yield _sse_event("creating_record", 55, "Creating document record...")
            doc = Document(
                title=title or safe_name,
                subject=subject,
                grade_level=grade_level,
                file_path=file_path,
                original_filename=safe_name,
                file_type=ext,
                file_size=len(content),
                status="processing",
                uploaded_by=user.id,
            )
            db.add(doc)
            await db.flush()

            try:
                yield _sse_event("parsing", 60, f"Parsing {ext} document...")
                processor = DocumentProcessor()
                parser = processor._detect_parser(file_path)
                parsed = parser.parse_with_metadata(file_path)
                text = parsed["text"]
                file_meta = {"subject": subject or "", "grade_level": grade_level or "", "title": title or safe_name}
                file_meta.update(parsed.get("metadata", {}))
                file_meta["source"] = file_path
                file_meta["file_type"] = ext

                document_id = str(uuid.uuid4())
                file_meta["document_id"] = document_id

                yield _sse_event("enriching", 70, "Enriching metadata...")
                enricher = ContentEnricher()
                enriched_meta = await enricher.enrich(text, file_meta)

                yield _sse_event("chunking", 80, "Creating semantic chunks...")
                chunker = SemanticChunker()
                chunks = chunker.chunk(text, enriched_meta)

                yield _sse_event("storing", 90, f"Storing {len(chunks)} chunks in knowledge base...")
                if retriever:
                    collection = retriever._get_collection()
                    if collection is not None:
                        ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
                        documents_list = [c["content"] for c in chunks]
                        metadatas = [DocumentProcessor._clean_metadata(c["metadata"]) for c in chunks]
                        collection.add(documents=documents_list, metadatas=metadatas, ids=ids)

                doc.chunk_count = len(chunks)
                doc.status = "completed"
                doc.processed_at = datetime.now(timezone.utc)
                doc.metadata_ = enriched_meta

                yield _sse_event("complete", 100, f"Processed '{title or safe_name}' — {len(chunks)} chunks", {
                    "document_id": str(doc.id),
                    "status": "completed",
                    "chunk_count": len(chunks),
                    "filename": safe_name,
                })
            except Exception as exc:
                doc.status = "failed"
                doc.metadata_ = {"error": str(exc)}
                yield _sse_event("error", 0, str(exc))

        return _sse_response(generate())

    # --- Non-streaming path (unchanged) ---
    with open(file_path, "wb") as f:
        f.write(content)

    # Create document record
    doc = Document(
        title=title or safe_name,
        subject=subject,
        grade_level=grade_level,
        file_path=file_path,
        original_filename=safe_name,
        file_type=ext,
        file_size=len(content),
        status="processing",
        uploaded_by=user.id,
    )
    db.add(doc)
    await db.flush()

    # Process document
    try:
        processor = DocumentProcessor(
            chunker=SemanticChunker(),
            enricher=ContentEnricher(),
            retriever=retriever,
        )
        result = await processor.process_file(file_path, metadata={
            "subject": subject or "",
            "grade_level": grade_level or "",
            "title": title or safe_name,
        })
        doc.chunk_count = result["chunk_count"]
        doc.status = "completed"
        doc.processed_at = datetime.now(timezone.utc)
        doc.metadata_ = result.get("metadata", {})
    except Exception as e:
        doc.status = "failed"
        doc.metadata_ = {"error": str(e)}

    return {
        "document_id": str(doc.id),
        "status": doc.status,
        "chunk_count": doc.chunk_count,
        "filename": safe_name,
    }


@router.post("/upload-url")
async def upload_url(
    body: UploadUrlRequest,
    stream: bool = Query(False),
    user: User = Depends(require_role(Role.teacher, Role.admin)),
    db: AsyncSession = Depends(get_db),
    retriever: KnowledgeRetriever = Depends(get_retriever),
):
    """Process a URL and ingest its content into the knowledge base."""
    url_str = str(body.url)

    if stream:
        async def generate():
            yield _sse_event("creating_record", 5, "Creating document record...")
            doc = Document(
                title=body.title or url_str,
                subject=body.subject,
                grade_level=body.grade_level,
                original_filename=url_str,
                file_type="url",
                status="processing",
                uploaded_by=user.id,
            )
            db.add(doc)
            await db.flush()

            try:
                yield _sse_event("fetching", 10, f"Fetching {url_str}...")
                from src.documents.parsers.web import WebParser
                web_parser = WebParser()
                text = await web_parser.parse_url(url_str)
                yield _sse_event("fetched", 25, f"Fetched {len(text)} characters")

                url_meta = {
                    "subject": body.subject or "",
                    "grade_level": body.grade_level or "",
                    "title": body.title or url_str,
                    "source": url_str,
                    "file_type": "url",
                }
                document_id = str(uuid.uuid4())
                url_meta["document_id"] = document_id

                yield _sse_event("enriching", 40, "Enriching metadata...")
                enricher = ContentEnricher()
                enriched_meta = await enricher.enrich(text, url_meta)

                yield _sse_event("chunking", 60, "Creating semantic chunks...")
                chunker = SemanticChunker()
                chunks = chunker.chunk(text, enriched_meta)

                yield _sse_event("storing", 80, f"Storing {len(chunks)} chunks in knowledge base...")
                if retriever:
                    collection = retriever._get_collection()
                    if collection is not None:
                        ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
                        documents_list = [c["content"] for c in chunks]
                        metadatas = [DocumentProcessor._clean_metadata(c["metadata"]) for c in chunks]
                        collection.add(documents=documents_list, metadatas=metadatas, ids=ids)

                doc.chunk_count = len(chunks)
                doc.status = "completed"
                doc.processed_at = datetime.now(timezone.utc)
                doc.metadata_ = enriched_meta

                yield _sse_event("complete", 100, f"Ingested URL — {len(chunks)} chunks", {
                    "document_id": str(doc.id),
                    "status": "completed",
                    "chunk_count": len(chunks),
                })
            except Exception as exc:
                doc.status = "failed"
                doc.metadata_ = {"error": str(exc)}
                yield _sse_event("error", 0, str(exc))

        return _sse_response(generate())

    # --- Non-streaming path (unchanged) ---
    doc = Document(
        title=body.title or url_str,
        subject=body.subject,
        grade_level=body.grade_level,
        original_filename=url_str,
        file_type="url",
        status="processing",
        uploaded_by=user.id,
    )
    db.add(doc)
    await db.flush()

    try:
        processor = DocumentProcessor(
            chunker=SemanticChunker(),
            enricher=ContentEnricher(),
            retriever=retriever,
        )
        result = await processor.process_url(url_str, metadata={
            "subject": body.subject or "",
            "grade_level": body.grade_level or "",
            "title": body.title or url_str,
        })
        doc.chunk_count = result["chunk_count"]
        doc.status = "completed"
        doc.processed_at = datetime.now(timezone.utc)
        doc.metadata_ = result.get("metadata", {})
    except Exception as e:
        doc.status = "failed"
        doc.metadata_ = {"error": str(e)}

    return {
        "document_id": str(doc.id),
        "status": doc.status,
        "chunk_count": doc.chunk_count,
    }


@router.get("/documents")
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List documents uploaded by the current user."""
    offset = (page - 1) * page_size
    stmt = (
        select(Document)
        .where(Document.uploaded_by == user.id)
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    docs = result.scalars().all()

    count_stmt = select(Document.id).where(Document.uploaded_by == user.id)
    count_result = await db.execute(count_stmt)
    total = len(count_result.all())

    return {
        "items": [
            {
                "id": str(d.id),
                "title": d.title,
                "subject": d.subject,
                "file_type": d.file_type,
                "status": d.status,
                "chunk_count": d.chunk_count,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get details of a specific document."""
    stmt = select(Document).where(
        Document.id == document_id,
        Document.uploaded_by == user.id,
    )
    result = await db.execute(stmt)
    doc = result.scalars().first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": str(doc.id),
        "title": doc.title,
        "subject": doc.subject,
        "grade_level": doc.grade_level,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "chunk_count": doc.chunk_count,
        "status": doc.status,
        "original_filename": doc.original_filename,
        "metadata": doc.metadata_,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "processed_at": doc.processed_at.isoformat() if doc.processed_at else None,
    }


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    user: User = Depends(require_role(Role.teacher, Role.admin)),
    db: AsyncSession = Depends(get_db),
    retriever: KnowledgeRetriever = Depends(get_retriever),
):
    """Delete a document and its chunks from the knowledge base."""
    stmt = select(Document).where(
        Document.id == document_id,
        Document.uploaded_by == user.id,
    )
    result = await db.execute(stmt)
    doc = result.scalars().first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove chunks from ChromaDB
    retriever.delete_document_chunks(document_id)

    # Delete the file if it exists and is within UPLOAD_DIR
    if doc.file_path and os.path.exists(doc.file_path):
        real_path = os.path.realpath(doc.file_path)
        real_upload_dir = os.path.realpath(UPLOAD_DIR)
        if real_path.startswith(real_upload_dir + os.sep):
            os.remove(real_path)

    await db.delete(doc)

    return {"status": "deleted", "document_id": document_id}


@router.get("/search")
async def search_content(
    q: str = Query("", description="Search query"),
    subject: str | None = Query(None),
    limit: int = Query(5, ge=1, le=20),
    user: User = Depends(get_current_user),
    retriever: KnowledgeRetriever = Depends(get_retriever),
):
    """Search the knowledge base with enhanced RAG and source citations."""
    if not q.strip():
        return {"query": q, "results": [], "total": 0}

    rag_results = await retriever.retrieve(
        query=q,
        subject=subject,
        k=limit,
    )

    sources = rag_results.get("sources", [])
    citations = rag_results.get("citations", [])

    results = []
    for i, src in enumerate(sources):
        citation = citations[i] if i < len(citations) else {}
        results.append({
            "content_preview": src.get("content_preview", ""),
            "metadata": src.get("metadata", {}),
            "distance": src.get("distance", 0.0),
            "citation": citation,
        })

    return {
        "query": q,
        "results": results,
        "total": rag_results.get("num_results", 0),
    }


@router.get("/rag-test")
async def rag_test(
    q: str = Query("", description="Search query"),
    subject: str | None = Query(None),
    limit: int = Query(5, ge=1, le=20),
    user: User = Depends(get_current_user),
    retriever: KnowledgeRetriever = Depends(get_retriever),
):
    """RAG debug endpoint — returns full chunk content, timing, and metadata."""
    if not q.strip():
        return {"query": q, "chunks": [], "timing": {}, "stats": {}}

    collection = retriever._get_collection()
    total_chunks = collection.count() if collection else 0

    # Step 1: Query rewriting
    t0 = time.perf_counter()
    context = {}
    if subject:
        context["subject"] = subject
    rewritten = await retriever._rewriter.rewrite(q, context)
    t_rewrite = time.perf_counter() - t0

    # Step 2: ChromaDB vector search
    t1 = time.perf_counter()
    where_filter = {}
    if subject:
        where_filter["subject"] = subject

    raw_results = None
    if collection:
        try:
            raw_results = collection.query(
                query_texts=[rewritten],
                n_results=limit,
                where=where_filter if where_filter else None,
            )
        except Exception as exc:
            return {"query": q, "error": str(exc), "chunks": [], "timing": {}, "stats": {}}
    t_search = time.perf_counter() - t1

    if not raw_results or not raw_results.get("documents") or not raw_results["documents"][0]:
        return {
            "query": q,
            "rewritten_query": rewritten,
            "chunks": [],
            "timing": {
                "rewrite_ms": round(t_rewrite * 1000, 2),
                "search_ms": round(t_search * 1000, 2),
                "total_ms": round((t_rewrite + t_search) * 1000, 2),
            },
            "stats": {"total_chunks_in_db": total_chunks, "results_found": 0},
        }

    documents = raw_results["documents"][0]
    metadatas = raw_results["metadatas"][0] if raw_results.get("metadatas") else [{}] * len(documents)
    distances = raw_results["distances"][0] if raw_results.get("distances") else [0.0] * len(documents)
    ids = raw_results["ids"][0] if raw_results.get("ids") else [""] * len(documents)

    # Step 3: Re-rank
    t2 = time.perf_counter()
    sources = [
        {"content_preview": doc, "metadata": meta, "distance": dist}
        for doc, meta, dist in zip(documents, metadatas, distances)
    ]
    ranked = retriever._ranker.rank(sources, q)
    t_rank = time.perf_counter() - t2

    total_time = t_rewrite + t_search + t_rank

    chunks = []
    for i, (src, chunk_id) in enumerate(zip(ranked, ids)):
        meta = src.get("metadata", {})
        chunks.append({
            "rank": i + 1,
            "chunk_id": chunk_id,
            "content": src["content_preview"],
            "distance": round(src.get("distance", 0.0), 4),
            "relevance": round(1.0 - src.get("distance", 0.0), 4),
            "metadata": {
                "source_type": meta.get("source_type", ""),
                "subject": meta.get("subject", ""),
                "title": meta.get("title", ""),
                "document_id": meta.get("document_id", ""),
            },
            "char_count": len(src["content_preview"]),
        })

    return {
        "query": q,
        "rewritten_query": rewritten,
        "subject_filter": subject,
        "chunks": chunks,
        "timing": {
            "rewrite_ms": round(t_rewrite * 1000, 2),
            "search_ms": round(t_search * 1000, 2),
            "rank_ms": round(t_rank * 1000, 2),
            "total_ms": round(total_time * 1000, 2),
        },
        "stats": {
            "total_chunks_in_db": total_chunks,
            "results_found": len(chunks),
            "limit": limit,
        },
    }
