"""Assessment system tests."""

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.assessment.grader import AutoGrader
from src.assessment.schemas import (
    AssessmentCreate,
    DifficultyLevel,
    GenerateRequest,
    GradeResult,
    QuestionCreate,
    QuestionResponse,
    QuestionType,
    QuickQuizRequest,
    SubmissionCreate,
    SubmissionResponse,
)
from src.assessment.validator import QuestionValidator


# --- Schema Tests ---


class TestQuestionTypeEnum:
    def test_values(self):
        assert QuestionType.mcq == "mcq"
        assert QuestionType.short_answer == "short_answer"
        assert QuestionType.essay == "essay"
        assert QuestionType.code == "code"

    def test_from_string(self):
        assert QuestionType("mcq") == QuestionType.mcq
        assert QuestionType("essay") == QuestionType.essay


class TestDifficultyLevelEnum:
    def test_values(self):
        assert DifficultyLevel.easy == "easy"
        assert DifficultyLevel.medium == "medium"
        assert DifficultyLevel.hard == "hard"


class TestAssessmentCreateSchema:
    def test_minimal(self):
        a = AssessmentCreate(title="Quiz 1", subject="Math", type="quiz")
        assert a.title == "Quiz 1"
        assert a.subject == "Math"
        assert a.questions is None
        assert a.config is None

    def test_with_questions(self):
        q = QuestionCreate(
            type=QuestionType.mcq,
            content="What is 2+2?",
            options=["3", "4", "5", "6"],
            correct_answer="4",
        )
        a = AssessmentCreate(
            title="Math Quiz",
            subject="Math",
            type="quiz",
            questions=[q],
        )
        assert len(a.questions) == 1
        assert a.questions[0].type == QuestionType.mcq
        assert a.questions[0].points == 10
        assert a.questions[0].difficulty == DifficultyLevel.medium


class TestQuestionResponseSchema:
    def test_no_correct_answer(self):
        """QuestionResponse must not expose correct_answer."""
        qr = QuestionResponse(
            id="abc",
            type=QuestionType.mcq,
            content="What is 2+2?",
            options=["3", "4", "5", "6"],
            points=10,
            difficulty=DifficultyLevel.easy,
        )
        dumped = qr.model_dump()
        assert "correct_answer" not in dumped


class TestGradeResultModel:
    def test_correct(self):
        gr = GradeResult(
            question_id="q1",
            score=10,
            max_score=10,
            feedback="Correct!",
            correct=True,
        )
        assert gr.correct is True
        assert gr.score == gr.max_score

    def test_incorrect(self):
        gr = GradeResult(
            question_id="q2",
            score=0,
            max_score=10,
            feedback="Wrong answer.",
            correct=False,
        )
        assert gr.correct is False
        assert gr.score == 0


class TestSubmissionCreateSchema:
    def test_answers_dict(self):
        sc = SubmissionCreate(answers={"q1": "A", "q2": "B"})
        assert sc.answers["q1"] == "A"


class TestGenerateRequestSchema:
    def test_defaults(self):
        gr = GenerateRequest(subject="Math", topic="Algebra")
        assert gr.question_count == 5
        assert gr.difficulty == DifficultyLevel.medium
        assert QuestionType.mcq in gr.question_types


# --- Grader Tests ---


class TestGradeMCQ:
    def test_correct_answer(self):
        grader = AutoGrader.__new__(AutoGrader)
        result = AutoGrader._grade_mcq(
            {"id": "q1", "correct_answer": "Paris", "points": 10},
            "Paris",
        )
        assert result.correct is True
        assert result.score == 10
        assert result.max_score == 10

    def test_incorrect_answer(self):
        result = AutoGrader._grade_mcq(
            {"id": "q1", "correct_answer": "Paris", "points": 10},
            "London",
        )
        assert result.correct is False
        assert result.score == 0
        assert "Paris" in result.feedback

    def test_case_insensitive(self):
        result = AutoGrader._grade_mcq(
            {"id": "q1", "correct_answer": "Paris", "points": 10},
            "paris",
        )
        assert result.correct is True

    def test_whitespace_tolerance(self):
        result = AutoGrader._grade_mcq(
            {"id": "q1", "correct_answer": "Paris", "points": 10},
            "  Paris  ",
        )
        assert result.correct is True


