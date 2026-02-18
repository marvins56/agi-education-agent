"""
Comprehensive tests for the Persistent Tutor Personality System

Tests all major components: StudentMemory, TutorPersonality, EmotionalIntelligence,
RapportBuilder, PersonalizedContent, and their integrations.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
import json

from src.tutor_personality import (
    StudentMemory, TutorPersonalityState, StudentTutorRelationship, ConversationHighlight,
    StudentMemoryManager, TutorPersonality, EmotionalIntelligence, RapportBuilder,
    PersonalizedContent, AccessibilityIntegration, PersistentTutorPersonalitySystem,
    EmotionalState, TeachingStyle, RelationshipStage, StudentPersonalityProfile,
    TutorPersonalityConfig
)
from src.accessibility_engine import AccessibilityProfile, ImpairmentType, SeverityLevel


# Fixtures

@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = Mock(spec=AsyncSession)
    session.query = Mock()
    session.add = Mock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def student_memory_manager(mock_db_session):
    """Student memory manager with mocked database"""
    return StudentMemoryManager(mock_db_session)


@pytest.fixture
def tutor_personality(mock_db_session):
    """Tutor personality with mocked database"""
    return TutorPersonality(mock_db_session)


@pytest.fixture
def emotional_intelligence(student_memory_manager):
    """Emotional intelligence component"""
    return EmotionalIntelligence(student_memory_manager)


@pytest.fixture
def rapport_builder(mock_db_session, student_memory_manager):
    """Rapport builder component"""
    return RapportBuilder(mock_db_session, student_memory_manager)


@pytest.fixture
def sample_student_profile():
    """Sample student profile for testing"""
    return StudentPersonalityProfile(
        student_id="test-student-123",
        interests=["football", "video games", "music"],
        learning_struggles=["fractions", "word problems"],
        strengths=["basic arithmetic", "pattern recognition"],
        goals=["improve math grade", "understand algebra"],
        emotional_patterns={
            "by_day_of_week": {"Monday": "frustrated", "Friday": "excited"},
            "by_hour": {"14": "energetic", "9": "sleepy"}
        },
        stress_triggers=["timed tests", "public speaking"],
        motivation_factors=["achievements", "peer recognition"]
    )


@pytest.fixture
def sample_accessibility_profile():
    """Sample accessibility profile"""
    return AccessibilityProfile(
        user_id="test-student-123",
        visual_impairments={"myopia": SeverityLevel.MILD},
        cognitive_impairments={"dyslexia": SeverityLevel.MODERATE},
        needs_simplified_language=True,
        requires_patience_mode=True
    )


# StudentMemoryManager Tests

class TestStudentMemoryManager:
    """Test the student memory management system"""

    @pytest.mark.asyncio
    async def test_get_student_memory_new_student(self, student_memory_manager, mock_db_session):
        """Test getting memory for a new student"""
        # Setup
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = AsyncMock(return_value=None)
        mock_db_session.query.return_value = mock_query

        # Test
        memory = await student_memory_manager.get_student_memory("new-student")

        # Assert
        assert memory.student_id == "new-student"
        assert memory.interests == []
        assert memory.learning_struggles == []

    @pytest.mark.asyncio
    async def test_get_student_memory_existing_student(self, student_memory_manager, mock_db_session):
        """Test getting memory for existing student"""
        # Setup
        mock_memory = Mock()
        mock_memory.interests = ["football", "music"]
        mock_memory.struggles = ["fractions"]
        mock_memory.strengths = ["arithmetic"]
        mock_memory.goals = ["improve grades"]
        mock_memory.emotional_patterns = {"Monday": "tired"}
        mock_memory.stress_triggers = ["tests"]
        mock_memory.motivation_factors = ["praise"]
        mock_memory.family_context = {"siblings": 2}
        mock_memory.external_pressures = ["homework load"]
        mock_memory.memorable_conversations = [{"type": "breakthrough", "content": "understood fractions"}]
        mock_memory.successful_explanations = [{"approach": "visual", "topic": "fractions"}]

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = AsyncMock(return_value=mock_memory)
        mock_db_session.query.return_value = mock_query

        # Test
        memory = await student_memory_manager.get_student_memory("existing-student")

        # Assert
        assert memory.student_id == "existing-student"
        assert "football" in memory.interests
        assert "fractions" in memory.learning_struggles

    @pytest.mark.asyncio
    async def test_update_student_memory(self, student_memory_manager, mock_db_session):
        """Test updating student memory"""
        # Setup
        mock_memory = Mock()
        mock_memory.interests = ["music"]
        mock_memory.struggles = []

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = AsyncMock(return_value=mock_memory)
        mock_db_session.query.return_value = mock_query

        updates = {
            "interests": ["football", "gaming"],
            "struggles": ["algebra"]
        }

        # Test
        await student_memory_manager.update_student_memory("student-123", updates)

        # Assert
        mock_db_session.commit.assert_called_once()
        # Note: Due to mocking complexity, we verify the method was called

    @pytest.mark.asyncio
    async def test_add_conversation_highlight(self, student_memory_manager, mock_db_session):
        """Test adding conversation highlight"""
        # Test
        await student_memory_manager.add_conversation_highlight(
            student_id="student-123",
            highlight_type="breakthrough",
            content="finally understood fractions",
            context="during fraction lesson",
            topic="fractions",
            emotional_state="excited",
            breakthrough_level=0.9
        )

        # Assert
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_conversation_highlights(self, student_memory_manager, mock_db_session):
        """Test retrieving conversation highlights"""
        # Setup
        mock_highlight = Mock()
        mock_highlight.highlight_type = "breakthrough"
        mock_highlight.content = "mastered algebra"
        mock_highlight.context = "challenging problem"
        mock_highlight.topic = "algebra"
        mock_highlight.student_emotional_state = "proud"
        mock_highlight.breakthrough_level = 0.8
        mock_highlight.created_at = datetime.now()
        mock_highlight.times_referenced = 2

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = AsyncMock(return_value=[mock_highlight])
        mock_db_session.query.return_value = mock_query

        # Test
        highlights = await student_memory_manager.get_conversation_highlights("student-123", 5)

        # Assert
        assert len(highlights) == 1
        assert highlights[0]["type"] == "breakthrough"
        assert highlights[0]["content"] == "mastered algebra"


# TutorPersonality Tests

class TestTutorPersonality:
    """Test the tutor personality system"""

    @pytest.mark.asyncio
    async def test_load_personality_new_tutor(self, tutor_personality, mock_db_session):
        """Test loading personality for new tutor"""
        # Setup
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = AsyncMock(return_value=None)
        mock_db_session.query.return_value = mock_query

        # Test
        config = await tutor_personality.load_personality()

        # Assert
        assert config.tutor_id == "main_tutor"
        assert config.base_formality == 0.5
        assert config.humor_tendency == 0.3

    @pytest.mark.asyncio
    async def test_adapt_teaching_style(self, tutor_personality, mock_db_session):
        """Test adaptation of teaching style based on effectiveness"""
        # Setup - mock existing state
        mock_state = Mock()
        mock_state.teaching_style_effectiveness = {"math": {"encouraging": 0.6}}
        mock_state.subject_confidence = {"math": 0.7}
        mock_state.formality_preference = 0.5
        mock_state.humor_effectiveness = 0.3
        mock_state.adaptation_rate = 0.1

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = AsyncMock(return_value=mock_state)
        mock_db_session.query.return_value = mock_query

        # Load personality first
        await tutor_personality.load_personality()

        # Test adaptation
        await tutor_personality.adapt_teaching_style(
            student_id="student-123",
            subject="math",
            style="encouraging",
            success_rate=0.9
        )

        # Assert
        mock_db_session.commit.assert_called()
        # The style effectiveness should have increased due to high success rate

    def test_get_recommended_teaching_style(self, tutor_personality):
        """Test getting recommended teaching style"""
        # Setup
        tutor_personality.config = TutorPersonalityConfig(
            preferred_teaching_styles={
                "math": {"encouraging": 0.8, "challenging": 0.6}
            }
        )

        # Test
        style = tutor_personality.get_recommended_teaching_style("math")

        # Assert
        assert style == "encouraging"  # Should return the most effective style

    def test_get_subject_confidence(self, tutor_personality):
        """Test getting subject confidence"""
        # Setup
        tutor_personality.config = TutorPersonalityConfig(
            subject_confidence_levels={"math": 0.9, "science": 0.6}
        )

        # Test
        confidence = tutor_personality.get_subject_confidence("math")
        unknown_confidence = tutor_personality.get_subject_confidence("history")

        # Assert
        assert confidence == 0.9
        assert unknown_confidence == 0.5  # Default confidence


# EmotionalIntelligence Tests

class TestEmotionalIntelligence:
    """Test the emotional intelligence system"""

    @pytest.mark.asyncio
    async def test_detect_emotional_state_confident(self, emotional_intelligence):
        """Test detecting confident emotional state"""
        interaction_data = {
            'response_time_seconds': 5,
            'correctness': 0.9,
            'hint_count': 0,
            'message_tone': 'excited'
        }

        state = await emotional_intelligence.detect_emotional_state("student-123", interaction_data)

        assert state == EmotionalState.CONFIDENT

    @pytest.mark.asyncio
    async def test_detect_emotional_state_frustrated(self, emotional_intelligence):
        """Test detecting frustrated emotional state"""
        interaction_data = {
            'response_time_seconds': 120,
            'correctness': 0.2,
            'hint_count': 5,
            'message_tone': 'frustrated'
        }

        state = await emotional_intelligence.detect_emotional_state("student-123", interaction_data)

        assert state == EmotionalState.FRUSTRATED

    @pytest.mark.asyncio
    async def test_track_emotional_pattern(self, emotional_intelligence):
        """Test tracking emotional patterns over time"""
        # Mock the memory update
        emotional_intelligence.memory.update_student_memory = AsyncMock()

        context = {"topic": "fractions"}
        
        await emotional_intelligence.track_emotional_pattern(
            "student-123", EmotionalState.FRUSTRATED, context
        )

        # Assert that memory was updated
        emotional_intelligence.memory.update_student_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_adaptive_tone_frustrated(self, emotional_intelligence):
        """Test getting adaptive tone for frustrated student"""
        # Mock student profile
        emotional_intelligence.memory.get_student_memory = AsyncMock(
            return_value=StudentPersonalityProfile(
                student_id="student-123",
                needs_frequent_encouragement=True
            )
        )

        tone = await emotional_intelligence.get_adaptive_tone("student-123", EmotionalState.FRUSTRATED)

        assert tone['tone'] == 'calm'
        assert tone['approach'] == 'methodical'
        assert tone['encouragement'] == 'very_high'  # Due to student preference

    def test_should_push_harder(self, emotional_intelligence):
        """Test decision making for pushing student harder"""
        # Should not push when frustrated
        assert not emotional_intelligence.should_push_harder(
            "student-123", EmotionalState.FRUSTRATED, RelationshipStage.ESTABLISHED
        )

        # Should push when confident and relationship is established
        assert emotional_intelligence.should_push_harder(
            "student-123", EmotionalState.CONFIDENT, RelationshipStage.ESTABLISHED
        )

        # Should be cautious with new relationships
        assert not emotional_intelligence.should_push_harder(
            "student-123", EmotionalState.CONFIDENT, RelationshipStage.FIRST_MEETING
        )

    def test_should_ease_off(self, emotional_intelligence):
        """Test decision making for easing off pressure"""
        # Should ease off when overwhelmed
        assert emotional_intelligence.should_ease_off(EmotionalState.OVERWHELMED, 1)

        # Should ease off after consecutive struggles
        assert emotional_intelligence.should_ease_off(EmotionalState.NEUTRAL, 4)

        # Should not ease off when doing well
        assert not emotional_intelligence.should_ease_off(EmotionalState.CONFIDENT, 1)


# RapportBuilder Tests

class TestRapportBuilder:
    """Test the rapport building system"""

    @pytest.mark.asyncio
    async def test_get_relationship_status_new_student(self, rapport_builder, mock_db_session):
        """Test getting relationship status for new student"""
        # Setup
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = AsyncMock(return_value=None)
        mock_db_session.query.return_value = mock_query

        # Test
        status = await rapport_builder.get_relationship_status("new-student")

        # Assert
        assert status['stage'] == RelationshipStage.FIRST_MEETING
        assert status['trust_level'] == 0.0
        assert status['rapport_score'] == 0.0

    @pytest.mark.asyncio
    async def test_generate_appropriate_greeting_first_meeting(self, rapport_builder, mock_db_session):
        """Test generating greeting for first meeting"""
        # Mock get_relationship_status to return first meeting
        rapport_builder.get_relationship_status = AsyncMock(
            return_value={'stage': RelationshipStage.FIRST_MEETING}
        )
        rapport_builder.memory.get_student_memory = AsyncMock(
            return_value=StudentPersonalityProfile(student_id="student-123")
        )

        # Test
        greeting = await rapport_builder.generate_appropriate_greeting("student-123")

        # Assert
        assert "Hi there!" in greeting or "excited to start" in greeting

    @pytest.mark.asyncio
    async def test_generate_appropriate_greeting_established(self, rapport_builder, mock_db_session):
        """Test generating greeting for established relationship"""
        # Mock established relationship with interests
        rapport_builder.get_relationship_status = AsyncMock(
            return_value={
                'stage': RelationshipStage.ESTABLISHED,
                'last_interaction_date': datetime.now() - timedelta(days=1)
            }
        )
        rapport_builder.memory.get_student_memory = AsyncMock(
            return_value=StudentPersonalityProfile(
                student_id="student-123",
                interests=["football", "music"]
            )
        )

        # Test
        greeting = await rapport_builder.generate_appropriate_greeting("student-123")

        # Assert
        assert len(greeting) > 0
        # Should be more personal for established relationship

    @pytest.mark.asyncio
    async def test_update_relationship_metrics_positive(self, rapport_builder, mock_db_session):
        """Test updating relationship metrics with positive interaction"""
        # Setup
        mock_relationship = Mock()
        mock_relationship.total_interactions = 5
        mock_relationship.positive_interactions = 3
        mock_relationship.challenging_interactions = 1
        mock_relationship.trust_level = 0.5
        mock_relationship.rapport_score = 0.6
        mock_relationship.total_sessions = 10

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = AsyncMock(return_value=mock_relationship)
        mock_db_session.query.return_value = mock_query

        interaction_outcome = {
            'success_rate': 0.8,
            'engagement_level': 0.7,
            'student_feedback': 'positive',
            'emotional_state': 'confident',
            'topic': 'fractions'
        }

        # Test
        await rapport_builder.update_relationship_metrics("student-123", interaction_outcome)

        # Assert
        assert mock_relationship.positive_interactions == 4
        assert mock_relationship.trust_level > 0.5  # Should increase
        mock_db_session.commit.assert_called_once()


# PersonalizedContent Tests

class TestPersonalizedContent:
    """Test the personalized content generation"""

    @pytest.fixture
    def personalized_content(self, student_memory_manager, rapport_builder):
        """Personalized content generator"""
        return PersonalizedContent(student_memory_manager, rapport_builder)

    @pytest.mark.asyncio
    async def test_generate_contextual_reference(self, personalized_content):
        """Test generating contextual reference to past success"""
        # Mock student memory and highlights
        personalized_content.memory.get_student_memory = AsyncMock(
            return_value=StudentPersonalityProfile(student_id="student-123")
        )
        personalized_content.memory.get_conversation_highlights = AsyncMock(
            return_value=[
                {
                    'type': 'breakthrough',
                    'content': 'solved that tricky fraction problem',
                    'topic': 'fractions',
                    'breakthrough_level': 0.8,
                    'created_at': datetime.now() - timedelta(days=3)
                }
            ]
        )

        # Test
        reference = await personalized_content.generate_contextual_reference(
            "student-123", "decimals", "similar"
        )

        # Assert
        assert reference is not None
        assert "Remember" in reference or "reminds me" in reference.lower()

    @pytest.mark.asyncio
    async def test_generate_interest_based_example_sports(self, personalized_content):
        """Test generating sports-based examples"""
        # Mock student with sports interest
        personalized_content.memory.get_student_memory = AsyncMock(
            return_value=StudentPersonalityProfile(
                student_id="student-123",
                interests=["football", "soccer"]
            )
        )

        # Test
        example = await personalized_content.generate_interest_based_example(
            "student-123", "math", "ratio"
        )

        # Assert
        assert example is not None
        assert "goal" in example.lower() or "game" in example.lower()

    @pytest.mark.asyncio
    async def test_generate_interest_based_example_gaming(self, personalized_content):
        """Test generating gaming-based examples"""
        # Mock student with gaming interest
        personalized_content.memory.get_student_memory = AsyncMock(
            return_value=StudentPersonalityProfile(
                student_id="student-123",
                interests=["video games", "gaming"]
            )
        )

        # Test
        example = await personalized_content.generate_interest_based_example(
            "student-123", "math", "percentage"
        )

        # Assert
        assert example is not None
        assert any(word in example.lower() for word in ["game", "level", "xp", "quest"])


# AccessibilityIntegration Tests

class TestAccessibilityIntegration:
    """Test accessibility integration"""

    @pytest.fixture
    def accessibility_integration(self, student_memory_manager):
        """Accessibility integration component"""
        return AccessibilityIntegration(student_memory_manager)

    @pytest.mark.asyncio
    async def test_remember_accessibility_needs(self, accessibility_integration, sample_accessibility_profile):
        """Test remembering accessibility needs"""
        # Mock memory update
        accessibility_integration.memory.update_student_memory = AsyncMock()

        # Test
        await accessibility_integration.remember_accessibility_needs(
            "student-123", sample_accessibility_profile
        )

        # Assert
        accessibility_integration.memory.update_student_memory.assert_called_once()
        call_args = accessibility_integration.memory.update_student_memory.call_args[0]
        assert call_args[0] == "student-123"
        assert 'accessibility_needs' in call_args[1]

    def test_should_apply_accessibility_adaptations(self, accessibility_integration):
        """Test determining accessibility adaptations"""
        accessibility_needs = {
            'needs_simplified_language': True,
            'requires_patience_mode': True,
            'visual_impairments': {'myopia': 'mild'}
        }

        # Test
        adaptations = accessibility_integration.should_apply_accessibility_adaptations(accessibility_needs)

        # Assert
        assert adaptations['language_complexity'] == 'simple'
        assert adaptations['response_time_expectation'] == 'extended'
        assert adaptations['text_size'] == 'large'


# Integration Tests

class TestPersistentTutorPersonalitySystem:
    """Test the complete personality system integration"""

    @pytest.fixture
    def personality_system(self, mock_db_session):
        """Complete personality system"""
        return PersistentTutorPersonalitySystem(mock_db_session)

    @pytest.mark.asyncio
    async def test_start_session_comprehensive(self, personality_system, sample_student_profile):
        """Test comprehensive session start with all components"""
        # Mock all components
        personality_system.student_memory.get_student_memory = AsyncMock(
            return_value=sample_student_profile
        )
        personality_system.rapport_builder.get_relationship_status = AsyncMock(
            return_value={
                'stage': RelationshipStage.ESTABLISHED,
                'trust_level': 0.8,
                'preferred_teaching_style': 'encouraging'
            }
        )
        personality_system.tutor_personality.load_personality = AsyncMock(
            return_value=TutorPersonalityConfig(
                subject_confidence_levels={"math": 0.9}
            )
        )
        personality_system.accessibility_integration.get_remembered_accessibility_needs = AsyncMock(
            return_value=None
        )
        personality_system.rapport_builder.generate_appropriate_greeting = AsyncMock(
            return_value="Hey! Ready to tackle some math?"
        )
        personality_system.rapport_builder.generate_check_in = AsyncMock(
            return_value="How was your weekend?"
        )
        personality_system.student_memory.get_conversation_highlights = AsyncMock(
            return_value=[]
        )

        # Test
        session_context = await personality_system.start_session(
            "student-123", {"subject": "math"}
        )

        # Assert
        assert session_context['greeting'] == "Hey! Ready to tackle some math?"
        assert session_context['relationship_stage'] == RelationshipStage.ESTABLISHED
        assert session_context['student_interests'] == ["football", "video games", "music"]
        assert 'math' in session_context['tutor_subject_confidence']

    @pytest.mark.asyncio
    async def test_process_interaction_comprehensive(self, personality_system):
        """Test comprehensive interaction processing"""
        # Mock components
        personality_system.emotional_intelligence.detect_emotional_state = AsyncMock(
            return_value=EmotionalState.CONFIDENT
        )
        personality_system.emotional_intelligence.track_emotional_pattern = AsyncMock()
        personality_system.emotional_intelligence.get_adaptive_tone = AsyncMock(
            return_value={
                'tone': 'supportive',
                'approach': 'challenging',
                'encouragement': 'moderate'
            }
        )
        personality_system.tutor_personality.adapt_teaching_style = AsyncMock()
        personality_system.tutor_personality.get_recommended_teaching_style = Mock(
            return_value="encouraging"
        )
        personality_system.tutor_personality.get_subject_confidence = Mock(
            return_value=0.8
        )
        personality_system.personalized_content.generate_contextual_reference = AsyncMock(
            return_value=None
        )
        personality_system.personalized_content.generate_interest_based_example = AsyncMock(
            return_value="Like scoring goals in football - you need the right ratio!"
        )
        personality_system.student_memory.add_conversation_highlight = AsyncMock()

        interaction_data = {
            'subject': 'math',
            'topic': 'ratios',
            'concept': 'ratio',
            'correctness': 0.9,
            'difficulty_level': 0.8,
            'teaching_style_used': 'encouraging',
            'needs_example': True
        }

        # Test
        response_context = await personality_system.process_interaction("student-123", interaction_data)

        # Assert
        assert response_context['emotional_state'] == EmotionalState.CONFIDENT.value
        assert response_context['recommended_teaching_style'] == "encouraging"
        assert "football" in response_context['interest_based_example']

    @pytest.mark.asyncio
    async def test_end_session_comprehensive(self, personality_system):
        """Test comprehensive session ending"""
        # Mock components
        personality_system.rapport_builder.update_relationship_metrics = AsyncMock()
        personality_system.student_memory.update_student_memory = AsyncMock()
        personality_system.rapport_builder.get_relationship_status = AsyncMock(
            return_value={
                'stage': RelationshipStage.ESTABLISHED,
                'trust_level': 0.85,
                'rapport_score': 0.9,
                'total_sessions': 25
            }
        )

        session_summary = {
            'success_rate': 0.8,
            'engagement_level': 0.9,
            'insights': {
                'interests': ['basketball'],
                'new_strength': 'problem_solving'
            }
        }

        # Test
        result = await personality_system.end_session("student-123", session_summary)

        # Assert
        assert result['relationship_updated'] == True
        assert result['trust_level'] == 0.85
        assert "productive session" in result['closing_message'].lower()

    @pytest.mark.asyncio
    async def test_integrate_with_fsrs(self, personality_system, sample_student_profile):
        """Test FSRS integration with personality insights"""
        # Mock components
        personality_system.student_memory.get_student_memory = AsyncMock(
            return_value=sample_student_profile
        )
        personality_system.rapport_builder.get_relationship_status = AsyncMock(
            return_value={'trust_level': 0.9}
        )

        fsrs_recommendations = {
            'next_review_date': '2024-02-20',
            'difficulty_level': 0.7,
            'review_interval': 3
        }

        # Test
        result = await personality_system.integrate_with_fsrs("student-123", fsrs_recommendations)

        # Assert
        assert 'personality_adjustments' in result
        assert 'combined_recommendations' in result
        # High trust level should allow high difficulty tolerance
        assert result['personality_adjustments'].get('difficulty_tolerance') == 'high'


# Performance and Edge Case Tests

class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_memory_manager_empty_updates(self, student_memory_manager):
        """Test handling empty updates gracefully"""
        student_memory_manager.db.query = Mock()
        student_memory_manager.db.commit = AsyncMock()
        
        # Should not crash with empty updates
        await student_memory_manager.update_student_memory("student-123", {})
        
        # Should still call commit
        student_memory_manager.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_emotional_detection_edge_cases(self, emotional_intelligence):
        """Test emotional state detection with missing data"""
        # Test with minimal data
        minimal_data = {}
        state = await emotional_intelligence.detect_emotional_state("student-123", minimal_data)
        assert state == EmotionalState.NEUTRAL

        # Test with extreme values
        extreme_data = {
            'response_time_seconds': 0,
            'correctness': 1.0,
            'hint_count': 0
        }
        state = await emotional_intelligence.detect_emotional_state("student-123", extreme_data)
        assert state == EmotionalState.CONFIDENT

    def test_personalized_content_time_strings(self, student_memory_manager, rapport_builder):
        """Test time string generation for various time differences"""
        content = PersonalizedContent(student_memory_manager, rapport_builder)
        
        now = datetime.now()
        
        # Test various time differences
        assert content._time_since_string(now) == "earlier today"
        assert content._time_since_string(now - timedelta(days=1)) == "yesterday"
        assert content._time_since_string(now - timedelta(days=3)) == "3 days ago"
        assert "week" in content._time_since_string(now - timedelta(days=10))
        assert "month" in content._time_since_string(now - timedelta(days=35))

    @pytest.mark.asyncio
    async def test_rapport_builder_relationship_progression(self, rapport_builder, mock_db_session):
        """Test relationship stage progression logic"""
        # Mock relationship with various session counts
        mock_relationship = Mock()
        
        # Test stage transitions
        test_cases = [
            (1, RelationshipStage.FIRST_MEETING),
            (5, RelationshipStage.GETTING_ACQUAINTED),
            (15, RelationshipStage.BUILDING_TRUST),
            (30, RelationshipStage.ESTABLISHED),
            (60, RelationshipStage.DEEP_CONNECTION)
        ]
        
        for session_count, expected_stage in test_cases:
            mock_relationship.total_sessions = session_count - 1
            mock_relationship.total_interactions = 10
            mock_relationship.positive_interactions = 5
            mock_relationship.challenging_interactions = 2
            mock_relationship.trust_level = 0.5
            mock_relationship.rapport_score = 0.6

            mock_query = Mock()
            mock_query.filter = Mock(return_value=mock_query)
            mock_query.first = AsyncMock(return_value=mock_relationship)
            mock_db_session.query.return_value = mock_query

            await rapport_builder.update_relationship_metrics("student-123", {
                'success_rate': 0.7,
                'engagement_level': 0.7
            })

            assert mock_relationship.relationship_stage == expected_stage.value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])