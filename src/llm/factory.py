"""Centralized LLM factory for multi-provider support."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from src.config import settings


class LLMFactory:
    """Create LLM instances for any supported provider."""

    SUPPORTED_PROVIDERS = ("ollama", "anthropic", "openai")

    @staticmethod
    def create(
        provider: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> BaseChatModel:
        """Return a BaseChatModel for the requested provider.

        Args:
            provider: "ollama", "anthropic", or "openai". Defaults to settings.LLM_PROVIDER.
            model: Model name/ID. Defaults to the provider's configured default.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            A LangChain chat model instance.

        Raises:
            ValueError: If the provider is not supported.
            ImportError: If the required package for a provider is not installed.
        """
        provider = (provider or settings.LLM_PROVIDER).lower()

        if provider == "ollama":
            return LLMFactory._create_ollama(model, temperature, max_tokens)
        elif provider == "anthropic":
            return LLMFactory._create_anthropic(model, temperature, max_tokens)
        elif provider == "openai":
            return LLMFactory._create_openai(model, temperature, max_tokens)
        else:
            raise ValueError(
                f"Unsupported LLM provider: {provider!r}. "
                f"Supported: {', '.join(LLMFactory.SUPPORTED_PROVIDERS)}"
            )

    @staticmethod
    def _create_ollama(
        model: str | None, temperature: float, max_tokens: int
    ) -> BaseChatModel:
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            raise ImportError(
                "langchain-ollama is required for Ollama support. "
                "Install it with: pip install langchain-ollama"
            )

        return ChatOllama(
            model=model or settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=temperature,
            num_predict=max_tokens,
        )

    @staticmethod
    def _create_anthropic(
        model: str | None, temperature: float, max_tokens: int
    ) -> BaseChatModel:
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError(
                "langchain-anthropic is required for Anthropic support. "
                "Install it with: pip install langchain-anthropic"
            )

        return ChatAnthropic(
            model=model or settings.DEFAULT_MODEL,
            temperature=temperature,
            max_tokens=max_tokens,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
        )

    @staticmethod
    def _create_openai(
        model: str | None, temperature: float, max_tokens: int
    ) -> BaseChatModel:
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "langchain-openai is required for OpenAI support. "
                "Install it with: pip install langchain-openai"
            )

        return ChatOpenAI(
            model=model or "gpt-4o",
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.OPENAI_API_KEY,
        )
