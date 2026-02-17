"""History-specific data models and schemas."""
from datetime import datetime, date
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class HistoricalPeriod(str, Enum):
    """Major historical periods."""
    PREHISTORY = "prehistory"
    ANCIENT_WORLD = "ancient_world"
    CLASSICAL_ANTIQUITY = "classical_antiquity"
    MEDIEVAL = "medieval"
    RENAISSANCE = "renaissance"
    EARLY_MODERN = "early_modern"
    INDUSTRIAL_AGE = "industrial_age"
    MODERN_ERA = "modern_era"
    CONTEMPORARY = "contemporary"


class EventType(str, Enum):
    """Types of historical events."""
    POLITICAL = "political"
    MILITARY = "military"
    ECONOMIC = "economic"
    SOCIAL = "social"
    CULTURAL = "cultural"
    TECHNOLOGICAL = "technological"
    RELIGIOUS = "religious"
    DIPLOMATIC = "diplomatic"


class SourceType(str, Enum):
    """Types of primary sources."""
    DOCUMENT = "document"
    LETTER = "letter"
    DIARY = "diary"
    SPEECH = "speech"
    TREATY = "treaty"
    PHOTOGRAPH = "photograph"
    ARTWORK = "artwork"
    ARTIFACT = "artifact"
    NEWSPAPER = "newspaper"
    GOVERNMENT_RECORD = "government_record"
    MEMOIR = "memoir"
    ORAL_HISTORY = "oral_history"


class HistoricalThinkingSkill(str, Enum):
    """Historical thinking skills framework."""
    CHRONOLOGICAL_REASONING = "chronological_reasoning"
    COMPARISON_CONTEXTUALIZATION = "comparison_contextualization"
    CRAFTING_ARGUMENTS = "crafting_arguments"
    HISTORICAL_INTERPRETATION = "historical_interpretation"
    SOURCE_ANALYSIS = "source_analysis"
    CAUSATION = "causation"
    PATTERNS_OF_CONTINUITY = "patterns_of_continuity"


# Timeline Models
class HistoricalEvent(BaseModel):
    """Individual historical event."""
    event_id: str
    title: str
    description: str
    date_start: Union[date, str]  # Can be partial dates like "1914" or "Summer 1941"
    date_end: Optional[Union[date, str]] = None
    
    # Categorization
    event_type: EventType
    period: HistoricalPeriod
    significance: float = Field(ge=0.0, le=1.0, description="Historical significance")
    
    # Geographic context
    location: Optional[str] = None
    countries_involved: List[str] = Field(default_factory=list)
    
    # Relationships
    causes: List[str] = Field(default_factory=list)  # Event IDs that led to this
    effects: List[str] = Field(default_factory=list)  # Event IDs this led to
    related_events: List[str] = Field(default_factory=list)
    
    # Key figures
    key_figures: List[str] = Field(default_factory=list)
    
    # Sources and evidence
    primary_sources: List[str] = Field(default_factory=list)
    
    # Educational metadata
    grade_level: Optional[int] = None
    concepts_taught: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Timeline(BaseModel):
    """Collection of events forming a timeline."""
    timeline_id: str
    title: str
    description: str
    theme: str  # "World War I", "Civil Rights Movement", etc.
    
    events: List[HistoricalEvent] = Field(default_factory=list)
    date_range_start: Union[date, str]
    date_range_end: Union[date, str]
    
    # Educational context
    grade_levels: List[int] = Field(default_factory=list)
    learning_objectives: List[str] = Field(default_factory=list)
    
    # Metadata
    created_by: Optional[str] = None
    difficulty_level: float = Field(ge=0.0, le=1.0, default=0.5)
    estimated_study_time_minutes: int = 30
    
    created_at: datetime = Field(default_factory=datetime.now)


