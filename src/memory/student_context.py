"""StudentContextBuilder — assemble enriched context from all 3 memory tiers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from src.memory.manager import MemoryManager


class StudentContextBuilder:
    """Build a rich student context by merging data from Redis, PostgreSQL, and ChromaDB."""

    def __init__(
        self,
        memory_manager: MemoryManager,
        db_session_factory: async_sessionmaker | None = None,
    ):
        self.memory = memory_manager
        self.db_session_factory = db_session_factory

    async def build_context(self, student_id: str, session_id: str) -> dict[str, Any]:
        """Assemble full context from all 3 tiers.

        - Tier 1 (Redis): current session state, recent conversation
        - Tier 2 (PostgreSQL): last 5 session summaries, mastery scores, struggle points
        - Tier 3 (ChromaDB): student-specific knowledge gaps (optional)
        """
        context: dict[str, Any] = {
            "student_id": student_id,
            "session_id": session_id,
        }

        # --- Tier 1: Working Memory (Redis) ---
        session_context = await self.memory.get_session_context(session_id)
        if session_context:
            context["session_state"] = session_context

        conversation = await self.memory.get_conversation_history(session_id, limit=20)
        context["recent_conversation"] = conversation

        # --- Tier 2: Episodic Memory (PostgreSQL) ---
        # Recent session summaries
        summaries = await self.memory.get_student_history(
            student_id=student_id,
            limit=5,
        )
        context["session_summaries"] = [
            s for s in summaries if s.get("event_type") == "session_summary"
        ]

        # Mastery scores
        mastery = await self.memory.get_student_mastery(student_id)
        context["mastery_scores"] = mastery

        # Struggle points
        struggles = await self.memory.get_struggle_points(student_id)
        context["struggle_points"] = struggles

        # --- Tier 3: Semantic Memory (ChromaDB, optional) ---
        try:
            gaps = await self.memory.search_knowledge(
                query=f"knowledge gaps for student {student_id}",
                collection_name="student_gaps",
                n_results=3,
                filters={"student_id": student_id} if student_id else None,
            )
            context["knowledge_gaps"] = gaps
        except Exception:
            context["knowledge_gaps"] = []

        return context
