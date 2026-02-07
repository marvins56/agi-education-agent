from __future__ import annotations

from typing import TYPE_CHECKING

from src.agents.base import AgentContext, AgentResponse
from src.agents.tutor import TutorAgent

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
        self.agents: dict[str, TutorAgent] = {}

    async def initialize(self) -> None:
        """Create and register all agents."""
        self.agents["tutor"] = TutorAgent(
            retriever=self.retriever,
            memory=self.memory_manager,
        )

    async def process(self, message: str, context: AgentContext) -> AgentResponse:
        """Route a message to the appropriate agent and return its response."""
        # For now, all messages go to the tutor agent.
        agent = self.agents["tutor"]
        return await agent.process(message, context)

    async def close(self) -> None:
        """Cleanup resources."""
        pass
