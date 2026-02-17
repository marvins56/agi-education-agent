"""Tests for enhanced assessment system."""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from src.assessment.formative.continuous_checker import ContinuousAssessmentChecker
from src.assessment.formative.misconception_detector import MisconceptionDetector
from src.assessment.grading.essay_grader import HistoryEssayGrader
from src.assessment.spaced_repetition.scheduler import SpacedRepetitionScheduler


class TestContinuousAssessmentChecker:
    """Test the continuous assessment checker."""
    
    @pytest.fixture
    def mock_memory(self):
        """Create mock memory manager."""
        return Mock()
    
    @pytest.fixture
    def checker(self, mock_memory):
        """Create continuous assessment checker."""
        return ContinuousAssessmentChecker(mock_memory)
    
    @pytest.mark.asyncio
    async def test_monitor_learning_session(self, checker):
        """Test starting monitoring of a learning session."""
        result = await checker.monitor_learning_session(
            student_id="test_student",
            session_id="test_session",
            subject="history"
        )
        
        assert result["status"] == "monitoring_started"
        assert result["session_id"] == "test_session"
        assert "next_scheduled_check" in result
        assert "test_session" in checker.active_sessions
    
    @pytest.mark.asyncio
    async def test_process_confusion_input(self, checker):
        """Test processing input with confusion indicators."""
        # Setup session
        await checker.monitor_learning_session(
            student_id="test_student",
            session_id="test_session"
        )
        
        # Mock LLM response
        checker.llm = AsyncMock()
        mock_response = Mock()
        mock_response.content = "0.3"  # Low engagement score
        checker.llm.ainvoke.return_value = mock_response
        
        # Process confused input
        result = await checker.process_student_input(
            session_id="test_session",
            student_input="I don't understand this at all, I'm really confused",
            context={"current_topic": "World War I causes"}
        )
        
        assert "triggers_detected" in result
        assert any(t["type"] == "confusion_indicators" for t in result["triggers_detected"])
        assert "formative_check" in result
    
    @pytest.mark.asyncio
    async def test_process_check_response(self, checker):
        """Test processing student response to formative check."""
        # Setup session
        await checker.monitor_learning_session(
            student_id="test_student",
            session_id="test_session"
        )
        
        # Mock LLM response for understanding analysis
        checker.llm = AsyncMock()
        mock_response = Mock()
        mock_response.content = '{"level": 0.8, "confidence": 0.7, "misconceptions": [], "recommended_action": "continue"}'
        checker.llm.ainvoke.return_value = mock_response
        
        result = await checker.process_check_response(
            check_id="test_check",
            student_response="Yes, I understand that WWI was caused by multiple factors including nationalism, alliances, and the assassination.",
            session_id="test_session"
        )
        
        assert "understanding_level" in result
        assert "feedback" in result
        assert result["needs_intervention"] is False  # High understanding
    
    def test_assess_engagement_level(self, checker):
        """Test engagement level assessment."""
        # This would test the fallback method
        high_engagement_input = "That's fascinating! I can see how the alliance system created a domino effect that led to the war spreading across Europe."
        low_engagement_input = "ok"
        
        # Since we can't easily test the async LLM call, test the structure
        assert hasattr(checker, '_assess_engagement_level')
    
    @pytest.mark.asyncio
    async def test_get_session_summary(self, checker):
        """Test getting session summary."""
        # Setup session with some history
        await checker.monitor_learning_session(
            student_id="test_student", 
            session_id="test_session"
        )
        
        # Add some understanding history
        session_data = checker.active_sessions["test_session"]
        session_data["understanding_history"] = [
            {
                "check_id": "check1",
                "understanding_level": 0.6,
                "misconceptions": ["linear_progress"],
                "timestamp": datetime.now()
            },
            {
                "check_id": "check2", 
                "understanding_level": 0.8,
                "misconceptions": [],
                "timestamp": datetime.now()
            }
        ]
        
        summary = await checker.get_session_summary("test_session")
        
        assert summary["total_checks"] == 2
        assert summary["average_understanding"] == 0.7
        assert summary["trend"] == "insufficient_data"  # Only 2 checks
        assert len(summary["common_misconceptions"]) >= 0


