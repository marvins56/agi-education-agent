"""Analytics models for daily and weekly metric aggregates."""

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.sql import func

from src.models.database import Base


class DailyMetric(Base):
    __tablename__ = "daily_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    student_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    date = Column(Date, nullable=False)
    sessions_count = Column(Integer, default=0)
    time_studied_minutes = Column(Integer, default=0)
    questions_answered = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)
    topics_covered = Column(ARRAY(String), default=[])
    created_at = Column(DateTime, server_default=func.now())


class WeeklyAggregate(Base):
    __tablename__ = "weekly_aggregates"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    student_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    week_start = Column(Date, nullable=False)
    avg_mastery = Column(Float, default=0.0)
    velocity = Column(Float, default=0.0)
    engagement_rate = Column(Float, default=0.0)
    streak_max = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
