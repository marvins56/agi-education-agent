"""Dedicated tests for enhanced TutorAgent with strategy integration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.base import AgentConfig, AgentContext, AgentResponse
from src.agents.strategies import StrategySelector, TeachingStrategy


class TestStrategySelectionRules:
    """Test detailed strategy selection logic."""

    def test_low_mastery_direct_explanation(self):
        """Mastery < 20 should always start with direct_explanation."""
        for mastery in [0, 5, 10, 15, 19.9]:
            strategy = StrategySelector.select_strategy(
                learning_style="balanced",
                topic_mastery=mastery,
                attempt_count=0,
            )
            assert strategy == TeachingStrategy.direct_explanation

    def test_repeat_attempts_switches_strategy(self):
        """3+ attempts with same strategy should switch to a different one."""
        strategy = StrategySelector.select_strategy(
            learning_style="balanced",
            topic_mastery=50.0,
            attempt_count=4,
            previous_strategy="socratic",
        )
        assert strategy != TeachingStrategy.socratic
        assert isinstance(strategy, TeachingStrategy)

    def test_visual_learner_gets_analogy(self):
        strategy = StrategySelector.select_strategy(
            learning_style="visual",
            topic_mastery=50.0,
            attempt_count=0,
        )
        assert strategy == TeachingStrategy.analogy

    def test_kinesthetic_learner_gets_worked_example(self):
        strategy = StrategySelector.select_strategy(
            learning_style="kinesthetic",
            topic_mastery=50.0,
            attempt_count=0,
        )
        assert strategy == TeachingStrategy.worked_example

    def test_auditory_learner_gets_socratic(self):
        """Non-visual, non-kinesthetic learner defaults to socratic."""
        strategy = StrategySelector.select_strategy(
            learning_style="auditory",
            topic_mastery=50.0,
            attempt_count=0,
        )
        assert strategy == TeachingStrategy.socratic

    def test_low_mastery_with_many_attempts_switches(self):
        """Low mastery + many attempts on direct_explanation should switch."""
        strategy = StrategySelector.select_strategy(
            learning_style="balanced",
            topic_mastery=10.0,
            attempt_count=5,
            previous_strategy="direct_explanation",
        )
        assert strategy != TeachingStrategy.direct_explanation

    def test_no_previous_strategy_does_not_crash(self):
        """None previous_strategy should not cause errors."""
        strategy = StrategySelector.select_strategy(
            learning_style="balanced",
            topic_mastery=50.0,
            attempt_count=0,
            previous_strategy=None,
        )
        assert isinstance(strategy, TeachingStrategy)


class TestStrategyPrompts:
    def test_all_strategies_have_prompts(self):
        """Every strategy variant should have a non-empty prompt."""
        for strategy in TeachingStrategy:
            prompt = StrategySelector.get_strategy_prompt(strategy)
            assert len(prompt) > 20
            assert isinstance(prompt, str)

    def test_socratic_prompt_mentions_questions(self):
        prompt = StrategySelector.get_strategy_prompt(TeachingStrategy.socratic)
        assert "question" in prompt.lower()

    def test_direct_explanation_prompt_mentions_clear(self):
        prompt = StrategySelector.get_strategy_prompt(TeachingStrategy.direct_explanation)
        assert "clear" in prompt.lower() or "explain" in prompt.lower()

    def test_worked_example_prompt_mentions_step(self):
        prompt = StrategySelector.get_strategy_prompt(TeachingStrategy.worked_example)
        assert "step" in prompt.lower()


class TestTutorSystemPromptEnhanced:
    @patch("src.agents.base.BaseAgent._initialize_llm")
    def test_prompt_with_strategy_and_enriched_context(self, mock_llm):
        """System prompt should incorporate strategy and enriched context."""
        mock_llm.return_value = AsyncMock()
        from src.agents.tutor import TutorAgent

        agent = TutorAgent()
        ctx = AgentContext(
            session_id="s1",
            student_id="stu-1",
            student_profile={
                "name": "Alice",
                "learning_style": "visual",
                "pace": "fast",
                "grade_level": "10th",
                "strengths": ["algebra"],
                "weaknesses": ["geometry"],
            },
            current_subject="Math",
            current_topic="Trigonometry",
        )
        enriched = {
            "struggle_points": [
                {"topic": "Sine Functions", "mastery_score": 15.0},
            ],
            "mastery_scores": [
                {"topic": "Trigonometry", "mastery_score": 42.0},
            ],
        }
        prompt = agent.get_system_prompt(
            ctx,
            strategy=TeachingStrategy.worked_example,
            enriched_context=enriched,
        )

        assert "Alice" in prompt
        assert "visual" in prompt
        assert "Math" in prompt
        assert "Trigonometry" in prompt
        assert "worked_example" in prompt
        assert "Sine Functions" in prompt
        assert "Struggle areas" in prompt
        assert "algebra" in prompt

    @patch("src.agents.base.BaseAgent._initialize_llm")
    def test_prompt_without_enriched_context(self, mock_llm):
        """Without enriched context, no struggle/mastery sections."""
        mock_llm.return_value = AsyncMock()
        from src.agents.tutor import TutorAgent

        agent = TutorAgent()
        ctx = AgentContext(
            session_id="s1",
            student_id="stu-1",
            student_profile={"name": "Bob"},
        )
        prompt = agent.get_system_prompt(ctx, strategy=TeachingStrategy.socratic)
        assert "Struggle areas" not in prompt
        assert "Recent mastery" not in prompt
        assert "socratic" in prompt.lower()

    @patch("src.agents.base.BaseAgent._initialize_llm")
    def test_backward_compatible_no_strategy(self, mock_llm):
        """Without strategy, prompt includes default guidelines."""
        mock_llm.return_value = AsyncMock()
        from src.agents.tutor import TutorAgent

        agent = TutorAgent()
        ctx = AgentContext(
            session_id="s1",
            student_id="stu-1",
            student_profile={"name": "Carol"},
        )
        prompt = agent.get_system_prompt(ctx)
        assert "Teaching guidelines:" in prompt
        assert "Socratic method" in prompt


class TestTutorProcessIntegration:
    @patch("src.agents.base.BaseAgent._initialize_llm")
    async def test_process_returns_strategy_metadata(self, mock_llm):
        """process() should include teaching_strategy in metadata."""
        mock_response = MagicMock()
        mock_response.content = "Let me help you understand this concept."
        llm_instance = AsyncMock()
        llm_instance.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm.return_value = llm_instance

        from src.agents.tutor import TutorAgent

        agent = TutorAgent()
        ctx = AgentContext(
            session_id="s1",
            student_id="stu-1",
            student_profile={"name": "Dan", "learning_style": "visual"},
            current_subject="Math",
            current_topic="Algebra",
        )

        response = await agent.process("What is a variable?", ctx)

        assert response.text == "Let me help you understand this concept."
        assert response.agent_name == "tutor"
        assert "teaching_strategy" in response.metadata
        assert response.metadata["teaching_strategy"] in [s.value for s in TeachingStrategy]

    @patch("src.agents.base.BaseAgent._initialize_llm")
    async def test_process_with_context_builder(self, mock_llm):
        """process() with context_builder should use enriched context."""
        mock_response = MagicMock()
        mock_response.content = "Great question about derivatives!"
        llm_instance = AsyncMock()
        llm_instance.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm.return_value = llm_instance

        mock_context_builder = AsyncMock()
        mock_context_builder.build_context = AsyncMock(return_value={
            "session_state": {"last_strategy": "socratic"},
            "mastery_scores": [
                {"topic": "Derivatives", "mastery_score": 25.0, "attempts": 1},
            ],
            "struggle_points": [
                {"topic": "Integrals", "mastery_score": 10.0},
            ],
            "knowledge_gaps": [],
        })

        from src.agents.tutor import TutorAgent

        agent = TutorAgent(context_builder=mock_context_builder)
        ctx = AgentContext(
            session_id="s1",
            student_id="stu-1",
            student_profile={"name": "Eve", "learning_style": "balanced"},
            current_subject="Math",
            current_topic="Derivatives",
        )

        response = await agent.process("Explain derivatives", ctx)

        mock_context_builder.build_context.assert_called_once_with(
            student_id="stu-1",
            session_id="s1",
        )
        assert response.text == "Great question about derivatives!"
        assert "teaching_strategy" in response.metadata

    @patch("src.agents.base.BaseAgent._initialize_llm")
    async def test_process_confusion_tracking(self, mock_llm):
        """When confusion count >= 3, strategy should switch to scaffolded."""
        mock_response = MagicMock()
        mock_response.content = "Let me break this down step by step."
        llm_instance = AsyncMock()
        llm_instance.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm.return_value = llm_instance

        mock_memory = AsyncMock()
        mock_memory.track_confusion = AsyncMock(return_value=3)

        from src.agents.tutor import TutorAgent

        agent = TutorAgent(memory=mock_memory)
        ctx = AgentContext(
            session_id="s1",
            student_id="stu-1",
            student_profile={"name": "Frank", "learning_style": "balanced"},
            current_topic="Limits",
        )

        response = await agent.process("I still don't understand limits", ctx)

        mock_memory.track_confusion.assert_called_once_with("s1", "Limits")
        assert response.metadata["teaching_strategy"] == "scaffolded"

    @patch("src.agents.base.BaseAgent._initialize_llm")
    async def test_visual_aid_detection(self, mock_llm):
        """Visual aid detection should flag requests for diagrams/charts."""
        mock_response = MagicMock()
        mock_response.content = "Here is a diagram showing the relationship."
        llm_instance = AsyncMock()
        llm_instance.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm.return_value = llm_instance

        from src.agents.tutor import TutorAgent

        agent = TutorAgent()
        ctx = AgentContext(
            session_id="s1",
            student_id="stu-1",
            student_profile={"name": "Grace"},
        )

        response = await agent.process("Can you draw a graph?", ctx)
        assert response.metadata["needs_visual_aid"] is True
