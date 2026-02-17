"""Tests for rule-based BKT predictor."""
import pytest
from datetime import datetime, timedelta

from src.adaptive.dkt.predictor import RuleBasedBKTPredictor
from src.adaptive.schemas import StudentInteraction


@pytest.fixture
def predictor():
    """Create BKT predictor for testing."""
    return RuleBasedBKTPredictor()


@pytest.fixture
def sample_interactions():
    """Create sample student interactions for testing."""
    base_time = datetime.now()
    return [
        StudentInteraction(
            student_id="test_student",
            session_id="session_1",
            concept_id=1,
            concept_name="World War I Causes",
            question_type="multiple_choice",
            correctness=0.8,
            response_time_seconds=15.0,
            hint_count=0,
            difficulty_level=0.5,
            context_features={},
            timestamp=base_time
        ),
        StudentInteraction(
            student_id="test_student", 
            session_id="session_1",
            concept_id=1,
            concept_name="World War I Causes",
            question_type="multiple_choice",
            correctness=0.6,
            response_time_seconds=25.0,
            hint_count=1,
            difficulty_level=0.6,
            context_features={},
            timestamp=base_time + timedelta(minutes=5)
        ),
        StudentInteraction(
            student_id="test_student",
            session_id="session_1", 
            concept_id=1,
            concept_name="World War I Causes",
            question_type="essay",
            correctness=0.9,
            response_time_seconds=45.0,
            hint_count=0,
            difficulty_level=0.7,
            context_features={},
            timestamp=base_time + timedelta(minutes=10)
        )
    ]


def test_predict_mastery_single_concept(predictor, sample_interactions):
    """Test mastery prediction for single concept."""
    
    masteries = await predictor.predict_mastery("test_student", sample_interactions)
    
    assert "World War I Causes" in masteries
    mastery = masteries["World War I Causes"]
    
    # Mastery should be reasonable (between 0 and 1)
    assert 0.0 <= mastery <= 1.0
    
    # With mixed performance, should be moderate
    assert 0.3 <= mastery <= 0.8


def test_predict_mastery_multiple_concepts(predictor):
    """Test mastery prediction for multiple concepts."""
    
    interactions = [
        StudentInteraction(
            student_id="test_student",
            session_id="session_1",
            concept_id=1,
            concept_name="WWI Causes",
            question_type="multiple_choice",
            correctness=0.9,
            response_time_seconds=10.0,
            hint_count=0,
            difficulty_level=0.5,
            context_features={},
            timestamp=datetime.now()
        ),
        StudentInteraction(
            student_id="test_student",
            session_id="session_1", 
            concept_id=2,
            concept_name="WWII Causes",
            question_type="multiple_choice",
            correctness=0.2,
            response_time_seconds=30.0,
            hint_count=3,
            difficulty_level=0.7,
            context_features={},
            timestamp=datetime.now() + timedelta(minutes=5)
        )
    ]
    
    masteries = await predictor.predict_mastery("test_student", interactions)
    
    assert len(masteries) == 2
    assert "WWI Causes" in masteries
    assert "WWII Causes" in masteries
    
    # Good performance concept should have higher mastery
    assert masteries["WWI Causes"] > masteries["WWII Causes"]


def test_concept_classification(predictor):
    """Test concept type classification."""
    
    # Test date concept classification
    date_concept = "World War I 1914-1918"
    concept_type = predictor._classify_concept(date_concept)
    assert concept_type == "dates_specific"
    
    # Test causal concept
    causal_concept = "Causes of French Revolution"
    concept_type = predictor._classify_concept(causal_concept)
    assert concept_type == "causal_relationships"
    
    # Test political concept
    political_concept = "Roman Empire Government"
    concept_type = predictor._classify_concept(political_concept)
    assert concept_type == "political_concepts"
    
    # Test social concept
    social_concept = "Medieval Society Culture"
    concept_type = predictor._classify_concept(social_concept)
    assert concept_type == "social_cultural"


def test_concept_specific_parameters(predictor):
    """Test that different concept types get different parameters."""
    
    date_params = predictor._get_concept_params("World War I 1914")
    causal_params = predictor._get_concept_params("Causes of WWI")
    
    # Date concepts should have different parameters than causal
    assert date_params["learning_rate"] != causal_params["learning_rate"]
    assert date_params["prior_knowledge"] != causal_params["prior_knowledge"]


def test_forgetting_curve(predictor):
    """Test forgetting curve application."""
    
    base_mastery = 0.8
    
    # No time passed - no forgetting
    current_mastery = predictor._apply_forgetting(base_mastery, datetime.now())
    assert current_mastery == base_mastery
    
    # Some time passed - should decrease
    old_time = datetime.now() - timedelta(days=7)
    decayed_mastery = predictor._apply_forgetting(base_mastery, old_time)
    assert decayed_mastery < base_mastery
    
    # Long time passed - should decay significantly
    very_old_time = datetime.now() - timedelta(days=30)
    highly_decayed = predictor._apply_forgetting(base_mastery, very_old_time)
    assert highly_decayed < decayed_mastery
    
    # Should not decay below minimum
    assert highly_decayed >= predictor.forgetting_params["minimum_retention"]


