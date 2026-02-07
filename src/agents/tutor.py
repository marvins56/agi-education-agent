from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING, Any

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.base import AgentConfig, AgentContext, AgentResponse, BaseAgent

if TYPE_CHECKING:
    from src.memory.manager import MemoryManager
    from src.rag.retriever import KnowledgeRetriever

VISUAL_KEYWORDS = re.compile(
    r"\b(graph|chart|diagram|plot|draw|visuali[sz]e|picture|image|illustration|figure|table|map)\b",
    re.IGNORECASE,
)


class TutorAgent(BaseAgent):
    """Adaptive tutoring agent that uses Socratic method."""

    def __init__(
        self,
        retriever: KnowledgeRetriever | None = None,
        memory: MemoryManager | None = None,
        config: AgentConfig | None = None,
    ):
        if config is None:
            config = AgentConfig(name="tutor")
        super().__init__(config)
        self.retriever = retriever
        self.memory = memory

    def get_system_prompt(self, context: AgentContext) -> str:
        """Build an adaptive system prompt from the student profile."""
        profile = context.student_profile
        name = profile.get("name", "Student")
        learning_style = profile.get("learning_style", "visual")
        pace = profile.get("pace", "moderate")
        grade_level = profile.get("grade_level", "")
        strengths = profile.get("strengths", [])
        weaknesses = profile.get("weaknesses", [])

        strengths_text = ", ".join(strengths) if strengths else "not yet identified"
        weaknesses_text = ", ".join(weaknesses) if weaknesses else "not yet identified"

        subject_line = ""
        if context.current_subject:
            subject_line = f"Current subject: {context.current_subject}"
            if context.current_topic:
                subject_line += f" — Topic: {context.current_topic}"

        objectives_text = ""
        if context.learning_objectives:
            objectives_text = "Learning objectives:\n" + "\n".join(
                f"- {obj}" for obj in context.learning_objectives
            )

        return (
            f"You are an expert adaptive tutor for {name}.\n"
            f"\n"
            f"Student profile:\n"
            f"- Learning style: {learning_style}\n"
            f"- Pace: {pace}\n"
            f"- Grade level: {grade_level}\n"
            f"- Strengths: {strengths_text}\n"
            f"- Weaknesses: {weaknesses_text}\n"
            f"\n"
            f"{subject_line}\n"
            f"{objectives_text}\n"
            f"\n"
            f"Teaching guidelines:\n"
            f"1. Use the Socratic method — guide discovery through questions rather than "
            f"giving answers directly.\n"
            f"2. Adapt to the student's learning style:\n"
            f"   - Visual: use diagrams, charts, and spatial representations.\n"
            f"   - Auditory: use verbal explanations, mnemonics, and discussions.\n"
            f"   - Kinesthetic: use hands-on examples, experiments, and practice problems.\n"
            f"   - Reading/Writing: use written explanations, lists, and note-taking prompts.\n"
            f"3. Break complex topics into smaller, manageable steps.\n"
            f"4. Encourage the student and celebrate progress.\n"
            f"5. Regularly check understanding before moving on.\n"
        )

    async def process(self, input_text: str, context: AgentContext) -> AgentResponse:
        """Process student input and generate a tutoring response."""
        start = time.time()

        # Retrieve relevant knowledge if a retriever is available.
        knowledge_context: list[dict[str, Any]] = []
        if self.retriever is not None:
            knowledge_context = await self.retriever.retrieve(
                query=input_text,
                subject=context.current_subject,
            )

        # Build message list.
        messages: list[SystemMessage | HumanMessage] = [
            SystemMessage(content=self.get_system_prompt(context)),
        ]

        if knowledge_context:
            sources_text = "\n\n".join(
                doc.get("content", "") for doc in knowledge_context
            )
            messages.append(
                SystemMessage(
                    content=(
                        "Relevant knowledge context (use to inform your answer, "
                        "but do not quote verbatim):\n\n" + sources_text
                    )
                )
            )

        # Include the last 10 turns of conversation history.
        for entry in context.conversation_history[-10:]:
            role = entry.get("role", "user")
            content = entry.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            else:
                messages.append(SystemMessage(content=content))

        messages.append(HumanMessage(content=input_text))

        # Call the LLM.
        response = await self.llm.ainvoke(messages)
        response_text: str = response.content  # type: ignore[assignment]

        elapsed = time.time() - start

        metadata: dict[str, Any] = {}
        if knowledge_context:
            metadata["knowledge_sources"] = [
                doc.get("source", "unknown") for doc in knowledge_context
            ]
        metadata["needs_visual_aid"] = self._needs_visual_aid(input_text, response_text)

        return AgentResponse(
            text=response_text,
            metadata=metadata,
            agent_name="tutor",
            processing_time=elapsed,
        )

    @staticmethod
    def _needs_visual_aid(input_text: str, response_text: str) -> bool:
        """Heuristic check for whether a visual aid would help."""
        return bool(
            VISUAL_KEYWORDS.search(input_text) or VISUAL_KEYWORDS.search(response_text)
        )
