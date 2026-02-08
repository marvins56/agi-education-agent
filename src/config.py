import secrets

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "EduAGI"
    DEBUG: bool = False
    TESTING: bool = False
    SECRET_KEY: str = "change-me"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://eduagi:eduagi_dev@localhost:5433/eduagi"
    REDIS_URL: str = "redis://localhost:6380/0"
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8100

    # AI/LLM
    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    DEFAULT_MODEL: str = "claude-sonnet-4-5-20250929"

    # Voice (optional)
    ELEVENLABS_API_KEY: str = ""

    # Security
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()

# C6 fix: Reject predictable JWT secrets in non-debug mode; auto-generate for dev/test
_INSECURE_SECRETS = {"change-me-jwt", "change-me", "secret", ""}
if settings.JWT_SECRET in _INSECURE_SECRETS:
    if not settings.DEBUG and not settings.TESTING:
        raise RuntimeError(
            "CRITICAL: JWT_SECRET is not set or uses a default value. "
            "Set a strong JWT_SECRET (32+ characters) via environment variable or .env file."
        )
    # In debug/test mode, generate a random secret so tokens are unpredictable
    settings.JWT_SECRET = secrets.token_urlsafe(32)
