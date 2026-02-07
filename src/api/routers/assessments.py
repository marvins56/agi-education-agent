"""Assessment endpoints: create, list, generate, submit, results."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.dependencies import get_current_user, get_db
from src.assessment.generator import QuestionGenerator
from src.assessment.grader import AutoGrader
from src.auth.rbac import Role, require_role
from src.assessment.schemas import (
    AssessmentCreate,
    AssessmentResponse,
    GenerateRequest,
    GradeResult,
    QuestionCreate,
    QuestionResponse,
    QuickQuizRequest,
    SubmissionCreate,
    SubmissionResponse,
)
from src.assessment.validator import QuestionValidator
from src.models.assessment import Assessment, Question, QuestionGrade, Submission
from src.models.user import User

router = APIRouter(tags=["Assessments"])


@router.post("", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    body: AssessmentCreate,
    user: User = Depends(require_role(Role.teacher, Role.admin)),
    db: AsyncSession = Depends(get_db),
):
    """Create an assessment with optional inline questions."""
    assessment = Assessment(
        created_by=user.id,
        title=body.title,
        subject=body.subject,
        type=body.type,
        config=body.config or {},
    )
    db.add(assessment)
    await db.flush()

    total_points = 0
    question_count = 0

    if body.questions:
        for i, q in enumerate(body.questions):
            question = Question(
                assessment_id=assessment.id,
                type=q.type.value,
                content=q.content,
                options=q.options,
                correct_answer=q.correct_answer,
                rubric=q.rubric,
                points=q.points,
                difficulty=q.difficulty.value,
                order_num=i,
            )
            db.add(question)
            total_points += q.points
            question_count += 1

        await db.flush()

    return AssessmentResponse(
        id=str(assessment.id),
        title=assessment.title,
        subject=assessment.subject,
        type=assessment.type,
        question_count=question_count,
        total_points=total_points,
        created_at=assessment.created_at,
        due_at=assessment.due_at,
    )


@router.get("", response_model=list[AssessmentResponse])
async def list_assessments(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List assessments created by the current user."""
    result = await db.execute(
        select(Assessment)
        .where(Assessment.created_by == user.id)
        .options(selectinload(Assessment.questions))
        .order_by(Assessment.created_at.desc())
    )
    assessments = result.scalars().all()

    return [
        AssessmentResponse(
            id=str(a.id),
            title=a.title,
            subject=a.subject,
            type=a.type,
            question_count=len(a.questions),
            total_points=sum(q.points for q in a.questions),
            created_at=a.created_at,
            due_at=a.due_at,
        )
        for a in assessments
    ]


