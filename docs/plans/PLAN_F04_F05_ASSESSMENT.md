# F04/F05: Assessment Generation + Auto-Grading System

## Overview
Build an AI-powered assessment system that can generate quizzes/exams and automatically grade student submissions using Claude for semantic evaluation.

## Features
- **F04 — Assessment Generation**: AI-generated questions (MCQ, short answer, essay, code) with configurable difficulty, subject, and topic
- **F05 — Auto-Grading**: Automatic grading with per-question feedback; deterministic for MCQ, AI-powered for open-ended

## Architecture

### New Modules
```
src/assessment/
  __init__.py
  schemas.py       # Pydantic v2 request/response models
  generator.py     # QuestionGenerator — LLM-based question generation
  grader.py        # AutoGrader — multi-strategy grading engine
  validator.py     # QuestionValidator — validates generated questions

src/models/assessment.py   # SQLAlchemy models (Assessment, Question, Submission, QuestionGrade)
src/agents/assessment.py   # AssessmentAgent(BaseAgent)
src/api/routers/assessments.py  # REST endpoints (8 endpoints)
migrations/versions/002_assessment_tables.py
tests/test_assessment.py   # 39 tests
```

### Data Model
- **Assessment** — container for a set of questions (quiz/exam/homework)
- **Question** — individual question with type, content, options, correct_answer, rubric
- **Submission** — a student's answers to an assessment
- **QuestionGrade** — per-question grade with score, feedback, grader identity

### Grading Strategy
| Question Type | Strategy |
|---|---|
| MCQ | Exact match (deterministic, case-insensitive, whitespace-tolerant) |
| Short Answer | Claude semantic comparison with keyword extraction + partial credit |
| Essay | Claude weighted rubric: content 40%, structure 25%, evidence 20%, clarity 15% |
| Code | subprocess execution with test cases (5s timeout, sandboxed) |

### API Endpoints
| Method | Path | Description |
|---|---|---|
| POST | /assessments | Create assessment with questions |
| GET | /assessments | List user's assessments |
| GET | /assessments/{id} | Get assessment (correct answers hidden) |
| POST | /assessments/generate | AI-generate questions for a topic |
| POST | /assessments/quick-quiz | Inline quiz during tutoring (3-5 questions) |
| POST | /assessments/{id}/generate | AI-generate questions for existing assessment |
| POST | /assessments/{id}/submit | Submit answers + auto-grade |
| GET | /assessments/{id}/results | Get grading results |

### Question Validation (validator.py)
- Content must be non-empty
- Valid question type (mcq, short_answer, essay, code)
- MCQ: must have options list, correct_answer must be in options, no duplicate options
- Valid difficulty (easy, medium, hard)
- Positive points
- Duplicate detection (SequenceMatcher, threshold 0.85)

### Security
- All endpoints require JWT auth via `get_current_user`
- Correct answers are never exposed in question list responses
- Code execution uses subprocess with timeout=5s, capture_output=True
- Results only visible to the submitting student
- Input validation on all submission data

## Dependencies
- No new pip packages required (uses existing langchain-anthropic, SQLAlchemy, FastAPI)
