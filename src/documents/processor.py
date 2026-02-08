"""Document processing pipeline: parse -> chunk -> enrich -> store."""

import logging
import os
import uuid
from typing import Any

from src.documents.chunker import SemanticChunker
from src.documents.enricher import ContentEnricher
from src.documents.parsers.docx import DocxParser
from src.documents.parsers.epub import EpubParser
from src.documents.parsers.html_parser import HtmlFileParser
from src.documents.parsers.pdf import PdfParser
from src.documents.parsers.pptx import PptxParser
from src.documents.parsers.text import TextParser
from src.documents.parsers.web import WebParser
from src.documents.parsers.xlsx import SpreadsheetParser
from src.documents.loaders.json_loader import JSONFileLoader
from src.rag.retriever import KnowledgeRetriever

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Orchestrate the full document processing pipeline."""

    SUPPORTED_EXTENSIONS = {
        ".pdf", ".docx", ".txt", ".md",
        ".pptx", ".xlsx", ".xls", ".csv",
        ".epub", ".html", ".htm", ".json",
    }

    def __init__(
        self,
        chunker: SemanticChunker | None = None,
        enricher: ContentEnricher | None = None,
        retriever: KnowledgeRetriever | None = None,
    ):
        self.chunker = chunker or SemanticChunker()
        self.enricher = enricher or ContentEnricher()
        self.retriever = retriever
        self._pdf_parser = PdfParser()
        self._docx_parser = DocxParser()
        self._text_parser = TextParser()
        self._web_parser = WebParser()
        self._pptx_parser = PptxParser()
        self._spreadsheet_parser = SpreadsheetParser()
        self._epub_parser = EpubParser()
        self._html_parser = HtmlFileParser()
        self._json_parser = JSONFileLoader()

    async def process_file(self, file_path: str, metadata: dict[str, Any] | None = None) -> dict:
        """Parse, chunk, enrich, and store a file. Returns processing result."""
        parser = self._detect_parser(file_path)
        result = parser.parse_with_metadata(file_path)

        text = result["text"]
        file_meta = metadata.copy() if metadata else {}
        file_meta.update(result.get("metadata", {}))
        file_meta["source"] = file_path
        file_meta["file_type"] = os.path.splitext(file_path)[1].lower()

        return await self._process_text(text, file_meta)

    async def process_url(self, url: str, metadata: dict[str, Any] | None = None) -> dict:
        """Fetch, parse, chunk, enrich, and store a URL. Returns processing result."""
        text = await self._web_parser.parse_url(url)

        url_meta = metadata.copy() if metadata else {}
        url_meta["source"] = url
        url_meta["file_type"] = "url"

        return await self._process_text(text, url_meta)

    async def _process_text(self, text: str, metadata: dict[str, Any]) -> dict:
        """Chunk, enrich, and store text content."""
        document_id = str(uuid.uuid4())
        metadata["document_id"] = document_id

        # Enrich
        enriched_meta = await self.enricher.enrich(text, metadata)

        # Chunk
        chunks = self.chunker.chunk(text, enriched_meta)

        # Store in ChromaDB
        if self.retriever and self.retriever._collection is not None:
            ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
            documents = [c["content"] for c in chunks]
            metadatas = [c["metadata"] for c in chunks]
            # Ensure metadata values are ChromaDB-compatible (str, int, float, bool)
            clean_metadatas = [self._clean_metadata(m) for m in metadatas]

            self.retriever._collection.add(
                documents=documents,
                metadatas=clean_metadatas,
                ids=ids,
            )

        return {
            "document_id": document_id,
            "chunk_count": len(chunks),
            "metadata": enriched_meta,
        }

    def _detect_parser(self, file_path: str):
        """Route to the appropriate parser based on file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return self._pdf_parser
        elif ext == ".docx":
            return self._docx_parser
        elif ext in (".txt", ".md"):
            return self._text_parser
        elif ext == ".pptx":
            return self._pptx_parser
        elif ext in (".xlsx", ".xls", ".csv"):
            return self._spreadsheet_parser
        elif ext == ".epub":
            return self._epub_parser
        elif ext in (".html", ".htm"):
            return self._html_parser
        elif ext == ".json":
            return self._json_parser
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    @staticmethod
    def _clean_metadata(meta: dict) -> dict:
        """Ensure metadata values are ChromaDB-compatible types."""
        clean = {}
        for k, v in meta.items():
            if isinstance(v, (str, int, float, bool)):
                clean[k] = v
            elif isinstance(v, list):
                clean[k] = ", ".join(str(item) for item in v)
            elif v is not None:
                clean[k] = str(v)
        return clean
