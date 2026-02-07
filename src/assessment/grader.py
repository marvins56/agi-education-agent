"""Auto-grading engine with multi-strategy support."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from src.assessment.schemas import GradeResult
from src.config import settings


class AutoGrader:
    """Grade student submissions using type-specific strategies."""

    def __init__(self, llm: ChatAnthropic | None = None):
        if llm is None:
            self.llm = ChatAnthropic(
                model=settings.DEFAULT_MODEL,
                temperature=0.0,
                max_tokens=2048,
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
            )
        else:
            self.llm = llm

    async def grade_submission(
        self,
        questions: list[dict[str, Any]],
        answers: dict[str, str],
    ) -> list[GradeResult]:
        """Grade all answers, routing to the appropriate strategy per question type."""
        results: list[GradeResult] = []

        for question in questions:
            q_id = str(question.get("id", ""))
            answer = answers.get(q_id, "")
            qtype = question.get("type", "mcq")

            if qtype == "mcq":
                result = self._grade_mcq(question, answer)
            elif qtype == "short_answer":
                result = await self._grade_short_answer(question, answer)
            elif qtype == "essay":
                result = await self._grade_essay(question, answer)
            elif qtype == "code":
                result = await self._grade_code(question, answer)
            else:
                result = GradeResult(
                    question_id=q_id,
                    score=0,
                    max_score=question.get("points", 10),
                    feedback="Unsupported question type.",
                    correct=False,
                )

            results.append(result)

        return results

    @staticmethod
    def _grade_mcq(question: dict[str, Any], answer: str) -> GradeResult:
        """Grade MCQ with exact match."""
        q_id = str(question.get("id", ""))
        correct_answer = question.get("correct_answer", "")
        max_score = question.get("points", 10)

        is_correct = answer.strip().lower() == correct_answer.strip().lower()

        return GradeResult(
            question_id=q_id,
            score=max_score if is_correct else 0,
            max_score=max_score,
            feedback="Correct!" if is_correct else f"Incorrect. The correct answer is: {correct_answer}",
            correct=is_correct,
        )

    async def _grade_short_answer(
        self, question: dict[str, Any], answer: str
    ) -> GradeResult:
        """Grade short answer using Claude for semantic comparison."""
        q_id = str(question.get("id", ""))
        correct_answer = question.get("correct_answer", "")
        max_score = question.get("points", 10)

        if not answer.strip():
            return GradeResult(
                question_id=q_id,
                score=0,
                max_score=max_score,
                feedback="No answer provided.",
                correct=False,
            )

        response = await self.llm.ainvoke([
            SystemMessage(content=(
                "You are a fair and precise grading assistant. "
                "Evaluate the student's answer against the expected answer. "
                "Respond with JSON only: "
                '{"score": <0 to max_score>, "feedback": "<brief explanation>", "correct": <true/false>}'
            )),
            HumanMessage(content=(
                f"Question: {question.get('content', '')}\n"
                f"Expected answer (key terms): {correct_answer}\n"
                f"Student answer: {answer}\n"
                f"Max score: {max_score}\n\n"
                "Evaluate semantic correctness. Award partial credit for partially correct answers."
            )),
        ])

        try:
            parsed = json.loads(response.content)
            return GradeResult(
                question_id=q_id,
                score=min(parsed.get("score", 0), max_score),
                max_score=max_score,
                feedback=parsed.get("feedback", ""),
                correct=parsed.get("correct", False),
            )
        except (json.JSONDecodeError, TypeError):
            return GradeResult(
                question_id=q_id,
                score=0,
                max_score=max_score,
                feedback="Grading error — could not evaluate response.",
                correct=False,
            )

    # Default weighted rubric criteria for essays
    ESSAY_RUBRIC_WEIGHTS = {
        "content": 0.40,
        "structure": 0.25,
        "evidence": 0.20,
        "clarity": 0.15,
    }

    async def _grade_essay(
        self, question: dict[str, Any], answer: str
    ) -> GradeResult:
        """Grade essay using Claude with weighted rubric-based evaluation."""
        q_id = str(question.get("id", ""))
        rubric = question.get("rubric", "")
        max_score = question.get("points", 20)

        if not answer.strip():
            return GradeResult(
                question_id=q_id,
                score=0,
                max_score=max_score,
                feedback="No answer provided.",
                correct=False,
            )

        weights_text = "\n".join(
            f"- {criterion} ({int(weight * 100)}%)"
            for criterion, weight in self.ESSAY_RUBRIC_WEIGHTS.items()
        )

        response = await self.llm.ainvoke([
            SystemMessage(content=(
                "You are an expert essay grader. Evaluate the essay using weighted criteria.\n"
                f"Criteria weights:\n{weights_text}\n\n"
                "Respond with JSON only:\n"
                '{"score": <0 to max_score>, '
                '"criteria": {"content": <0-100>, "structure": <0-100>, '
                '"evidence": <0-100>, "clarity": <0-100>}, '
                '"feedback": "<detailed per-criteria feedback>", '
                '"correct": <true if score >= 60% of max>}'
            )),
            HumanMessage(content=(
                f"Essay prompt: {question.get('content', '')}\n"
                f"Additional rubric: {rubric}\n" if rubric else
                f"Essay prompt: {question.get('content', '')}\n"
                f"Max score: {max_score}\n\n"
                f"Student essay:\n{answer}\n\n"
                "Grade this essay according to the weighted criteria."
            )),
        ])

        try:
            parsed = json.loads(response.content)
            score = min(parsed.get("score", 0), max_score)
            return GradeResult(
                question_id=q_id,
                score=score,
                max_score=max_score,
                feedback=parsed.get("feedback", ""),
                correct=parsed.get("correct", score >= max_score * 0.6),
            )
        except (json.JSONDecodeError, TypeError):
            return GradeResult(
                question_id=q_id,
                score=0,
                max_score=max_score,
                feedback="Grading error — could not evaluate essay.",
                correct=False,
            )

    async def _grade_code(
        self, question: dict[str, Any], answer: str
    ) -> GradeResult:
        """Grade code by executing against test cases with resource limits."""
        q_id = str(question.get("id", ""))
        max_score = question.get("points", 15)

        if not answer.strip():
            return GradeResult(
                question_id=q_id,
                score=0,
                max_score=max_score,
                feedback="No code provided.",
                correct=False,
            )

        # Extract test code from correct_answer
        test_code = ""
        correct_answer = question.get("correct_answer", "")
        if correct_answer:
            try:
                test_data = json.loads(correct_answer)
                test_code = test_data.get("test_code", "")
            except (json.JSONDecodeError, TypeError):
                test_code = correct_answer

        if not test_code:
            return GradeResult(
                question_id=q_id,
                score=0,
                max_score=max_score,
                feedback="No test cases available for this question.",
                correct=False,
            )

        # Combine student code with test code
        full_code = f"{answer}\n\n{test_code}"

        # Execute in a subprocess with timeout
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, dir=tempfile.gettempdir()
        ) as f:
            f.write(full_code)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["python3", temp_path],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                return GradeResult(
                    question_id=q_id,
                    score=max_score,
                    max_score=max_score,
                    feedback="All tests passed!",
                    correct=True,
                )
            else:
                error_msg = result.stderr[:500] if result.stderr else "Tests failed."
                return GradeResult(
                    question_id=q_id,
                    score=0,
                    max_score=max_score,
                    feedback=f"Tests failed: {error_msg}",
                    correct=False,
                )
        except subprocess.TimeoutExpired:
            return GradeResult(
                question_id=q_id,
                score=0,
                max_score=max_score,
                feedback="Code execution timed out (5s limit).",
                correct=False,
            )
        finally:
            Path(temp_path).unlink(missing_ok=True)
