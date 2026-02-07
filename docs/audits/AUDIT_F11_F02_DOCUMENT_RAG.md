# Audit Report: F11/F02 Document Processing Pipeline + RAG Enhancement

**Auditor**: Code Audit Agent
**Date**: 2026-02-07
**Scope**: `src/documents/`, `src/rag/`, `src/models/document.py`, `src/api/routers/content.py`, `migrations/versions/003_document_tables.py`, `tests/test_documents.py`
**Verdict**: Functional with notable gaps in security, error handling, and test coverage

---

## 1. Architecture Overview

The F11/F02 feature implements a five-stage document processing pipeline:

```
Parse --> Chunk --> Enrich --> Store (ChromaDB) --> Retrieve (RAG)
```

### Module Map

| Module | File | Purpose |
|--------|------|---------|
| **Processor** | `src/documents/processor.py` | Orchestrates the full pipeline |
| **Chunker** | `src/documents/chunker.py` | Section-aware text splitting with overlap |
| **Enricher** | `src/documents/enricher.py` | Keyword extraction + optional LLM analysis |
| **PDF Parser** | `src/documents/parsers/pdf.py` | PDF text extraction via PyMuPDF (fitz) |
| **DOCX Parser** | `src/documents/parsers/docx.py` | DOCX text extraction via python-docx |
| **Text Parser** | `src/documents/parsers/text.py` | Plain text / Markdown file reader |
| **Web Parser** | `src/documents/parsers/web.py` | URL fetching + HTML content extraction |
| **Retriever** | `src/rag/retriever.py` | ChromaDB vector search with rewriting + re-ranking |
| **Rewriter** | `src/rag/rewriter.py` | LLM-based query expansion (optional) |
| **Ranker** | `src/rag/ranker.py` | Hybrid semantic + keyword re-ranking |
| **Document Model** | `src/models/document.py` | SQLAlchemy ORM model for PostgreSQL |
| **Content API** | `src/api/routers/content.py` | REST endpoints (upload, URL ingest, search, CRUD) |
| **Migration** | `migrations/versions/003_document_tables.py` | Alembic migration for `documents` table |

---

## 2. Execution Flow Traces

### 2.1 File Upload Flow (`POST /api/v1/content/upload`)

**Entry**: `src/api/routers/content.py:72-147`

1. **Validation** (lines 83-96):
   - Checks filename exists (line 83-84)
   - Validates file extension against `ALLOWED_EXTENSIONS` (line 86-91)
   - Reads entire file content into memory, checks against `MAX_FILE_SIZE` (50MB) (lines 94-96)
2. **Filesystem Write** (lines 98-105):
   - Sanitizes filename via `_sanitize_filename()` (line 99)
   - Generates UUID-prefixed unique name (line 100)
   - Creates `data/uploads/` directory and writes file (lines 101-105)
3. **Database Record** (lines 107-120):
   - Creates `Document` ORM object with status="processing" (line 108-118)
   - Flushes to DB to get the auto-generated UUID `doc.id` (line 120)
4. **Processing Pipeline** (lines 122-141):
   - Creates `DocumentProcessor` with fresh `SemanticChunker`, `ContentEnricher`, and injected `retriever` (lines 124-128)
   - Calls `processor.process_file(file_path, metadata)` (line 129)
     - `processor._detect_parser()` routes to correct parser by extension (line 37, lines 89-99)
     - Parser's `parse_with_metadata()` extracts text + metadata
     - `enricher.enrich()` extracts key terms and summary (line 64)
     - `chunker.chunk()` splits into overlapping chunks (line 67)
     - Chunks stored in ChromaDB via `retriever._collection.add()` (lines 70-81)
   - On success: updates doc status to "completed", sets chunk_count, processed_at (lines 134-137)
   - On failure: sets status to "failed", stores error in metadata (lines 138-140)
5. **Response** (lines 142-147): Returns `document_id`, `status`, `chunk_count`, `filename`

