import logging
import pathlib

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import Any

from src.rag.ranker import ResultRanker
from src.rag.rewriter import QueryRewriter

logger = logging.getLogger(__name__)


class KnowledgeRetriever:
    """RAG-based knowledge retrieval using ChromaDB."""

    def __init__(
        self,
        chroma_host: str = "localhost",
        chroma_port: int = 8100,
        collection_name: str = "educational_content",
        query_rewriter: QueryRewriter | None = None,
        result_ranker: ResultRanker | None = None,
    ):
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.collection_name = collection_name
        self._client: chromadb.HttpClient | None = None
        self._collection = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self._rewriter = query_rewriter or QueryRewriter()
        self._ranker = result_ranker or ResultRanker()

    async def initialize(self):
        self._client = chromadb.HttpClient(host=self.chroma_host, port=self.chroma_port)
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def _get_collection(self):
        """Get collection, re-creating if the reference is stale."""
        if self._collection is None and self._client is not None:
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        try:
            self._collection.count()
        except Exception:
            if self._client is not None:
                logger.info("Re-creating ChromaDB collection reference (stale)")
                self._collection = self._client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
        return self._collection

    def ingest_document(self, text: str, metadata: dict[str, Any] | None = None) -> int:
        """Split text into chunks and add to collection. Returns number of chunks."""
        chunks = self.text_splitter.split_text(text)
        if not chunks:
            return 0

        ids = [f"chunk_{hash(c)}_{i}" for i, c in enumerate(chunks)]
        metadatas = [metadata or {} for _ in chunks]

        collection = self._get_collection()
        collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids,
        )
        return len(chunks)

    def ingest_file(self, file_path: str, metadata: dict[str, Any] | None = None) -> int:
        """Read a file and ingest its contents. Returns number of chunks."""
        text = pathlib.Path(file_path).read_text(encoding="utf-8")
        file_metadata = {"source": file_path}
        if metadata:
            file_metadata.update(metadata)
        return self.ingest_document(text, metadata=file_metadata)

    async def retrieve(
        self,
        query: str,
        subject: str | None = None,
        filters: dict[str, Any] | None = None,
        k: int = 5,
        rewrite: bool = True,
    ) -> dict[str, Any]:
        """Retrieve relevant knowledge for a query with optional rewriting and re-ranking."""
        collection = self._get_collection()
        if collection is None:
            return {"context": "", "sources": [], "num_results": 0}

        # Query rewriting
        search_query = query
        if rewrite:
            context = {}
            if subject:
                context["subject"] = subject
            search_query = await self._rewriter.rewrite(query, context)

        where_filter = {}
        if subject:
            where_filter["subject"] = subject
        if filters:
            where_filter.update(filters)

        try:
            results = collection.query(
                query_texts=[search_query],
                n_results=k,
                where=where_filter if where_filter else None,
            )
        except Exception:
            logger.warning("ChromaDB query failed for query: %s", search_query[:100], exc_info=True)
            return {"context": "", "sources": [], "num_results": 0}

        if not results or not results.get("documents") or not results["documents"][0]:
            return {"context": "", "sources": [], "num_results": 0}

        documents = results["documents"][0]
        metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(documents)
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(documents)

        sources = [
            {
                "content_preview": doc[:200] + "..." if len(doc) > 200 else doc,
                "metadata": meta,
                "distance": dist,
            }
            for doc, meta, dist in zip(documents, metadatas, distances)
        ]

        # Re-rank results
        sources = self._ranker.rank(sources, query)

        # Format source citations
        citations = self._format_citations(sources)

        return {
            "context": "\n\n---\n\n".join(documents),
            "sources": sources,
            "citations": citations,
            "num_results": len(documents),
        }

    @staticmethod
    def _format_citations(sources: list[dict]) -> list[dict]:
        """Format sources into structured citations."""
        citations = []
        for i, src in enumerate(sources, 1):
            meta = src.get("metadata", {})
            citations.append({
                "index": i,
                "preview": src.get("content_preview", ""),
                "source": meta.get("source", "unknown"),
                "document_id": meta.get("document_id", ""),
                "relevance_score": src.get("_rank_score", 1.0 - src.get("distance", 0.0)),
            })
        return citations

    def delete_document_chunks(self, document_id: str) -> None:
        """Delete all chunks for a given document_id from the collection."""
        collection = self._get_collection()
        if collection is None:
            return
        try:
            collection.delete(where={"document_id": document_id})
        except Exception:
            logger.warning("Failed to delete chunks for document %s from ChromaDB", document_id, exc_info=True)

    def close(self):
        self._client = None
        self._collection = None
