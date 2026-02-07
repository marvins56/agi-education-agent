"""TopicMastery model for tracking per-topic student mastery."""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.models.database import Base


class TopicMastery(Base):
    __tablename__ = "topic_mastery"
    __table_args__ = (
        UniqueConstraint("student_id", "subject", "topic", name="uq_student_subject_topic"),
        Index("ix_topic_mastery_student_id", "student_id"),
        Index("ix_topic_mastery_subject", "subject"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    subject = Column(String(100), nullable=False)
    topic = Column(String(255), nullable=False)
    mastery_score = Column(Float, default=0.0, nullable=False)
    confidence = Column(Float, default=0.0, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    last_assessed = Column(DateTime, nullable=True)
    last_reviewed = Column(DateTime, nullable=True)
    decay_rate = Column(Float, default=0.02, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