**Critical Observation**: The database commit happens implicitly via the `get_db` dependency's `yield` + `commit()` pattern (`src/api/dependencies.py:25`). If the request handler completes without exception, the session commits. However, if processing fails (line 138-140), the doc with status="failed" IS still committed -- this is intentional, allowing users to see failed uploads.

### 2.2 URL Ingest Flow (`POST /api/v1/content/upload-url`)

**Entry**: `src/api/routers/content.py:150-195`

1. **Validation**: Pydantic `UploadUrlRequest` validates `url` as `HttpUrl` (line 39)
2. **Database Record**: Creates Document with `file_type="url"`, no `file_path` or `file_size` (lines 160-168)
3. **Processing Pipeline**: Calls `processor.process_url(url_str, metadata)` (line 178)
   - `WebParser.parse_url()` fetches URL via httpx with 30s timeout (line 14)
   - Strips nav/footer/script tags via BeautifulSoup (lines 21-22)
   - Extracts main content from `<main>`, `<article>`, or `<body>` (line 25)
   - Remainder follows same enrich -> chunk -> store pipeline as file upload

### 2.3 Search Query Flow (`GET /api/v1/content/search`)

**Entry**: `src/api/routers/content.py:303-337`

1. **Validation**: Empty query returns empty results immediately (lines 311-312)
2. **Retrieval**: Calls `retriever.retrieve(query, subject, k=limit)` (lines 314-318)
   - `QueryRewriter.rewrite()` optionally expands query (line 84) -- no-op without LLM
   - ChromaDB `collection.query()` performs vector search (lines 93-97)
   - `ResultRanker.rank()` re-scores with hybrid semantic + keyword scoring (line 119)
   - `_format_citations()` builds structured citation objects (line 122)
3. **Response**: Maps sources + citations to `SearchResult` schema (lines 320-337)

**Note**: The search endpoint does NOT require authentication (`get_current_user` is not a dependency). Any caller can search the knowledge base.

### 2.4 Document Deletion Flow (`DELETE /api/v1/content/documents/{document_id}`)

**Entry**: `src/api/routers/content.py:273-300`

1. **Authorization**: Fetches document filtered by `document_id` AND `uploaded_by == user.id` (lines 281-285)
2. **ChromaDB Cleanup**: Calls `retriever.delete_document_chunks(document_id)` (line 292)
   - Deletes by `where={"document_id": document_id}` filter (retriever.py:151)
   - Silently catches all exceptions (retriever.py:152-153)
3. **Filesystem Cleanup**: Deletes the file from disk if `file_path` exists (lines 295-296)
4. **Database Cleanup**: Deletes the Document ORM record (line 298)

---

## 3. Integration Points

### 3.1 Application Startup (`src/api/main.py:15-48`)

- `KnowledgeRetriever` is instantiated during lifespan startup (lines 25-33)
- Stored on `app.state.retriever`
- ChromaDB initialization failure is silently caught (line 31-32), meaning the app runs even if ChromaDB is down, but with a non-functional retriever

### 3.2 Dependency Injection (`src/api/dependencies.py:41-43`)

```python
def get_retriever(request: Request) -> KnowledgeRetriever:
    return request.app.state.retriever
```

- Singleton retriever shared across all requests (no per-request instantiation)
- Injected into content upload, URL upload, delete, and search endpoints

### 3.3 Tutor Agent Integration (`src/agents/tutor.py:180-206`)

The tutor agent uses the retriever at line 183:
```python
knowledge_context = await self.retriever.retrieve(
    query=input_text,
    subject=context.current_subject,
)
```

**BUG**: The tutor agent treats `knowledge_context` as `list[dict]` (line 181, 196-198) but `retriever.retrieve()` returns a single `dict` with keys `context`, `sources`, `citations`, `num_results`. The tutor iterates over it as a list and calls `.get("content", "")` on each item (line 197), which will iterate over the dict's string keys, producing empty strings. **The RAG context is effectively lost in the tutor agent.**

