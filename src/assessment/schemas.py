"""Assessment-related Pydantic schemas."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class QuestionType(str, Enum):
    mcq = "mcq"
    short_answer = "short_answer"
    essay = "essay"
    code = "code"


class DifficultyLevel(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class QuestionCreate(BaseModel):
    type: QuestionType
    content: str
    options: list[str] | None = None
    correct_answer: str | None = None
    rubric: str | None = None
    points: int = 10
    difficulty: DifficultyLevel = DifficultyLevel.medium


class QuestionResponse(BaseModel):
    id: str
    type: QuestionType
    content: str
    options: list[str] | None = None
    points: int
    difficulty: DifficultyLevel

    model_config = {"from_attributes": True}


class AssessmentCreate(BaseModel):
    title: str
    subject: str
    type: str = Field(description="quiz, exam, or homework")
    questions: list[QuestionCreate] | None = None
    config: dict | None = None


class AssessmentResponse(BaseModel):
    id: str
    title: str
    subject: str
    type: str
    question_count: int
    total_points: int
    created_at: datetime
    due_at: datetime | None = None

    model_config = {"from_attributes": True}


MAX_ANSWER_LENGTH = 50_000  # 50KB per answer


class SubmissionCreate(BaseModel):
    answers: dict[str, str]

    @field_validator("answers")
    @classmethod
    def validate_answer_lengths(cls, v: dict[str, str]) -> dict[str, str]:
        for key, answer in v.items():
            if len(answer) > MAX_ANSWER_LENGTH:
                raise ValueError(
                    f"Answer for question '{key}' exceeds maximum length of {MAX_ANSWER_LENGTH} characters"
                )
        return v


class GradeResult(BaseModel):
    question_id: str
    score: float
    max_score: float
    feedback: str
    correct: bool


class SubmissionResponse(BaseModel):
    id: str
    assessment_id: str
    total_score: float
    max_score: float
    percentage: float
    grades: list[GradeResult]
    submitted_at: datetime
    graded_at: datetime | None = None

    model_config = {"from_attributes": True}


class GenerateRequest(BaseModel):
    subject: str
    topic: str
    question_count: int = 5
    question_types: list[QuestionType] = [QuestionType.mcq]
    difficulty: DifficultyLevel = DifficultyLevel.medium


class QuickQuizRequest(BaseModel):
    subject: str
    topic: str
    question_count: int = Field(default=3, ge=1, le=5)
    difficulty: DifficultyLevel = DifficultyLevel.medium