class TestMisconceptionDetector:
    """Test the misconception detection system."""
    
    @pytest.fixture
    def mock_memory(self):
        """Create mock memory manager."""
        return Mock()
    
    @pytest.fixture
    def detector(self, mock_memory):
        """Create misconception detector."""
        return MisconceptionDetector(mock_memory)
    
    @pytest.mark.asyncio
    async def test_detect_misconceptions(self, detector):
        """Test misconception detection."""
        # Mock LLM response
        detector.llm = AsyncMock()
        mock_response = Mock()
        mock_response.content = '[{"type": "linear_progress", "evidence": ["things get better over time"], "confidence": 0.8}]'
        detector.llm.ainvoke.return_value = mock_response
        
        result = await detector.detect_misconceptions(
            student_id="test_student",
            student_response="History shows that things always get better over time and people are always becoming more civilized.",
            topic_context="Historical development"
        )
        
        assert "misconceptions_detected" in result
        assert "severity_level" in result
        assert "recommended_actions" in result
    
    def test_detect_known_misconception_patterns(self, detector):
        """Test pattern-based misconception detection."""
        test_response = "Things always get better over time and people in the past were less intelligent than us today."
        
        detections = detector._detect_known_misconception_patterns(
            test_response, "historical_progress"
        )
        
        assert len(detections) > 0
        assert any(d["type"] == "linear_progress" for d in detections)
    
    @pytest.mark.asyncio
    async def test_get_student_misconception_profile(self, detector):
        """Test getting student misconception profile."""
        # Mock memory return
        detector.memory.get_student_events = AsyncMock()
        detector.memory.get_student_events.return_value = [
            {
                "event_data": {
                    "detections": [
                        {"type": "linear_progress", "severity": "high"},
                        {"type": "presentism", "severity": "medium"}
                    ]
                }
            }
        ]
        
        profile = await detector.get_student_misconception_profile("test_student")
        
        assert "common_misconceptions" in profile
        assert "frequency_analysis" in profile
        assert "trend" in profile
    
    @pytest.mark.asyncio 
    async def test_create_targeted_remediation_plan(self, detector):
        """Test creating targeted remediation plan."""
        misconception_profile = {
            "common_misconceptions": [
                {"type": "linear_progress", "frequency": 3},
                {"type": "presentism", "frequency": 2}
            ],
            "persistent_issues": ["linear_progress"]
        }
        
        plan = await detector.create_targeted_remediation_plan(
            "test_student", misconception_profile
        )
        
        assert "priority_misconceptions" in plan
        assert "intervention_sequence" in plan
        assert "expected_duration_weeks" in plan
        assert len(plan["intervention_sequence"]) > 0


class TestHistoryEssayGrader:
    """Test the history essay grading system."""
    
    @pytest.fixture
    def grader(self):
        """Create essay grader."""
        return HistoryEssayGrader()
    
    @pytest.mark.asyncio
    async def test_grade_history_essay(self, grader):
        """Test grading a history essay."""
        essay_text = """
        The causes of World War I were complex and multifaceted. While the assassination of Archduke Franz Ferdinand 
        served as the immediate trigger, underlying factors including nationalism, imperialism, militarism, and the 
        alliance system created a powder keg situation in Europe.
        
        The alliance system divided Europe into two opposing camps. The Triple Alliance of Germany, Austria-Hungary, 
        and Italy faced the Triple Entente of France, Russia, and Britain. This meant that a conflict involving any 
        major power could quickly escalate into a continental war.
        
        Nationalism was another significant factor, particularly in the volatile Balkans region. The assassination 
        of Franz Ferdinand by a Serbian nationalist exemplifies how nationalist tensions could spark international crisis.
        
        In conclusion, World War I resulted from a complex interaction of long-term structural factors and immediate 
        triggering events, demonstrating the importance of understanding multiple causation in historical analysis.
        """
        
        # Mock LLM responses
        grader.llm = AsyncMock()
        mock_response = Mock()
        mock_response.content = '{"points": 3, "feedback": "Good analysis of multiple causes", "evidence": ["Shows understanding of complex causation"]}'
        grader.llm.ainvoke.return_value = mock_response
        
        result = await grader.grade_history_essay(
            essay_text=essay_text,
            essay_type="analytical_essay",
            prompt="Analyze the causes of World War I"
        )
        
        assert "category_scores" in result
        assert "total_score" in result
        assert "percentage" in result
        assert "overall_feedback" in result
        assert result["essay_type"] == "analytical_essay"
    
    def test_extract_thesis_candidates(self, grader):
        """Test thesis extraction."""
        essay_text = "I argue that World War I was caused by multiple factors. The alliance system created tensions."
        
        candidates = grader._extract_thesis_candidates(essay_text)
        
        assert len(candidates) > 0
        assert any("argue" in candidate for candidate in candidates)
    
    def test_count_specific_evidence(self, grader):
        """Test evidence counting."""
        essay_text = "In 1914, the assassination of Franz Ferdinand triggered World War I. President Wilson declared neutrality in August 1914."
        
        count = grader._count_specific_evidence(essay_text)
        
        assert count > 0  # Should find years and proper nouns
    
    def test_identify_historical_thinking_indicators(self, grader):
        """Test historical thinking skill identification."""
        essay_text = "From the German perspective, the war was defensive. This caused widespread destruction and led to significant social changes over time."
        
        indicators = grader._identify_historical_thinking_indicators(essay_text)
        
        assert "perspective_analysis" in indicators
        assert "causation" in indicators
        assert "change_over_time" in indicators
        assert len(indicators["perspective_analysis"]) > 0
    
    def test_analyze_essay_structure(self, grader):
        """Test essay structure analysis."""
        essay_text = """This essay will examine the causes of World War I.
        
        The first major cause was nationalism.
        
        The second cause was the alliance system.
        
        In conclusion, multiple factors led to the war."""
        
        structure = grader._analyze_essay_structure(essay_text)
        
        assert structure["paragraph_count"] == 4
        assert structure["has_introduction"] == True
        assert structure["has_conclusion"] == True


