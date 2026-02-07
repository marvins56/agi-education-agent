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

    # === Scratchpad & Session Enhancements (Redis) ===

    async def set_scratchpad(self, session_id: str, content: str, ttl: int = 7200) -> None:
        """Store student's working notes for the current problem."""
        if not self._redis:
            return
        key = f"session:{session_id}:scratchpad"
        await self._redis.setex(key, ttl, content)

    async def get_scratchpad(self, session_id: str) -> str | None:
        """Retrieve the student's scratchpad content."""
        if not self._redis:
            return None
        key = f"session:{session_id}:scratchpad"
        return await self._redis.get(key)

    async def set_session_mood(self, session_id: str, mood: str, ttl: int = 3600) -> None:
        """Store a mood indicator for the current session."""
        if not self._redis:
            return
        key = f"session:{session_id}:mood"
        await self._redis.setex(key, ttl, mood)

    async def get_session_mood(self, session_id: str) -> str | None:
        """Get the current session mood indicator."""
        if not self._redis:
            return None
        key = f"session:{session_id}:mood"
        return await self._redis.get(key)

    # === Student Mastery (PostgreSQL) ===

    async def get_student_mastery(
        self,
        student_id: str,
        subject: str | None = None,
    ) -> list[dict[str, Any]]:
        """Query TopicMastery records for a student."""
        if not self.db_session_factory:
            return []
        from src.models.mastery import TopicMastery
        from sqlalchemy import select
        async with self.db_session_factory() as session:
            stmt = select(TopicMastery).where(TopicMastery.student_id == student_id)
            if subject:
                stmt = stmt.where(TopicMastery.subject == subject)
            stmt = stmt.order_by(TopicMastery.subject, TopicMastery.topic)
            result = await session.execute(stmt)
            records = result.scalars().all()
            return [
                {
                    "id": str(r.id),
                    "subject": r.subject,
                    "topic": r.topic,
                    "mastery_score": r.mastery_score,
                    "confidence": r.confidence,
                    "attempts": r.attempts,
                    "last_assessed": r.last_assessed.isoformat() if r.last_assessed else None,
                    "last_reviewed": r.last_reviewed.isoformat() if r.last_reviewed else None,
                    "decay_rate": r.decay_rate,
                }
                for r in records
            ]

    async def update_mastery(
        self,
        student_id: str,
        subject: str,
        topic: str,
        new_score: float,
        confidence: float | None = None,
    ) -> None:
        """Upsert a TopicMastery record."""
        if not self.db_session_factory:
            return
        from src.models.mastery import TopicMastery
        from sqlalchemy import select
        async with self.db_session_factory() as session:
            stmt = select(TopicMastery).where(
                TopicMastery.student_id == student_id,
                TopicMastery.subject == subject,
                TopicMastery.topic == topic,
            )
            result = await session.execute(stmt)
            record = result.scalars().first()
            if record:
                record.mastery_score = new_score
                record.attempts = record.attempts + 1
                if confidence is not None:
                    record.confidence = confidence
                record.last_assessed = datetime.now(timezone.utc)
            else:
                record = TopicMastery(
                    student_id=student_id,
                    subject=subject,
                    topic=topic,
                    mastery_score=new_score,
                    confidence=confidence or 0.0,
                    attempts=1,
                    last_assessed=datetime.now(timezone.utc),
                )
                session.add(record)
            await session.commit()

    async def get_struggle_points(
        self,
        student_id: str,
        threshold: float = 30.0,
    ) -> list[dict[str, Any]]:
        """Return topics where mastery is below the given threshold."""
        if not self.db_session_factory:
            return []
        from src.models.mastery import TopicMastery
        from sqlalchemy import select
        async with self.db_session_factory() as session:
            stmt = (
                select(TopicMastery)
                .where(
                    TopicMastery.student_id == student_id,
                    TopicMastery.mastery_score < threshold,
                )
                .order_by(TopicMastery.mastery_score.asc())
            )
            result = await session.execute(stmt)
            records = result.scalars().all()
            return [
                {
                    "subject": r.subject,
                    "topic": r.topic,
                    "mastery_score": r.mastery_score,
                    "attempts": r.attempts,
                }
                for r in records
            ]

    async def track_confusion(self, session_id: str, topic: str) -> int:
        """Increment a confusion counter in Redis for a session+topic.

        Returns the new count.
        """
        if not self._redis:
            return 0
        key = f"session:{session_id}:confusion:{topic}"
        count = await self._redis.incr(key)
        await self._redis.expire(key, 7200)  # 2 hour TTL
        return count

    async def close(self):
        if self._redis:
            await self._redis.close()
