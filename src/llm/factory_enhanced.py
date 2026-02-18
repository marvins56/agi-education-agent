"""Enhanced centralized LLM factory with multi-provider and user-specific API key support."""

from __future__ import annotations

import logging
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.llm_settings import UserLLMSettings
from src.utils.encryption import api_key_encryption

logger = logging.getLogger(__name__)


class EnhancedLLMFactory:
    """Create LLM instances with user-specific configurations and fallback support."""

    SUPPORTED_PROVIDERS = ("ollama", "anthropic", "openai", "google", "groq")

    @staticmethod
    async def create_for_user(
        user_id: str,
        db: AsyncSession,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        use_fallback: bool = True,
    ) -> BaseChatModel:
        """Create LLM instance for a specific user with their API keys and preferences.

        Args:
            user_id: User UUID
            db: Database session
            provider: Override provider (if None, uses user's preferred or fallback)
            model: Override model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            use_fallback: Whether to use fallback chain on failure

        Returns:
            A LangChain chat model instance

        Raises:
            ValueError: If no working provider is available
        """
        # Get user's LLM settings
        user_settings = await EnhancedLLMFactory._get_user_settings(user_id, db)
        
        # Determine provider priority
        if provider:
            providers_to_try = [provider]
        elif user_settings and user_settings.preferred_provider:
            providers_to_try = [user_settings.preferred_provider]
        else:
            providers_to_try = ["ollama"]  # Default fallback
        
        if use_fallback:
            # Add fallback chain: user's preferred → ollama (always available)
            if "ollama" not in providers_to_try:
                providers_to_try.append("ollama")
        
        last_error = None
        for provider_name in providers_to_try:
            try:
                # Get API key for this provider
                api_key = await EnhancedLLMFactory._get_api_key_for_provider(
                    provider_name, user_settings
                )
                
                # Get model name
                model_name = model or EnhancedLLMFactory._get_default_model(
                    provider_name, user_settings
                )
                
                # Create LLM instance
                llm = EnhancedLLMFactory._create_provider_instance(
                    provider_name, api_key, model_name, temperature, max_tokens
                )
                
                logger.info(f"Successfully created {provider_name} LLM for user {user_id}")
                return llm
                
            except Exception as e:
                logger.warning(f"Failed to create {provider_name} LLM: {e}")
                last_error = e
                continue
        
        # If all providers failed
        raise ValueError(
            f"No working LLM provider available. Last error: {last_error}"
        )

    @staticmethod
    async def _get_user_settings(
        user_id: str, db: AsyncSession
    ) -> Optional[UserLLMSettings]:
        """Fetch user's LLM settings from database."""
        from sqlalchemy import select
        
        result = await db.execute(
            select(UserLLMSettings).where(UserLLMSettings.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _get_api_key_for_provider(
        provider: str, user_settings: Optional[UserLLMSettings]
    ) -> Optional[str]:
        """Get API key for a provider (user-specific or system fallback)."""
        if provider == "ollama":
            return None  # Ollama doesn't need API keys
        
        user_key = None
        if user_settings:
            # Decrypt user's API key
            encrypted_key = getattr(user_settings, f"{provider}_api_key_encrypted", None)
            if encrypted_key:
                user_key = api_key_encryption.decrypt(encrypted_key)
        
        if user_key:
            return user_key
        
        # Fall back to system-wide API key
        system_key = getattr(settings, f"{provider.upper()}_API_KEY", "")
        return system_key if system_key else None

    @staticmethod
    def _get_default_model(
        provider: str, user_settings: Optional[UserLLMSettings]
    ) -> str:
        """Get default model for a provider."""
        # User's preferred model
        if user_settings and user_settings.preferred_model:
            return user_settings.preferred_model
        
        # System defaults
        model_map = {
            "ollama": settings.DEFAULT_OLLAMA_MODEL,
            "anthropic": settings.DEFAULT_ANTHROPIC_MODEL,
            "openai": settings.DEFAULT_OPENAI_MODEL,
            "google": settings.DEFAULT_GOOGLE_MODEL,
            "groq": settings.DEFAULT_GROQ_MODEL,
        }
        return model_map.get(provider, "gpt-4o-mini")

    @staticmethod
    def _create_provider_instance(
        provider: str,
        api_key: Optional[str],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> BaseChatModel:
        """Create LLM instance for a specific provider."""
        if provider == "ollama":
            return EnhancedLLMFactory._create_ollama(model, temperature, max_tokens)
        elif provider == "anthropic":
            return EnhancedLLMFactory._create_anthropic(api_key, model, temperature, max_tokens)
        elif provider == "openai":
            return EnhancedLLMFactory._create_openai(api_key, model, temperature, max_tokens)
        elif provider == "google":
            return EnhancedLLMFactory._create_google(api_key, model, temperature, max_tokens)
        elif provider == "groq":
            return EnhancedLLMFactory._create_groq(api_key, model, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    @staticmethod
    def _create_ollama(model: str, temperature: float, max_tokens: int) -> BaseChatModel:
        """Create Ollama chat instance."""
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            raise ImportError(
                "langchain-ollama is required for Ollama support. "
                "Install it with: pip install langchain-ollama"
            )

        return ChatOllama(
            model=model,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=temperature,
            num_predict=max_tokens,
        )

    @staticmethod
    def _create_anthropic(
        api_key: str, model: str, temperature: float, max_tokens: int
    ) -> BaseChatModel:
        """Create Anthropic Claude instance."""
        if not api_key:
            raise ValueError("Anthropic API key is required")
        
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError(
                "langchain-anthropic is required for Anthropic support. "
                "Install it with: pip install langchain-anthropic"
            )

        return ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            anthropic_api_key=api_key,
        )

    @staticmethod
    def _create_openai(
        api_key: str, model: str, temperature: float, max_tokens: int
    ) -> BaseChatModel:
        """Create OpenAI chat instance."""
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "langchain-openai is required for OpenAI support. "
                "Install it with: pip install langchain-openai"
            )

        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
        )

    @staticmethod
    def _create_google(
        api_key: str, model: str, temperature: float, max_tokens: int
    ) -> BaseChatModel:
        """Create Google Gemini instance."""
        if not api_key:
            raise ValueError("Google API key is required")
        
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            raise ImportError(
                "langchain-google-genai is required for Google Gemini support. "
                "Install it with: pip install langchain-google-genai"
            )

        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            google_api_key=api_key,
        )

    @staticmethod
    def _create_groq(
        api_key: str, model: str, temperature: float, max_tokens: int
    ) -> BaseChatModel:
        """Create Groq chat instance."""
        if not api_key:
            raise ValueError("Groq API key is required")
        
        try:
            from langchain_groq import ChatGroq
        except ImportError:
            raise ImportError(
                "langchain-groq is required for Groq support. "
                "Install it with: pip install langchain-groq"
            )

        return ChatGroq(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            groq_api_key=api_key,
        )


# Maintain backward compatibility
LLMFactory = EnhancedLLMFactory