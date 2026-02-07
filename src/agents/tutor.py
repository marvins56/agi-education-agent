from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING, Any

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.base import AgentConfig, AgentContext, AgentResponse, BaseAgent
from src.agents.strategies import StrategySelector, TeachingStrategy

if TYPE_CHECKING:
    from src.memory.manager import MemoryManager
    from src.memory.student_context import StudentContextBuilder
    from src.rag.retriever import KnowledgeRetriever

VISUAL_KEYWORDS = re.compile(
    r"\b(graph|chart|diagram|plot|draw|visuali[sz]e|picture|image|illustration|figure|table|map)\b",
    re.IGNORECASE,
)


class TutorAgent(BaseAgent):
    """Adaptive tutoring agent with strategy selection and enriched context."""

    strategy_selector: StrategySelector = StrategySelector()

    def __init__(
        self,
        retriever: KnowledgeRetriever | None = None,
        memory: MemoryManager | None = None,
        context_builder: StudentContextBuilder | None = None,
        config: AgentConfig | None = None,
    ):
        if config is None:
            config = AgentConfig(name="tutor")
        super().__init__(config)
        self.retriever = retriever
        self.memory = memory
        self.context_builder = context_builder

    def get_system_prompt(
        self,
        context: AgentContext,
        strategy: TeachingStrategy | None = None,
        enriched_context: dict[str, Any] | None = None,
    ) -> str:
        """Build an adaptive system prompt from the student profile and strategy."""
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

        # Strategy-specific teaching instructions
        if strategy:
            strategy_instructions = (
                f"Teaching strategy: {strategy.value}\n"
                f"{self.strategy_selector.get_strategy_prompt(strategy)}\n"
            )
        else:
            strategy_instructions = (
                "Teaching guidelines:\n"
                "1. Use the Socratic method — guide discovery through questions rather than "
                "giving answers directly.\n"
                "2. Adapt to the student's learning style:\n"
                "   - Visual: use diagrams, charts, and spatial representations.\n"
                "   - Auditory: use verbal explanations, mnemonics, and discussions.\n"
                "   - Kinesthetic: use hands-on examples, experiments, and practice problems.\n"
                "   - Reading/Writing: use written explanations, lists, and note-taking prompts.\n"
                "3. Break complex topics into smaller, manageable steps.\n"
                "4. Encourage the student and celebrate progress.\n"
                "5. Regularly check understanding before moving on.\n"
            )

        # Enriched context section
        enriched_section = ""
        if enriched_context:
            struggles = enriched_context.get("struggle_points", [])
            if struggles:
                struggle_topics = ", ".join(
                    f"{s['topic']} ({s['mastery_score']:.0f}%)" for s in struggles[:5]
                )
                enriched_section += f"\nStruggle areas: {struggle_topics}\n"

            mastery = enriched_context.get("mastery_scores", [])
            if mastery:
                mastery_summary = ", ".join(
                    f"{m['topic']}: {m['mastery_score']:.0f}%"
                    for m in mastery[:5]
                )
                enriched_section += f"Recent mastery: {mastery_summary}\n"

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
            f"{enriched_section}\n"
            f"{strategy_instructions}"
        )

    async def process(self, input_text: str, context: AgentContext) -> AgentResponse:
        """Process student input and generate a tutoring response."""
        start = time.time()

        # Build enriched context if context_builder is available
        enriched_context: dict[str, Any] | None = None
        if self.context_builder:
            try:
                enriched_context = await self.context_builder.build_context(
                    student_id=context.student_id,
                    session_id=context.session_id,
                )
            except Exception:
                enriched_context = None

        # Select teaching strategy based on student mastery and history
        strategy: TeachingStrategy | None = None
        topic_mastery = 50.0  # default if unknown
        attempt_count = 0
        previous_strategy: str | None = None

        if enriched_context:
            mastery_scores = enriched_context.get("mastery_scores", [])
            if context.current_topic and mastery_scores:
                for m in mastery_scores:
                    if m.get("topic") == context.current_topic:
                        topic_mastery = m.get("mastery_score", 50.0)
                        attempt_count = m.get("attempts", 0)
                        break

            session_state = enriched_context.get("session_state", {})
            previous_strategy = session_state.get("last_strategy")

        learning_style = context.student_profile.get("learning_style", "balanced")
        strategy = self.strategy_selector.select_strategy(
            learning_style=learning_style,
            topic_mastery=topic_mastery,
            attempt_count=attempt_count,
            previous_strategy=previous_strategy,
        )

        # Track confusion if same topic asked 3+ times
        if self.memory and context.current_topic:
            try:
                confusion_count = await self.memory.track_confusion(
                    context.session_id, context.current_topic
                )
                if confusion_count >= 3:
                    # Switch to scaffolded for confused students
                    strategy = TeachingStrategy.scaffolded
            except Exception:
                pass

        # Retrieve relevant knowledge if a retriever is available.
        knowledge_context: list[dict[str, Any]] = []
        if self.retriever is not None:
            knowledge_context = await self.retriever.retrieve(
                query=input_text,
                subject=context.current_subject,
            )

        # Build message list.
        messages: list[SystemMessage | HumanMessage] = [
            SystemMessage(
                content=self.get_system_prompt(context, strategy, enriched_context)
            ),
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
        if strategy:
            metadata["teaching_strategy"] = strategy.value

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