### 3.4 ChromaDB Connection

- Uses `chromadb.HttpClient` (client-server mode), not embedded
- Default host/port: `localhost:8100`
- Collection: `educational_content` with cosine distance metric
- Document IDs in ChromaDB: `{document_id}_chunk_{i}` (processor.py:71) vs `chunk_{hash}_{i}` (retriever.py:48)

**BUG**: Two different ID schemes exist. The `DocumentProcessor` uses `{document_id}_chunk_{i}` when storing chunks (processor.py:71), but `KnowledgeRetriever.ingest_document()` uses `chunk_{hash}_{i}` (retriever.py:48). The `delete_document_chunks()` method deletes by `where={"document_id": document_id}` metadata filter (retriever.py:151), not by ID prefix. This works IF the `document_id` metadata is correctly set on each chunk -- and it is (processor.py:61,73). However, if `ingest_document()` is used directly (bypassing the processor), chunks won't have `document_id` metadata and will be un-deletable.

---

## 4. Data Models

### 4.1 Document Model (`src/models/document.py`)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK, auto-generated | `gen_random_uuid()` |
| `title` | String(255) | NOT NULL | Falls back to sanitized filename |
| `subject` | String(100) | Nullable | Academic subject |
| `grade_level` | String(50) | Nullable | e.g., "Grade 5" |
| `file_path` | String(500) | Nullable | Null for URL ingests |
| `original_filename` | String(255) | NOT NULL | Sanitized; URL string for URL ingests |
| `file_type` | String(50) | NOT NULL | Extension or "url" |
| `file_size` | Integer | Nullable | Null for URL ingests |
| `chunk_count` | Integer | Default 0 | Updated after processing |
| `status` | String(50) | Default "pending" | pending/processing/completed/failed |
| `metadata_` | JSONB | Default '{}' | Mapped as `metadata` in DB |
| `uploaded_by` | UUID | FK -> users.id CASCADE | NOT NULL |
| `created_at` | DateTime | server_default now() | |
| `processed_at` | DateTime | Nullable | Set on completion |

### 4.2 Migration (`migrations/versions/003_document_tables.py`)

- Creates `documents` table with 3 indexes: `uploaded_by`, `subject`, `status`
- FK cascade on delete from `users` table
- Model and migration are in sync -- all columns match

### 4.3 Missing Elements

- **No `updated_at` column**: Cannot track when a document record was last modified
- **No relationship defined**: The `Document` model has no SQLAlchemy `relationship()` to `User`, requiring manual joins
- **No content hash/checksum**: Cannot detect duplicate uploads
- **`original_filename` stores URL string for URL ingests** (content.py:164): The field name is misleading for URL documents

---

## 5. Code Quality Issues

### 5.1 CRITICAL: Tutor Agent RAG Integration is Broken

**File**: `src/agents/tutor.py:183-198`

```python
knowledge_context = await self.retriever.retrieve(...)  # Returns dict
# ...
sources_text = "\n\n".join(
    doc.get("content", "") for doc in knowledge_context  # Iterates over dict KEYS
)
```

`retriever.retrieve()` returns `{"context": str, "sources": list, ...}`. Iterating over this dict yields string keys `"context"`, `"sources"`, etc. Calling `.get("content", "")` on strings raises `AttributeError`. The `if knowledge_context:` check at line 195 will be True (dict is non-empty), so this code path IS reached but will either crash or produce garbage.

**Severity**: CRITICAL -- The core RAG-to-tutor integration does not work.

### 5.2 HIGH: Processor `process_file` is Synchronous I/O in Async Context

**File**: `src/documents/processor.py:38`

```python
result = parser.parse_with_metadata(file_path)
```

