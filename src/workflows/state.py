"""Workflow state definitions for educational flows."""
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, TypedDict, Annotated
from langgraph.graph import add_messages
from pydantic import BaseModel, Field


class StudentIntent(str, Enum):
    """Classified student intents."""
    NEW_TOPIC = "new_topic"                    # "Tell me about the French Revolution"
    CLARIFICATION = "clarification"            # "I don't understand what you mean"
    PRACTICE = "practice"                      # "Can I try some problems?"
    ASSESSMENT = "assessment"                  # "Test my knowledge"
    REVIEW = "review"                         # "Let's go over what we learned"
    HELP_STUCK = "help_stuck"                 # "I'm stuck on this problem"
    CASUAL = "casual"                         # General conversation
    META_LEARNING = "meta_learning"           # Questions about learning itself


class WorkflowType(str, Enum):
    """Types of educational workflows."""
    CONCEPT_EXPLANATION = "concept_explanation"
    SOCRATIC_QUESTIONING = "socratic_questioning"
    PRACTICE_PROBLEMS = "practice_problems"
    ASSESSMENT_FLOW = "assessment_flow"
    REVIEW_SESSION = "review_session"
    HISTORY_TIMELINE = "history_timeline"
    SOURCE_ANALYSIS = "source_analysis"
    CAUSE_EFFECT_ANALYSIS = "cause_effect_analysis"
    DBQ_ESSAY = "dbq_essay"


class LearningPhase(str, Enum):
    """Phases of learning process."""
    ASSESS_PRIOR_KNOWLEDGE = "assess_prior_knowledge"
    INTRODUCE_CONCEPT = "introduce_concept"
    GUIDED_PRACTICE = "guided_practice"
    INDEPENDENT_PRACTICE = "independent_practice"
    ASSESSMENT = "assessment"
    REVIEW_REINFORCE = "review_reinforce"
    APPLY_TRANSFER = "apply_transfer"


class HistoryThinkingSkill(str, Enum):
    """Historical thinking skills progression."""
    CHRONOLOGICAL_REASONING = "chronological_reasoning"
    CRAFTING_ARGUMENTS = "crafting_arguments"
    ANALYZING_SOURCES = "analyzing_sources"
    CONTEXTUALIZATION = "contextualization"
    SYNTHESIS = "synthesis"


class WorkflowState(TypedDict):
    """Base state for all educational workflows."""
    # Message handling
    messages: Annotated[List[Dict[str, str]], add_messages]
    
    # Student context
    student_id: str
    session_id: str
    student_intent: Optional[StudentIntent]
    
    # Educational context
    current_topic: Optional[str]
    subject: Optional[str]
    learning_objectives: List[str]
    prior_knowledge_level: float  # 0.0-1.0
    
    # Workflow control
    workflow_type: Optional[WorkflowType]
    current_phase: Optional[LearningPhase]
    phase_attempts: int
    max_phase_attempts: int
    
    # Educational tracking
    concepts_covered: List[str]
    misconceptions_identified: List[str]
    breakthrough_moments: List[str]
    engagement_level: float  # 0.0-1.0
    
    # Teaching strategy
    teaching_strategy: Optional[str]
    adaptation_history: List[Dict[str, Any]]
    
    # Flow control
    next_action: Optional[str]
    workflow_complete: bool
    should_exit: bool
    
    # Metadata
    workflow_start_time: datetime
    last_update_time: datetime
    debug_info: Dict[str, Any]


class ConceptExplanationState(WorkflowState):
    """State for concept explanation workflow."""
    concept_name: str
    explanation_depth: str  # "basic", "intermediate", "advanced"
    scaffolding_level: float  # 0.0-1.0, how much guidance to provide
    understanding_checks: List[Dict[str, Any]]
    visual_aids_used: List[str]


class SocraticQuestioningState(WorkflowState):
    """State for Socratic questioning workflow."""
    target_insight: str  # What we want student to discover
    question_sequence: List[str]
    current_question_index: int
    student_responses: List[str]
    discovery_level: float  # 0.0-1.0, how close to insight


class PracticeProblemsState(WorkflowState):
    """State for practice problems workflow."""
    problem_type: str
    difficulty_level: float  # 0.0-1.0
    problems_attempted: int
    problems_correct: int
    current_problem: Optional[Dict[str, Any]]
    hint_level: int  # 0 = no hints, increasing = more guidance
    mistakes_log: List[Dict[str, Any]]


class AssessmentFlowState(WorkflowState):
    """State for assessment workflow."""
    assessment_type: str  # "formative", "summative", "diagnostic"
    questions: List[Dict[str, Any]]
    current_question_index: int
    responses: List[Dict[str, Any]]
    scores: Dict[str, float]
    feedback_generated: bool


class HistoryTimelineState(WorkflowState):
    """State for History timeline exploration."""
    time_period: str  # "Ancient Rome", "World War I", etc.
    timeline_events: List[Dict[str, Any]]
    current_focus_event: Optional[Dict[str, Any]]
    connections_explored: List[str]
    thinking_skill_focus: HistoryThinkingSkill


class SourceAnalysisState(WorkflowState):
    """State for primary source analysis."""
    source_document: Dict[str, Any]
    analysis_questions: List[str]
    current_question_index: int
    student_analysis: List[str]
    source_context_provided: bool
    bias_discussion_completed: bool


class WorkflowResult(BaseModel):
    """Result of a workflow execution."""
    workflow_type: WorkflowType
    final_state: Dict[str, Any]
    learning_outcomes: List[str]
    concepts_mastered: List[str]
    engagement_score: float = Field(ge=0.0, le=1.0)
    time_spent_minutes: float
    next_recommended_actions: List[str] = Field(default_factory=list)
    student_feedback: Optional[str] = None
    teacher_notes: Optional[str] = None
    
    # Assessment results
    assessment_scores: Dict[str, float] = Field(default_factory=dict)
    areas_needing_work: List[str] = Field(default_factory=list)
    strengths_identified: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))