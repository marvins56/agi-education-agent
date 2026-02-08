from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from src.config import settings


class AgentConfig(BaseModel):
    """Configuration for agent initialization."""

    name: str
    model: str = settings.DEFAULT_MODEL
    temperature: float = 0.7
    max_tokens: int = 4096
    tools: list[str] = []
    memory_enabled: bool = True


class AgentContext(BaseModel):
    """Shared context passed between agents."""

    session_id: str
    student_id: str
    student_profile: dict[str, Any] = {}
    conversation_history: list[dict[str, str]] = []
    current_subject: str | None = None
    current_topic: str | None = None
    learning_objectives: list[str] = []


class AgentResponse(BaseModel):
    """Standardized agent response."""

    text: str
    metadata: dict[str, Any] = {}
    suggested_actions: list[str] = []
    agent_name: str = ""
    processing_time: float = 0.0


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.llm = self._initialize_llm()

    @abstractmethod
    async def process(self, input_text: str, context: AgentContext) -> AgentResponse:
        """Process input and return response."""
        pass

    @abstractmethod
    def get_system_prompt(self, context: AgentContext) -> str:
        """Generate system prompt based on context."""
        pass

    def _initialize_llm(self):
        """Initialize the LLM with configuration."""
        from src.llm.factory import LLMFactory

        return LLMFactory.create(
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