# Primary Source Models
class PrimarySource(BaseModel):
    """Primary source document or artifact."""
    source_id: str
    title: str
    description: str
    source_type: SourceType
    
    # Content
    content: Optional[str] = None  # Transcribed text content
    image_url: Optional[str] = None
    document_url: Optional[str] = None
    
    # Historical context
    date_created: Union[date, str]
    author: Optional[str] = None
    origin_location: Optional[str] = None
    historical_period: HistoricalPeriod
    
    # Analysis framework
    intended_audience: Optional[str] = None
    purpose: Optional[str] = None
    biases: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    
    # Relationships
    related_events: List[str] = Field(default_factory=list)  # Event IDs
    corroborating_sources: List[str] = Field(default_factory=list)  # Source IDs
    contradicting_sources: List[str] = Field(default_factory=list)  # Source IDs
    
    # Educational metadata
    complexity_level: float = Field(ge=0.0, le=1.0, default=0.5)
    key_concepts: List[str] = Field(default_factory=list)
    discussion_questions: List[str] = Field(default_factory=list)
    
    # Authenticity and reliability
    authenticity_verified: bool = False
    reliability_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    created_at: datetime = Field(default_factory=datetime.now)


class SourceAnalysis(BaseModel):
    """Student's analysis of a primary source."""
    analysis_id: str
    student_id: str
    source_id: str
    
    # Analysis components
    source_description: str
    author_purpose: str
    intended_audience: str
    historical_context: str
    
    # Critical analysis
    biases_identified: List[str] = Field(default_factory=list)
    limitations_noted: List[str] = Field(default_factory=list)
    reliability_assessment: str
    
    # Connections
    connections_to_events: List[str] = Field(default_factory=list)
    connections_to_other_sources: List[str] = Field(default_factory=list)
    
    # Evidence evaluation
    evidence_quality: float = Field(ge=0.0, le=1.0)
    usefulness_for_historian: str
    
    # Grading
    score: Optional[float] = Field(None, ge=0.0, le=100.0)
    feedback: Optional[str] = None
    rubric_scores: Dict[str, float] = Field(default_factory=dict)
    
    completed_at: datetime = Field(default_factory=datetime.now)


# DBQ (Document-Based Question) Models
class DBQDocument(BaseModel):
    """Document in a DBQ set."""
    document_id: str
    document_label: str  # "Document A", "Document B", etc.
    source: PrimarySource
    
    # DBQ-specific annotations
    guiding_questions: List[str] = Field(default_factory=list)
    key_points_highlighted: List[str] = Field(default_factory=list)
    background_context: Optional[str] = None


class DBQPrompt(BaseModel):
    """DBQ essay prompt and requirements."""
    prompt_id: str
    title: str
    historical_question: str
    task_description: str
    
    # Context
    historical_context_provided: str
    time_period: str
    geographic_focus: Optional[str] = None
    
    # Requirements
    essay_length_words: int = 1000
    minimum_documents_required: int = 4
    outside_evidence_required: bool = True
    
    # Learning objectives
    historical_thinking_skills: List[HistoricalThinkingSkill] = Field(default_factory=list)
    concepts_assessed: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.now)


class DBQSet(BaseModel):
    """Complete DBQ with prompt and documents."""
    dbq_id: str
    title: str
    prompt: DBQPrompt
    documents: List[DBQDocument] = Field(default_factory=list)
    
    # Educational metadata
    grade_level: int = 11  # Default to AP US History level
    estimated_time_minutes: int = 60
    difficulty_level: float = Field(ge=0.0, le=1.0, default=0.7)
    
    # Historical period and theme
    historical_period: HistoricalPeriod
    theme: str
    
    created_at: datetime = Field(default_factory=datetime.now)


class DBQEssay(BaseModel):
    """Student's DBQ essay response."""
    essay_id: str
    student_id: str
    dbq_id: str
    
    # Essay content
    thesis_statement: str
    body_paragraphs: List[str] = Field(default_factory=list)
    conclusion: str
    full_text: str
    
    # Document usage tracking
    documents_used: List[str] = Field(default_factory=list)  # Document IDs
    document_citations: Dict[str, List[str]] = Field(default_factory=dict)  # Doc ID -> citations
    outside_evidence: List[str] = Field(default_factory=list)
    
    # Analysis tracking
    arguments_made: List[str] = Field(default_factory=list)
    evidence_provided: List[str] = Field(default_factory=list)
    counterarguments_addressed: List[str] = Field(default_factory=list)
    
    # Grading
    score: Optional[float] = Field(None, ge=0.0, le=100.0)
    rubric_scores: Dict[str, float] = Field(default_factory=dict)
    feedback: Optional[str] = None
    
    # Metadata
    word_count: int = 0
    time_spent_minutes: int = 0
    draft_number: int = 1
    
    submitted_at: datetime = Field(default_factory=datetime.now)


