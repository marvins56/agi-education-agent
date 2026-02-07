"""Dependency injection functions for FastAPI."""

from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.orchestrator import MasterOrchestrator
from src.auth.security import verify_token
from src.memory.manager import MemoryManager
from src.models.database import async_session
from src.models.user import User
from src.rag.retriever import KnowledgeRetriever

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_memory(request: Request) -> MemoryManager:
    """Get the MemoryManager from app state."""
    return request.app.state.memory_manager


def get_orchestrator(request: Request) -> MasterOrchestrator:
    """Get the MasterOrchestrator from app state."""
    return request.app.state.orchestrator


def get_retriever(request: Request) -> KnowledgeRetriever:
    """Get the KnowledgeRetriever from app state."""
    return request.app.state.retriever


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Verify JWT and return the current user."""
    payload = verify_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return user
