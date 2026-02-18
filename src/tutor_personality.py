"""
Persistent Tutor Personality System for EduAGI

This module creates tutors that genuinely KNOW their students. It tracks relationships,
remembers conversations, adapts teaching styles, and builds rapport over time.

What makes EduAGI different: tutors that aren't just smart, but personally connected.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Float, Integer, Boolean, text
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
import json
import logging
import random
from collections import defaultdict

from src.models.database import Base
from src.accessibility_engine import AccessibilityProfile, ImpairmentType, SeverityLevel
from src.adaptive.schemas import LearningStyleProfile

logger = logging.getLogger(__name__)


class EmotionalState(Enum):
    """Student's current emotional state"""
    EXCITED = "excited"
    CONFIDENT = "confident"
    CURIOUS = "curious"
    NEUTRAL = "neutral"
    CONFUSED = "confused"
    FRUSTRATED = "frustrated"
    OVERWHELMED = "overwhelmed"
    DISCOURAGED = "discouraged"


class TeachingStyle(Enum):
    """Different teaching approaches"""
    ENCOURAGING = "encouraging"
    CHALLENGING = "challenging"
    METHODICAL = "methodical"
    CREATIVE = "creative"
    SOCRATIC = "socratic"
    PRACTICAL = "practical"
    STORYTELLING = "storytelling"


class CommunicationStyle(Enum):
    """How the tutor communicates"""
    FORMAL = "formal"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    ENTHUSIASTIC = "enthusiastic"
    CALM = "calm"


class RelationshipStage(Enum):
    """Stages of tutor-student relationship"""
    FIRST_MEETING = "first_meeting"          # 0-2 sessions
    GETTING_ACQUAINTED = "getting_acquainted"  # 3-10 sessions
    BUILDING_TRUST = "building_trust"        # 11-25 sessions
    ESTABLISHED = "established"              # 26-50 sessions
    DEEP_CONNECTION = "deep_connection"      # 51+ sessions


class MilestoneType(Enum):
    """Types of achievements to celebrate"""
    STREAK = "streak"                        # Study streak milestones
    MASTERY = "mastery"                     # Mastering difficult concepts
    BREAKTHROUGH = "breakthrough"            # Major understanding breakthrough
    CONSISTENCY = "consistency"             # Regular practice
    IMPROVEMENT = "improvement"             # Performance improvement
    PERSONAL = "personal"                   # Personal goals achieved


# Database Models

class StudentMemory(Base):
    """Stores comprehensive per-student context and history"""
    __tablename__ = "student_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Personal context
    interests = Column(JSONB, server_default=text("'[]'"))  # List of interests
    struggles = Column(JSONB, server_default=text("'[]'"))  # Common struggle areas
    strengths = Column(JSONB, server_default=text("'[]'"))  # Strong subjects/skills
    preferences = Column(JSONB, server_default=text("'{}'"))  # Learning preferences
    goals = Column(JSONB, server_default=text("'[]'"))  # Personal goals
    
    # Emotional patterns
    emotional_patterns = Column(JSONB, server_default=text("'{}'"))  # Time-based patterns
    stress_triggers = Column(JSONB, server_default=text("'[]'"))  # What causes stress
    motivation_factors = Column(JSONB, server_default=text("'[]'"))  # What motivates them
    
    # Conversation highlights
    memorable_conversations = Column(JSONB, server_default=text("'[]'"))  # Key conversation moments
    favorite_examples = Column(JSONB, server_default=text("'[]'"))  # Examples that worked well
    successful_explanations = Column(JSONB, server_default=text("'[]'"))  # Teaching approaches that worked
    
    # Context tracking
    family_context = Column(JSONB, server_default=text("'{}'"))  # Family info they've shared
    school_context = Column(JSONB, server_default=text("'{}'"))  # School situation
    external_pressures = Column(JSONB, server_default=text("'[]'"))  # External pressures they face
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class TutorPersonalityState(Base):
    """Stores the tutor's evolving personality and teaching style"""
    __tablename__ = "tutor_personality_states"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tutor_id = Column(String(100), nullable=False, default="main_tutor")  # Support multiple tutors
    
    # Teaching effectiveness tracking
    teaching_style_effectiveness = Column(JSONB, server_default=text("'{}'"))  # style -> success rate
    subject_confidence = Column(JSONB, server_default=text("'{}'"))  # subject -> confidence level
    explanation_success_rate = Column(JSONB, server_default=text("'{}'"))  # approach -> success rate
    
    # Communication patterns learned
    communication_patterns = Column(JSONB, server_default=text("'{}'"))  # what works with different students
    humor_effectiveness = Column(Float, default=0.5)  # How well humor works
    formality_preference = Column(Float, default=0.5)  # 0=casual, 1=formal
    encouragement_style = Column(JSONB, server_default=text("'{}'"))  # types of encouragement that work
    
    # Relationship management
    total_students_taught = Column(Integer, default=0)
    successful_relationships = Column(Integer, default=0)
    challenging_relationships = Column(Integer, default=0)
    
    # Learning and adaptation
    adaptation_rate = Column(Float, default=0.1)  # How quickly to adapt
    confidence_threshold = Column(Float, default=0.7)  # When to try new approaches
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class StudentTutorRelationship(Base):
    """Tracks the specific relationship between a tutor and student"""
    __tablename__ = "student_tutor_relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tutor_id = Column(String(100), nullable=False, default="main_tutor")
    
    # Relationship metrics
    relationship_stage = Column(String(50), default=RelationshipStage.FIRST_MEETING.value)
    trust_level = Column(Float, default=0.0)  # 0.0-1.0
    rapport_score = Column(Float, default=0.0)  # 0.0-1.0
    communication_effectiveness = Column(Float, default=0.5)  # How well they communicate
    
    # Interaction history
    total_sessions = Column(Integer, default=0)
    total_interactions = Column(Integer, default=0)
    positive_interactions = Column(Integer, default=0)
    challenging_interactions = Column(Integer, default=0)
    
    # Personalization data
    preferred_teaching_style = Column(String(50), nullable=True)
    preferred_communication_style = Column(String(50), nullable=True)
    effective_strategies = Column(JSONB, server_default=text("'[]'"))
    ineffective_strategies = Column(JSONB, server_default=text("'[]'"))
    
    # Milestones and celebrations
    milestones_achieved = Column(JSONB, server_default=text("'[]'"))
    celebrations_given = Column(JSONB, server_default=text("'[]'"))
    
    # Last interaction context
    last_topic_discussed = Column(String(255), nullable=True)
    last_emotional_state = Column(String(50), nullable=True)
    last_session_summary = Column(Text, nullable=True)
    last_interaction_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ConversationHighlight(Base):
    """Memorable moments from conversations to reference later"""
    __tablename__ = "conversation_highlights"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Highlight details
    highlight_type = Column(String(50), nullable=False)  # "breakthrough", "funny", "personal", "struggle"
    content = Column(Text, nullable=False)  # What happened
    context = Column(Text, nullable=True)  # Additional context
    topic = Column(String(255), nullable=True)  # What topic was being discussed
    
    # Emotional context
    student_emotional_state = Column(String(50), nullable=True)
    breakthrough_level = Column(Float, default=0.0)  # How significant was this moment
    
    # Usage tracking
    times_referenced = Column(Integer, default=0)
    last_referenced = Column(DateTime, nullable=True)
    reference_effectiveness = Column(Float, default=0.0)  # How helpful when referenced
    
    created_at = Column(DateTime, server_default=func.now())


