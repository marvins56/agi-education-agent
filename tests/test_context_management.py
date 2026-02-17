"""Tests for the context management system."""
import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock

from src.context.schemas import (
    AnnotatedMessage, 
    MessageAnnotation, 
    SummaryType,
    TutoringContext,
    ContextTier
)
from src.context.manager import ContextManager
from src.context.summarizer import EducationalSummarizer
from src.context.window import SlidingContextWindow


@pytest.fixture
def mock_memory_manager():
    """Mock memory manager for testing."""
    mock_memory = Mock()
    mock_memory._redis = AsyncMock()
    mock_memory.get_session_context = AsyncMock(return_value={
        "student_id": "test_student_123",
        "session_start": datetime.now(timezone.utc).isoformat()
    })
    mock_memory.get_student_mastery = AsyncMock(return_value=[
        {"topic": "american_revolution", "mastery_score": 0.8},
        {"topic": "civil_war", "mastery_score": 0.6}
    ])
    return mock_memory


@pytest.fixture
def context_manager(mock_memory_manager):
    """Create context manager with mocked dependencies."""
    return ContextManager(mock_memory_manager)


@pytest.mark.asyncio
async def test_annotated_message_creation():
    """Test creating annotated messages."""
    annotation = MessageAnnotation(
        type="confusion",
        confidence=0.8,
        concepts=["photosynthesis"],
        timestamp=datetime.now(timezone.utc)
    )
    
    message = AnnotatedMessage(
        role="user",
        content="I don't understand how plants make food",
        timestamp=datetime.now(timezone.utc),
        token_count=10,
        annotations=[annotation]
    )
    
    assert message.role == "user"
    assert message.token_count == 10
    assert len(message.annotations) == 1
    assert message.annotations[0].type == "confusion"


@pytest.mark.asyncio
async def test_tutoring_context_token_estimation():
    """Test token estimation for tutoring context."""
    # Create sample messages
    message1 = AnnotatedMessage(
        role="user",
        content="What is photosynthesis?",
        timestamp=datetime.now(timezone.utc),
        token_count=5
    )
    
    message2 = AnnotatedMessage(
        role="assistant", 
        content="Photosynthesis is the process by which plants convert sunlight into energy.",
        timestamp=datetime.now(timezone.utc),
        token_count=15
    )
    
    context = TutoringContext(
        session_id="test_session",
        student_id="test_student",
        active_messages=[message1, message2],
        topic_mastery={"photosynthesis": 0.7, "respiration": 0.5}
    )
    
    estimated_tokens = context.estimate_tokens()
    
    # Should be: 20 (messages) + 0 (summaries) + 40 (2 concepts * 20)
    assert estimated_tokens == 60


@pytest.mark.asyncio
async def test_sliding_window_educational_importance():
    """Test educational importance scoring in sliding window."""
    window = SlidingContextWindow()
    
    # Message with breakthrough annotation (high importance)
    breakthrough_annotation = MessageAnnotation(
        type="breakthrough",
        confidence=0.9,
        concepts=["photosynthesis"],
        timestamp=datetime.now(timezone.utc)
    )
    
    important_message = AnnotatedMessage(
        role="user",
        content="Oh I see! So plants are like solar panels that convert light to chemical energy!",
        timestamp=datetime.now(timezone.utc),
        token_count=15,
        annotations=[breakthrough_annotation]
    )
    
    # Regular message (lower importance)
    regular_message = AnnotatedMessage(
        role="user",
        content="OK",
        timestamp=datetime.now(timezone.utc),
        token_count=2,
        annotations=[]
    )
    
    # Test importance scoring
    important_score = await window._calculate_educational_importance(important_message)
    regular_score = await window._calculate_educational_importance(regular_message)
    
    assert important_score > regular_score
    assert important_score > 2.0  # Should get boost from breakthrough annotation


@pytest.mark.asyncio  
async def test_context_manager_add_message(context_manager, mock_memory_manager):
    """Test adding messages to context manager."""
    session_id = "test_session_123"
    
    # Mock Redis operations
    mock_memory_manager._redis.rpush = AsyncMock()
    mock_memory_manager._redis.ltrim = AsyncMock()
    mock_memory_manager._redis.expire = AsyncMock()
    mock_memory_manager._redis.lrange = AsyncMock(return_value=[])
    mock_memory_manager._redis.llen = AsyncMock(return_value=5)
    
    # Add message
    await context_manager.add_message_with_annotation(
        session_id=session_id,
        role="user", 
        content="What is the capital of France?",
        annotations=[]
    )
    
    # Verify Redis operations were called
    mock_memory_manager._redis.rpush.assert_called_once()
    mock_memory_manager._redis.ltrim.assert_called_once()
    mock_memory_manager._redis.expire.assert_called_once()


@pytest.mark.asyncio
async def test_educational_summarizer_empty_summary():
    """Test educational summarizer with empty messages."""
    summarizer = EducationalSummarizer()
    
    summary = await summarizer.create_educational_summary(
        messages=[],
        session_id="test_session",
        student_id="test_student",
        summary_type=SummaryType.PROGRESS
    )
    
    assert summary.session_id == "test_session"
    assert summary.student_id == "test_student"
    assert summary.summary_type == SummaryType.PROGRESS
    assert summary.message_count == 0
    assert summary.student_engagement_level == 0.0


def test_context_tier_enum():
    """Test context tier enumeration."""
    assert ContextTier.ACTIVE.value == "active"
    assert ContextTier.SESSION.value == "session"
    assert ContextTier.TOPIC.value == "topic"


def test_summary_type_enum():
    """Test summary type enumeration."""
    assert SummaryType.PROGRESS.value == "progress"
    assert SummaryType.CONCEPTUAL.value == "conceptual"
    assert SummaryType.STRATEGIC.value == "strategic"
    assert SummaryType.SESSION_END.value == "session_end"


@pytest.mark.asyncio
async def test_context_manager_build_context(context_manager, mock_memory_manager):
    """Test building complete tutoring context."""
    session_id = "test_session_123"
    
    # Mock active messages
    sample_message_data = {
        "role": "user",
        "content": "What is photosynthesis?",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "token_count": 5,
        "annotations": []
    }
    
    mock_memory_manager._redis.lrange = AsyncMock(return_value=[
        '{"role": "user", "content": "What is photosynthesis?", "timestamp": "2026-02-17T14:30:00Z", "token_count": 5, "annotations": []}'
    ])
    
    # Build context
    context = await context_manager.get_tutoring_context(session_id)
    
    assert context.session_id == session_id
    assert context.student_id == "test_student_123"
    assert len(context.active_messages) == 1
    assert context.active_messages[0].content == "What is photosynthesis?"
    assert "american_revolution" in context.topic_mastery
    assert context.topic_mastery["american_revolution"] == 0.8


if __name__ == "__main__":
    # Run tests
    asyncio.run(pytest.main([__file__, "-v"]))