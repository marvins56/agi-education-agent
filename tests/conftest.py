"""Shared test fixtures."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.agents.base import AgentResponse
from src.agents.orchestrator import MasterOrchestrator
from src.memory.manager import MemoryManager
from src.models.user import User


@pytest.fixture
def sample_user():
    """Create a sample user object for testing."""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.name = "Test Student"
    user.role = "student"
    user.is_active = True
    user.created_at = datetime.now(timezone.utc)
    user.profile = MagicMock()
    user.profile.learning_style = "visual"
    user.profile.pace = "moderate"
    user.profile.grade_level = "high_school"
    user.profile.strengths = ["math"]
    user.profile.weaknesses = ["writing"]
    return user


@pytest.fixture
def mock_memory():
    """Create a mock MemoryManager."""
    memory = AsyncMock(spec=MemoryManager)
    memory.get_session_context = AsyncMock(return_value={
        "session_id": "test-session-id",
        "student_id": "test-user-id",
        "student_profile": {"learning_style": "visual", "name": "Test"},
        "conversation_history": [],
        "current_subject": None,
        "current_topic": None,
        "learning_objectives": [],
    })
    memory.add_to_conversation = AsyncMock()
    memory.get_conversation_history = AsyncMock(return_value=[])
    memory.set_session_context = AsyncMock()
    memory.save_learning_event = AsyncMock()
    return memory


@pytest.fixture
def mock_orchestrator():
    """Create a mock MasterOrchestrator."""
    orchestrator = AsyncMock(spec=MasterOrchestrator)
    orchestrator.process = AsyncMock(return_value=AgentResponse(
        text="This is a test response from the tutor.",
        agent_name="tutor",
        processing_time=0.5,
    ))
    return orchestrator


@pytest.fixture
async def test_client(sample_user, mock_memory, mock_orchestrator):
    """Create a test client with mocked dependencies."""
    from src.api.dependencies import get_current_user, get_db, get_memory, get_orchestrator

    # Import app without triggering lifespan
    with patch("src.api.main.lifespan") as mock_lifespan:
        # Create a no-op lifespan
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def noop_lifespan(app):
            app.state.memory_manager = mock_memory
            app.state.orchestrator = mock_orchestrator
            app.state.retriever = MagicMock()
            yield

        mock_lifespan.side_effect = noop_lifespan

        # Re-import to get the patched app
        import importlib
        import src.api.main
        importlib.reload(src.api.main)
        app = src.api.main.app

    # Override dependencies
    async def override_get_current_user():
        return sample_user

    async def override_get_db():
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        yield mock_session

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_memory] = lambda: mock_memory
    app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
