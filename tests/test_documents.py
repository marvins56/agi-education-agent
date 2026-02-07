"""Tests for document processing pipeline and RAG enhancement."""

import os
import tempfile
import uuid
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.documents.chunker import SemanticChunker
from src.documents.enricher import ContentEnricher
from src.documents.parsers.text import TextParser
from src.documents.processor import DocumentProcessor
from src.models.document import Document
from src.rag.ranker import ResultRanker
from src.rag.rewriter import QueryRewriter


# --- Parser tests ---


class TestTextParser:
    def test_parse_reads_file(self, tmp_path):
        """TextParser.parse should read and return file contents."""
        f = tmp_path / "sample.txt"
        f.write_text("Hello, this is a test document.\nSecond line.", encoding="utf-8")
        parser = TextParser()
        result = parser.parse(str(f))
        assert "Hello, this is a test document." in result
        assert "Second line." in result

    def test_parse_with_metadata(self, tmp_path):
        """TextParser.parse_with_metadata should return text, pages, and metadata."""
        f = tmp_path / "sample.md"
        f.write_text("# Title\nSome content here.", encoding="utf-8")
        parser = TextParser()
        result = parser.parse_with_metadata(str(f))
        assert "text" in result
        assert result["pages"] == 1
        assert result["metadata"]["extension"] == ".md"
        assert result["metadata"]["filename"] == "sample.md"


# --- Chunker tests ---


class TestSemanticChunker:
    def test_chunker_basic(self):
        """Chunker should produce multiple chunks for long text."""
        text = "This is a paragraph about science.\n\n" * 50
        chunker = SemanticChunker(chunk_size=200, chunk_overlap=50)
        chunks = chunker.chunk(text)
        assert len(chunks) > 1
        # Each chunk should have content and metadata
        for c in chunks:
            assert "content" in c
            assert "metadata" in c
            assert "chunk_index" in c["metadata"]
            assert "total_chunks" in c["metadata"]

    def test_chunker_metadata_preservation(self):
        """Chunker should preserve provided metadata in each chunk."""
        text = "Alpha bravo charlie.\n\n" * 30
        meta = {"subject": "military", "source": "test"}
        chunker = SemanticChunker(chunk_size=100, chunk_overlap=20)
        chunks = chunker.chunk(text, metadata=meta)
        assert len(chunks) > 0
        for c in chunks:
            assert c["metadata"]["subject"] == "military"
            assert c["metadata"]["source"] == "test"

    def test_chunker_empty_text(self):
        """Chunker should return empty list for empty text."""
        chunker = SemanticChunker()
        assert chunker.chunk("") == []
        assert chunker.chunk("   ") == []


# --- Enricher tests ---


class TestContentEnricher:
    @pytest.mark.asyncio
    async def test_enricher_key_terms(self):
        """Enricher should extract meaningful key terms from text."""
        text = (
            "Photosynthesis is the process by which plants convert sunlight into energy. "
            "Photosynthesis occurs in chloroplasts. Chloroplasts contain chlorophyll. "
            "The process of photosynthesis is essential for plant growth and oxygen production."
        )
        enricher = ContentEnricher()
        result = await enricher.enrich(text)
        assert "key_terms" in result
        assert "summary" in result
        terms = result["key_terms"]
        assert len(terms) > 0
        # "photosynthesis" should be a top term due to frequency
        assert "photosynthesis" in terms

    def test_extract_key_terms(self):
        """extract_key_terms should return top-frequency words excluding stop words."""
        enricher = ContentEnricher()
        text = "math math math science science history"
        terms = enricher.extract_key_terms(text, top_n=3)
        assert terms[0] == "math"
        assert "science" in terms
        assert "history" in terms


# --- Query Rewriter tests ---


class TestQueryRewriter:
    @pytest.mark.asyncio
    async def test_passthrough_without_llm(self):
        """QueryRewriter without LLM should return query unchanged."""
        rewriter = QueryRewriter(llm=None)
        result = await rewriter.rewrite("What is photosynthesis?")
        assert result == "What is photosynthesis?"

    @pytest.mark.asyncio
    async def test_passthrough_with_context(self):
        """QueryRewriter without LLM should still return query unchanged even with context."""
        rewriter = QueryRewriter(llm=None)
        result = await rewriter.rewrite("explain gravity", context={"subject": "physics"})
        assert result == "explain gravity"


# --- Result Ranker tests ---


class TestResultRanker:
    def test_rank_reorders_by_keyword_overlap(self):
        """ResultRanker should boost results with higher keyword overlap."""
        ranker = ResultRanker()
        results = [
            {"content_preview": "Unrelated topic about cooking recipes", "distance": 0.3},
            {"content_preview": "Photosynthesis is the process of converting light energy", "distance": 0.4},
        ]
        ranked = ranker.rank(results, "photosynthesis light energy")
        # The second result has more keyword overlap, should rank higher despite worse distance
        assert "photosynthesis" in ranked[0]["content_preview"].lower()

    def test_rank_empty_results(self):
        """ResultRanker should handle empty results gracefully."""
        ranker = ResultRanker()
        assert ranker.rank([], "test query") == []