All parsers (`PdfParser`, `DocxParser`, `TextParser`) perform synchronous file I/O. In an async FastAPI endpoint, this blocks the event loop. For large PDF files, this can stall all concurrent requests.

**Severity**: HIGH -- Performance degradation under load.

### 5.3 HIGH: No `await db.commit()` After Upload Processing

**File**: `src/api/routers/content.py:119-141`

The upload endpoint modifies `doc.status`, `doc.chunk_count`, `doc.processed_at`, and `doc.metadata_` after `flush()`, but never explicitly commits. The commit happens via the `get_db` dependency's finally block (`dependencies.py:25`). If any exception occurs between the status update (line 134) and the dependency cleanup, those changes may be lost. Additionally, if the commit in the dependency fails, the file has already been written to disk and chunks to ChromaDB, creating an inconsistency.

**Severity**: HIGH -- Data inconsistency risk between PostgreSQL, filesystem, and ChromaDB.

### 5.4 MEDIUM: `_force_split` Potential Infinite Loop

**File**: `src/documents/chunker.py:84-96`

```python
def _force_split(self, text: str) -> list[str]:
    start = 0
    while start < len(text):
        end = start + self.chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - self.chunk_overlap
        if start >= len(text):
            break
```

If `chunk_overlap >= chunk_size`, `start` never advances (`start = end - overlap = start + size - overlap <= start`), causing an infinite loop. No guard validates `chunk_overlap < chunk_size`.

**Severity**: MEDIUM -- Could hang processing if misconfigured.

### 5.5 MEDIUM: Enricher Silently Swallows LLM Errors

**File**: `src/documents/enricher.py:41-42`

```python
except Exception:
    pass  # Graceful fallback to basic enrichment
```

All LLM errors are silently swallowed with a bare `pass`. This includes:
- Authentication failures (bad API key)
- Rate limiting
- Network errors
- Malformed responses

No logging, no metrics, no indication to the caller that enrichment was degraded.

**Severity**: MEDIUM -- Debugging production issues becomes very difficult.

### 5.6 MEDIUM: Retriever Silently Swallows Delete Errors

**File**: `src/rag/retriever.py:152-153`

```python
except Exception:
    pass  # Best effort deletion
```

If ChromaDB deletion fails, the document record is still deleted from PostgreSQL and the file from disk. This leaves orphaned chunks in ChromaDB forever.

**Severity**: MEDIUM -- Data leak / storage bloat over time.

### 5.7 LOW: Duplicate Chunking Logic

The codebase contains TWO text splitters:
- `SemanticChunker` in `src/documents/chunker.py` (custom, used by `DocumentProcessor`)
- `RecursiveCharacterTextSplitter` from LangChain in `src/rag/retriever.py:27-31` (used by `ingest_document()`)

The `DocumentProcessor` pipeline uses `SemanticChunker`, while `KnowledgeRetriever.ingest_document()` / `ingest_file()` use LangChain's splitter. These paths are independent but both write to the same ChromaDB collection, potentially with different chunk sizes and strategies.

**Severity**: LOW -- Confusion and inconsistent chunking if both paths are used.

### 5.8 LOW: `_clean_metadata` Discards None Values Silently

**File**: `src/documents/processor.py:102-112`

`None` values are filtered out entirely. If downstream code expects a key to exist, this could cause `KeyError`.

### 5.9 LOW: Count Query Inefficiency

**File**: `src/api/routers/content.py:217-219`

```python
count_stmt = select(Document.id).where(Document.uploaded_by == user.id)
count_result = await db.execute(count_stmt)
total = len(count_result.all())
```

This fetches ALL document IDs into Python memory just to count them. Should use `select(func.count(Document.id))` instead.

---

## 6. Security Concerns

### 6.1 HIGH: Search Endpoint Has No Authentication

**File**: `src/api/routers/content.py:303-308`

