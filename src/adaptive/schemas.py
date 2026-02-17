"""Adaptive learning data schemas and models."""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field
from dataclasses import dataclass
import numpy as np


class LearningObjective(str, Enum):
    """Learning objectives aligned with Bloom's taxonomy."""
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class HistoryThinkingSkill(str, Enum):
    """Historical thinking skills taxonomy."""
    CHRONOLOGICAL_REASONING = "chronological_reasoning"
    CRAFTING_ARGUMENTS = "crafting_arguments"
    ANALYZING_SOURCES = "analyzing_sources"
    CONTEXTUALIZATION = "contextualization"
    SYNTHESIS = "synthesis"


class CognitiveLoadType(str, Enum):
    """Types of cognitive load."""
    INTRINSIC = "intrinsic"      # Inherent difficulty of material
    EXTRANEOUS = "extraneous"    # Poor instructional design
    GERMANE = "germane"          # Processing that builds schemas


@dataclass
class StudentInteraction:
    """Single student learning interaction."""
    student_id: str
    session_id: str
    concept_id: int               # Index in concept vocabulary
    concept_name: str
    question_type: str           # "multiple_choice", "essay", "timeline", etc.
    correctness: float           # 0.0-1.0 for partial credit
    response_time_seconds: float
    hint_count: int
    difficulty_level: float      # 0.0-1.0
    context_features: Dict[str, float]  # Additional context
    timestamp: datetime


@dataclass
class ConceptEmbedding:
    """Concept representation with relationships."""
    concept_id: int
    concept_name: str
    subject: str
    prerequisites: List[int]     # Concept IDs this depends on
    enables: List[int]           # Concept IDs this unlocks
    difficulty: float           # Inherent difficulty 0.0-1.0
    importance: float           # Curriculum importance 0.0-1.0
    embedding_vector: Optional[np.ndarray] = None  # Dense representation


class KnowledgeState(BaseModel):
    """Student's knowledge state at a point in time."""
    student_id: str
    concept_probabilities: Dict[str, float]  # concept_name -> mastery probability
    confidence_intervals: Dict[str, Tuple[float, float]]  # confidence bounds
    knowledge_growth_rate: float
    forgetting_rate: float
    learning_efficiency: float
    last_updated: datetime
    interaction_count: int


class FSRSCard(BaseModel):
    """FSRS card state for spaced repetition."""
    concept_id: int
    concept_name: str
    student_id: str
    
    # FSRS parameters
    stability: float = Field(ge=0.0)      # Memory stability in days
    difficulty: float = Field(ge=0.0, le=10.0)  # Learning difficulty
    retrievability: float = Field(ge=0.0, le=1.0)  # Current recall probability
    
    # Scheduling
    due_date: datetime
    last_review: Optional[datetime] = None
    review_count: int = 0
    
    # Performance tracking
    average_response_time: float = 0.0
    success_rate: float = 0.0
    consecutive_successes: int = 0


class AdaptiveRecommendation(BaseModel):
    """Recommendation from adaptive learning engine."""
    student_id: str
    
    # Next learning actions
    next_concept: Optional[str] = None
    next_difficulty: float = Field(ge=0.0, le=1.0)
    teaching_strategy: str
    
    # Review recommendations  
    concepts_to_review: List[Tuple[str, datetime]]  # (concept, due_date)
    
    # Difficulty adjustments
    difficulty_adjustments: Dict[str, float]  # concept -> new difficulty
    
    # Learning path
    recommended_sequence: List[str]  # Concept names in order
    
    # Confidence metrics
    recommendation_confidence: float = Field(ge=0.0, le=1.0)
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.now)
    reasoning: str = ""


