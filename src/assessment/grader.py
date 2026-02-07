"""Auto-grading engine with multi-strategy support."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import textwrap
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
                score=max(0, min(parsed.get("score", 0), max_score)),
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
                + (f"Additional rubric: {rubric}\n" if rubric else "")
                + f"Max score: {max_score}\n\n"
                f"Student essay:\n{answer}\n\n"
                "Grade this essay according to the weighted criteria."
            )),
        ])

        try:
            parsed = json.loads(response.content)
            score = max(0, min(parsed.get("score", 0), max_score))
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

        # Build sandboxed wrapper that restricts dangerous builtins
        sandbox_wrapper = textwrap.dedent("""\
            import resource as _resource
            # Set resource limits BEFORE restricting builtins
            # Limit memory to 50MB
            _resource.setrlimit(_resource.RLIMIT_AS, (50 * 1024 * 1024, 50 * 1024 * 1024))
            # Limit file size to 1MB
            _resource.setrlimit(_resource.RLIMIT_FSIZE, (1 * 1024 * 1024, 1 * 1024 * 1024))
            # No new processes
            _resource.setrlimit(_resource.RLIMIT_NPROC, (0, 0))
            del _resource

            import builtins as _builtins

            _original_import = _builtins.__import__

            def _make_safe_import(_orig, _blocked):
                def _safe_import(name, *args, **kwargs):
                    if name.split('.')[0] in _blocked:
                        raise ImportError(f"Module '{name}' is not allowed")
                    return _orig(name, *args, **kwargs)
                return _safe_import

            _builtins.__import__ = _make_safe_import(_original_import, frozenset({
                'os', 'sys', 'subprocess', 'shutil', 'signal',
                'socket', 'http', 'urllib', 'requests', 'pathlib',
                'ctypes', 'importlib', 'code', 'codeop', 'compileall',
                'multiprocessing', 'threading', 'resource',
            }))

            # Disable dangerous builtins
            for _name in ('exec', 'eval', 'compile', 'open', 'breakpoint', 'exit', 'quit'):
                if hasattr(_builtins, _name):
                    setattr(_builtins, _name, None)

            del _builtins, _original_import, _make_safe_import, _name
        """)

        full_code = f"{sandbox_wrapper}\n\n{answer}\n\n{test_code}"

        # Execute in a dedicated temp directory with sandboxing
        sandbox_dir = tempfile.mkdtemp(prefix="code_grade_")
        temp_path = os.path.join(sandbox_dir, "submission.py")
        try:
            with open(temp_path, "w") as f:
                f.write(full_code)

            result = subprocess.run(
                ["python3", "-I", temp_path],
                capture_output=True,
                text=True,
                timeout=5,
                env={},
                cwd=sandbox_dir,
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
                # Sanitize error output to avoid leaking internal paths
                error_msg = result.stderr[:500] if result.stderr else "Tests failed."
                # Strip file paths from error messages
                sanitized = error_msg.replace(temp_path, "<submission>")
                sanitized = sanitized.replace(sandbox_dir, "<sandbox>")
                return GradeResult(
                    question_id=q_id,
                    score=0,
                    max_score=max_score,
                    feedback=f"Tests failed: {sanitized}",
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
            # Clean up the entire sandbox directory
            import shutil
            shutil.rmtree(sandbox_dir, ignore_errors=True)
