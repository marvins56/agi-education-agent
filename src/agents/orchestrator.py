from __future__ import annotations

from typing import TYPE_CHECKING

from src.agents.base import AgentContext, AgentResponse
from src.agents.tutor import TutorAgent
from src.memory.student_context import StudentContextBuilder

if TYPE_CHECKING:
    from src.memory.manager import MemoryManager
    from src.rag.retriever import KnowledgeRetriever


class MasterOrchestrator:
    """Routes messages to the appropriate specialist agent."""

    def __init__(
        self,
        memory_manager: MemoryManager | None = None,
        retriever: KnowledgeRetriever | None = None,
    ):
        self.memory_manager = memory_manager
        self.retriever = retriever
        self.context_builder: StudentContextBuilder | None = None
        self.agents: dict[str, TutorAgent] = {}

    async def initialize(self) -> None:
        """Create and register all agents."""
        # Build a context builder if we have a memory manager
        if self.memory_manager:
            self.context_builder = StudentContextBuilder(
                memory_manager=self.memory_manager,
                db_session_factory=self.memory_manager.db_session_factory,
            )

        self.agents["tutor"] = TutorAgent(
            retriever=self.retriever,
            memory=self.memory_manager,
            context_builder=self.context_builder,
        )

    async def process(self, message: str, context: AgentContext) -> AgentResponse:
        """Route a message to the appropriate agent and return its response.

        Enriches the context with mastery/struggle data before routing.
        """
        # Enrich student profile with mastery data if available
        if self.memory_manager and context.student_id:
            try:
                struggles = await self.memory_manager.get_struggle_points(context.student_id)
                if struggles:
                    context.student_profile["struggle_points"] = [
                        s["topic"] for s in struggles[:5]
                    ]
            except Exception:
                pass

        # For now, all messages go to the tutor agent.
        agent = self.agents["tutor"]
        return await agent.process(message, context)

    async def close(self) -> None:
        """Cleanup resources."""
        pass