# Pydantic Models for Business Logic

class StudentPersonalityProfile(BaseModel):
    """Complete personality profile for a student"""
    student_id: str
    
    # Personal characteristics
    interests: List[str] = []
    learning_struggles: List[str] = []
    strengths: List[str] = []
    goals: List[str] = []
    
    # Emotional patterns
    emotional_patterns: Dict[str, Any] = {}  # day_of_week, time_of_day patterns
    stress_triggers: List[str] = []
    motivation_factors: List[str] = []
    
    # Communication preferences
    prefers_casual_language: bool = False
    responds_well_to_humor: bool = True
    needs_frequent_encouragement: bool = False
    prefers_direct_feedback: bool = True
    
    # Learning context
    family_context: Dict[str, Any] = {}
    school_pressures: List[str] = []
    external_challenges: List[str] = []
    
    # Memory highlights
    memorable_moments: List[Dict[str, Any]] = []
    successful_teaching_approaches: List[Dict[str, Any]] = []
    
    last_updated: datetime = Field(default_factory=datetime.now)


class TutorPersonalityConfig(BaseModel):
    """Configuration for tutor's personality and behavior"""
    tutor_id: str = "main_tutor"
    
    # Teaching style preferences (learned from effectiveness)
    preferred_teaching_styles: Dict[str, float] = {}  # style -> preference score
    subject_confidence_levels: Dict[str, float] = {}  # subject -> confidence
    
    # Communication style
    base_formality: float = 0.5  # 0=casual, 1=formal
    humor_tendency: float = 0.3  # How often to use humor
    encouragement_frequency: float = 0.7  # How often to encourage
    
    # Adaptation behavior
    adaptation_rate: float = 0.1  # How quickly to adapt to feedback
    experimentation_willingness: float = 0.2  # Willingness to try new approaches
    
    # Relationship building
    small_talk_frequency: float = 0.3  # How often to make small talk
    personal_connection_priority: float = 0.8  # Priority on building connections
    
    last_updated: datetime = Field(default_factory=datetime.now)


# Core Business Logic Classes

class StudentMemoryManager:
    """Manages comprehensive memory about individual students"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def get_student_memory(self, student_id: str) -> Optional[StudentPersonalityProfile]:
        """Retrieve comprehensive memory about a student"""
        # Get from database
        memory = await self.db.query(StudentMemory).filter(
            StudentMemory.student_id == student_id
        ).first()
        
        if not memory:
            return StudentPersonalityProfile(student_id=student_id)
        
        return StudentPersonalityProfile(
            student_id=student_id,
            interests=memory.interests or [],
            learning_struggles=memory.struggles or [],
            strengths=memory.strengths or [],
            goals=memory.goals or [],
            emotional_patterns=memory.emotional_patterns or {},
            stress_triggers=memory.stress_triggers or [],
            motivation_factors=memory.motivation_factors or [],
            family_context=memory.family_context or {},
            school_pressures=memory.external_pressures or [],
            memorable_moments=memory.memorable_conversations or [],
            successful_teaching_approaches=memory.successful_explanations or [],
        )
    
    async def update_student_memory(self, student_id: str, updates: Dict[str, Any]):
        """Update student memory with new information"""
        memory = await self.db.query(StudentMemory).filter(
            StudentMemory.student_id == student_id
        ).first()
        
        if not memory:
            memory = StudentMemory(student_id=student_id)
            self.db.add(memory)
        
        # Update fields based on what's provided
        for field, value in updates.items():
            if hasattr(memory, field):
                if field in ['interests', 'struggles', 'strengths', 'goals', 'stress_triggers', 'motivation_factors']:
                    # For list fields, merge with existing
                    existing = getattr(memory, field) or []
                    if isinstance(value, list):
                        setattr(memory, field, list(set(existing + value)))
                elif field in ['emotional_patterns', 'preferences', 'family_context']:
                    # For dict fields, merge with existing
                    existing = getattr(memory, field) or {}
                    if isinstance(value, dict):
                        existing.update(value)
                        setattr(memory, field, existing)
                else:
                    setattr(memory, field, value)
        
        await self.db.commit()
    
    async def add_conversation_highlight(self, student_id: str, highlight_type: str, 
                                       content: str, context: str = None, topic: str = None,
                                       emotional_state: str = None, breakthrough_level: float = 0.0):
        """Add a memorable moment from conversation"""
        highlight = ConversationHighlight(
            student_id=student_id,
            highlight_type=highlight_type,
            content=content,
            context=context,
            topic=topic,
            student_emotional_state=emotional_state,
            breakthrough_level=breakthrough_level
        )
        self.db.add(highlight)
        await self.db.commit()
    
    async def get_conversation_highlights(self, student_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get memorable conversation moments for reference"""
        highlights = await self.db.query(ConversationHighlight).filter(
            ConversationHighlight.student_id == student_id
        ).order_by(ConversationHighlight.breakthrough_level.desc()).limit(limit).all()
        
        return [
            {
                "type": h.highlight_type,
                "content": h.content,
                "context": h.context,
                "topic": h.topic,
                "emotional_state": h.student_emotional_state,
                "breakthrough_level": h.breakthrough_level,
                "created_at": h.created_at,
                "times_referenced": h.times_referenced
            }
            for h in highlights
        ]


class TutorPersonality:
    """The tutor's evolving personality and teaching expertise"""
    
    def __init__(self, db_session, tutor_id: str = "main_tutor"):
        self.db = db_session
        self.tutor_id = tutor_id
        self.config: Optional[TutorPersonalityConfig] = None
    
    async def load_personality(self) -> TutorPersonalityConfig:
        """Load the tutor's current personality configuration"""
        if self.config:
            return self.config
        
        state = await self.db.query(TutorPersonalityState).filter(
            TutorPersonalityState.tutor_id == self.tutor_id
        ).first()
        
        if not state:
            # Create default personality
            self.config = TutorPersonalityConfig(tutor_id=self.tutor_id)
            await self._save_personality_state()
        else:
            self.config = TutorPersonalityConfig(
                tutor_id=self.tutor_id,
                preferred_teaching_styles=state.teaching_style_effectiveness or {},
                subject_confidence_levels=state.subject_confidence or {},
                base_formality=state.formality_preference or 0.5,
                humor_tendency=state.humor_effectiveness or 0.3,
                adaptation_rate=state.adaptation_rate or 0.1
            )
        
        return self.config
    
    async def _save_personality_state(self):
        """Save current personality state to database"""
        if not self.config:
            return
        
        state = await self.db.query(TutorPersonalityState).filter(
            TutorPersonalityState.tutor_id == self.tutor_id
        ).first()
        
        if not state:
            state = TutorPersonalityState(tutor_id=self.tutor_id)
            self.db.add(state)
        
        state.teaching_style_effectiveness = self.config.preferred_teaching_styles
        state.subject_confidence = self.config.subject_confidence_levels
        state.formality_preference = self.config.base_formality
        state.humor_effectiveness = self.config.humor_tendency
        state.adaptation_rate = self.config.adaptation_rate
        
        await self.db.commit()
    
    async def adapt_teaching_style(self, student_id: str, subject: str, style: str, success_rate: float):
        """Learn from teaching effectiveness and adapt"""
        await self.load_personality()
        
        # Update teaching style effectiveness
        if subject not in self.config.preferred_teaching_styles:
            self.config.preferred_teaching_styles[subject] = {}
        
        current_rate = self.config.preferred_teaching_styles[subject].get(style, 0.5)
        # Exponential moving average
        new_rate = current_rate * (1 - self.config.adaptation_rate) + success_rate * self.config.adaptation_rate
        self.config.preferred_teaching_styles[subject][style] = new_rate
        
        # Update subject confidence
        current_confidence = self.config.subject_confidence_levels.get(subject, 0.5)
        confidence_adjustment = 0.1 if success_rate > 0.7 else -0.05
        self.config.subject_confidence_levels[subject] = max(0.1, min(1.0, current_confidence + confidence_adjustment))
        
        await self._save_personality_state()
    
    def get_recommended_teaching_style(self, subject: str) -> str:
        """Get the most effective teaching style for a subject"""
        if not self.config:
            return TeachingStyle.ENCOURAGING.value
        
        subject_styles = self.config.preferred_teaching_styles.get(subject, {})
        if not subject_styles:
            return TeachingStyle.ENCOURAGING.value
        
        # Return the style with highest effectiveness
        best_style = max(subject_styles.items(), key=lambda x: x[1])
        return best_style[0]
    
    def get_subject_confidence(self, subject: str) -> float:
        """Get confidence level for teaching a subject"""
        if not self.config:
            return 0.5
        return self.config.subject_confidence_levels.get(subject, 0.5)


class PersonalizedContent:
    """Generates contextual, personalized content that references shared history"""
    
    def __init__(self, student_memory: StudentMemoryManager, relationship_manager):
        self.memory = student_memory
        self.relationships = relationship_manager
    
    async def generate_contextual_reference(self, student_id: str, current_topic: str, 
                                          difficulty_type: str = "similar") -> Optional[str]:
        """Generate a reference to past success to build confidence"""
        profile = await self.memory.get_student_memory(student_id)
        highlights = await self.memory.get_conversation_highlights(student_id, limit=20)
        
        # Find relevant past success
        relevant_highlights = [
            h for h in highlights 
            if h['type'] in ['breakthrough', 'mastery'] and h['breakthrough_level'] > 0.6
        ]
        
        if not relevant_highlights:
            return None
        
        # Pick a relevant highlight
        best_highlight = max(relevant_highlights, key=lambda x: x['breakthrough_level'])
        
        # Generate natural reference
        time_ago = self._time_since_string(best_highlight['created_at'])
        
        references = [
            f"Remember {time_ago} when you {best_highlight['content']}? You can use that same approach here.",
            f"This reminds me of {time_ago} when you figured out {best_highlight['topic']}. Same principle applies!",
            f"You've got this! {time_ago} you {best_highlight['content']} - this is just as manageable."
        ]
        
        return random.choice(references)
    
    async def generate_interest_based_example(self, student_id: str, topic: str, 
                                            concept: str) -> Optional[str]:
        """Generate examples using student's interests"""
        profile = await self.memory.get_student_memory(student_id)
        
        if not profile.interests:
            return None
        
        # Simple mapping of interests to example domains
        interest_examples = {
            "football": self._generate_sports_example,
            "soccer": self._generate_sports_example,
            "basketball": self._generate_sports_example,
            "video games": self._generate_gaming_example,
            "music": self._generate_music_example,
            "art": self._generate_art_example,
            "cooking": self._generate_cooking_example,
            "animals": self._generate_animal_example
        }
        
        # Find matching interests
        for interest in profile.interests:
            interest_lower = interest.lower()
            for key, example_func in interest_examples.items():
                if key in interest_lower:
                    return example_func(concept, topic)
        
        return None
    
    def _generate_sports_example(self, concept: str, topic: str) -> str:
        """Generate sports-based examples"""
        examples = {
            "ratio": "If a soccer player scores 3 goals in 2 games, what's their goal-to-game ratio?",
            "percentage": "If a basketball player makes 15 out of 20 free throws, what's their success percentage?",
            "fractions": "A football team completed 3/4 of their passes. How many passes did they complete out of 20 attempts?",
            "multiplication": "If each soccer match lasts 90 minutes and you watch 3 matches, how many total minutes?",
            "division": "A baseball team scored 24 runs in 6 games. What's their average runs per game?"
        }
        return examples.get(concept.lower(), f"Think of this like tracking stats in your favorite sport!")
    
    def _generate_gaming_example(self, concept: str, topic: str) -> str:
        """Generate gaming-based examples"""
        examples = {
            "ratio": "If you defeat 12 enemies using 4 health potions, what's your enemy-to-potion ratio?",
            "percentage": "You completed 85% of the game. If there are 40 levels total, how many have you finished?",
            "probability": "If a rare item has a 5% drop rate, what are the chances of getting it in 100 tries?",
            "multiplication": "Each quest gives 150 XP. How much XP do you get from completing 8 quests?"
        }
        return examples.get(concept.lower(), f"Imagine this concept as a game mechanic!")
    
    def _generate_music_example(self, concept: str, topic: str) -> str:
        """Generate music-based examples"""
        examples = {
            "fractions": "A song is 4 minutes long. If you've listened to 3/4 of it, how much time is left?",
            "ratio": "If a playlist has 15 rock songs and 10 pop songs, what's the rock-to-pop ratio?",
            "patterns": "Music has patterns too - like how chord progressions repeat!"
        }
        return examples.get(concept.lower(), f"Think of this like musical patterns and rhythms!")
    
    def _time_since_string(self, past_date: datetime) -> str:
        """Convert a datetime to friendly 'time ago' string"""
        if not isinstance(past_date, datetime):
            return "recently"
        
        now = datetime.now()
        diff = now - past_date
        
        if diff.days == 0:
            return "earlier today"
        elif diff.days == 1:
            return "yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        else:
            months = diff.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"