# --- Endpoint Tests ---


@pytest.fixture
async def assessment_client():
    """Create a test client with the assessments router."""
    from fastapi import FastAPI

    from src.api.routers.assessments import router

    app = FastAPI()

    # Mock dependencies
    mock_user = MagicMock()
    mock_user.id = uuid.uuid4()
    mock_user.email = "test@example.com"
    mock_user.role = "student"

    mock_db = AsyncMock()

    async def override_get_current_user():
        return mock_user

    async def override_get_db():
        yield mock_db

    from src.api.dependencies import get_current_user, get_db

    app.include_router(router, prefix="/api/v1/assessments")
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, mock_db, mock_user

    app.dependency_overrides.clear()


async def test_create_assessment_endpoint(assessment_client):
    """Test POST /assessments creates an assessment."""
    client, mock_session, mock_user = assessment_client

    # The endpoint calls db.add, db.flush — mock them
    mock_session = AsyncMock()
    created_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # Patch the Assessment model so flush populates id/created_at
    with patch("src.api.routers.assessments.Assessment") as MockAssessment:
        instance = MagicMock()
        instance.id = created_id
        instance.title = "Test Quiz"
        instance.subject = "Math"
        instance.type = "quiz"
        instance.config = {}
        instance.created_at = now
        instance.due_at = None
        MockAssessment.return_value = instance

        # Need to override get_db to use our controlled mock
        from fastapi import FastAPI
        from src.api.routers.assessments import router
        from src.api.dependencies import get_current_user, get_db

        app = FastAPI()
        app.include_router(router, prefix="/api/v1/assessments")

        async def override_get_current_user():
            return mock_user

        async def override_get_db():
            yield mock_session

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            response = await c.post(
                "/api/v1/assessments",
                json={
                    "title": "Test Quiz",
                    "subject": "Math",
                    "type": "quiz",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Quiz"
        assert data["subject"] == "Math"
        assert data["question_count"] == 0

        app.dependency_overrides.clear()


async def test_list_assessments_endpoint(assessment_client):
    """Test GET /assessments returns the user's assessments."""
    client, mock_session, mock_user = assessment_client

    # Create mock assessment objects
    mock_assessment = MagicMock()
    mock_assessment.id = uuid.uuid4()
    mock_assessment.title = "Algebra Quiz"
    mock_assessment.subject = "Math"
    mock_assessment.type = "quiz"
    mock_assessment.created_at = datetime.now(timezone.utc)
    mock_assessment.due_at = None
    mock_question = MagicMock()
    mock_question.points = 10
    mock_assessment.questions = [mock_question]

    # Build the mock chain: db.execute(...) -> result.scalars().all() -> [mock_assessment]
    from fastapi import FastAPI
    from src.api.routers.assessments import router
    from src.api.dependencies import get_current_user, get_db

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/assessments")

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [mock_assessment]
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    async def override_get_current_user():
        return mock_user

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        response = await c.get("/api/v1/assessments")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["title"] == "Algebra Quiz"
    assert data[0]["question_count"] == 1
    assert data[0]["total_points"] == 10

    app.dependency_overrides.clear()


# --- Generator parse test ---


class TestGeneratorParseJson:
    def test_parse_json_array(self):
        from src.assessment.generator import QuestionGenerator

        raw = '[{"type": "mcq", "content": "Q1"}]'
        result = QuestionGenerator._parse_json_response(raw)
        assert len(result) == 1
        assert result[0]["type"] == "mcq"

    def test_parse_with_code_fences(self):
        from src.assessment.generator import QuestionGenerator

        raw = '```json\n[{"type": "mcq", "content": "Q1"}]\n```'
        result = QuestionGenerator._parse_json_response(raw)
        assert len(result) == 1

    def test_parse_invalid_json(self):
        from src.assessment.generator import QuestionGenerator

        raw = "This is not JSON at all."
        result = QuestionGenerator._parse_json_response(raw)
        assert result == []

    def test_parse_dict_with_questions_key(self):
        from src.assessment.generator import QuestionGenerator

        raw = '{"questions": [{"type": "mcq", "content": "Q1"}]}'
        result = QuestionGenerator._parse_json_response(raw)
        assert len(result) == 1


# --- Validator Tests ---


class TestQuestionValidator:
    def test_valid_mcq(self):
        validator = QuestionValidator()
        questions = [
            {
                "type": "mcq",
                "content": "What is the capital of France?",
                "options": ["London", "Paris", "Berlin", "Madrid"],
                "correct_answer": "Paris",
                "points": 10,
                "difficulty": "medium",
            }
        ]
        result = validator.validate_questions(questions)
        assert len(result) == 1

    def test_mcq_missing_options(self):
        validator = QuestionValidator()
        questions = [
            {
                "type": "mcq",
                "content": "What is 2+2?",
                "points": 10,
                "difficulty": "easy",
            }
        ]
        result = validator.validate_questions(questions)
        assert len(result) == 0

    def test_mcq_correct_answer_not_in_options(self):
        validator = QuestionValidator()
        questions = [
            {
                "type": "mcq",
                "content": "What is 2+2?",
                "options": ["1", "2", "3", "5"],
                "correct_answer": "4",
                "points": 10,
                "difficulty": "easy",
            }
        ]
        result = validator.validate_questions(questions)
        assert len(result) == 0

    def test_remove_duplicates(self):
        validator = QuestionValidator()
        questions = [
            {
                "type": "short_answer",
                "content": "What is the capital of France?",
                "correct_answer": "Paris",
                "points": 10,
                "difficulty": "easy",
            },
            {
                "type": "short_answer",
                "content": "What is the capital of France?",
                "correct_answer": "Paris",
                "points": 10,
                "difficulty": "easy",
            },
        ]
        result = validator.validate_questions(questions)
        assert len(result) == 1

    def test_empty_content_rejected(self):
        validator = QuestionValidator()
        questions = [
            {
                "type": "short_answer",
                "content": "",
                "correct_answer": "test",
                "points": 10,
                "difficulty": "easy",
            }
        ]
        result = validator.validate_questions(questions)
        assert len(result) == 0

    def test_invalid_difficulty_rejected(self):
        validator = QuestionValidator()
        questions = [
            {
                "type": "short_answer",
                "content": "What is 2+2?",
                "correct_answer": "4",
                "points": 10,
                "difficulty": "impossible",
            }
        ]
        result = validator.validate_questions(questions)
        assert len(result) == 0


# --- Short Answer Grading (mock Claude) ---


class TestGradeShortAnswer:
    async def test_empty_answer(self):
        grader = AutoGrader(llm=MagicMock())
        result = await grader._grade_short_answer(
            {"id": "q1", "content": "What is 2+2?", "correct_answer": "4", "points": 10},
            "",
        )
        assert result.score == 0
        assert result.correct is False
        assert "No answer" in result.feedback

    async def test_grading_with_mock_llm(self):
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(
            content='{"score": 8, "feedback": "Good answer, mostly correct.", "correct": true}'
        ))
        grader = AutoGrader(llm=mock_llm)
        result = await grader._grade_short_answer(
            {"id": "q1", "content": "Explain gravity", "correct_answer": "force; mass; attraction", "points": 10},
            "Gravity is the force of attraction between objects with mass.",
        )
        assert result.score == 8
        assert result.correct is True
        assert "Good answer" in result.feedback

    async def test_grading_handles_invalid_llm_response(self):
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content="not valid json"))
        grader = AutoGrader(llm=mock_llm)
        result = await grader._grade_short_answer(
            {"id": "q1", "content": "What?", "correct_answer": "answer", "points": 10},
            "some answer",
        )
        assert result.score == 0
        assert "Grading error" in result.feedback


