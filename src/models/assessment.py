"""Assessment, Question, Submission, and QuestionGrade models."""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.models.database import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    created_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(255), nullable=False)
    subject = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    config = Column(JSONB, server_default=text("'{}'"))
    created_at = Column(DateTime, server_default=func.now())
    due_at = Column(DateTime, nullable=True)

    questions = relationship("Question", back_populates="assessment", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="assessment")


class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    assessment_id = Column(
        UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False
    )
    type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    options = Column(JSONB, nullable=True)
    correct_answer = Column(Text, nullable=True)
    rubric = Column(Text, nullable=True)
    points = Column(Integer, default=10)
    difficulty = Column(String(20), default="medium")
    order_num = Column(Integer, default=0)

    assessment = relationship("Assessment", back_populates="questions")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    assessment_id = Column(
        UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False
    )
    student_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    answers = Column(JSONB, nullable=False)
    submitted_at = Column(DateTime, server_default=func.now())
    graded_at = Column(DateTime, nullable=True)
    total_score = Column(Float, nullable=True)
    max_score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)

    assessment = relationship("Assessment", back_populates="submissions")
    grades = relationship("QuestionGrade", back_populates="submission", cascade="all, delete-orphan")


class QuestionGrade(Base):
    __tablename__ = "question_grades"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    submission_id = Column(
        UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False
    )
    question_id = Column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    score = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False)
    feedback = Column(Text, nullable=True)
    graded_by = Column(String(50), default="ai")

    submission = relationship("Submission", back_populates="grades")
