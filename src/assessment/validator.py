"""Validation utilities for generated assessment questions."""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any


class QuestionValidator:
    """Validates generated questions for quality and correctness."""

    DUPLICATE_THRESHOLD = 0.85

    def validate_questions(self, questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Run all validation checks and return only valid, deduplicated questions."""
        valid = []
        for q in questions:
            errors = self._validate_single(q)
            if not errors:
                valid.append(q)

        return self._remove_duplicates(valid)

    def _validate_single(self, question: dict[str, Any]) -> list[str]:
        """Validate a single question dict. Return list of error strings (empty = valid)."""
        errors: list[str] = []
        qtype = question.get("type", "")
        content = question.get("content", "")

        if not content or not content.strip():
            errors.append("Question content is empty.")

        if qtype not in ("mcq", "short_answer", "essay", "code"):
            errors.append(f"Invalid question type: {qtype}")

        if qtype == "mcq":
            errors.extend(self._validate_mcq(question))

        difficulty = question.get("difficulty", "medium")
        if difficulty not in ("easy", "medium", "hard"):
            errors.append(f"Invalid difficulty: {difficulty}")

        points = question.get("points", 10)
        if not isinstance(points, (int, float)) or points <= 0:
            errors.append("Points must be a positive number.")

        return errors

    @staticmethod
    def _validate_mcq(question: dict[str, Any]) -> list[str]:
        """MCQ-specific validation."""
        errors: list[str] = []
        options = question.get("options")
        correct_answer = question.get("correct_answer", "")

        if not options or not isinstance(options, list):
            errors.append("MCQ must have an options list.")
            return errors

        if len(options) < 2:
            errors.append("MCQ must have at least 2 options.")

        if len(options) != len(set(options)):
            errors.append("MCQ options contain duplicates.")

        if correct_answer and correct_answer not in options:
            errors.append("Correct answer not found in options list.")

        return errors

    def _remove_duplicates(self, questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Remove near-duplicate questions based on content similarity."""
        unique: list[dict[str, Any]] = []
        for q in questions:
            content = q.get("content", "")
            is_dup = False
            for existing in unique:
                similarity = SequenceMatcher(
                    None, content.lower(), existing.get("content", "").lower()
                ).ratio()
                if similarity >= self.DUPLICATE_THRESHOLD:
                    is_dup = True
                    break
            if not is_dup:
                unique.append(q)
        return unique
