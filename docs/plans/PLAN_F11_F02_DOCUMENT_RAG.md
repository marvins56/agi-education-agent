# F11 + F02: Document Processing Pipeline + RAG Enhancement

## Overview
Build a document processing pipeline (F11) that handles PDF, DOCX, TXT/MD, and web URL ingestion,
with semantic chunking, metadata enrichment, and ChromaDB storage. Enhance the existing RAG retriever (F02)
with query rewriting and result re-ranking.

## Architecture

```
Upload/URL -> Parser -> Chunker -> Enricher -> ChromaDB
                                                  ^
Query -> QueryRewriter -> Retriever -> ResultRanker -> Response with Citations
```

## New Files

### Document Processing (src/documents/)
- `parsers/pdf.py` - PdfParser: PyMuPDF-based PDF text extraction
- `parsers/docx.py` - DocxParser: python-docx-based DOCX extraction
- `parsers/text.py` - TextParser: plain text/markdown reading
- `parsers/web.py` - WebParser: httpx + BeautifulSoup URL fetching
- `chunker.py` - SemanticChunker: section-aware overlapping text splitting
- `enricher.py` - ContentEnricher: keyword extraction + optional LLM enrichment
- `processor.py` - DocumentProcessor: orchestrates parse -> chunk -> enrich -> store

### RAG Enhancement (src/rag/)
- `rewriter.py` - QueryRewriter: query expansion (LLM optional)
- `ranker.py` - ResultRanker: hybrid semantic + keyword re-ranking
- Enhanced `retriever.py` - integrated rewriting + re-ranking + citations

### Data Model
- `src/models/document.py` - Document SQLAlchemy model
- `migrations/versions/003_document_tables.py` - DB migration (depends on 002)

### API (src/api/routers/content.py)
- POST /upload - file upload with processing
- POST /upload-url - URL ingestion
- GET /documents - list with pagination
- GET /documents/{id} - document details
- DELETE /documents/{id} - delete + cleanup ChromaDB
- GET /search - enhanced search with citations

## Constraints
- Max file size: 50MB
- Supported types: .pdf, .docx, .txt, .md
- Filenames sanitized against path traversal
- All async, Pydantic v2, SQLAlchemy 2.0
- Backward-compatible retriever enhancement