@router.get("/{assessment_id}")
async def get_assessment(
    assessment_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get assessment with questions (correct answers hidden)."""
    result = await db.execute(
        select(Assessment)
        .where(Assessment.id == assessment_id)
        .options(selectinload(Assessment.questions))
    )
    assessment = result.scalars().first()

    if assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    # Access control: only the creator can view via this endpoint
    if assessment.created_by != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this assessment")

    questions = [
        QuestionResponse(
            id=str(q.id),
            type=q.type,
            content=q.content,
            options=q.options,
            points=q.points,
            difficulty=q.difficulty,
        )
        for q in sorted(assessment.questions, key=lambda q: q.order_num)
    ]

    return {
        "id": str(assessment.id),
        "title": assessment.title,
        "subject": assessment.subject,
        "type": assessment.type,
        "questions": [q.model_dump() for q in questions],
        "created_at": assessment.created_at.isoformat() if assessment.created_at else None,
        "due_at": assessment.due_at.isoformat() if assessment.due_at else None,
    }


@router.post("/generate", response_model=list[QuestionCreate])
async def generate_questions(
    body: GenerateRequest,
    user: User = Depends(require_role(Role.teacher, Role.admin)),
):
    """AI-generate questions for a topic."""
    generator = QuestionGenerator()
    raw_questions = await generator.generate_questions(
        subject=body.subject,
        topic=body.topic,
        count=body.question_count,
        types=[t.value for t in body.question_types],
        difficulty=body.difficulty.value,
    )

    validator = QuestionValidator()
    validated = validator.validate_questions(raw_questions)

    return [
        QuestionCreate(
            type=q.get("type", "mcq"),
            content=q.get("content", ""),
            options=q.get("options"),
            correct_answer=q.get("correct_answer"),
            rubric=q.get("rubric"),
            points=q.get("points", 10),
            difficulty=q.get("difficulty", "medium"),
        )
        for q in validated
    ]


@router.post("/quick-quiz")
async def quick_quiz(
    body: QuickQuizRequest,
    user: User = Depends(get_current_user),
):
    """Generate a quick inline quiz (3-5 questions) for use during tutoring."""
    generator = QuestionGenerator()
    raw_questions = await generator.generate_questions(
        subject=body.subject,
        topic=body.topic,
        count=body.question_count,
        types=["mcq", "short_answer"],
        difficulty=body.difficulty.value,
    )

    validator = QuestionValidator()
    validated = validator.validate_questions(raw_questions)

    questions = [
        {
            "type": q.get("type", "mcq"),
            "content": q.get("content", ""),
            "options": q.get("options"),
            "points": q.get("points", 10),
            "difficulty": q.get("difficulty", "medium"),
            "correct_answer": q.get("correct_answer"),
        }
        for q in validated[:body.question_count]
    ]

    return {
        "subject": body.subject,
        "topic": body.topic,
        "questions": questions,
        "question_count": len(questions),
    }


@router.post("/{assessment_id}/generate", response_model=AssessmentResponse)
async def generate_for_assessment(
    assessment_id: uuid.UUID,
    body: GenerateRequest,
    user: User = Depends(require_role(Role.teacher, Role.admin)),
    db: AsyncSession = Depends(get_db),
):
    """AI-generate questions and add them to an existing assessment."""
    result = await db.execute(
        select(Assessment)
        .where(Assessment.id == assessment_id, Assessment.created_by == user.id)
        .options(selectinload(Assessment.questions))
    )
    assessment = result.scalars().first()

    if assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    generator = QuestionGenerator()
    raw_questions = await generator.generate_questions(
        subject=body.subject,
        topic=body.topic,
        count=body.question_count,
        types=[t.value for t in body.question_types],
        difficulty=body.difficulty.value,
    )

    validator = QuestionValidator()
    validated = validator.validate_questions(raw_questions)

    existing_count = len(assessment.questions)
    for i, q in enumerate(validated):
        question = Question(
            assessment_id=assessment.id,
            type=q.get("type", "mcq"),
            content=q.get("content", ""),
            options=q.get("options"),
            correct_answer=q.get("correct_answer"),
            rubric=q.get("rubric"),
            points=q.get("points", 10),
            difficulty=q.get("difficulty", "medium"),
            order_num=existing_count + i,
        )
        db.add(question)

    await db.flush()

    # Re-query to get updated counts
    result = await db.execute(
        select(Assessment)
        .where(Assessment.id == assessment_id)
        .options(selectinload(Assessment.questions))
    )
    assessment = result.scalars().first()

    return AssessmentResponse(
        id=str(assessment.id),
        title=assessment.title,
        subject=assessment.subject,
        type=assessment.type,
        question_count=len(assessment.questions),
        total_points=sum(q.points for q in assessment.questions),
        created_at=assessment.created_at,
        due_at=assessment.due_at,
    )


@router.post("/{assessment_id}/submit", response_model=SubmissionResponse)
async def submit_assessment(
    assessment_id: uuid.UUID,
    body: SubmissionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit answers and auto-grade."""
    result = await db.execute(
        select(Assessment)
        .where(Assessment.id == assessment_id)
        .options(selectinload(Assessment.questions))
    )
    assessment = result.scalars().first()

    if assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    # Check for duplicate submission
    existing = await db.execute(
        select(Submission).where(
            Submission.assessment_id == assessment_id,
            Submission.student_id == user.id,
        )
    )
    if existing.scalars().first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already submitted this assessment",
        )

    # Build question dicts for the grader
    question_dicts = [
        {
            "id": str(q.id),
            "type": q.type,
            "content": q.content,
            "options": q.options,
            "correct_answer": q.correct_answer,
            "rubric": q.rubric,
            "points": q.points,
        }
        for q in assessment.questions
    ]

    # Grade
    grader = AutoGrader()
    grade_results = await grader.grade_submission(question_dicts, body.answers)

    # Persist submission
    total_score = sum(g.score for g in grade_results)
    max_score = sum(g.max_score for g in grade_results)
    now = datetime.now(timezone.utc)

    submission = Submission(
        assessment_id=assessment_id,
        student_id=user.id,
        answers=body.answers,
        submitted_at=now,
        graded_at=now,
        total_score=total_score,
        max_score=max_score,
    )
    db.add(submission)
    await db.flush()

    # Persist per-question grades
    for grade in grade_results:
        qg = QuestionGrade(
            submission_id=submission.id,
            question_id=uuid.UUID(grade.question_id),
            score=grade.score,
            max_score=grade.max_score,
            feedback=grade.feedback,
            graded_by="ai",
        )
        db.add(qg)

    await db.flush()

    return SubmissionResponse(
        id=str(submission.id),
        assessment_id=str(assessment_id),
        total_score=total_score,
        max_score=max_score,
        percentage=(total_score / max_score * 100) if max_score > 0 else 0,
        grades=grade_results,
        submitted_at=now,
        graded_at=now,
    )


@router.get("/{assessment_id}/results", response_model=list[SubmissionResponse])
async def get_results(
    assessment_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get grading results for an assessment."""
    result = await db.execute(
        select(Submission)
        .where(
            Submission.assessment_id == assessment_id,
            Submission.student_id == user.id,
        )
        .options(selectinload(Submission.grades))
        .order_by(Submission.submitted_at.desc())
    )
    submissions = result.scalars().all()

    responses = []
    for sub in submissions:
        grades = [
            GradeResult(
                question_id=str(g.question_id),
                score=g.score,
                max_score=g.max_score,
                feedback=g.feedback or "",
                correct=g.score >= g.max_score * 0.6,
            )
            for g in sub.grades
        ]
        responses.append(
            SubmissionResponse(
                id=str(sub.id),
                assessment_id=str(sub.assessment_id),
                total_score=sub.total_score or 0,
                max_score=sub.max_score or 0,
                percentage=(
                    (sub.total_score / sub.max_score * 100)
                    if sub.max_score and sub.max_score > 0
                    else 0
                ),
                grades=grades,
                submitted_at=sub.submitted_at,
                graded_at=sub.graded_at,
            )
        )

    return responses
