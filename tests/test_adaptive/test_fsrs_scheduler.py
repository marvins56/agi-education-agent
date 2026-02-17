"""Tests for FSRS scheduler."""
import pytest
from datetime import datetime, timedelta

from src.adaptive.fsrs.scheduler import FSRSScheduler, FSRSParameters
from src.adaptive.schemas import FSRSCard


@pytest.fixture
def scheduler():
    """Create FSRS scheduler for testing."""
    return FSRSScheduler(FSRSParameters())


@pytest.fixture
def sample_card():
    """Create a sample FSRS card for testing."""
    return FSRSCard(
        concept_id=1,
        concept_name="World War I Causes",
        student_id="test_student",
        stability=1.0,
        difficulty=5.0,
        retrievability=1.0,
        due_date=datetime.now(),
        review_count=0
    )


def test_schedule_first_review_good(scheduler, sample_card):
    """Test scheduling first review with good rating."""
    now = datetime.now()
    
    # Schedule with rating 3 (good)
    updated_card = scheduler.schedule_review(sample_card, rating=3, now=now)
    
    assert updated_card.review_count == 1
    assert updated_card.last_review == now
    assert updated_card.due_date > now
    assert updated_card.success_rate > 0


def test_schedule_first_review_again(scheduler, sample_card):
    """Test scheduling first review with again rating."""
    now = datetime.now()
    
    # Schedule with rating 1 (again)
    updated_card = scheduler.schedule_review(sample_card, rating=1, now=now)
    
    assert updated_card.review_count == 1
    assert updated_card.consecutive_successes == 0
    
    # Should have short interval
    days_until_due = (updated_card.due_date - now).total_seconds() / 86400
    assert days_until_due < 2  # Less than 2 days for "again"


def test_schedule_multiple_reviews(scheduler, sample_card):
    """Test scheduling multiple reviews."""
    now = datetime.now()
    
    # First review - good
    card1 = scheduler.schedule_review(sample_card, rating=3, now=now)
    assert card1.review_count == 1
    
    # Second review - good again
    card2 = scheduler.schedule_review(card1, rating=3, now=now + timedelta(days=1))
    assert card2.review_count == 2
    assert card2.consecutive_successes == 2
    
    # Interval should increase
    first_interval = (card1.due_date - now).total_seconds() / 86400
    second_interval = (card2.due_date - (now + timedelta(days=1))).total_seconds() / 86400
    assert second_interval > first_interval


def test_get_due_cards(scheduler):
    """Test getting cards due for review."""
    now = datetime.now()
    
    # Create cards with different due dates
    cards = [
        FSRSCard(
            concept_id=1,
            concept_name="Concept 1",
            student_id="test",
            stability=1.0,
            difficulty=5.0,
            retrievability=1.0,
            due_date=now - timedelta(days=1),  # Overdue
            review_count=1
        ),
        FSRSCard(
            concept_id=2,
            concept_name="Concept 2", 
            student_id="test",
            stability=1.0,
            difficulty=5.0,
            retrievability=1.0,
            due_date=now + timedelta(hours=1),  # Not due yet
            review_count=1
        ),
        FSRSCard(
            concept_id=3,
            concept_name="Concept 3",
            student_id="test", 
            stability=1.0,
            difficulty=5.0,
            retrievability=1.0,
            due_date=now,  # Due now
            review_count=1
        )
    ]
    
    due_cards = scheduler.get_due_cards(cards, now=now)
    
    assert len(due_cards) == 2  # Only overdue and due-now cards
    assert due_cards[0].concept_name == "Concept 1"  # Overdue first
    assert due_cards[1].concept_name == "Concept 3"  # Then due-now


def test_optimize_study_session(scheduler):
    """Test optimizing cards for study session."""
    now = datetime.now()
    
    # Create many due cards
    cards = []
    for i in range(20):
        cards.append(FSRSCard(
            concept_id=i,
            concept_name=f"Concept {i}",
            student_id="test",
            stability=1.0,
            difficulty=5.0,
            retrievability=1.0,
            due_date=now - timedelta(minutes=i),  # All overdue
            review_count=1
        ))
    
    # 30-minute session should select reasonable number of cards
    selected_cards = scheduler.optimize_study_session(cards, session_duration_minutes=30)
    
    # Should select around 12 cards (30 min / 2.5 min per card)
    assert 10 <= len(selected_cards) <= 15
    
    # Should prioritize most overdue
    assert selected_cards[0].concept_name == "Concept 19"


def test_history_concept_classification(scheduler):
    """Test History-specific concept classification."""
    
    # Test political concept
    political_concept = "French Revolution Politics"
    concept_type = scheduler._classify_history_concept(political_concept)
    assert concept_type == "political_causes"
    
    # Test economic concept
    economic_concept = "Industrial Revolution Economy"
    concept_type = scheduler._classify_history_concept(economic_concept)
    assert concept_type == "economic_factors"
    
    # Test date concept
    date_concept = "World War I 1914-1918"
    concept_type = scheduler._classify_history_concept(date_concept)
    assert concept_type == "dates_specific"


def test_retrievability_calculation(scheduler):
    """Test retrievability calculation based on forgetting curve."""
    
    # Just reviewed - should be high
    retrievability = scheduler._calculate_retrievability(stability=10.0, elapsed_days=0)
    assert retrievability == 1.0
    
    # After some time - should decrease
    retrievability = scheduler._calculate_retrievability(stability=10.0, elapsed_days=5)
    assert 0.5 < retrievability < 1.0
    
    # After long time - should be low but not zero
    retrievability = scheduler._calculate_retrievability(stability=1.0, elapsed_days=30)
    assert 0.01 <= retrievability < 0.5


def test_difficulty_update(scheduler):
    """Test difficulty update based on performance."""
    
    initial_difficulty = 5.0
    
    # Good performance should decrease difficulty
    updated_difficulty = scheduler._update_difficulty(initial_difficulty, rating=3)
    assert updated_difficulty < initial_difficulty
    
    # Poor performance should increase difficulty
    updated_difficulty = scheduler._update_difficulty(initial_difficulty, rating=1)
    assert updated_difficulty > initial_difficulty
    
    # Difficulty should stay within bounds
    extreme_difficulty = 9.5
    bounded_difficulty = scheduler._update_difficulty(extreme_difficulty, rating=1)
    assert bounded_difficulty <= 10.0
    
    low_difficulty = 0.5
    bounded_difficulty = scheduler._update_difficulty(low_difficulty, rating=4)
    assert bounded_difficulty >= 1.0