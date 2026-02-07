"""Learning path models: topic graph, student goals, review schedules."""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.models.database import Base


class TopicNode(Base):
    __tablename__ = "topic_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    subject = Column(String(100), nullable=False)
    topic = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=True)
    difficulty = Column(String(20), default="medium")
    estimated_minutes = Column(Integer, default=30)
    metadata_ = Column("metadata", JSONB, server_default=text("'{}'"))


class TopicEdge(Base):
    __tablename__ = "topic_edges"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    from_topic_id = Column(
        UUID(as_uuid=True), ForeignKey("topic_nodes.id", ondelete="CASCADE"), nullable=False
    )
    to_topic_id = Column(
        UUID(as_uuid=True), ForeignKey("topic_nodes.id", ondelete="CASCADE"), nullable=False
    )
    relationship_type = Column(String(50), default="requires")
    weight = Column(Float, default=1.0)


class StudentGoal(Base):
    __tablename__ = "student_goals"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    student_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    topic_id = Column(
        UUID(as_uuid=True), ForeignKey("topic_nodes.id", ondelete="CASCADE"), nullable=False
    )
    target_mastery = Column(Float, default=80.0)
    deadline = Column(Date, nullable=True)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


class ReviewSchedule(Base):
    __tablename__ = "review_schedule"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    student_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    topic_id = Column(
        UUID(as_uuid=True), ForeignKey("topic_nodes.id", ondelete="CASCADE"), nullable=False
    )
    next_review_date = Column(Date, nullable=False)
    interval_days = Column(Integer, default=1)
    easiness_factor = Column(Float, default=2.5)
    review_count = Column(Integer, default=0)
    last_quality = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
