"""Memory consolidation — promote short-term (Redis) to long-term (PostgreSQL)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from src.memory.manager import MemoryManager


class MemoryConsolidator:
    """Consolidate session data from Redis into PostgreSQL summaries."""

    def __init__(
        self,
        memory_manager: MemoryManager,
        db_session_factory: async_sessionmaker | None = None,
    ):
        self.memory = memory_manager
        self.db_session_factory = db_session_factory

    async def consolidate_session(self, session_id: str) -> dict[str, Any]:
        """Read conversation from Redis, generate summary, store in PostgreSQL.

        Returns the summary dict.
        """
        history = await self.memory.get_conversation_history(session_id, limit=50)
        context = await self.memory.get_session_context(session_id)

        topics_discussed: list[str] = []
        questions_asked: int = 0
        mastery_indicators: list[str] = []

        for msg in history:
            content = msg.get("content", "")
            if msg.get("role") == "user":
                questions_asked += 1
                # Simple heuristic: extract topic mentions from questions
                if "?" in content:
                    mastery_indicators.append("question_asked")
            else:
                mastery_indicators.append("response_received")

        subject = context.get("current_subject") if context else None
        topic = context.get("current_topic") if context else None
        if topic:
            topics_discussed.append(topic)

        summary = {
            "session_id": session_id,
            "subject": subject,
            "topics_discussed": topics_discussed,
            "questions_asked": questions_asked,
            "message_count": len(history),
            "mastery_indicators": mastery_indicators,
            "consolidated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Persist to PostgreSQL as a learning event
        if self.memory.db_session_factory:
            student_id = context.get("student_id") if context else None
            if student_id:
                await self.memory.save_learning_event(
                    student_id=student_id,
                    event_type="session_summary",
                    subject=subject,
                    topic=topic,
                    data=summary,
                    outcome="consolidated",
                )

        return summary

    async def archive_expired_sessions(self, max_age_hours: int = 24) -> int:
        """Find Redis sessions older than max_age, consolidate each, delete from Redis.

        Returns the number of sessions archived.
        """
        # Scan for session context keys
        redis = self.memory._redis
        if not redis:
            return 0

        archived = 0
        cursor = 0
        now = datetime.now(timezone.utc)

        while True:
            cursor, keys = await redis.scan(cursor, match="session:*:context", count=100)
            for key in keys:
                raw = await redis.get(key)
                if not raw:
                    continue
                try:
                    ctx = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    continue

                # Check session age via the stored timestamp or TTL
                created = ctx.get("created_at")
                if created:
                    created_dt = datetime.fromisoformat(created)
                    age_hours = (now - created_dt).total_seconds() / 3600
                    if age_hours < max_age_hours:
                        continue

                # Extract session_id from key pattern "session:{id}:context"
                parts = key.split(":")
                if len(parts) >= 2:
                    session_id = parts[1]
                    await self.consolidate_session(session_id)
                    # Clean up Redis keys for this session
                    await redis.delete(key)
                    await redis.delete(f"session:{session_id}:messages")
                    archived += 1

            if cursor == 0:
                break

        return archived
