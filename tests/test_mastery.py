"""Dedicated tests for mastery calculation, decay, and consolidation."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.memory.mastery import MasteryCalculator
from src.memory.consolidation import MemoryConsolidator


class TestMasteryWeightedAverage:
    """Test the weighted mastery formula in detail."""

    def test_perfect_scores_fresh(self):
        """100% on all inputs with no decay should yield 100."""
        score = MasteryCalculator.calculate_mastery(
            quiz_scores=[100.0],
            ai_assessments=[100.0],
            interaction_quality=[100.0],
            days_since_last=0,
        )
        assert score == 100.0

    def test_all_zeros(self):
        """Zero scores with fresh recency should yield only recency component."""
        score = MasteryCalculator.calculate_mastery(
            quiz_scores=[0.0],
            ai_assessments=[0.0],
            interaction_quality=[0.0],
            days_since_last=0,
        )
        # 0*0.4 + 0*0.3 + 0*0.2 + 1.0*100*0.1 = 10
        assert score == 10.0

    def test_multiple_scores_averaged(self):
        """Multiple scores per category should be averaged before weighting."""
        score = MasteryCalculator.calculate_mastery(
            quiz_scores=[60.0, 80.0],        # avg 70
            ai_assessments=[50.0, 70.0],      # avg 60
            interaction_quality=[40.0, 60.0],  # avg 50
            days_since_last=0,
        )
        # 70*0.4 + 60*0.3 + 50*0.2 + 100*0.1 = 28+18+10+10 = 66
        assert score == 66.0

    def test_partial_decay(self):
        """10 days with 0.02 decay: recency = max(0, 1 - 0.2) = 0.8."""
        score = MasteryCalculator.calculate_mastery(
            quiz_scores=[100.0],
            ai_assessments=[100.0],
            interaction_quality=[100.0],
            days_since_last=10,
        )
        # 40 + 30 + 20 + 0.8*100*0.1 = 90 + 8 = 98
        assert score == 98.0

    def test_custom_decay_rate(self):
        """Custom decay rate should be applied to recency."""
        score = MasteryCalculator.calculate_mastery(
            quiz_scores=[100.0],
            ai_assessments=[100.0],
            interaction_quality=[100.0],
            days_since_last=10,
            decay_rate=0.1,
        )
        # recency = max(0, 1 - 10*0.1) = 0
        # 40 + 30 + 20 + 0 = 90
        assert score == 90.0


class TestMasteryDecayFunction:
    def test_no_time_passed(self):
        assert MasteryCalculator.apply_decay(80.0, 0) == 80.0

    def test_one_day(self):
        assert MasteryCalculator.apply_decay(80.0, 1) == 79.98

    def test_large_decay_clamps_to_zero(self):
        result = MasteryCalculator.apply_decay(5.0, 500)
        assert result == 0.0

    def test_zero_mastery_stays_zero(self):
        assert MasteryCalculator.apply_decay(0.0, 10) == 0.0


class TestMasteryLevelBoundaries:
    """Test every boundary of mastery levels."""

    def test_novice_lower(self):
        assert MasteryCalculator.get_mastery_level(0.0) == "Novice"

    def test_novice_upper(self):
        assert MasteryCalculator.get_mastery_level(20.0) == "Novice"

    def test_beginner_lower(self):
        assert MasteryCalculator.get_mastery_level(20.1) == "Beginner"

    def test_intermediate_boundary(self):
        assert MasteryCalculator.get_mastery_level(40.1) == "Intermediate"

    def test_advanced_boundary(self):
        assert MasteryCalculator.get_mastery_level(60.1) == "Advanced"

    def test_expert_boundary(self):
        assert MasteryCalculator.get_mastery_level(80.1) == "Expert"

    def test_above_100(self):
        """Score above 100 should still map to Expert."""
        assert MasteryCalculator.get_mastery_level(150) == "Expert"


class TestMemoryConsolidation:
    async def test_consolidate_session_basic(self):
        """Consolidation should produce a summary dict from Redis history."""
        memory = AsyncMock()
        memory.get_conversation_history = AsyncMock(return_value=[
            {"role": "user", "content": "What is photosynthesis?"},
            {"role": "assistant", "content": "Photosynthesis is the process..."},
            {"role": "user", "content": "Can you explain the light reactions?"},
            {"role": "assistant", "content": "The light reactions occur..."},
        ])
        memory.get_session_context = AsyncMock(return_value={
            "student_id": "stu-1",
            "current_subject": "Biology",
            "current_topic": "Photosynthesis",
        })
        memory.db_session_factory = None

        consolidator = MemoryConsolidator(memory_manager=memory)
        summary = await consolidator.consolidate_session("sess-1")

        assert summary["session_id"] == "sess-1"
        assert summary["subject"] == "Biology"
        assert summary["message_count"] == 4
        assert summary["questions_asked"] == 2
        assert "Photosynthesis" in summary["topics_discussed"]
        assert "consolidated_at" in summary

    async def test_consolidate_empty_session(self):
        """Consolidating an empty session should still produce a valid summary."""
        memory = AsyncMock()
        memory.get_conversation_history = AsyncMock(return_value=[])
        memory.get_session_context = AsyncMock(return_value=None)
        memory.db_session_factory = None

        consolidator = MemoryConsolidator(memory_manager=memory)
        summary = await consolidator.consolidate_session("empty-sess")

        assert summary["session_id"] == "empty-sess"
        assert summary["message_count"] == 0
        assert summary["questions_asked"] == 0

    async def test_consolidate_with_db_saves_event(self):
        """When db_session_factory is available, should save a learning event."""
        memory = AsyncMock()
        memory.get_conversation_history = AsyncMock(return_value=[
            {"role": "user", "content": "Test question?"},
        ])
        memory.get_session_context = AsyncMock(return_value={
            "student_id": "stu-2",
            "current_subject": "Math",
            "current_topic": "Algebra",
        })
        memory.db_session_factory = MagicMock()  # truthy
        memory.save_learning_event = AsyncMock()

        consolidator = MemoryConsolidator(memory_manager=memory)
        summary = await consolidator.consolidate_session("sess-2")

        memory.save_learning_event.assert_called_once()
        call_kwargs = memory.save_learning_event.call_args[1]
        assert call_kwargs["student_id"] == "stu-2"
        assert call_kwargs["event_type"] == "session_summary"
        assert call_kwargs["subject"] == "Math"
