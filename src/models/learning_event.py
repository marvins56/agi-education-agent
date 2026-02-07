"""LearningEvent model for tracking student interactions."""

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.models.database import Base


class LearningEvent(Base):
    __tablename__ = "learning_events"
    __table_args__ = (
        Index("ix_learning_events_student_id", "student_id"),
        Index("ix_learning_events_subject", "subject"),
        Index("ix_learning_events_created_at", "created_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), nullable=False)
    subject = Column(String(100), nullable=True)
    topic = Column(String(255), nullable=True)
    data = Column(JSONB, nullable=True)
    outcome = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
