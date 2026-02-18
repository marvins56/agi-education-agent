"""User LLM provider settings models."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from src.models.database import Base


class UserLLMSettings(Base):
    """Store user-specific LLM provider configurations."""
    
    __tablename__ = "user_llm_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Preferred provider and model
    preferred_provider = Column(String(50), default="ollama")  # ollama, anthropic, openai, google, groq
    preferred_model = Column(String(100), nullable=True)
    
    # Encrypted API keys (use application-level encryption)
    anthropic_api_key_encrypted = Column(Text, nullable=True)
    openai_api_key_encrypted = Column(Text, nullable=True) 
    google_api_key_encrypted = Column(Text, nullable=True)
    groq_api_key_encrypted = Column(Text, nullable=True)
    
    # Settings
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    user = relationship("User", backref="llm_settings")