class HistoryKnowledgeGraph(BaseModel):
    """Knowledge graph structure for History concepts."""
    concepts: Dict[int, ConceptEmbedding] = {}
    prerequisite_matrix: Optional[np.ndarray] = None  # [num_concepts, num_concepts]
    difficulty_matrix: Optional[np.ndarray] = None    # [num_concepts, num_concepts] - difficulty relationships
    
    # History-specific structures
    chronological_ordering: Dict[str, List[int]] = {}  # time_period -> concept_ids
    thematic_clusters: Dict[str, List[int]] = {}       # theme -> concept_ids
    thinking_skill_mapping: Dict[HistoryThinkingSkill, List[int]] = {}
    
    class Config:
        arbitrary_types_allowed = True
    
    @classmethod
    def build_history_graph(cls) -> 'HistoryKnowledgeGraph':
        """Build comprehensive History knowledge graph."""
        # Basic implementation for now - will be enhanced
        return cls()


class LearningStyleProfile(BaseModel):
    """Student's learning style profile."""
    student_id: str
    
    # Learning preferences (0.0-1.0)
    visual_preference: float = 0.5
    auditory_preference: float = 0.5
    kinesthetic_preference: float = 0.5
    reading_preference: float = 0.5
    
    # Processing styles
    sequential_vs_global: float = 0.5    # 0=sequential, 1=global
    active_vs_reflective: float = 0.5    # 0=active, 1=reflective
    sensing_vs_intuitive: float = 0.5    # 0=sensing, 1=intuitive
    
    # Engagement patterns
    preferred_session_length_minutes: int = 30
    optimal_difficulty_preference: float = 0.6  # Slightly challenging
    feedback_frequency_preference: float = 0.8  # Frequent feedback
    
    # Performance indicators
    attention_span_indicator: float = 0.5
    motivation_level: float = 0.7
    self_regulation_skill: float = 0.5
    
    last_updated: datetime = Field(default_factory=datetime.now)


class DifficultyCalibration(BaseModel):
    """Difficulty calibration for concepts and students."""
    concept_name: str
    student_id: str
    
    # Current calibration
    current_difficulty: float = Field(ge=0.0, le=1.0)
    target_success_rate: float = 0.75  # Target 75% success rate
    actual_success_rate: float = 0.0
    
    # Calibration history
    difficulty_history: List[Tuple[datetime, float]] = []
    performance_history: List[Tuple[datetime, float]] = []
    
    # Adjustment parameters
    adjustment_rate: float = 0.1  # How quickly to adjust difficulty
    confidence_interval: Tuple[float, float] = (0.0, 1.0)
    
    last_calibrated: datetime = Field(default_factory=datetime.now)


class MasteryThreshold(BaseModel):
    """Mastery thresholds for concepts."""
    concept_name: str
    
    # Threshold levels
    basic_understanding: float = 0.6    # Basic comprehension
    functional_mastery: float = 0.75    # Can apply knowledge
    advanced_mastery: float = 0.9       # Can teach others
    
    # Requirements
    minimum_interactions: int = 3        # Minimum attempts before mastery
    consistency_required: int = 2        # Consecutive successes needed
    
    # Time factors
    retention_period_days: int = 14     # How long mastery must be maintained
    decay_rate: float = 0.05           # How fast mastery decays without practice


class AdaptiveLearningMetrics(BaseModel):
    """Metrics for adaptive learning system performance."""
    student_id: str
    
    # Learning efficiency metrics
    concepts_learned_per_hour: float = 0.0
    average_time_to_mastery_minutes: float = 0.0
    retention_rate_after_week: float = 0.0
    
    # Engagement metrics
    session_completion_rate: float = 0.0
    voluntary_practice_frequency: float = 0.0
    help_seeking_behavior_score: float = 0.0
    
    # System accuracy metrics
    prediction_accuracy: float = 0.0      # How well we predict performance
    recommendation_acceptance_rate: float = 0.0
    difficulty_calibration_accuracy: float = 0.0
    
    # Progress metrics
    knowledge_growth_velocity: float = 0.0  # Rate of knowledge acquisition
    learning_momentum: float = 0.0          # Consistency of progress
    plateau_detection_score: float = 0.0   # When learning stalls
    
    calculation_date: datetime = Field(default_factory=datetime.now)