```python
@router.get("/search")
async def search_content(
    q: str = Query("", description="Search query"),
    subject: str | None = Query(None),
    limit: int = Query(5, ge=1, le=20),
    retriever: KnowledgeRetriever = Depends(get_retriever),
):
```

No `user: User = Depends(get_current_user)` dependency. Any unauthenticated caller can search the entire knowledge base. If documents contain sensitive educational content, this is a data exposure risk.

### 6.2 HIGH: SSRF via URL Ingest

**File**: `src/documents/parsers/web.py:14`

```python
async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
    response = await client.get(url)
```

The URL ingest endpoint accepts ANY URL, including:
- `http://localhost:*` or `http://127.0.0.1:*` -- access internal services
- `http://169.254.169.254/` -- AWS metadata service
- `http://[::1]:*` -- IPv6 localhost
- Internal hostnames on the Docker network

No URL validation, allowlisting, or blocklisting is performed. The `follow_redirects=True` flag makes it worse, as an attacker can set up a redirect from an external URL to an internal one.

**Severity**: HIGH -- Server-Side Request Forgery (SSRF) vulnerability.

### 6.3 MEDIUM: Path Traversal Incomplete Sanitization

**File**: `src/api/routers/content.py:28-35`

```python
def _sanitize_filename(filename: str) -> str:
    name = os.path.basename(filename)
    name = name.replace("..", "").replace("/", "").replace("\\", "")
    name = re.sub(r"[^\w.\-]", "_", name)
    return name or "unnamed"
```

While `os.path.basename()` is the correct first step, the subsequent `replace("..", "")` is applied AFTER basename. A filename like `....//test.txt` becomes `test.txt` after basename, then the replaces are redundant. However, the UUID prefix on line 100 (`f"{uuid.uuid4().hex}_{safe_name}"`) provides an additional safety layer. The real protection comes from writing to a fixed `UPLOAD_DIR` with a UUID prefix.

**Severity**: MEDIUM -- Defense-in-depth is adequate but the sanitization logic is misleadingly incomplete.

### 6.4 MEDIUM: No Content-Type Validation (Magic Bytes)

**File**: `src/api/routers/content.py:86-91`

Only the file extension is validated, not the actual file content. An attacker could upload a malicious executable renamed to `.txt`. While this doesn't directly enable code execution (the file is processed by a text parser), the file is stored on disk at a predictable location. If any other part of the system serves these files, it becomes an attack vector.

### 6.5 MEDIUM: Stored Content Not Sanitized for XSS

Content fetched from URLs and stored in ChromaDB is never HTML-escaped or sanitized. If the search API response is rendered in a browser without escaping, stored XSS is possible. The `content_preview` field in search results (content.py:326) is returned raw.

### 6.6 LOW: File Deletion Without Checking Ownership of Path

**File**: `src/api/routers/content.py:295-296`

```python
if doc.file_path and os.path.exists(doc.file_path):
    os.remove(doc.file_path)
```

The `file_path` is stored in the database. If the database is compromised or a bug sets an arbitrary `file_path`, this could delete any file the process has write access to. The code trusts the stored path without verifying it's within `UPLOAD_DIR`.

### 6.7 LOW: No Rate Limiting on Upload Endpoints

The upload endpoints (`/upload`, `/upload-url`) do not have rate limiting. An authenticated attacker could flood the system with uploads, consuming disk space, ChromaDB storage, and processing resources.

---

## 7. Test Coverage Analysis

### 7.1 What IS Tested (`tests/test_documents.py`)

| Test Class | Count | Coverage |
|------------|-------|----------|
| `TestTextParser` | 2 | `parse()` and `parse_with_metadata()` |
| `TestSemanticChunker` | 3 | Basic chunking, metadata preservation, empty text |
| `TestContentEnricher` | 2 | Key term extraction, `enrich()` async |
| `TestQueryRewriter` | 2 | Passthrough without LLM, with context |
| `TestResultRanker` | 2 | Keyword overlap re-ranking, empty results |
| `TestDocumentModel` | 1 | Field existence check |
| `TestUploadEndpoint` | 1 | File upload via ASGI test client |
| `TestSearchEndpoint` | 2 | Search with results, empty query |
| **Total** | **15** | |

