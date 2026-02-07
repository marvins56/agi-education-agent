"""User and StudentProfile models."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.models.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), default="student")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)

    profile = relationship("StudentProfile", back_populates="user", uselist=False)


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    learning_style = Column(String(50), default="balanced")
    pace = Column(String(50), default="moderate")
    grade_level = Column(String(50), nullable=True)
    strengths = Column(ARRAY(String), nullable=True)
    weaknesses = Column(ARRAY(String), nullable=True)
    preferences = Column(JSONB, server_default=text("'{}'"))
    # Engagement tracking
    total_study_minutes = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    last_study_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="profile")
