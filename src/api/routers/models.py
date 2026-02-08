"""Model management endpoints."""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.auth.rbac import Role, require_role
from src.config import settings
from src.models.user import User

router = APIRouter()


class ModelInfo(BaseModel):
    provider: str
    model: str
    available: bool = True


class CurrentModelResponse(BaseModel):
    provider: str
    model: str


class SetDefaultRequest(BaseModel):
    provider: str
    model: str


class SetDefaultResponse(BaseModel):
    provider: str
    model: str
    message: str


@router.get("/models", response_model=list[dict[str, Any]])
async def list_models():
    """List all available providers and their models."""
    results: list[dict[str, Any]] = []

    # Ollama — query live API for available models
    ollama_models: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                ollama_models = [m["name"] for m in data.get("models", [])]
    except Exception:
        pass  # Ollama not reachable

    results.append({
        "provider": "ollama",
        "available": len(ollama_models) > 0,
        "models": ollama_models,
        "base_url": settings.OLLAMA_BASE_URL,
    })

    # Anthropic
    results.append({
        "provider": "anthropic",
        "available": bool(settings.ANTHROPIC_API_KEY),
        "models": [settings.DEFAULT_MODEL],
    })

    # OpenAI
    results.append({
        "provider": "openai",
        "available": bool(settings.OPENAI_API_KEY),
        "models": ["gpt-4o", "gpt-4o-mini"],
    })

    return results


@router.get("/models/current", response_model=CurrentModelResponse)
async def get_current_model():
    """Get the current default provider and model."""
    if settings.LLM_PROVIDER == "ollama":
        model = settings.OLLAMA_MODEL
    elif settings.LLM_PROVIDER == "anthropic":
        model = settings.DEFAULT_MODEL
    else:
        model = "gpt-4o"

    return CurrentModelResponse(provider=settings.LLM_PROVIDER, model=model)


@router.post("/models/default", response_model=SetDefaultResponse)
async def set_default_model(
    body: SetDefaultRequest,
    _current_user: User = Depends(require_role(Role.admin)),
):
    """Switch the default LLM provider and model (admin only).

    This changes the runtime default for the current process.
    It does NOT persist across restarts — update .env for that.
    """
    provider = body.provider.lower()
    if provider not in ("ollama", "anthropic", "openai"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {body.provider!r}",
        )

    settings.LLM_PROVIDER = provider

    if provider == "ollama":
        settings.OLLAMA_MODEL = body.model
    elif provider == "anthropic":
        settings.DEFAULT_MODEL = body.model
    # OpenAI model is passed directly via factory; no separate setting needed

    return SetDefaultResponse(
        provider=provider,
        model=body.model,
        message=f"Default switched to {provider}/{body.model} (runtime only)",
    )
