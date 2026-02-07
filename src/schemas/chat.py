"""Chat and session schemas."""

from datetime import datetime

from pydantic import BaseModel


class MessageRequest(BaseModel):
    content: str
    session_id: str
    subject: str | None = None
    topic: str | None = None


class MessageResponse(BaseModel):
    text: str
    session_id: str
    sources: list[dict] = []
    suggested_actions: list[str] = []
    metadata: dict = {}


class SessionCreateRequest(BaseModel):
    subject: str | None = None
    topic: str | None = None
    mode: str = "tutoring"


class SessionResponse(BaseModel):
    session_id: str
    created_at: datetime
    mode: str


class ConversationMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime
