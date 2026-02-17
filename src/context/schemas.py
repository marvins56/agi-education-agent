"""Context management schemas and data structures."""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class ContextTier(str, Enum):
    """Context storage tiers."""
    ACTIVE = "active"           # Redis - immediate access
    SESSION = "session"         # PostgreSQL - recent summaries  
    TOPIC = "topic"            # ChromaDB - long-term knowledge


class SummaryType(str, Enum):
    """Types of educational summaries."""
    PROGRESS = "progress"       # Learning progress summary
    CONCEPTUAL = "conceptual"   # Concept understanding summary
    STRATEGIC = "strategic"     # Teaching strategy effectiveness
    SESSION_END = "session_end" # End-of-session wrap-up


class MessageAnnotation(BaseModel):
    """Annotations added to raw messages."""
    type: str                   # "confusion", "breakthrough", "misconception", "mastery"
    confidence: float = Field(ge=0.0, le=1.0)
    concepts: List[str] = Field(default_factory=list)
    timestamp: datetime


class AnnotatedMessage(BaseModel):
    """Message with educational annotations."""
    role: str
    content: str
    timestamp: datetime
    token_count: int
    annotations: List[MessageAnnotation] = Field(default_factory=list)


class EducationalSummary(BaseModel):
    """Structured summary of learning interactions."""
    summary_type: SummaryType
    session_id: str
    student_id: str
    time_range: tuple[datetime, datetime]
    
    # Core educational insights
    concepts_discussed: List[str] = Field(default_factory=list)
    mastery_assessments: Dict[str, float] = Field(default_factory=dict)  # concept -> confidence
    misconceptions_identified: List[str] = Field(default_factory=list)
    breakthrough_moments: List[str] = Field(default_factory=list)
    
    # Teaching effectiveness
    effective_strategies: List[str] = Field(default_factory=list)
    ineffective_approaches: List[str] = Field(default_factory=list)
    student_engagement_level: float = Field(ge=0.0, le=1.0)
    
    # Forward-looking
    suggested_next_topics: List[str] = Field(default_factory=list)
    recommended_teaching_approach: Optional[str] = None
    
    # Metadata
    message_count: int
    total_tokens: int
    created_at: datetime = Field(default_factory=datetime.now)


class TutoringContext(BaseModel):
    """Complete context package for tutoring LLM."""
    session_id: str
    student_id: str
    
    # Tier 1: Active conversation
    active_messages: List[AnnotatedMessage] = Field(default_factory=list)
    
    # Tier 2: Session summaries
    session_summaries: List[EducationalSummary] = Field(default_factory=list)
    
    # Tier 3: Topic knowledge
    topic_mastery: Dict[str, float] = Field(default_factory=dict)
    learning_patterns: Dict[str, Any] = Field(default_factory=dict)
    effective_teaching_methods: List[str] = Field(default_factory=list)
    
    # Context metadata
    total_token_estimate: int = 0
    context_freshness: datetime = Field(default_factory=datetime.now)
    
    def estimate_tokens(self) -> int:
        """Rough token estimation for the complete context."""
        # Active messages: ~4 tokens per word average
        active_tokens = sum(msg.token_count for msg in self.active_messages)
        
        # Summaries: ~300 tokens per summary average
        summary_tokens = len(self.session_summaries) * 300
        
        # Topic knowledge: ~20 tokens per concept
        topic_tokens = len(self.topic_mastery) * 20
        
        return active_tokens + summary_tokens + topic_tokens


class ContextWindow(BaseModel):
    """Sliding window configuration."""
    max_messages: int = 25
    max_tokens: int = 2000
    min_messages: int = 10  # Never go below this even if tokens exceeded
    adaptive_sizing: bool = True