# --- Code Grading (sandbox security) ---


class TestGradeCodeSandbox:
    async def test_code_correct(self):
        grader = AutoGrader(llm=MagicMock())
        question = {
            "id": "q1",
            "type": "code",
            "content": "Write a function add(a, b) that returns a + b.",
            "correct_answer": json.dumps({"test_code": "assert add(1, 2) == 3\nassert add(0, 0) == 0"}),
            "points": 15,
        }
        result = await grader._grade_code(question, "def add(a, b):\n    return a + b")
        assert result.correct is True
        assert result.score == 15

    async def test_code_incorrect(self):
        grader = AutoGrader(llm=MagicMock())
        question = {
            "id": "q1",
            "type": "code",
            "content": "Write a function add(a, b).",
            "correct_answer": json.dumps({"test_code": "assert add(1, 2) == 3"}),
            "points": 15,
        }
        result = await grader._grade_code(question, "def add(a, b):\n    return a - b")
        assert result.correct is False
        assert result.score == 0

    async def test_code_timeout(self):
        grader = AutoGrader(llm=MagicMock())
        question = {
            "id": "q1",
            "type": "code",
            "content": "Write a function.",
            "correct_answer": json.dumps({"test_code": "pass"}),
            "points": 15,
        }
        result = await grader._grade_code(
            question, "import time\ntime.sleep(10)\ndef f(): pass"
        )
        assert result.correct is False
        assert "timed out" in result.feedback.lower()

    async def test_code_empty_answer(self):
        grader = AutoGrader(llm=MagicMock())
        question = {
            "id": "q1",
            "type": "code",
            "content": "Write something.",
            "correct_answer": json.dumps({"test_code": "pass"}),
            "points": 15,
        }
        result = await grader._grade_code(question, "")
        assert result.score == 0
        assert "No code" in result.feedback

    async def test_code_no_test_cases(self):
        grader = AutoGrader(llm=MagicMock())
        question = {
            "id": "q1",
            "type": "code",
            "content": "Write something.",
            "correct_answer": "",
            "points": 15,
        }
        result = await grader._grade_code(question, "print('hello')")
        assert result.score == 0
        assert "No test cases" in result.feedback


