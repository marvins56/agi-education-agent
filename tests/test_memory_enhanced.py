"""Tests for enhanced memory system and adaptive tutoring."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.base import AgentConfig, AgentContext, AgentResponse
from src.agents.strategies import StrategySelector, TeachingStrategy
from src.memory.mastery import MasteryCalculator
from src.memory.student_context import StudentContextBuilder


# === MasteryCalculator Tests ===


class TestMasteryCalculation:
    def test_mastery_calculation_basic(self):
        """Basic weighted average with no decay."""
        score = MasteryCalculator.calculate_mastery(
            quiz_scores=[80.0, 90.0],        # avg 85 * 0.4 = 34
            ai_assessments=[70.0, 80.0],      # avg 75 * 0.3 = 22.5
            interaction_quality=[60.0, 70.0],  # avg 65 * 0.2 = 13
            days_since_last=0,                 # recency = 1.0 * 100 * 0.1 = 10
        )
        # 34 + 22.5 + 13 + 10 = 79.5
        assert score == 79.5

    def test_mastery_calculation_with_decay(self):
        """Mastery should decrease as days_since_last increases."""
        score_fresh = MasteryCalculator.calculate_mastery(
            quiz_scores=[80.0],
            ai_assessments=[80.0],
            interaction_quality=[80.0],
            days_since_last=0,
        )
        score_stale = MasteryCalculator.calculate_mastery(
            quiz_scores=[80.0],
            ai_assessments=[80.0],
            interaction_quality=[80.0],
            days_since_last=30,
        )
        assert score_fresh > score_stale

    def test_mastery_calculation_empty_lists(self):
        """Empty input lists should yield only recency component."""
        score = MasteryCalculator.calculate_mastery(
            quiz_scores=[],
            ai_assessments=[],
            interaction_quality=[],
            days_since_last=0,
        )
        # Only recency: 1.0 * 100 * 0.1 = 10
        assert score == 10.0

    def test_mastery_calculation_full_decay(self):
        """After 50 days with default decay_rate=0.02, recency=0."""
        score = MasteryCalculator.calculate_mastery(
            quiz_scores=[100.0],
            ai_assessments=[100.0],
            interaction_quality=[100.0],
            days_since_last=50,
        )
        # quiz: 40, ai: 30, interaction: 20, recency: 0 = 90
        assert score == 90.0


class TestMasteryLevel:
    def test_mastery_level_mapping(self):
        """Each level boundary should map correctly."""
        assert MasteryCalculator.get_mastery_level(0) == "Novice"
        assert MasteryCalculator.get_mastery_level(10) == "Novice"
        assert MasteryCalculator.get_mastery_level(20) == "Novice"
        assert MasteryCalculator.get_mastery_level(21) == "Beginner"
        assert MasteryCalculator.get_mastery_level(40) == "Beginner"
        assert MasteryCalculator.get_mastery_level(41) == "Intermediate"
        assert MasteryCalculator.get_mastery_level(60) == "Intermediate"
        assert MasteryCalculator.get_mastery_level(61) == "Advanced"
        assert MasteryCalculator.get_mastery_level(80) == "Advanced"
        assert MasteryCalculator.get_mastery_level(81) == "Expert"
        assert MasteryCalculator.get_mastery_level(100) == "Expert"


class TestMasteryDecay:
    def test_apply_decay_basic(self):
        decayed = MasteryCalculator.apply_decay(80.0, days_since_review=10)
        # 80 - 0.02 * 10 = 79.8
        assert decayed == 79.8

    def test_apply_decay_floors_at_zero(self):
        decayed = MasteryCalculator.apply_decay(1.0, days_since_review=1000)
        assert decayed == 0.0

    def test_apply_decay_custom_rate(self):
        decayed = MasteryCalculator.apply_decay(50.0, days_since_review=10, decay_rate=0.5)
        # 50 - 0.5 * 10 = 45
        assert decayed == 45.0


# === Strategy Selection Tests ===


class TestStrategySelection:
    def test_strategy_selection_low_mastery(self):
        """Very low mastery should trigger direct_explanation."""
        strategy = StrategySelector.select_strategy(
            learning_style="balanced",
            topic_mastery=10.0,
            attempt_count=0,
        )
        assert strategy == TeachingStrategy.direct_explanation

    def test_strategy_selection_repeat_attempts(self):
        """After 3+ attempts with same strategy, should switch."""
        strategy = StrategySelector.select_strategy(
            learning_style="balanced",
            topic_mastery=50.0,
            attempt_count=3,
            previous_strategy="socratic",
        )
        assert strategy != TeachingStrategy.socratic

    def test_strategy_selection_visual_learner(self):
        """Visual learners should get analogy strategy."""
        strategy = StrategySelector.select_strategy(
            learning_style="visual",
            topic_mastery=50.0,
            attempt_count=0,
        )
        assert strategy == TeachingStrategy.analogy

    def test_strategy_selection_kinesthetic_learner(self):
        """Kinesthetic learners should get worked_example strategy."""
        strategy = StrategySelector.select_strategy(
            learning_style="kinesthetic",
            topic_mastery=50.0,
            attempt_count=0,
        )
        assert strategy == TeachingStrategy.worked_example

    def test_strategy_selection_default_socratic(self):
        """Default balanced learner with moderate mastery should get socratic."""
        strategy = StrategySelector.select_strategy(
            learning_style="balanced",
            topic_mastery=50.0,
            attempt_count=0,
        )
        assert strategy == TeachingStrategy.socratic

    def test_get_strategy_prompt(self):
        """Each strategy should have a non-empty prompt."""
        for strat in TeachingStrategy:
            prompt = StrategySelector.get_strategy_prompt(strat)
            assert isinstance(prompt, str)
            assert len(prompt) > 10


# === StudentContextBuilder Tests ===


class TestStudentContextBuilder:
    async def test_student_context_builder(self):
        """Context builder should merge all 3 tiers into a single dict."""
        memory = AsyncMock()
        memory.get_session_context = AsyncMock(return_value={
            "session_id": "sess-1",
            "student_id": "stu-1",
            "current_subject": "Math",
            "current_topic": "Algebra",
        })
        memory.get_conversation_history = AsyncMock(return_value=[
            {"role": "user", "content": "What is x?"},
            {"role": "assistant", "content": "Let me explain..."},
        ])
        memory.get_student_history = AsyncMock(return_value=[
            {
                "event_type": "session_summary",
                "subject": "Math",
                "topic": "Algebra",
                "data": {"message_count": 5},
            },
        ])
        memory.get_student_mastery = AsyncMock(return_value=[
            {"topic": "Algebra", "mastery_score": 45.0, "attempts": 3},
        ])
        memory.get_struggle_points = AsyncMock(return_value=[
            {"subject": "Math", "topic": "Calculus", "mastery_score": 15.0, "attempts": 1},
        ])
        memory.search_knowledge = AsyncMock(return_value=[])

        builder = StudentContextBuilder(memory_manager=memory)
        ctx = await builder.build_context(student_id="stu-1", session_id="sess-1")

        assert ctx["student_id"] == "stu-1"
        assert ctx["session_id"] == "sess-1"
        assert ctx["session_state"]["current_subject"] == "Math"
        assert len(ctx["recent_conversation"]) == 2
        assert len(ctx["session_summaries"]) == 1
        assert len(ctx["mastery_scores"]) == 1
        assert ctx["mastery_scores"][0]["topic"] == "Algebra"
        assert len(ctx["struggle_points"]) == 1
        assert ctx["struggle_points"][0]["topic"] == "Calculus"
        assert ctx["knowledge_gaps"] == []


# === Profile Endpoint Tests ===


class TestProfileEndpoint:
    async def test_profile_endpoint_get(self):
        """GET /profile should return user profile data."""
        from fastapi import FastAPI
        from httpx import ASGITransport, AsyncClient

        from src.api.dependencies import get_current_user, get_db
        from src.api.routers.profile import router

        app = FastAPI()
        app.include_router(router, prefix="/api/v1")

        # Mock user
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.name = "Test Student"
        mock_user.email = "test@example.com"
        mock_user.role = "student"

        # Mock profile result
        mock_profile = MagicMock()
        mock_profile.learning_style = "visual"
        mock_profile.pace = "fast"
        mock_profile.grade_level = "10th"
        mock_profile.strengths = ["math", "science"]
        mock_profile.weaknesses = ["writing"]
        mock_profile.preferences = {"theme": "dark"}

        # Mock DB session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_profile
        mock_session.execute = AsyncMock(return_value=mock_result)

        async def override_get_current_user():
            return mock_user

        async def override_get_db():
            yield mock_session

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/profile")

        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test Student"
        assert data["email"] == "test@example.com"
        assert data["learning_style"] == "visual"
        assert data["pace"] == "fast"
        assert data["grade_level"] == "10th"
        assert data["strengths"] == ["math", "science"]
        assert data["weaknesses"] == ["writing"]

        app.dependency_overrides.clear()


# === TutorAgent Strategy Integration ===


class TestTutorAgentStrategy:
    @patch("src.agents.base.BaseAgent._initialize_llm")
    def test_tutor_system_prompt_includes_strategy(self, mock_llm):
        """System prompt should include the selected strategy."""
        mock_llm.return_value = AsyncMock()
        from src.agents.tutor import TutorAgent

        agent = TutorAgent()
        ctx = AgentContext(
            session_id="s1",
            student_id="stu-1",
            student_profile={"name": "Alice", "learning_style": "visual"},
        )
        prompt = agent.get_system_prompt(ctx, strategy=TeachingStrategy.analogy)
        assert "analogy" in prompt.lower()
        assert "Teaching strategy:" in prompt

    @patch("src.agents.base.BaseAgent._initialize_llm")
    def test_tutor_system_prompt_backward_compatible(self, mock_llm):
        """Without a strategy, prompt should fall back to default guidelines."""
        mock_llm.return_value = AsyncMock()
        from src.agents.tutor import TutorAgent

        agent = TutorAgent()
        ctx = AgentContext(
            session_id="s1",
            student_id="stu-1",
            student_profile={"name": "Bob"},
        )
        prompt = agent.get_system_prompt(ctx)
        assert "Socratic method" in prompt
        assert "Teaching guidelines:" in prompt