# --- Document Model test ---


class TestDocumentModel:
    def test_document_model_fields(self):
        """Document model should have all expected columns."""
        assert hasattr(Document, "id")
        assert hasattr(Document, "title")
        assert hasattr(Document, "subject")
        assert hasattr(Document, "grade_level")
        assert hasattr(Document, "file_path")
        assert hasattr(Document, "original_filename")
        assert hasattr(Document, "file_type")
        assert hasattr(Document, "file_size")
        assert hasattr(Document, "chunk_count")
        assert hasattr(Document, "status")
        assert hasattr(Document, "metadata_")
        assert hasattr(Document, "uploaded_by")
        assert hasattr(Document, "created_at")
        assert hasattr(Document, "processed_at")
        assert Document.__tablename__ == "documents"


# --- API Endpoint tests ---


class TestUploadEndpoint:
    @pytest.mark.asyncio
    async def test_upload_endpoint(self):
        """POST /upload should accept a file and return document info."""
        from contextlib import asynccontextmanager
        from httpx import ASGITransport, AsyncClient

        with patch("src.api.main.lifespan") as mock_lifespan:
            @asynccontextmanager
            async def noop_lifespan(app):
                app.state.memory_manager = MagicMock()
                app.state.orchestrator = MagicMock()
                app.state.retriever = MagicMock()
                app.state.retriever._collection = None
                yield

            mock_lifespan.side_effect = noop_lifespan

            import importlib
            import src.api.main
            importlib.reload(src.api.main)
            app = src.api.main.app

        from src.api.dependencies import get_current_user, get_db, get_retriever

        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.email = "test@example.com"
        mock_user.name = "Test User"
        mock_user.role = "teacher"

        async def override_get_current_user():
            return mock_user

        mock_retriever = MagicMock()
        mock_retriever._collection = None

        async def override_get_db():
            mock_session = AsyncMock()
            mock_session.add = MagicMock()
            mock_session.flush = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session.rollback = AsyncMock()
            yield mock_session

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_retriever] = lambda: mock_retriever

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Create a simple text file
            file_content = b"This is a test document for upload."
            response = await client.post(
                "/api/v1/content/upload",
                files={"file": ("test.txt", BytesIO(file_content), "text/plain")},
            )
            assert response.status_code == 200
            data = response.json()
            assert "document_id" in data
            assert data["status"] in ("completed", "failed", "processing")
            assert data["filename"] == "test.txt"

        app.dependency_overrides.clear()


class TestSearchEndpoint:
    @pytest.mark.asyncio
    async def test_search_endpoint(self):
        """GET /search should return results from the retriever."""
        from contextlib import asynccontextmanager
        from httpx import ASGITransport, AsyncClient

        with patch("src.api.main.lifespan") as mock_lifespan:
            @asynccontextmanager
            async def noop_lifespan(app):
                app.state.memory_manager = MagicMock()
                app.state.orchestrator = MagicMock()
                app.state.retriever = MagicMock()
                yield

            mock_lifespan.side_effect = noop_lifespan

            import importlib
            import src.api.main
            importlib.reload(src.api.main)
            app = src.api.main.app

        from src.api.dependencies import get_current_user, get_retriever

        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.role = "student"

        async def override_get_current_user():
            return mock_user

        mock_retriever = AsyncMock()
        mock_retriever.retrieve = AsyncMock(return_value={
            "context": "Photosynthesis is a process...",
            "sources": [
                {
                    "content_preview": "Photosynthesis is a process...",
                    "metadata": {"subject": "biology"},
                    "distance": 0.1,
                },
            ],
            "citations": [
                {
                    "index": 1,
                    "preview": "Photosynthesis is a process...",
                    "source": "textbook.pdf",
                    "document_id": "doc-123",
                    "relevance_score": 0.9,
                },
            ],
            "num_results": 1,
        })

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_retriever] = lambda: mock_retriever

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/content/search", params={"q": "photosynthesis"})
            assert response.status_code == 200
            data = response.json()
            assert data["query"] == "photosynthesis"
            assert data["total"] == 1
            assert len(data["results"]) == 1
            assert "Photosynthesis" in data["results"][0]["content_preview"]

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_search_empty_query(self):
        """GET /search with empty query should return empty results."""
        from contextlib import asynccontextmanager
        from httpx import ASGITransport, AsyncClient

        with patch("src.api.main.lifespan") as mock_lifespan:
            @asynccontextmanager
            async def noop_lifespan(app):
                app.state.memory_manager = MagicMock()
                app.state.orchestrator = MagicMock()
                app.state.retriever = MagicMock()
                yield

            mock_lifespan.side_effect = noop_lifespan

            import importlib
            import src.api.main
            importlib.reload(src.api.main)
            app = src.api.main.app

        from src.api.dependencies import get_current_user, get_retriever

        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.role = "student"

        async def override_get_current_user():
            return mock_user

        mock_retriever = MagicMock()
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_retriever] = lambda: mock_retriever

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/content/search", params={"q": ""})
            assert response.status_code == 200
            data = response.json()
            assert data["results"] == []
            assert data["total"] == 0

        app.dependency_overrides.clear()
