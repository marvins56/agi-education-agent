"""API endpoints for user LLM configuration."""

from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.models.database import get_db
from src.models.llm_settings import UserLLMSettings
from src.models.user import User
from src.utils.encryption import api_key_encryption

router = APIRouter(prefix="/models", tags=["LLM Configuration"])


class ProviderConfigRequest(BaseModel):
    """Request model for configuring user's LLM provider."""
    preferred_provider: str = Field(..., pattern="^(ollama|anthropic|openai|google|groq)$")
    preferred_model: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None


class ProviderInfo(BaseModel):
    """Information about an LLM provider."""
    name: str
    display_name: str
    requires_api_key: bool
    default_model: str
    available_models: List[str]
    description: str


class UserProviderStatus(BaseModel):
    """User's current provider configuration status."""
    preferred_provider: str
    preferred_model: Optional[str]
    has_anthropic_key: bool
    has_openai_key: bool
    has_google_key: bool
    has_groq_key: bool
    configured_providers: List[str]


@router.get("/providers", response_model=List[ProviderInfo])
async def list_providers():
    """List all available LLM providers and their information."""
    providers = [
        ProviderInfo(
            name="ollama",
            display_name="Ollama (Local)",
            requires_api_key=False,
            default_model="qwen2.5:3b",
            available_models=["qwen2.5:3b", "llama3.2:3b", "mistral:7b"],
            description="Local LLM inference. Free but requires local setup."
        ),
        ProviderInfo(
            name="anthropic",
            display_name="Anthropic Claude",
            requires_api_key=True,
            default_model="claude-3-5-sonnet-20241022",
            available_models=[
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022",
                "claude-3-opus-20240229"
            ],
            description="Anthropic's Claude models. High quality, good for reasoning."
        ),
        ProviderInfo(
            name="openai",
            display_name="OpenAI GPT",
            requires_api_key=True,
            default_model="gpt-4o-mini",
            available_models=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
            description="OpenAI's GPT models. Well-rounded, widely compatible."
        ),
        ProviderInfo(
            name="google",
            display_name="Google Gemini",
            requires_api_key=True,
            default_model="gemini-1.5-flash",
            available_models=["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"],
            description="Google's Gemini models. Strong multimodal capabilities."
        ),
        ProviderInfo(
            name="groq",
            display_name="Groq (Fast)",
            requires_api_key=True,
            default_model="llama-3.1-8b-instant",
            available_models=[
                "llama-3.1-8b-instant",
                "llama-3.1-70b-versatile",
                "mixtral-8x7b-32768",
                "gemma2-9b-it"
            ],
            description="Groq's fast inference. Great speed, generous free tier."
        ),
    ]
    return providers


@router.get("/status", response_model=UserProviderStatus)
async def get_user_provider_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's current LLM provider configuration."""
    # Fetch user settings
    result = await db.execute(
        select(UserLLMSettings).where(UserLLMSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Return defaults
        return UserProviderStatus(
            preferred_provider="ollama",
            preferred_model=None,
            has_anthropic_key=False,
            has_openai_key=False,
            has_google_key=False,
            has_groq_key=False,
            configured_providers=["ollama"],
        )
    
    # Check which providers have API keys
    configured_providers = ["ollama"]  # Always available
    has_keys = {}
    
    for provider in ["anthropic", "openai", "google", "groq"]:
        encrypted_key = getattr(settings, f"{provider}_api_key_encrypted", None)
        has_key = bool(encrypted_key and api_key_encryption.decrypt(encrypted_key))
        has_keys[f"has_{provider}_key"] = has_key
        if has_key:
            configured_providers.append(provider)
    
    return UserProviderStatus(
        preferred_provider=settings.preferred_provider,
        preferred_model=settings.preferred_model,
        configured_providers=configured_providers,
        **has_keys,
    )


@router.post("/configure")
async def configure_provider(
    config: ProviderConfigRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Configure user's preferred LLM provider and API keys."""
    # Fetch or create user settings
    result = await db.execute(
        select(UserLLMSettings).where(UserLLMSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = UserLLMSettings(user_id=current_user.id)
        db.add(settings)
    
    # Update basic settings
    settings.preferred_provider = config.preferred_provider
    if config.preferred_model:
        settings.preferred_model = config.preferred_model
    
    # Encrypt and store API keys
    if config.anthropic_api_key:
        settings.anthropic_api_key_encrypted = api_key_encryption.encrypt(
            config.anthropic_api_key
        )
    if config.openai_api_key:
        settings.openai_api_key_encrypted = api_key_encryption.encrypt(
            config.openai_api_key
        )
    if config.google_api_key:
        settings.google_api_key_encrypted = api_key_encryption.encrypt(
            config.google_api_key
        )
    if config.groq_api_key:
        settings.groq_api_key_encrypted = api_key_encryption.encrypt(
            config.groq_api_key
        )
    
    await db.commit()
    
    return {
        "message": "LLM provider configuration updated successfully",
        "preferred_provider": settings.preferred_provider,
        "preferred_model": settings.preferred_model,
    }


@router.delete("/api-key/{provider}")
async def delete_api_key(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a specific provider's API key."""
    if provider not in ["anthropic", "openai", "google", "groq"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider"
        )
    
    # Fetch user settings
    result = await db.execute(
        select(UserLLMSettings).where(UserLLMSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No LLM settings found"
        )
    
    # Clear the encrypted API key
    setattr(settings, f"{provider}_api_key_encrypted", None)
    
    # If this was the preferred provider, switch to ollama
    if settings.preferred_provider == provider:
        settings.preferred_provider = "ollama"
    
    await db.commit()
    
    return {"message": f"{provider.title()} API key deleted successfully"}


@router.post("/test/{provider}")
async def test_provider(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Test if a provider is working with user's configuration."""
    if provider not in ["ollama", "anthropic", "openai", "google", "groq"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider"
        )
    
    try:
        from src.llm.factory_enhanced import EnhancedLLMFactory
        
        # Try to create an LLM instance
        llm = await EnhancedLLMFactory.create_for_user(
            user_id=str(current_user.id),
            db=db,
            provider=provider,
            use_fallback=False,  # Don't use fallback for testing
        )
        
        # Try a simple generation
        response = llm.invoke("Hello! Please respond with just 'OK' if you can see this message.")
        
        return {
            "success": True,
            "message": f"{provider.title()} is working correctly",
            "test_response": str(response.content)[:100],  # First 100 chars
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to connect to {provider.title()}",
            "error": str(e),
        }