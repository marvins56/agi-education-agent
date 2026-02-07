"""AI-powered question generation using Claude."""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import settings


class QuestionGenerator:
    """Generate assessment questions using an LLM."""

    def __init__(self, llm: ChatAnthropic | None = None):
        if llm is None:
            self.llm = ChatAnthropic(
                model=settings.DEFAULT_MODEL,
                temperature=0.7,
                max_tokens=4096,
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
            )
        else:
            self.llm = llm

    async def generate_questions(
        self,
        subject: str,
        topic: str,
        count: int,
        types: list[str],
        difficulty: str,
        context: str = "",
    ) -> list[dict[str, Any]]:
        """Generate questions for the given parameters using Claude."""
        questions: list[dict[str, Any]] = []

        per_type = max(1, count // len(types))
        remainder = count - per_type * len(types)

        for i, qtype in enumerate(types):
            n = per_type + (1 if i < remainder else 0)
            prompt = self._build_generation_prompt(subject, topic, qtype, difficulty, context, n)

            response = await self.llm.ainvoke([
                SystemMessage(content=(
                    "You are an expert educational assessment creator. "
                    "Always respond with valid JSON only, no markdown fences."
                )),
                HumanMessage(content=prompt),
            ])

            parsed = self._parse_json_response(response.content)
            questions.extend(parsed)

        return questions[:count]

    def _build_generation_prompt(
        self,
        subject: str,
        topic: str,
        qtype: str,
        difficulty: str,
        context: str,
        count: int,
    ) -> str:
        """Build a prompt tailored to the question type."""
        base = (
            f"Generate {count} {difficulty} difficulty {qtype} question(s) "
            f"about {topic} in the subject of {subject}.\n"
        )

        if context:
            base += f"\nAdditional context: {context}\n"

        format_instructions = {
            "mcq": (
                'Return a JSON array. Each element must have:\n'
                '- "type": "mcq"\n'
                '- "content": the question text\n'
                '- "options": array of exactly 4 options (1 correct, 3 plausible distractors)\n'
                '- "correct_answer": the correct option text (must match one of the options exactly)\n'
                f'- "difficulty": "{difficulty}"\n'
                '- "points": 10'
            ),
            "short_answer": (
                'Return a JSON array. Each element must have:\n'
                '- "type": "short_answer"\n'
                '- "content": the question text\n'
                '- "correct_answer": expected answer with key terms separated by semicolons\n'
                f'- "difficulty": "{difficulty}"\n'
                '- "points": 10'
            ),
            "essay": (
                'Return a JSON array. Each element must have:\n'
                '- "type": "essay"\n'
                '- "content": the essay prompt\n'
                '- "rubric": detailed rubric with criteria and point distribution\n'
                f'- "difficulty": "{difficulty}"\n'
                '- "points": 20'
            ),
            "code": (
                'Return a JSON array. Each element must have:\n'
                '- "type": "code"\n'
                '- "content": the coding problem description\n'
                '- "correct_answer": JSON string containing {"test_code": "python test code that '
                'calls the student function and uses assert statements"}\n'
                f'- "difficulty": "{difficulty}"\n'
                '- "points": 15'
            ),
        }

        base += "\n" + format_instructions.get(qtype, format_instructions["mcq"])
        return base

    @staticmethod
    def _parse_json_response(content: str) -> list[dict[str, Any]]:
        """Parse LLM response into a list of question dicts."""
        if not isinstance(content, str):
            content = str(content)

        # Strip markdown code fences if present
        content = re.sub(r"```(?:json)?\s*", "", content)
        content = re.sub(r"```\s*$", "", content)
        content = content.strip()

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            # Try to find a JSON array in the content
            match = re.search(r"\[.*\]", content, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
            else:
                return []

        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict) and "questions" in parsed:
            return parsed["questions"]
        return [parsed]
