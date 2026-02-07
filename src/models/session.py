"""Session model for tutoring sessions."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.models.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mode = Column(String(50), default="tutoring")
    subject = Column(String(100), nullable=True)
    topic = Column(String(255), nullable=True)
    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime, nullable=True)
    metadata_ = Column("metadata", JSONB, server_default=text("'{}'"))
    summary = Column(Text, nullable=True)
    is_archived = Column(Boolean, default=False)
    message_count = Column(Integer, default=0)
    device_info = Column(String(255), nullable=True)