### 7.2 What is NOT Tested

**Parsers:**
- PDF parser (`PdfParser`) -- no tests at all
- DOCX parser (`DocxParser`) -- no tests at all
- Web parser (`WebParser`) -- no tests at all
- Parser error handling (corrupt files, non-UTF-8 text, empty files)

**Processor:**
- `DocumentProcessor.process_file()` end-to-end
- `DocumentProcessor.process_url()` end-to-end
- `_detect_parser()` routing logic
- `_clean_metadata()` edge cases (nested dicts, None values, list values)
- Unsupported file type handling

**Retriever:**
- `KnowledgeRetriever.initialize()` -- ChromaDB connection
- `KnowledgeRetriever.retrieve()` -- full retrieval flow
- `KnowledgeRetriever.ingest_document()` / `ingest_file()`
- `KnowledgeRetriever.delete_document_chunks()`
- `KnowledgeRetriever._format_citations()`
- Behavior when ChromaDB is down

**API Endpoints:**
- `POST /upload-url` -- no test
- `GET /documents` -- list endpoint not tested
- `GET /documents/{document_id}` -- get single document not tested
- `DELETE /documents/{document_id}` -- deletion not tested
- Upload with invalid extension
- Upload exceeding size limit
- Upload with path traversal filename
- Authentication/authorization enforcement
- Error handling paths (processing failure, DB errors)

**Enricher:**
- LLM enrichment path (only tested without LLM)
- LLM failure fallback behavior

**Ranker:**
- Score calculation accuracy
- Tie-breaking behavior
- Edge cases (all zero distances, all identical content)

### 7.3 Test Quality Observations

- **Upload test leaves files on disk** (`content.py:104` writes to `UPLOAD_DIR`): no cleanup in test
- **Module reload pattern** (`importlib.reload(src.api.main)`) in API tests is fragile and can cause import side effects in other tests
- **No integration tests** with actual ChromaDB (all mocked)
- **No parameterized tests** for edge cases (very long text, Unicode, binary content as text)

---

## 8. Additional Observations

### 8.1 Sentence Splitting Heuristic

**File**: `src/documents/chunker.py:73`

```python
sentences = text.replace(". ", ".\n").split("\n")
```

This naive sentence boundary detection breaks on:
- Abbreviations: "Dr. Smith" -> splits incorrectly
- Decimal numbers: "3.14 is pi" -> "3.14" and "is pi"
- URLs: "visit https://example.com. Then" -> breaks mid-URL
- Ellipses: "and so on... But then" -> won't split

### 8.2 Web Parser Does Not Limit Response Size

**File**: `src/documents/parsers/web.py:14-16`

```python
response = await client.get(url)
```

No `max_content_length` or streaming. A URL pointing to a multi-GB file would be fully downloaded into memory.

### 8.3 ChromaDB ID Hash Collisions

**File**: `src/rag/retriever.py:48`

```python
ids = [f"chunk_{hash(c)}_{i}" for i, c in enumerate(chunks)]
```

Python's `hash()` is not stable across processes (randomized since Python 3.3 by default with `PYTHONHASHSEED`). This means:
- The same content produces different IDs across restarts
- Duplicate detection is impossible
- Re-ingesting the same document creates duplicate chunks

### 8.4 No Transactions Across Stores

The pipeline writes to three stores (filesystem, PostgreSQL, ChromaDB) without any transactional guarantees. Failure at any stage can leave the system in an inconsistent state:
- File on disk but no DB record (crash between lines 105 and 120)
- DB record but no ChromaDB chunks (ChromaDB failure during processing)
- ChromaDB chunks but failed DB record (DB commit failure)

---

