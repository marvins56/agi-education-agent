import json
from datetime import datetime, timezone
from typing import Any

import chromadb
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class MemoryManager:
    """
    Unified memory management:
    - Working Memory (Redis): session context, conversation history
    - Episodic Memory (PostgreSQL via SQLAlchemy): learning events
    - Semantic Memory (ChromaDB): knowledge search
    """

    def __init__(
        self,
        redis_url: str,
        db_session_factory: async_sessionmaker | None = None,
        chroma_host: str = "localhost",
        chroma_port: int = 8100,
    ):
        self.redis_url = redis_url
        self.db_session_factory = db_session_factory
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self._redis: aioredis.Redis | None = None
        self._chroma: chromadb.HttpClient | None = None

    async def initialize(self):
        self._redis = aioredis.from_url(self.redis_url, decode_responses=True)
        self._chroma = chromadb.HttpClient(host=self.chroma_host, port=self.chroma_port)

    # === Working Memory (Redis) ===

    async def set_session_context(self, session_id: str, context: dict[str, Any], ttl: int = 3600):
        key = f"session:{session_id}:context"
        await self._redis.setex(key, ttl, json.dumps(context, default=str))

    async def get_session_context(self, session_id: str) -> dict[str, Any] | None:
        key = f"session:{session_id}:context"
        data = await self._redis.get(key)
        return json.loads(data) if data else None

    async def add_to_conversation(self, session_id: str, role: str, content: str):
        key = f"session:{session_id}:messages"
        message = json.dumps({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        await self._redis.rpush(key, message)
        await self._redis.ltrim(key, -50, -1)

    async def get_conversation_history(self, session_id: str, limit: int = 20) -> list[dict[str, str]]:
        key = f"session:{session_id}:messages"
        messages = await self._redis.lrange(key, -limit, -1)
        return [json.loads(m) for m in messages]

    # === Episodic Memory (PostgreSQL) ===

    async def save_learning_event(
        self,
        student_id: str,
        event_type: str,
        subject: str | None = None,
        topic: str | None = None,
        data: dict[str, Any] | None = None,
        outcome: str | None = None,
    ):
        if not self.db_session_factory:
            return None
        from src.models.learning_event import LearningEvent
        async with self.db_session_factory() as session:
            event = LearningEvent(
                student_id=student_id,
                event_type=event_type,
                subject=subject,
                topic=topic,
                data=data or {},
                outcome=outcome,
            )
            session.add(event)
            await session.commit()
            await session.refresh(event)
            return str(event.id)

    async def get_student_history(
        self,
        student_id: str,
        subject: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if not self.db_session_factory:
            return []
        from src.models.learning_event import LearningEvent
        from sqlalchemy import select
        async with self.db_session_factory() as session:
            stmt = select(LearningEvent).where(LearningEvent.student_id == student_id)
            if subject:
                stmt = stmt.where(LearningEvent.subject == subject)
            stmt = stmt.order_by(LearningEvent.created_at.desc()).limit(limit)
            result = await session.execute(stmt)
            events = result.scalars().all()
            return [
                {
                    "id": str(e.id),
                    "event_type": e.event_type,
                    "subject": e.subject,
                    "topic": e.topic,
                    "data": e.data,
                    "outcome": e.outcome,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in events
            ]

    # === Semantic Memory (ChromaDB) ===

    async def store_knowledge(
        self,
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        collection_name: str = "knowledge_base",
    ):
        """Store documents in ChromaDB for semantic search."""
        if not self._chroma:
            return
        collection = self._chroma.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        ids = [f"doc_{hash(d)}_{i}" for i, d in enumerate(documents)]
        collection.add(
            documents=documents,
            metadatas=metadatas or [{} for _ in documents],
            ids=ids,
        )

    async def search_knowledge(
        self,
        query: str,
        collection_name: str = "knowledge_base",
        n_results: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search ChromaDB for relevant knowledge."""
        if not self._chroma:
            return []
        try:
            collection = self._chroma.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filters if filters else None,
            )
        except Exception:
            return []

        if not results or not results.get("documents") or not results["documents"][0]:
            return []

        documents = results["documents"][0]
        metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(documents)
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(documents)

        return [
            {"document": doc, "metadata": meta, "distance": dist}
            for doc, meta, dist in zip(documents, metadatas, distances)
        ]

    async def close(self):
        if self._redis:
            await self._redis.close()
