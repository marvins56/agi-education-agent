"""FastAPI application with lifespan management."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.memory.manager import MemoryManager
from src.models.database import async_session, close_db
from src.rag.retriever import KnowledgeRetriever
from src.agents.orchestrator import MasterOrchestrator


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    memory = MemoryManager(
        redis_url=settings.REDIS_URL,
        db_session_factory=async_session,
    )
    await memory.initialize()
    app.state.memory_manager = memory

    retriever = KnowledgeRetriever(
        chroma_host=settings.CHROMA_HOST,
        chroma_port=settings.CHROMA_PORT,
    )
    try:
        await retriever.initialize()
    except Exception:
        pass  # ChromaDB may not be available in dev/test
    app.state.retriever = retriever

    orchestrator = MasterOrchestrator(
        memory_manager=memory,
        retriever=retriever,
    )
    await orchestrator.initialize()
    app.state.orchestrator = orchestrator

    yield

    # Shutdown
    await orchestrator.close()
    await memory.close()
    retriever.close()
    await close_db()


app = FastAPI(
    title="EduAGI API",
    description="Self-Learning Educational AI Agent",
    version="1.0.0",
    lifespan=lifespan,
)

# Import and include routers
from src.api.routers import auth, chat, content, health, models, profile, sessions, analytics, learning_path, assessments  # noqa: E402
from src.api.middleware.request_id import RequestIDMiddleware  # noqa: E402
from src.api.middleware.rate_limit import RateLimiter, RateLimitMiddleware  # noqa: E402

# Middleware order: added last = runs first (outermost).
# CORS must be outermost so it handles preflight and adds headers to all responses.
app.add_middleware(RequestIDMiddleware)

# C5 fix: Register rate limit middleware
_rate_limiter = RateLimiter(redis_url=settings.REDIS_URL)
app.add_middleware(RateLimitMiddleware, rate_limiter=_rate_limiter)

# CORS added last = outermost middleware = always runs first
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(content.router, prefix="/api/v1/content", tags=["Content"])
app.include_router(profile.router, prefix="/api/v1", tags=["Profile"])
app.include_router(sessions.router, prefix="/api/v1", tags=["Sessions"])
app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])
app.include_router(learning_path.router, prefix="/api/v1", tags=["Learning Path"])
app.include_router(assessments.router, prefix="/api/v1/assessments", tags=["Assessments"])
app.include_router(models.router, prefix="/api/v1", tags=["Models"])