## 9. Recommendations

### P0 -- Critical (Fix Before Production)

1. **Fix tutor agent RAG integration** (`src/agents/tutor.py:183-198`): `retrieve()` returns a dict, not a list. The tutor should use `knowledge_context.get("sources", [])` or `knowledge_context.get("context", "")` to extract usable content.

2. **Add SSRF protection to URL ingest**: Implement a URL allowlist or blocklist. At minimum, block private IP ranges (`10.x`, `172.16-31.x`, `192.168.x`, `127.x`, `169.254.x`, `::1`, `fd00::/8`). Consider using a library like `ssrf-king` or manual IP resolution check before fetching.

3. **Add authentication to the search endpoint**: Add `user: User = Depends(get_current_user)` to `search_content()`.

### P1 -- High (Fix Before Beta)

4. **Run parser I/O in thread pool**: Wrap synchronous parser calls with `asyncio.to_thread()` or `loop.run_in_executor()` to avoid blocking the event loop.

5. **Validate file deletion paths**: Before `os.remove(doc.file_path)`, verify the path starts with `UPLOAD_DIR`.

6. **Add content-type / magic-byte validation**: Check that file content matches the declared extension (e.g., PDF starts with `%PDF`).

7. **Limit web response size**: Use `httpx` streaming with a max content length for URL fetching.

8. **Add logging to all silent `except` blocks**: Replace `pass` with `logger.warning(...)` in enricher, retriever, and tutor agent.

### P2 -- Medium (Fix Before GA)

9. **Guard `_force_split` against infinite loop**: Add `assert chunk_overlap < chunk_size` in `SemanticChunker.__init__()`.

10. **Use SQL `count()` instead of fetching all IDs**: In `list_documents()`, use `select(func.count(Document.id))` for the total count.

11. **Unify chunking strategy**: Either remove the LangChain `text_splitter` from `KnowledgeRetriever` or document when each path should be used. Ideally, all ingestion should go through `DocumentProcessor`.

12. **Add `updated_at` column to Document model**: For auditing and cache invalidation.

13. **Sanitize stored content for XSS**: HTML-escape content previews in search responses, or document that the frontend must escape.

14. **Add rate limiting to upload endpoints**: Use the existing Redis-based rate limiting middleware.

### P3 -- Low (Improve Over Time)

15. **Add tests for PDF, DOCX, and Web parsers**: Create fixture files and test parsing, error handling, and edge cases.

16. **Add integration tests with ChromaDB**: At least one test should verify the full ingest-retrieve round trip with an in-process ChromaDB instance.

17. **Test all API endpoints**: Cover list, get, delete, upload-url, invalid extensions, size limits.

18. **Improve sentence boundary detection**: Consider using a proper NLP sentence tokenizer (e.g., spaCy, NLTK `sent_tokenize`).

19. **Add content deduplication**: Compute a hash (SHA-256) of uploaded content to prevent duplicate ingestion.

20. **Use stable hashing for ChromaDB IDs**: Replace `hash()` with `hashlib.sha256()` for deterministic chunk IDs.

---

## 10. Summary

The F11/F02 Document Processing + RAG Enhancement feature provides a well-structured pipeline with clean separation of concerns. The architecture (parse -> chunk -> enrich -> store -> retrieve) is sound and the module boundaries are well-defined.

However, the implementation has several critical issues:

- **The tutor-RAG integration is broken** due to a type mismatch (dict treated as list)
- **SSRF vulnerability** in URL ingestion allows access to internal services
- **Unauthenticated search** exposes all indexed content to any caller
- **Synchronous I/O in async context** will cause performance issues under load
- **No transactional consistency** across the three data stores (disk, PostgreSQL, ChromaDB)
- **Test coverage is approximately 40%** -- parsers, processor, retriever, and most API endpoints are untested

The codebase is clean and readable, with consistent patterns. The security and correctness issues are fixable without architectural changes.
