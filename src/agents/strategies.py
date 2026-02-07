"""Teaching strategy selection for adaptive tutoring."""

from enum import Enum


class TeachingStrategy(str, Enum):
    socratic = "socratic"
    direct_explanation = "direct_explanation"
    analogy = "analogy"
    worked_example = "worked_example"
    scaffolded = "scaffolded"


# Ordered list used when switching away from a failed strategy
_STRATEGY_ROTATION = [
    TeachingStrategy.socratic,
    TeachingStrategy.direct_explanation,
    TeachingStrategy.analogy,
    TeachingStrategy.worked_example,
    TeachingStrategy.scaffolded,
]

_STRATEGY_PROMPTS: dict[TeachingStrategy, str] = {
    TeachingStrategy.socratic: (
        "Use the Socratic method. Ask probing questions to guide the student "
        "toward understanding. Do not give the answer directly — help them discover it."
    ),
    TeachingStrategy.direct_explanation: (
        "Provide a clear, structured explanation. Start with the core concept, "
        "then add details. Use simple language appropriate to the student's level."
    ),
    TeachingStrategy.analogy: (
        "Teach using analogies and comparisons to familiar concepts. "
        "Create vivid mental models that connect new ideas to what the student already knows."
    ),
    TeachingStrategy.worked_example: (
        "Walk through a complete worked example step by step. "
        "Show each step clearly, explain the reasoning, then invite the student to try a similar problem."
    ),
    TeachingStrategy.scaffolded: (
        "Break the problem into small, manageable sub-tasks. "
        "Guide the student through each sub-task, providing hints when they get stuck, "
        "and gradually reduce support as they gain confidence."
    ),
}


class StrategySelector:
    """Select teaching strategy based on student state."""

    @staticmethod
    def select_strategy(
        learning_style: str,
        topic_mastery: float,
        attempt_count: int,
        previous_strategy: str | None = None,
    ) -> TeachingStrategy:
        """Pick the best strategy given student context.

        Rules (in priority order):
        1. If mastery < 20 -> direct_explanation (they need fundamentals)
        2. If attempt_count > 2 on same topic -> switch to a different strategy
        3. If learning_style == "visual" -> prefer analogy
        4. If learning_style == "kinesthetic" -> prefer worked_example
        5. Default -> socratic
        """
        # Rule 1: very low mastery needs direct instruction
        if topic_mastery < 20:
            candidate = TeachingStrategy.direct_explanation
            # Still switch if they've already tried this strategy 3+ times
            if attempt_count > 2 and previous_strategy == candidate.value:
                return _next_strategy(candidate, previous_strategy)
            return candidate

        # Rule 2: repeated attempts — switch strategy
        if attempt_count > 2 and previous_strategy:
            return _next_strategy(
                TeachingStrategy(previous_strategy)
                if previous_strategy in TeachingStrategy.__members__
                else TeachingStrategy.socratic,
                previous_strategy,
            )

        # Rule 3 & 4: learning style preferences
        if learning_style == "visual":
            return TeachingStrategy.analogy
        if learning_style == "kinesthetic":
            return TeachingStrategy.worked_example

        # Default
        return TeachingStrategy.socratic

    @staticmethod
    def get_strategy_prompt(strategy: TeachingStrategy) -> str:
        """Return teaching instructions for the given strategy."""
        return _STRATEGY_PROMPTS.get(strategy, _STRATEGY_PROMPTS[TeachingStrategy.socratic])


def _next_strategy(current: TeachingStrategy, previous: str | None) -> TeachingStrategy:
    """Pick the next strategy in rotation, skipping the previous one."""
    idx = _STRATEGY_ROTATION.index(current) if current in _STRATEGY_ROTATION else 0
    for offset in range(1, len(_STRATEGY_ROTATION)):
        candidate = _STRATEGY_ROTATION[(idx + offset) % len(_STRATEGY_ROTATION)]
        if candidate.value != previous:
            return candidate
    return _STRATEGY_ROTATION[(idx + 1) % len(_STRATEGY_ROTATION)]