# --- Submission Flow Test ---


class TestSubmissionFlow:
    async def test_grade_full_submission(self):
        """Test grading a multi-question submission with mixed types."""
        grader = AutoGrader(llm=MagicMock())
        questions = [
            {
                "id": "q1",
                "type": "mcq",
                "content": "What is 2+2?",
                "correct_answer": "4",
                "points": 10,
            },
            {
                "id": "q2",
                "type": "mcq",
                "content": "What is 3+3?",
                "correct_answer": "6",
                "points": 10,
            },
        ]
        answers = {"q1": "4", "q2": "5"}
        results = await grader.grade_submission(questions, answers)

        assert len(results) == 2
        assert results[0].correct is True
        assert results[0].score == 10
        assert results[1].correct is False
        assert results[1].score == 0

    async def test_grade_missing_answer(self):
        """A missing answer should score 0."""
        grader = AutoGrader(llm=MagicMock())
        questions = [
            {
                "id": "q1",
                "type": "mcq",
                "content": "What is 2+2?",
                "correct_answer": "4",
                "points": 10,
            },
        ]
        answers = {}  # no answers at all
        results = await grader.grade_submission(questions, answers)
        assert len(results) == 1
        assert results[0].score == 0
        assert results[0].correct is False


# --- QuickQuizRequest Schema ---


class TestQuickQuizRequestSchema:
    def test_defaults(self):
        qr = QuickQuizRequest(subject="Math", topic="Fractions")
        assert qr.question_count == 3
        assert qr.difficulty == DifficultyLevel.medium

    def test_max_questions(self):
        qr = QuickQuizRequest(subject="Math", topic="Algebra", question_count=5)
        assert qr.question_count == 5

    def test_rejects_too_many_questions(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            QuickQuizRequest(subject="Math", topic="Algebra", question_count=10)