class EmotionalIntelligence:
    """Tracks emotional patterns and adapts tutoring approach accordingly"""
    
    def __init__(self, student_memory: StudentMemoryManager):
        self.memory = student_memory
    
    async def detect_emotional_state(self, student_id: str, interaction_data: Dict[str, Any]) -> EmotionalState:
        """Detect current emotional state from interaction patterns"""
        # Simple heuristics - could be enhanced with NLP
        response_time = interaction_data.get('response_time_seconds', 0)
        correctness = interaction_data.get('correctness', 0.0)
        hint_requests = interaction_data.get('hint_count', 0)
        message_tone = interaction_data.get('message_tone', 'neutral')
        
        # Fast responses with high correctness = confident/excited
        if response_time < 10 and correctness > 0.8:
            return EmotionalState.CONFIDENT
        
        # Slow responses with low correctness = struggling
        if response_time > 60 and correctness < 0.3:
            return EmotionalState.FRUSTRATED
        
        # Many hints requested = confused but trying
        if hint_requests > 3:
            return EmotionalState.CONFUSED
        
        # Analyze message tone if available
        if message_tone in ['excited', 'happy']:
            return EmotionalState.EXCITED
        elif message_tone in ['frustrated', 'angry']:
            return EmotionalState.FRUSTRATED
        elif message_tone in ['confused', 'uncertain']:
            return EmotionalState.CONFUSED
        
        return EmotionalState.NEUTRAL
    
    async def track_emotional_pattern(self, student_id: str, emotional_state: EmotionalState, 
                                    context: Dict[str, Any]):
        """Track emotional patterns over time"""
        now = datetime.now()
        day_of_week = now.strftime('%A')
        hour_of_day = now.hour
        topic = context.get('topic', 'unknown')
        
        # Update emotional patterns in memory
        pattern_update = {
            'emotional_patterns': {
                'by_day_of_week': {day_of_week: emotional_state.value},
                'by_hour': {str(hour_of_day): emotional_state.value},
                'by_topic': {topic: emotional_state.value},
                'recent_states': [emotional_state.value]  # Keep last 10
            }
        }
        
        await self.memory.update_student_memory(student_id, pattern_update)
    
    async def get_adaptive_tone(self, student_id: str, current_state: EmotionalState) -> Dict[str, Any]:
        """Get appropriate tone and approach based on emotional state"""
        profile = await self.memory.get_student_memory(student_id)
        
        # Base adaptive responses
        responses = {
            EmotionalState.EXCITED: {
                'tone': 'enthusiastic',
                'approach': 'challenging',
                'encouragement': 'high',
                'pace': 'faster'
            },
            EmotionalState.CONFIDENT: {
                'tone': 'supportive',
                'approach': 'challenging',
                'encouragement': 'moderate',
                'pace': 'steady'
            },
            EmotionalState.FRUSTRATED: {
                'tone': 'calm',
                'approach': 'methodical',
                'encouragement': 'high',
                'pace': 'slower'
            },
            EmotionalState.CONFUSED: {
                'tone': 'patient',
                'approach': 'step_by_step',
                'encouragement': 'high',
                'pace': 'slower'
            },
            EmotionalState.OVERWHELMED: {
                'tone': 'reassuring',
                'approach': 'break_down',
                'encouragement': 'very_high',
                'pace': 'much_slower'
            }
        }
        
        base_response = responses.get(current_state, responses[EmotionalState.NEUTRAL])
        
        # Customize based on student preferences
        if profile.needs_frequent_encouragement:
            base_response['encouragement'] = 'very_high'
        
        if not profile.responds_well_to_humor and current_state in [EmotionalState.FRUSTRATED, EmotionalState.OVERWHELMED]:
            base_response['avoid_humor'] = True
        
        return base_response
    
    def should_push_harder(self, student_id: str, current_state: EmotionalState, 
                          relationship_stage: RelationshipStage) -> bool:
        """Determine if it's appropriate to push the student harder"""
        # Don't push if they're struggling emotionally
        if current_state in [EmotionalState.FRUSTRATED, EmotionalState.OVERWHELMED, EmotionalState.DISCOURAGED]:
            return False
        
        # Can push more with established relationships
        if relationship_stage in [RelationshipStage.ESTABLISHED, RelationshipStage.DEEP_CONNECTION]:
            return current_state in [EmotionalState.CONFIDENT, EmotionalState.EXCITED]
        
        # Be gentle with new relationships
        return current_state == EmotionalState.EXCITED
    
    def should_ease_off(self, current_state: EmotionalState, consecutive_struggles: int) -> bool:
        """Determine if we should reduce difficulty/pressure"""
        return (current_state in [EmotionalState.FRUSTRATED, EmotionalState.OVERWHELMED] or
                consecutive_struggles >= 3)


