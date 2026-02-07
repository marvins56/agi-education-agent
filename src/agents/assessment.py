"""Assessment agent — generates assessments and grades submissions."""

from __future__ import annotations

import time
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.base import AgentConfig, AgentContext, AgentResponse, BaseAgent
from src.assessment.generator import QuestionGenerator
from src.assessment.grader import AutoGrader


class AssessmentAgent(BaseAgent):
    """Agent specialized in assessment generation and grading."""

    def __init__(self, config: AgentConfig | None = None):
        if config is None:
            config = AgentConfig(name="assessment", temperature=0.5)
        super().__init__(config)
        self.generator = QuestionGenerator(llm=self.llm)
        self.grader = AutoGrader(llm=self.llm)

    def get_system_prompt(self, context: AgentContext) -> str:
        """Build system prompt for assessment-related interactions."""
        profile = context.student_profile
        name = profile.get("name", "Student")
        grade_level = profile.get("grade_level", "")

        subject_line = ""
        if context.current_subject:
            subject_line = f"Current subject: {context.current_subject}"
            if context.current_topic:
                subject_line += f" — Topic: {context.current_topic}"

        return (
            f"You are an expert assessment specialist for {name}.\n"
            f"\n"
            f"Student grade level: {grade_level}\n"
            f"{subject_line}\n"
            f"\n"
            f"Your role:\n"
            f"1. Generate well-structured assessments (quizzes, exams, homework).\n"
            f"2. Create questions appropriate to the student's level.\n"
            f"3. Provide detailed, constructive feedback when grading.\n"
            f"4. Suggest areas for improvement based on assessment results.\n"
        )

    async def process(self, input_text: str, context: AgentContext) -> AgentResponse:
        """Process assessment-related requests."""
        start = time.time()

        messages = [
            SystemMessage(content=self.get_system_prompt(context)),
        ]

        for entry in context.conversation_history[-10:]:
            role = entry.get("role", "user")
            content = entry.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            else:
                messages.append(SystemMessage(content=content))

        messages.append(HumanMessage(content=input_text))

        response = await self.llm.ainvoke(messages)
        response_text: str = response.content  # type: ignore[assignment]

        elapsed = time.time() - start

        metadata: dict[str, Any] = {"agent_type": "assessment"}

        return AgentResponse(
            text=response_text,
            metadata=metadata,
            agent_name="assessment",
            processing_time=elapsed,
        )
