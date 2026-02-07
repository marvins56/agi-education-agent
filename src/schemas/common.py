"""Common response schemas used across the API."""

from typing import Any

from pydantic import BaseModel


class APIResponse(BaseModel):
    success: bool = True
    message: str = ""
    data: Any | None = None


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int = 1
    page_size: int = 20