class RapportBuilder:
    """Builds and maintains rapport with students over time"""
    
    def __init__(self, db_session, student_memory: StudentMemoryManager):
        self.db = db_session
        self.memory = student_memory
    
    async def get_relationship_status(self, student_id: str) -> Dict[str, Any]:
        """Get current relationship status with student"""
        relationship = await self.db.query(StudentTutorRelationship).filter(
            StudentTutorRelationship.student_id == student_id
        ).first()
        
        if not relationship:
            return {
                'stage': RelationshipStage.FIRST_MEETING,
                'trust_level': 0.0,
                'rapport_score': 0.0,
                'total_sessions': 0,
                'recommended_approach': 'introductory'
            }
        
        return {
            'stage': RelationshipStage(relationship.relationship_stage),
            'trust_level': relationship.trust_level,
            'rapport_score': relationship.rapport_score,
            'total_sessions': relationship.total_sessions,
            'last_interaction_date': relationship.last_interaction_date,
            'preferred_teaching_style': relationship.preferred_teaching_style,
            'effective_strategies': relationship.effective_strategies
        }
    
    async def generate_appropriate_greeting(self, student_id: str) -> str:
        """Generate contextually appropriate greeting"""
        relationship = await self.get_relationship_status(student_id)
        profile = await self.memory.get_student_memory(student_id)
        stage = relationship['stage']
        
        # First meeting
        if stage == RelationshipStage.FIRST_MEETING:
            return "Hi there! I'm excited to start learning with you. What should I call you?"
        
        # Getting acquainted
        elif stage == RelationshipStage.GETTING_ACQUAINTED:
            greetings = [
                "Hey! Good to see you again. Ready to tackle something interesting?",
                "Welcome back! How are you feeling about today's learning session?",
                "Hi! I've been looking forward to our session. What's on your mind today?"
            ]
            return random.choice(greetings)
        
        # Established relationship
        elif stage in [RelationshipStage.ESTABLISHED, RelationshipStage.DEEP_CONNECTION]:
            # Reference recent context or interests
            personal_greetings = []
            
            if profile.interests:
                interest = random.choice(profile.interests)
                personal_greetings.append(f"Hey! How's {interest} going? Ready to learn something cool?")
            
            # Check if it's been a while
            last_session = relationship.get('last_interaction_date')
            if last_session and (datetime.now() - last_session).days > 3:
                personal_greetings.append("Welcome back! I missed our sessions. How have you been?")
            else:
                personal_greetings.append("Hey there! Ready to continue where we left off?")
            
            return random.choice(personal_greetings) if personal_greetings else "Hi! Great to see you again!"
        
        # Default
        return "Hello! Ready to learn together?"
    
    async def generate_check_in(self, student_id: str) -> Optional[str]:
        """Generate appropriate check-in based on relationship and history"""
        relationship = await self.get_relationship_status(student_id)
        profile = await self.memory.get_student_memory(student_id)
        
        # Only check in if relationship is established enough
        if relationship['stage'] in [RelationshipStage.FIRST_MEETING, RelationshipStage.GETTING_ACQUAINTED]:
            return None
        
        # Don't check in too often
        if random.random() > 0.3:  # 30% chance of check-in
            return None
        
        check_ins = [
            "How was your weekend?",
            "How are things going at school?",
            "Anything interesting happen recently?",
            "How are you feeling today?"
        ]
        
        # Personalized check-ins based on known context
        if profile.school_pressures:
            check_ins.append("How are things going with your classes?")
        
        if profile.interests:
            interest = random.choice(profile.interests)
            check_ins.append(f"Any updates on your {interest} interests?")
        
        return random.choice(check_ins)
    
    async def update_relationship_metrics(self, student_id: str, interaction_outcome: Dict[str, Any]):
        """Update relationship metrics based on interaction"""
        relationship = await self.db.query(StudentTutorRelationship).filter(
            StudentTutorRelationship.student_id == student_id
        ).first()
        
        if not relationship:
            relationship = StudentTutorRelationship(student_id=student_id)
            self.db.add(relationship)
        
        # Update interaction counts
        relationship.total_interactions += 1
        
        # Determine if interaction was positive
        success_rate = interaction_outcome.get('success_rate', 0.5)
        student_feedback = interaction_outcome.get('student_feedback', 'neutral')
        engagement_level = interaction_outcome.get('engagement_level', 0.5)
        
        if success_rate > 0.7 and engagement_level > 0.6:
            relationship.positive_interactions += 1
            # Increase trust and rapport
            relationship.trust_level = min(1.0, relationship.trust_level + 0.02)
            relationship.rapport_score = min(1.0, relationship.rapport_score + 0.03)
        elif success_rate < 0.3 or engagement_level < 0.3:
            relationship.challenging_interactions += 1
            # Slight decrease in rapport if consistently poor
            if relationship.challenging_interactions % 3 == 0:
                relationship.rapport_score = max(0.0, relationship.rapport_score - 0.01)
        
        # Update relationship stage based on total sessions
        total_sessions = relationship.total_sessions + 1
        relationship.total_sessions = total_sessions
        
        if total_sessions <= 2:
            relationship.relationship_stage = RelationshipStage.FIRST_MEETING.value
        elif total_sessions <= 10:
            relationship.relationship_stage = RelationshipStage.GETTING_ACQUAINTED.value
        elif total_sessions <= 25:
            relationship.relationship_stage = RelationshipStage.BUILDING_TRUST.value
        elif total_sessions <= 50:
            relationship.relationship_stage = RelationshipStage.ESTABLISHED.value
        else:
            relationship.relationship_stage = RelationshipStage.DEEP_CONNECTION.value
        
        # Update last interaction
        relationship.last_interaction_date = datetime.now()
        relationship.last_emotional_state = interaction_outcome.get('emotional_state')
        relationship.last_topic_discussed = interaction_outcome.get('topic')
        
        await self.db.commit()