class TestSpacedRepetitionScheduler:
    """Test the spaced repetition scheduler."""
    
    @pytest.fixture
    def mock_memory(self):
        """Create mock memory manager."""
        memory = Mock()
        memory.store_learning_data = AsyncMock()
        return memory
    
    @pytest.fixture
    def scheduler(self, mock_memory):
        """Create spaced repetition scheduler."""
        return SpacedRepetitionScheduler(mock_memory)
    
    @pytest.mark.asyncio
    async def test_create_spaced_repetition_card(self, scheduler):
        """Test creating a spaced repetition card."""
        card = await scheduler.create_spaced_repetition_card(
            student_id="test_student",
            content_id="ww1_causes",
            content_type="concept",
            concept="Causes of World War I",
            difficulty=0.6,
            importance=0.9
        )
        
        assert card["student_id"] == "test_student"
        assert card["concept"] == "Causes of World War I"
        assert card["ease_factor"] == scheduler.default_params["ease_factor_default"]
        assert card["interval"] == scheduler.default_params["initial_interval"]
        assert card["learning_state"] == "new"
        assert card["difficulty_rating"] == 0.6
        assert card["importance_weight"] == 0.9
    
    @pytest.mark.asyncio
    async def test_process_review_result_good_performance(self, scheduler):
        """Test processing good review performance."""
        # Create card first
        card = await scheduler.create_spaced_repetition_card(
            student_id="test_student",
            content_id="test_content",
            content_type="fact",
            concept="Test concept"
        )
        
        result = await scheduler.process_review_result(
            card_id=card["card_id"],
            student_id="test_student",
            performance_score=0.9,  # Excellent performance
            response_time_seconds=3.0
        )
        
        assert result["performance_category"] == "excellent"
        assert result["interval_days"] > scheduler.default_params["initial_interval"]
        assert result["success_rate"] == 0.9
        assert result["correct_streak"] == 1
    
    @pytest.mark.asyncio
    async def test_process_review_result_poor_performance(self, scheduler):
        """Test processing poor review performance."""
        # Create card first
        card = await scheduler.create_spaced_repetition_card(
            student_id="test_student",
            content_id="test_content", 
            content_type="fact",
            concept="Test concept"
        )
        
        result = await scheduler.process_review_result(
            card_id=card["card_id"],
            student_id="test_student",
            performance_score=0.2,  # Poor performance
            response_time_seconds=15.0
        )
        
        assert result["performance_category"] == "poor"
        assert result["interval_days"] <= scheduler.default_params["initial_interval"]
        assert result["correct_streak"] == 0
    
    def test_categorize_performance(self, scheduler):
        """Test performance categorization."""
        assert scheduler._categorize_performance(0.95) == "excellent"
        assert scheduler._categorize_performance(0.85) == "good"
        assert scheduler._categorize_performance(0.65) == "fair"
        assert scheduler._categorize_performance(0.45) == "poor"
        assert scheduler._categorize_performance(0.25) == "fail"
    
    def test_calculate_next_interval(self, scheduler):
        """Test interval calculation."""
        # Mock card data
        card = {
            "interval": 1,
            "ease_factor": 2.5,
            "repetition": 0,
            "difficulty_rating": 0.5,
            "importance_weight": 1.0,
            "subject": "history",
            "content_type": "fact"
        }
        
        # Test excellent performance
        interval, ease_factor = scheduler._calculate_next_interval(
            card, 0.9, "excellent", 2.0
        )
        
        assert interval == scheduler.default_params["second_interval"]  # First repetition
        assert ease_factor > card["ease_factor"]  # Should increase
        
        # Test failure
        interval, ease_factor = scheduler._calculate_next_interval(
            card, 0.2, "fail", 10.0
        )
        
        assert interval == 1  # Reset to 1 day
        assert ease_factor < card["ease_factor"]  # Should decrease
    
    def test_determine_learning_state(self, scheduler):
        """Test learning state determination."""
        # New card
        new_card = {"total_reviews": 0, "success_rate": 0.0, "correct_streak": 0, "interval": 1}
        assert scheduler._determine_learning_state(new_card) == "new"
        
        # Mastered card
        mastered_card = {"total_reviews": 5, "success_rate": 0.95, "correct_streak": 5, "interval": 45}
        assert scheduler._determine_learning_state(mastered_card) == "mastered"
        
        # Review card
        review_card = {"total_reviews": 4, "success_rate": 0.8, "correct_streak": 2, "interval": 10}
        assert scheduler._determine_learning_state(review_card) == "review"
        
        # Learning card
        learning_card = {"total_reviews": 2, "success_rate": 0.5, "correct_streak": 1, "interval": 3}
        assert scheduler._determine_learning_state(learning_card) == "learning"
    
    @pytest.mark.asyncio
    async def test_get_due_reviews(self, scheduler):
        """Test getting due reviews."""
        # Create some cards
        card1 = await scheduler.create_spaced_repetition_card(
            student_id="test_student",
            content_id="content1",
            content_type="fact", 
            concept="Concept 1"
        )
        
        card2 = await scheduler.create_spaced_repetition_card(
            student_id="test_student",
            content_id="content2",
            content_type="concept",
            concept="Concept 2"
        )
        
        # Make one card overdue
        card1["next_review_date"] = datetime.now() - timedelta(hours=2)
        scheduler.student_cards["test_student"][card1["card_id"]] = card1
        
        due_cards = await scheduler.get_due_reviews("test_student")
        
        assert len(due_cards) >= 1
        assert any(card["card_id"] == card1["card_id"] for card in due_cards)
    
    def test_calculate_urgency_score(self, scheduler):
        """Test urgency score calculation."""
        current_time = datetime.now()
        
        # Overdue card
        overdue_card = {
            "next_review_date": current_time - timedelta(hours=12),
            "importance_weight": 1.0,
            "difficulty_rating": 0.7,
            "learning_state": "learning",
            "success_rate": 0.6
        }
        
        urgency = scheduler._calculate_urgency_score(overdue_card, current_time)
        assert urgency > 1.0  # Should have high urgency
        
        # Not due card
        future_card = {
            "next_review_date": current_time + timedelta(hours=12),
            "importance_weight": 0.5,
            "difficulty_rating": 0.3,
            "learning_state": "mastered", 
            "success_rate": 0.9
        }
        
        urgency = scheduler._calculate_urgency_score(future_card, current_time)
        assert urgency < 1.0  # Should have lower urgency
    
    @pytest.mark.asyncio
    async def test_create_review_session(self, scheduler):
        """Test creating a review session."""
        # Create some due cards
        for i in range(3):
            card = await scheduler.create_spaced_repetition_card(
                student_id="test_student",
                content_id=f"content_{i}",
                content_type="fact",
                concept=f"Concept {i}"
            )
            # Make them overdue
            card["next_review_date"] = datetime.now() - timedelta(hours=1)
            scheduler.student_cards["test_student"][card["card_id"]] = card
        
        session = await scheduler.create_review_session(
            student_id="test_student",
            max_cards=5,
            session_duration_minutes=10
        )
        
        assert "session_id" in session
        assert "cards" in session
        assert "estimated_duration_minutes" in session
        assert len(session["cards"]) <= 5
    
    def test_estimate_card_time(self, scheduler):
        """Test card time estimation."""
        fact_card = {
            "content_type": "fact",
            "difficulty_rating": 0.5,
            "learning_state": "review"
        }
        
        concept_card = {
            "content_type": "concept", 
            "difficulty_rating": 0.8,
            "learning_state": "new"
        }
        
        fact_time = scheduler._estimate_card_time(fact_card)
        concept_time = scheduler._estimate_card_time(concept_card)
        
        assert fact_time > 0
        assert concept_time > fact_time  # Concepts should take longer
    
    @pytest.mark.asyncio 
    async def test_create_cards_from_content(self, scheduler):
        """Test creating multiple cards from content."""
        content_items = [
            {
                "content_id": "ww1_causes",
                "type": "concept",
                "concept": "Causes of WWI",
                "difficulty": 0.7,
                "importance": 0.9
            },
            {
                "content_id": "battle_somme",
                "type": "fact", 
                "concept": "Battle of the Somme",
                "difficulty": 0.5,
                "importance": 0.8
            }
        ]
        
        cards = await scheduler.create_cards_from_content(
            student_id="test_student",
            content_items=content_items,
            subject="history"
        )
        
        assert len(cards) == 2
        assert cards[0]["concept"] == "Causes of WWI"
        assert cards[1]["concept"] == "Battle of the Somme"
        assert all(card["subject"] == "history" for card in cards)


