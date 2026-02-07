"""Tests for the agent framework."""

import pytest
from unittest.mock import AsyncMock, patch

from src.agents.base import AgentConfig, AgentContext, AgentResponse, BaseAgent


class ConcreteTestAgent(BaseAgent):
    """Concrete agent for testing the abstract base class."""

    def get_system_prompt(self, context: AgentContext) -> str:
        return f"You are a test agent for {context.student_id}."

    async def process(self, input_text: str, context: AgentContext) -> AgentResponse:
        return AgentResponse(
            text=f"Echo: {input_text}",
            agent_name=self.config.name,
        )


class TestAgentConfig:
    def test_defaults(self):
        config = AgentConfig(name="test")
        assert config.name == "test"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.tools == []
        assert config.memory_enabled is True

    def test_custom_values(self):
        config = AgentConfig(
            name="custom",
            temperature=0.3,
            max_tokens=2048,
            tools=["search"],
            memory_enabled=False,
        )
        assert config.name == "custom"
        assert config.temperature == 0.3
        assert config.max_tokens == 2048
        assert config.tools == ["search"]
        assert config.memory_enabled is False


class TestAgentContext:
    def test_minimal_context(self):
        ctx = AgentContext(
            session_id="sess-1",
            student_id="student-1",
        )
        assert ctx.session_id == "sess-1"
        assert ctx.student_id == "student-1"
        assert ctx.student_profile == {}
        assert ctx.conversation_history == []
        assert ctx.current_subject is None
        assert ctx.current_topic is None
        assert ctx.learning_objectives == []

    def test_full_context(self):
        ctx = AgentContext(
            session_id="sess-1",
            student_id="student-1",
            student_profile={"name": "Alice", "learning_style": "visual"},
            conversation_history=[{"role": "user", "content": "hi"}],
            current_subject="Math",
            current_topic="Algebra",
            learning_objectives=["Solve equations"],
        )
        assert ctx.student_profile["name"] == "Alice"
        assert len(ctx.conversation_history) == 1
        assert ctx.current_subject == "Math"


class TestAgentResponse:
    def test_minimal_response(self):
        resp = AgentResponse(text="Hello!")
        assert resp.text == "Hello!"
        assert resp.metadata == {}
        assert resp.suggested_actions == []
        assert resp.agent_name == ""
        assert resp.processing_time == 0.0

    def test_full_response(self):
        resp = AgentResponse(
            text="Here's your answer",
            metadata={"source": "textbook"},
            suggested_actions=["Try a practice problem"],
            agent_name="tutor",
            processing_time=1.5,
        )
        assert resp.agent_name == "tutor"
        assert resp.processing_time == 1.5


class TestBaseAgent:
    @patch("src.agents.base.BaseAgent._initialize_llm")
    def test_agent_creation(self, mock_llm):
        mock_llm.return_value = AsyncMock()
        config = AgentConfig(name="test-agent")
        agent = ConcreteTestAgent(config)
        assert agent.config.name == "test-agent"

    @patch("src.agents.base.BaseAgent._initialize_llm")
    def test_system_prompt(self, mock_llm):
        mock_llm.return_value = AsyncMock()
        agent = ConcreteTestAgent(AgentConfig(name="test"))
        ctx = AgentContext(session_id="s1", student_id="stu-1")
        prompt = agent.get_system_prompt(ctx)
        assert "stu-1" in prompt

    @patch("src.agents.base.BaseAgent._initialize_llm")
    async def test_process(self, mock_llm):
        mock_llm.return_value = AsyncMock()
        agent = ConcreteTestAgent(AgentConfig(name="echo"))
        ctx = AgentContext(session_id="s1", student_id="stu-1")
        response = await agent.process("hello", ctx)
        assert response.text == "Echo: hello"
        assert response.agent_name == "echo"