class AccessibilityIntegration:
    """Integrates with accessibility engine to remember and respect accessibility needs"""
    
    def __init__(self, student_memory: StudentMemoryManager):
        self.memory = student_memory
    
    async def remember_accessibility_needs(self, student_id: str, accessibility_profile: AccessibilityProfile):
        """Remember accessibility needs so we don't ask again"""
        accessibility_context = {
            'accessibility_needs': {
                'visual_impairments': {k: v.value for k, v in accessibility_profile.visual_impairments.items()},
                'hearing_impairments': {k: v.value for k, v in accessibility_profile.hearing_impairments.items()},
                'cognitive_impairments': {k: v.value for k, v in accessibility_profile.cognitive_impairments.items()},
                'motor_impairments': {k: v.value for k, v in accessibility_profile.motor_impairments.items()},
                'preferred_interaction_mode': accessibility_profile.preferred_interaction_mode,
                'requires_voice_only': accessibility_profile.requires_voice_only,
                'needs_simplified_language': accessibility_profile.needs_simplified_language,
                'requires_patience_mode': accessibility_profile.requires_patience_mode
            }
        }
        
        await self.memory.update_student_memory(student_id, accessibility_context)
    
    async def get_remembered_accessibility_needs(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Get remembered accessibility needs"""
        profile = await self.memory.get_student_memory(student_id)
        return profile.family_context.get('accessibility_needs')  # Store in family_context for now
    
    def should_apply_accessibility_adaptations(self, accessibility_needs: Dict[str, Any]) -> Dict[str, Any]:
        """Determine what adaptations to apply based on remembered needs"""
        adaptations = {}
        
        if accessibility_needs.get('needs_simplified_language'):
            adaptations['language_complexity'] = 'simple'
            adaptations['sentence_length'] = 'short'
        
        if accessibility_needs.get('requires_patience_mode'):
            adaptations['response_time_expectation'] = 'extended'
            adaptations['hint_frequency'] = 'high'
        
        if accessibility_needs.get('requires_voice_only'):
            adaptations['interaction_mode'] = 'voice'
            adaptations['visual_elements'] = 'minimal'
        
        visual_impairments = accessibility_needs.get('visual_impairments', {})
        if visual_impairments:
            adaptations['text_size'] = 'large'
            adaptations['contrast'] = 'high'
            adaptations['screen_reader_friendly'] = True
        
        return adaptations


class PersistentTutorPersonalitySystem:
    """Main orchestrator for the persistent tutor personality system"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.student_memory = StudentMemoryManager(db_session)
        self.tutor_personality = TutorPersonality(db_session)
        self.emotional_intelligence = EmotionalIntelligence(self.student_memory)
        self.rapport_builder = RapportBuilder(db_session, self.student_memory)
        self.accessibility_integration = AccessibilityIntegration(self.student_memory)
        self.personalized_content = PersonalizedContent(self.student_memory, self.rapport_builder)
    
    async def start_session(self, student_id: str, session_context: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new session with personalized approach"""
        # Get comprehensive student context
        student_profile = await self.student_memory.get_student_memory(student_id)
        relationship_status = await self.rapport_builder.get_relationship_status(student_id)
        tutor_config = await self.tutor_personality.load_personality()
        
        # Check for accessibility needs
        accessibility_needs = await self.accessibility_integration.get_remembered_accessibility_needs(student_id)
        accessibility_adaptations = {}
        if accessibility_needs:
            accessibility_adaptations = self.accessibility_integration.should_apply_accessibility_adaptations(accessibility_needs)
        
        # Generate personalized greeting
        greeting = await self.rapport_builder.generate_appropriate_greeting(student_id)
        check_in = await self.rapport_builder.generate_check_in(student_id)
        
        # Prepare personalized session context
        session_personality = {
            'greeting': greeting,
            'check_in': check_in,
            'relationship_stage': relationship_status['stage'],
            'trust_level': relationship_status['trust_level'],
            'preferred_teaching_style': relationship_status.get('preferred_teaching_style'),
            'student_interests': student_profile.interests,
            'known_struggles': student_profile.learning_struggles,
            'known_strengths': student_profile.strengths,
            'emotional_patterns': student_profile.emotional_patterns,
            'accessibility_adaptations': accessibility_adaptations,
            'tutor_subject_confidence': tutor_config.subject_confidence_levels,
            'conversation_highlights': await self.student_memory.get_conversation_highlights(student_id, 5)
        }
        
        return session_personality
    
    async def process_interaction(self, student_id: str, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a learning interaction and update personality state"""
        # Detect emotional state
        emotional_state = await self.emotional_intelligence.detect_emotional_state(student_id, interaction_data)
        
        # Track emotional patterns
        await self.emotional_intelligence.track_emotional_pattern(student_id, emotional_state, interaction_data)
        
        # Get adaptive response approach
        adaptive_tone = await self.emotional_intelligence.get_adaptive_tone(student_id, emotional_state)
        
        # Update tutor's learning about effectiveness
        subject = interaction_data.get('subject', 'general')
        teaching_style = interaction_data.get('teaching_style_used', 'encouraging')
        success_rate = interaction_data.get('correctness', 0.0)
        
        await self.tutor_personality.adapt_teaching_style(student_id, subject, teaching_style, success_rate)
        
        # Generate contextual content if appropriate
        contextual_reference = None
        interest_example = None
        
        if success_rate < 0.5:  # If struggling, provide encouraging reference
            contextual_reference = await self.personalized_content.generate_contextual_reference(
                student_id, interaction_data.get('topic', ''), 'encouraging'
            )
        
        if interaction_data.get('needs_example'):
            interest_example = await self.personalized_content.generate_interest_based_example(
                student_id, interaction_data.get('topic', ''), interaction_data.get('concept', '')
            )
        
        # Check if this was a breakthrough moment
        if success_rate > 0.8 and interaction_data.get('difficulty_level', 0) > 0.7:
            await self.student_memory.add_conversation_highlight(
                student_id=student_id,
                highlight_type='breakthrough',
                content=f"mastered {interaction_data.get('concept', 'difficult concept')}",
                topic=interaction_data.get('topic'),
                emotional_state=emotional_state.value,
                breakthrough_level=success_rate
            )
        
        # Prepare response context
        response_context = {
            'emotional_state': emotional_state.value,
            'adaptive_tone': adaptive_tone,
            'contextual_reference': contextual_reference,
            'interest_based_example': interest_example,
            'recommended_teaching_style': self.tutor_personality.get_recommended_teaching_style(subject),
            'tutor_subject_confidence': self.tutor_personality.get_subject_confidence(subject)
        }
        
        return response_context
    
    async def end_session(self, student_id: str, session_summary: Dict[str, Any]) -> Dict[str, Any]:
        """End session and update relationship metrics"""
        # Update relationship based on session outcome
        await self.rapport_builder.update_relationship_metrics(student_id, session_summary)
        
        # Store any new insights about the student
        insights = session_summary.get('insights', {})
        if insights:
            await self.student_memory.update_student_memory(student_id, insights)
        
        # Generate appropriate closing
        relationship_status = await self.rapport_builder.get_relationship_status(student_id)
        
        closings = {
            RelationshipStage.FIRST_MEETING: "Great first session! I'm looking forward to learning more with you.",
            RelationshipStage.GETTING_ACQUAINTED: "Nice work today! See you next time.",
            RelationshipStage.BUILDING_TRUST: "You did really well today! Keep up the great work.",
            RelationshipStage.ESTABLISHED: "Another productive session! You're making great progress.",
            RelationshipStage.DEEP_CONNECTION: "Awesome session as always! I'm proud of how far you've come."
        }
        
        closing = closings.get(relationship_status['stage'], "Good session! Keep learning!")
        
        return {
            'closing_message': closing,
            'relationship_updated': True,
            'trust_level': relationship_status['trust_level'],
            'rapport_score': relationship_status['rapport_score'],
            'sessions_completed': relationship_status['total_sessions']
        }
    
    async def get_milestone_celebrations(self, student_id: str) -> List[Dict[str, Any]]:
        """Check for milestones to celebrate"""
        profile = await self.student_memory.get_student_memory(student_id)
        relationship = await self.rapport_builder.get_relationship_status(student_id)
        
        celebrations = []
        
        # Check various milestone types
        # This would integrate with other systems to detect achievements
        # For now, return structure for potential celebrations
        
        return celebrations
    
    async def integrate_with_fsrs(self, student_id: str, fsrs_recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate personality-informed insights with FSRS scheduling"""
        profile = await self.student_memory.get_student_memory(student_id)
        relationship = await self.rapport_builder.get_relationship_status(student_id)
        
        # Adjust FSRS recommendations based on personality insights
        personality_adjustments = {}
        
        # If student has anxiety patterns, space reviews more gently
        if 'anxiety' in profile.stress_triggers:
            personality_adjustments['review_spacing_multiplier'] = 1.2
        
        # If relationship is strong, can handle more challenging sequences
        if relationship['trust_level'] > 0.8:
            personality_adjustments['difficulty_tolerance'] = 'high'
        
        # Account for emotional patterns
        emotional_patterns = profile.emotional_patterns.get('by_day_of_week', {})
        difficult_days = [day for day, emotion in emotional_patterns.items() 
                         if emotion in ['frustrated', 'overwhelmed']]
        if difficult_days:
            personality_adjustments['avoid_difficult_reviews_on'] = difficult_days
        
        return {
            'original_recommendations': fsrs_recommendations,
            'personality_adjustments': personality_adjustments,
            'combined_recommendations': {**fsrs_recommendations, **personality_adjustments}
        }