# Causation and Reasoning Models
class CausalRelationship(BaseModel):
    """Cause-and-effect relationship between events."""
    relationship_id: str
    cause_event_id: str
    effect_event_id: str
    
    # Relationship strength
    causation_strength: float = Field(ge=0.0, le=1.0, description="How direct the causation is")
    time_delay: Optional[str] = None  # "immediate", "short-term", "long-term"
    
    # Explanation
    explanation: str
    mechanism: str  # How the cause led to the effect
    
    # Alternative perspectives
    historians_agree: bool = True
    alternative_explanations: List[str] = Field(default_factory=list)
    
    # Evidence
    supporting_evidence: List[str] = Field(default_factory=list)
    contradicting_evidence: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.now)


class HistoricalArgument(BaseModel):
    """Structured historical argument."""
    argument_id: str
    student_id: Optional[str] = None
    
    # Argument structure
    claim: str
    evidence: List[str] = Field(default_factory=list)
    reasoning: str
    
    # Context
    historical_context: str
    counterarguments: List[str] = Field(default_factory=list)
    responses_to_counterarguments: List[str] = Field(default_factory=list)
    
    # Quality assessment
    evidence_quality: float = Field(ge=0.0, le=1.0, default=0.5)
    reasoning_quality: float = Field(ge=0.0, le=1.0, default=0.5)
    historical_accuracy: float = Field(ge=0.0, le=1.0, default=0.5)
    
    created_at: datetime = Field(default_factory=datetime.now)


# Historical Thinking Skills Assessment
class ThinkingSkillAssessment(BaseModel):
    """Assessment of historical thinking skills."""
    assessment_id: str
    student_id: str
    skill: HistoricalThinkingSkill
    
    # Assessment task
    task_description: str
    student_response: str
    
    # Rubric scoring
    proficiency_level: int = Field(ge=1, le=4, description="1=Inadequate, 2=Developing, 3=Proficient, 4=Advanced")
    specific_scores: Dict[str, int] = Field(default_factory=dict)
    
    # Feedback
    strengths: List[str] = Field(default_factory=list)
    areas_for_improvement: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    
    # Progress tracking
    previous_assessments: List[str] = Field(default_factory=list)  # Assessment IDs
    growth_indicators: Dict[str, float] = Field(default_factory=dict)
    
    assessed_at: datetime = Field(default_factory=datetime.now)


# Content Organization Models
class HistoricalEra(BaseModel):
    """Major historical era with themes and concepts."""
    era_id: str
    name: str
    description: str
    period: HistoricalPeriod
    
    # Time boundaries
    start_date: Union[date, str]
    end_date: Union[date, str]
    
    # Key themes and concepts
    major_themes: List[str] = Field(default_factory=list)
    key_concepts: List[str] = Field(default_factory=list)
    
    # Events and figures
    defining_events: List[str] = Field(default_factory=list)  # Event IDs
    key_figures: List[str] = Field(default_factory=list)
    
    # Geographic scope
    regions_affected: List[str] = Field(default_factory=list)
    
    # Educational alignment
    grade_levels: List[int] = Field(default_factory=list)
    standards_alignment: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.now)


class HistoricalConcept(BaseModel):
    """Individual historical concept with relationships."""
    concept_id: str
    name: str
    definition: str
    
    # Categorization
    concept_type: str  # "political", "economic", "social", etc.
    era: HistoricalPeriod
    
    # Relationships
    prerequisite_concepts: List[str] = Field(default_factory=list)
    related_concepts: List[str] = Field(default_factory=list)
    example_events: List[str] = Field(default_factory=list)
    
    # Educational metadata
    difficulty_level: float = Field(ge=0.0, le=1.0, default=0.5)
    importance_level: float = Field(ge=0.0, le=1.0, default=0.5)
    
    # Teaching resources
    explanation_strategies: List[str] = Field(default_factory=list)
    common_misconceptions: List[str] = Field(default_factory=list)
    assessment_ideas: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.now)