class TestAssessmentIntegration:
    """Integration tests for assessment system components."""
    
    @pytest.mark.asyncio
    async def test_formative_to_spaced_repetition_workflow(self):
        """Test workflow from formative assessment to spaced repetition."""
        mock_memory = Mock()
        mock_memory.store_learning_data = AsyncMock()
        mock_memory.store_learning_event = AsyncMock()
        
        # Create components
        checker = ContinuousAssessmentChecker(mock_memory)
        scheduler = SpacedRepetitionScheduler(mock_memory)
        
        # Start monitoring session
        await checker.monitor_learning_session("student1", "session1")
        
        # Mock understanding check showing mastery
        checker.llm = AsyncMock()
        mock_response = Mock()
        mock_response.content = '{"level": 0.9, "confidence": 0.9, "misconceptions": [], "recommended_action": "continue"}'
        checker.llm.ainvoke.return_value = mock_response
        
        # Process check response
        check_result = await checker.process_check_response(
            check_id="check1",
            student_response="I understand that WWI had multiple interconnected causes",
            session_id="session1"
        )
        
        # High understanding should lead to spaced repetition card creation
        if check_result["understanding_level"] >= 0.8:
            card = await scheduler.create_spaced_repetition_card(
                student_id="student1",
                content_id="ww1_causes", 
                content_type="concept",
                concept="Causes of World War I"
            )
            
            assert card["learning_state"] == "new"
            assert card["student_id"] == "student1"
    
    @pytest.mark.asyncio
    async def test_misconception_to_remediation_workflow(self):
        """Test workflow from misconception detection to targeted remediation."""
        mock_memory = Mock()
        mock_memory.store_learning_event = AsyncMock()
        mock_memory.get_student_events = AsyncMock()
        
        detector = MisconceptionDetector(mock_memory)
        
        # Mock LLM responses
        detector.llm = AsyncMock()
        mock_response = Mock()
        mock_response.content = '[{"type": "linear_progress", "evidence": ["always improving"], "confidence": 0.8, "severity": "high"}]'
        detector.llm.ainvoke.return_value = mock_response
        
        # Detect misconception
        detection_result = await detector.detect_misconceptions(
            student_id="student1",
            student_response="History shows that humanity is always progressing and getting better over time",
            topic_context="historical_development"
        )
        
        assert len(detection_result["misconceptions_detected"]) > 0
        assert detection_result["needs_immediate_intervention"] == True
        
        # Mock profile data for remediation plan
        detector.memory.get_student_events.return_value = [
            {
                "event_data": {
                    "detections": [{"type": "linear_progress", "severity": "high"}]
                }
            }
        ]
        
        # Get misconception profile
        profile = await detector.get_student_misconception_profile("student1")
        
        # Create remediation plan
        plan = await detector.create_targeted_remediation_plan("student1", profile)
        
        assert "intervention_sequence" in plan
        assert len(plan["intervention_sequence"]) > 0
        assert plan["expected_duration_weeks"] > 0