def test_learning_rate_adjustment(predictor):
    """Test learning rate adjustment based on interaction context."""
    
    base_learning_rate = 0.3
    
    # Easy question - lower adjustment
    easy_interaction = StudentInteraction(
        student_id="test",
        session_id="session",
        concept_id=1,
        concept_name="Test Concept",
        question_type="multiple_choice",
        correctness=0.8,
        response_time_seconds=5.0,  # Very quick
        hint_count=0,
        difficulty_level=0.3,  # Easy
        context_features={},
        timestamp=datetime.now()
    )
    
    adjusted_rate = predictor._adjust_learning_rate(base_learning_rate, easy_interaction)
    # Quick response should reduce learning rate
    assert adjusted_rate < base_learning_rate
    
    # Hard question with hints
    hard_interaction = StudentInteraction(
        student_id="test",
        session_id="session",
        concept_id=1, 
        concept_name="Test Concept",
        question_type="essay",
        correctness=0.6,
        response_time_seconds=40.0,
        hint_count=2,  # Used hints
        difficulty_level=0.8,  # Hard
        context_features={},
        timestamp=datetime.now()
    )
    
    adjusted_rate = predictor._adjust_learning_rate(base_learning_rate, hard_interaction)
    # Hard question increases learning, but hints reduce it
    # Net effect depends on the specific adjustments


def test_predict_performance(predictor):
    """Test performance prediction for future questions."""
    
    concept_name = "Test Concept"
    current_mastery = 0.7
    question_difficulty = 0.5
    
    prob_correct, metrics = predictor.predict_performance(
        concept_name, current_mastery, question_difficulty
    )
    
    # Probability should be reasonable
    assert 0.0 <= prob_correct <= 1.0
    
    # Should have required metrics
    assert "expected_correctness" in metrics
    assert "confidence_interval_lower" in metrics
    assert "confidence_interval_upper" in metrics
    assert "mastery_probability" in metrics
    
    # Higher mastery should lead to higher expected performance
    high_mastery_prob, _ = predictor.predict_performance(concept_name, 0.9, 0.5)
    low_mastery_prob, _ = predictor.predict_performance(concept_name, 0.3, 0.5)
    
    assert high_mastery_prob > low_mastery_prob


def test_learning_trajectory(predictor):
    """Test learning trajectory calculation."""
    
    interactions = [
        StudentInteraction(
            student_id="test",
            session_id="session",
            concept_id=1,
            concept_name="Test Concept",
            question_type="multiple_choice",
            correctness=0.4,
            response_time_seconds=20.0,
            hint_count=1,
            difficulty_level=0.5,
            context_features={},
            timestamp=datetime.now() - timedelta(hours=2)
        ),
        StudentInteraction(
            student_id="test",
            session_id="session",
            concept_id=1,
            concept_name="Test Concept", 
            question_type="multiple_choice",
            correctness=0.7,
            response_time_seconds=15.0,
            hint_count=0,
            difficulty_level=0.5,
            context_features={},
            timestamp=datetime.now() - timedelta(hours=1)
        ),
        StudentInteraction(
            student_id="test",
            session_id="session",
            concept_id=1,
            concept_name="Test Concept",
            question_type="multiple_choice", 
            correctness=0.9,
            response_time_seconds=12.0,
            hint_count=0,
            difficulty_level=0.5,
            context_features={},
            timestamp=datetime.now()
        )
    ]
    
    trajectory = predictor.get_learning_trajectory("Test Concept", interactions)
    
    # Should have entry for each interaction plus initial
    assert len(trajectory) == len(interactions) + 1
    
    # Mastery should generally increase (with good performance)
    timestamps, masteries = zip(*trajectory)
    
    # Later masteries should generally be higher than earlier ones
    assert masteries[-1] > masteries[0]


def test_plateau_detection(predictor):
    """Test learning plateau detection."""
    
    # Create interactions showing plateau
    base_time = datetime.now() - timedelta(hours=10)
    plateau_interactions = []
    
    # First show improvement
    for i in range(5):
        plateau_interactions.append(StudentInteraction(
            student_id="test",
            session_id="session",
            concept_id=1,
            concept_name="Test Concept",
            question_type="multiple_choice",
            correctness=0.4 + i * 0.1,  # Improving
            response_time_seconds=20.0,
            hint_count=0,
            difficulty_level=0.5,
            context_features={},
            timestamp=base_time + timedelta(hours=i)
        ))
    
    # Then plateau
    for i in range(5, 15):
        plateau_interactions.append(StudentInteraction(
            student_id="test",
            session_id="session",
            concept_id=1,
            concept_name="Test Concept",
            question_type="multiple_choice",
            correctness=0.75,  # Plateau at 75%
            response_time_seconds=20.0,
            hint_count=0,
            difficulty_level=0.5,
            context_features={},
            timestamp=base_time + timedelta(hours=i)
        ))
    
    is_plateau = predictor.detect_learning_plateau("Test Concept", plateau_interactions)
    assert is_plateau
    
    # Test with insufficient data
    short_interactions = plateau_interactions[:8]
    is_plateau_short = predictor.detect_learning_plateau("Test Concept", short_interactions)
    assert not is_plateau_short  # Not enough data to detect plateau