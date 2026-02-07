import pathlib

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import Any


class KnowledgeRetriever:
    """RAG-based knowledge retrieval using ChromaDB."""

    def __init__(self, chroma_host: str = "localhost", chroma_port: int = 8100, collection_name: str = "educational_content"):
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

    async def initialize(self):
        self._client = chromadb.HttpClient(host=self.chroma_host, port=self.chroma_port)
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def ingest_document(self, text: str, metadata: dict[str, Any] | None = None) -> int:
        """Split text into chunks and add to collection. Returns number of chunks."""
        chunks = self.text_splitter.split_text(text)
        if not chunks:
            return 0

        ids = [f"chunk_{hash(c)}_{i}" for i, c in enumerate(chunks)]
        metadatas = [metadata or {} for _ in chunks]

        self._collection.add(
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
    ) -> dict[str, Any]:
        """Retrieve relevant knowledge for a query."""
        if not self._collection:
            return {"context": "", "sources": [], "num_results": 0}

        where_filter = {}
        if subject:
            where_filter["subject"] = subject
        if filters:
            where_filter.update(filters)

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=k,
                where=where_filter if where_filter else None,
            )
        except Exception:
            # Collection may be empty or filter invalid
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

        return {
            "context": "\n\n---\n\n".join(documents),
            "sources": sources,
            "num_results": len(documents),
        }

    def close(self):
        self._client = None
        self._collection = None
