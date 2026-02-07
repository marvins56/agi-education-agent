from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "EduAGI"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://eduagi:eduagi_dev@localhost:5433/eduagi"
    REDIS_URL: str = "redis://localhost:6380/0"
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8100

    # AI/LLM
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    DEFAULT_MODEL: str = "claude-sonnet-4-5-20250929"

    # Voice (optional)
    ELEVENLABS_API_KEY: str = ""

    # Security
    JWT_SECRET: str = "change-me-jwt"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
