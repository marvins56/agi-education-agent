# History-Specific Features Implementation

**Document:** 05_HISTORY_SPECIFIC_FEATURES.md  
**Version:** 1.0  
**Date:** February 17, 2026  
**Dependencies:** D3.js, PostgreSQL, ChromaDB, React, LangChain  

---

## Overview

This document details the implementation of specialized History education features including interactive timelines, primary source analysis tools, Document-Based Question (DBQ) essays, cause-and-effect reasoning frameworks, and historical thinking skills progression systems.

## Architecture Design

### History-Specific Features System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 HISTORY EDUCATION FEATURES                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ FRONTEND COMPONENTS                 BACKEND SERVICES            │
│                                                                 │
│ ┌─────────────────────┐            ┌─────────────────────┐      │
│ │ TIMELINE VIEWER     │            │ TIMELINE GENERATOR  │      │
│ │ • D3.js Timeline    │◄──────────►│ • Historical Events │      │
│ │ • Interactive Zoom  │            │ • Causal Links      │      │
│ │ • Event Details     │            │ • Multi-scale Views │      │
│ │ • Connection Lines  │            │ • Context-aware     │      │
│ └─────────────────────┘            └─────────────────────┘      │
│                                                                 │
│ ┌─────────────────────┐            ┌─────────────────────┐      │
│ │ SOURCE ANALYZER     │            │ SOURCE PROCESSOR    │      │
│ │ • Document Viewer   │◄──────────►│ • OCR & Parsing     │      │
│ │ • Annotation Tools  │            │ • Context Detection │      │
│ │ • Bias Indicators   │            │ • Authenticity      │      │
│ │ • Compare Mode      │            │ • Analysis Prompts  │      │
│ └─────────────────────┘            └─────────────────────┘      │
│                                                                 │
│ ┌─────────────────────┐            ┌─────────────────────┐      │
│ │ DBQ ESSAY BUILDER   │            │ DBQ ORCHESTRATOR    │      │
│ │ • Source Integration│◄──────────►│ • Question Generation│     │
│ │ • Evidence Tracker  │            │ • Rubric Scoring    │      │
│ │ • Argument Builder  │            │ • Feedback Engine   │      │
│ │ • Draft Versions    │            │ • Thesis Evaluation │      │
│ └─────────────────────┘            └─────────────────────┘      │
│                                                                 │
│ ┌─────────────────────┐            ┌─────────────────────┐      │
│ │ THINKING SKILLS     │            │ SKILLS ASSESSOR     │      │
│ │ • Skill Tracker     │◄──────────►│ • Progression Model │      │
│ │ • Activity Picker   │            │ • Difficulty Scaling│      │
│ │ • Progress Visual   │            │ • Scaffolding       │      │
│ │ • Skill Challenges  │            │ • Competency Maps   │      │
│ └─────────────────────┘            └─────────────────────┘      │
│                                                                 │
│ KNOWLEDGE ORGANIZATION              CONTENT MANAGEMENT          │
│                                                                 │
│ ┌─────────────────────┐            ┌─────────────────────┐      │
│ │ ERA-BASED BROWSER   │            │ CONTENT CURATOR     │      │
│ │ • Chronological Nav │◄──────────►│ • Historical Periods│      │
│ │ • Theme Clusters    │            │ • Topic Hierarchies │      │
│ │ • Knowledge Maps    │            │ • Prerequisite Trees│      │
│ │ • Connection Graph  │            │ • Content Seeding   │      │
│ └─────────────────────┘            └─────────────────────┘      │
│                                                                 │
│                    HISTORICAL REASONING ENGINE                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ • Causal Chain Analysis    • Contextualization Support     │ │
│ │ • Perspective Recognition  • Change-over-Time Analysis     │ │
│ │ • Evidence Evaluation      • Historical Significance       │ │
│ │ • Argument Construction    • Bias Detection & Analysis     │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Structure

### Directory Structure
```
src/history/
├── __init__.py
├── timeline/
│   ├── __init__.py
│   ├── generator.py          # Timeline data generation
│   ├── events_processor.py   # Historical event processing
│   ├── causal_analyzer.py    # Cause-effect relationship analysis
│   └── timeline_schemas.py   # Timeline data models
├── sources/
│   ├── __init__.py
│   ├── analyzer.py           # Primary source analysis
│   ├── document_processor.py # Document parsing and OCR
│   ├── bias_detector.py      # Historical bias detection
│   ├── authenticity_checker.py # Source authenticity verification
│   └── source_schemas.py     # Source analysis data models
├── dbq/
│   ├── __init__.py
│   ├── orchestrator.py       # DBQ workflow management
│   ├── question_generator.py # DBQ question creation
│   ├── essay_evaluator.py    # Essay grading and feedback
│   ├── rubric_engine.py      # Rubric-based assessment
│   └── dbq_schemas.py        # DBQ data models
├── thinking_skills/
│   ├── __init__.py
│   ├── assessor.py           # Historical thinking skills assessment
│   ├── progression_tracker.py # Skill development tracking
│   ├── scaffolding_engine.py # Adaptive scaffolding
│   └── skills_schemas.py     # Skills data models
├── reasoning/
│   ├── __init__.py
│   ├── causal_chains.py      # Cause-effect reasoning
│   ├── contextualization.py  # Historical context analysis
│   ├── perspective_analysis.py # Multiple perspectives
│   └── argument_builder.py   # Historical argument construction
├── content/
│   ├── __init__.py
│   ├── curator.py            # Content curation and organization
│   ├── era_organizer.py      # Era-based content organization
│   ├── knowledge_graph.py    # Historical knowledge relationships
│   └── content_seeder.py     # Initial content population
└── schemas.py                # Common History feature schemas
```

---

## Core Implementation

### 1. `src/history/schemas.py` - Core Data Models
```python
"""Core data models for History-specific features."""
from datetime import datetime, date
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
import uuid


class HistoricalPeriod(str, Enum):
    """Major historical periods for organization."""
    ANCIENT_CIVILIZATIONS = "ancient_civilizations"
    CLASSICAL_ANTIQUITY = "classical_antiquity"
    MEDIEVAL = "medieval"
    RENAISSANCE = "renaissance"
    EARLY_MODERN = "early_modern"
    INDUSTRIAL_REVOLUTION = "industrial_revolution"
    MODERN = "modern"
    CONTEMPORARY = "contemporary"


class HistoricalThinkingSkill(str, Enum):
    """Historical thinking skills taxonomy."""
    CHRONOLOGICAL_REASONING = "chronological_reasoning"
    CRAFTING_ARGUMENTS = "crafting_arguments"
    ANALYZING_SOURCES = "analyzing_sources"
    CONTEXTUALIZATION = "contextualization"
    SYNTHESIS = "synthesis"


class SourceType(str, Enum):
    """Types of historical sources."""
    PRIMARY_TEXT = "primary_text"
    PRIMARY_IMAGE = "primary_image"
    PRIMARY_AUDIO = "primary_audio"
    PRIMARY_VIDEO = "primary_video"
    SECONDARY_TEXT = "secondary_text"
    ARTIFACT = "artifact"
    STATISTICAL_DATA = "statistical_data"
    MAP = "map"
    TIMELINE = "timeline"


class CausalRelationType(str, Enum):
    """Types of causal relationships between historical events."""
    IMMEDIATE_CAUSE = "immediate_cause"
    UNDERLYING_CAUSE = "underlying_cause"
    CONTRIBUTING_FACTOR = "contributing_factor"
    NECESSARY_CONDITION = "necessary_condition"
    SUFFICIENT_CONDITION = "sufficient_condition"
    CATALYST = "catalyst"
    CONSEQUENCE = "consequence"


class HistoricalEvent(BaseModel):
    """Represents a historical event or development."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(description="Event title")
    description: str = Field(description="Detailed description")
    
    # Temporal information
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    date_precision: str = "exact"  # "exact", "approximate", "circa", "between"
    
    # Classification
    period: HistoricalPeriod
    region: str = Field(description="Geographic region")
    themes: List[str] = Field(default_factory=list, description="Thematic tags")
    
    # Relationships
    causal_relationships: Dict[str, CausalRelationType] = Field(
        default_factory=dict, 
        description="event_id -> relationship_type"
    )
    
    # Educational metadata
    difficulty_level: float = Field(ge=0.0, le=1.0, default=0.5)
    importance_score: float = Field(ge=0.0, le=1.0, description="Curriculum importance")
    prerequisite_events: List[str] = Field(default_factory=list)
    
    # Content
    primary_sources: List[str] = Field(default_factory=list, description="Source IDs")
    key_figures: List[str] = Field(default_factory=list)
    key_concepts: List[str] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)


class PrimarySource(BaseModel):
    """Represents a historical primary source."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    
    # Source information
    source_type: SourceType
    author: Optional[str] = None
    date_created: Optional[date] = None
    origin_location: Optional[str] = None
    language: str = "en"
    
    # Content
    content_text: Optional[str] = None  # For text sources
    content_url: Optional[str] = None   # For media/images
    content_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Analysis
    bias_indicators: List[str] = Field(default_factory=list)
    perspective: Optional[str] = None   # Whose perspective this represents
    reliability_score: float = Field(ge=0.0, le=1.0, default=0.5)
    authenticity_verified: bool = False
    
    # Educational use
    related_events: List[str] = Field(default_factory=list, description="Event IDs")
    analysis_questions: List[str] = Field(default_factory=list)
    difficulty_level: float = Field(ge=0.0, le=1.0, default=0.5)
    
    # Context
    historical_context: str = Field(description="Background context")
    modern_relevance: Optional[str] = None


class TimelineView(BaseModel):
    """Configuration for timeline visualization."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    
    # Timeline scope
    start_date: date
    end_date: date
    focus_events: List[str] = Field(description="Event IDs to highlight")
    
    # Filtering
    included_periods: List[HistoricalPeriod] = Field(default_factory=list)
    included_regions: List[str] = Field(default_factory=list)
    included_themes: List[str] = Field(default_factory=list)
    
    # Visualization
    zoom_levels: List[str] = Field(
        default=["decade", "year", "month", "day"],
        description="Available zoom levels"
    )
    show_causal_connections: bool = True
    show_concurrent_events: bool = True
    
    # Educational context
    grade_level: Optional[str] = None
    learning_objectives: List[str] = Field(default_factory=list)


class DBQExercise(BaseModel):
    """Document-Based Question exercise."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    prompt: str = Field(description="Main essay prompt")
    
    # Sources
    primary_sources: List[str] = Field(description="Source IDs")
    source_analysis_questions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Questions for each source"
    )
    
    # Requirements
    historical_thinking_skills: List[HistoricalThinkingSkill] = Field(default_factory=list)
    time_period: HistoricalPeriod
    minimum_sources_required: int = 3
    word_count_target: int = 1000
    
    # Scaffolding
    thesis_guidance: str = Field(description="Guidance for thesis development")
    evidence_requirements: List[str] = Field(description="Types of evidence needed")
    argument_structure_guide: str = Field(description="Suggested argument structure")
    
    # Assessment
    rubric_categories: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    sample_responses: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata
    difficulty_level: float = Field(ge=0.0, le=1.0, default=0.5)
    estimated_time_minutes: int = 90
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class HistoricalThinkingAssessment(BaseModel):
    """Assessment of historical thinking skills."""
    student_id: str
    skill: HistoricalThinkingSkill
    
    # Assessment data
    current_level: int = Field(ge=1, le=5, description="1=Novice, 5=Expert")
    evidence: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Evidence supporting this assessment"
    )
    
    # Sub-skills breakdown
    sub_skill_scores: Dict[str, float] = Field(default_factory=dict)
    
    # Progress tracking
    previous_assessments: List[Dict[str, Any]] = Field(default_factory=list)
    growth_rate: float = 0.0
    
    # Recommendations
    next_activities: List[str] = Field(default_factory=list)
    scaffolding_needed: List[str] = Field(default_factory=list)
    
    # Metadata
    assessment_date: datetime = Field(default_factory=datetime.now)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)


class CausalChain(BaseModel):
    """Represents a chain of causally related historical events."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    
    # Chain structure
    events: List[str] = Field(description="Event IDs in causal order")
    relationships: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Detailed relationship descriptions"
    )
    
    # Analysis
    complexity_level: float = Field(ge=0.0, le=1.0, description="Chain complexity")
    alternative_explanations: List[str] = Field(default_factory=list)
    historian_debates: List[str] = Field(default_factory=list)
    
    # Educational use
    teaching_points: List[str] = Field(default_factory=list)
    common_misconceptions: List[str] = Field(default_factory=list)
    discussion_questions: List[str] = Field(default_factory=list)


class HistoricalEra(BaseModel):
    """Represents a historical era/period organization."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    period: HistoricalPeriod
    
    # Temporal boundaries
    start_date: date
    end_date: date
    
    # Organization
    major_themes: List[str] = Field(default_factory=list)
    key_events: List[str] = Field(description="Event IDs")
    important_figures: List[str] = Field(default_factory=list)
    technological_developments: List[str] = Field(default_factory=list)
    
    # Transitions
    preceding_era: Optional[str] = None
    following_era: Optional[str] = None
    transition_factors: List[str] = Field(default_factory=list)
    
    # Geographic scope
    primary_regions: List[str] = Field(default_factory=list)
    cultural_areas: List[str] = Field(default_factory=list)
    
    # Educational metadata
    grade_level_appropriateness: Dict[str, bool] = Field(default_factory=dict)
    prerequisite_knowledge: List[str] = Field(default_factory=list)
    key_concepts: List[str] = Field(default_factory=list)
```

### 2. `src/history/timeline/generator.py` - Timeline Generation System
```python
"""Historical timeline generation with intelligent event selection and organization."""
import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from collections import defaultdict

from src.history.schemas import (
    HistoricalEvent, TimelineView, HistoricalPeriod, CausalRelationType
)
from src.history.timeline.events_processor import HistoricalEventsProcessor
from src.history.timeline.causal_analyzer import CausalAnalyzer
from src.rag.retriever import KnowledgeRetriever
from src.memory.manager import MemoryManager

logger = logging.getLogger(__name__)


class TimelineGenerator:
    """Generates intelligent, adaptive historical timelines for education."""
    
    def __init__(
        self,
        knowledge_retriever: KnowledgeRetriever,
        memory_manager: MemoryManager,
        events_processor: HistoricalEventsProcessor = None,
        causal_analyzer: CausalAnalyzer = None
    ):
        self.retriever = knowledge_retriever
        self.memory = memory_manager
        self.events_processor = events_processor or HistoricalEventsProcessor()
        self.causal_analyzer = causal_analyzer or CausalAnalyzer()
        
        # Pre-loaded historical periods for quick access
        self.period_boundaries = self._initialize_period_boundaries()
        
        # Event importance weights for different educational contexts
        self.importance_weights = {
            "political": 1.2,
            "military": 1.0,
            "social": 1.1,
            "economic": 1.15,
            "cultural": 0.9,
            "technological": 1.05,
            "religious": 0.95
        }
    
    def _initialize_period_boundaries(self) -> Dict[HistoricalPeriod, Tuple[date, date]]:
        """Initialize standard historical period boundaries."""
        return {
            HistoricalPeriod.ANCIENT_CIVILIZATIONS: (
                date(3500, 1, 1), date(500, 1, 1)
            ),
            HistoricalPeriod.CLASSICAL_ANTIQUITY: (
                date(800, 1, 1), date(500, 1, 1)
            ),
            HistoricalPeriod.MEDIEVAL: (
                date(500, 1, 1), date(1500, 1, 1)
            ),
            HistoricalPeriod.RENAISSANCE: (
                date(1300, 1, 1), date(1600, 1, 1)
            ),
            HistoricalPeriod.EARLY_MODERN: (
                date(1450, 1, 1), date(1800, 1, 1)
            ),
            HistoricalPeriod.INDUSTRIAL_REVOLUTION: (
                date(1750, 1, 1), date(1900, 1, 1)
            ),
            HistoricalPeriod.MODERN: (
                date(1900, 1, 1), date(1990, 1, 1)
            ),
            HistoricalPeriod.CONTEMPORARY: (
                date(1990, 1, 1), date.today()
            )
        }
    
    async def generate_topic_timeline(
        self,
        topic: str,
        student_id: Optional[str] = None,
        time_range: Optional[Tuple[date, date]] = None,
        max_events: int = 20,
        focus_themes: Optional[List[str]] = None,
        difficulty_level: float = 0.5
    ) -> TimelineView:
        """Generate a focused timeline for a specific historical topic."""
        
        logger.info(f"Generating timeline for topic: {topic}")
        
        # 1. Retrieve relevant historical events
        events = await self._retrieve_events_for_topic(
            topic, time_range, max_events * 2  # Get more than needed for filtering
        )
        
        # 2. Analyze student's prior knowledge if student_id provided
        if student_id:
            prior_knowledge = await self._analyze_student_knowledge(student_id, topic)
            events = self._filter_events_by_knowledge(events, prior_knowledge, difficulty_level)
        
        # 3. Select most important events for timeline
        selected_events = await self._select_timeline_events(
            events, max_events, focus_themes
        )
        
        # 4. Analyze causal relationships
        causal_relationships = await self.causal_analyzer.analyze_event_relationships(
            selected_events
        )
        
        # 5. Determine timeline boundaries
        if not time_range:
            time_range = self._calculate_timeline_boundaries(selected_events)
        
        # 6. Create timeline view configuration
        timeline_view = TimelineView(
            title=f"Timeline: {topic}",
            description=f"Interactive timeline exploring {topic} with {len(selected_events)} key events",
            start_date=time_range[0],
            end_date=time_range[1],
            focus_events=[event.id for event in selected_events],
            included_themes=focus_themes or [],
            show_causal_connections=True,
            show_concurrent_events=True
        )
        
        # 7. Add educational metadata
        timeline_view.learning_objectives = await self._generate_learning_objectives(
            topic, selected_events
        )
        
        logger.info(
            f"Generated timeline with {len(selected_events)} events "
            f"spanning {time_range[0]} to {time_range[1]}"
        )
        
        return timeline_view
    
    async def _retrieve_events_for_topic(
        self,
        topic: str,
        time_range: Optional[Tuple[date, date]] = None,
        limit: int = 40
    ) -> List[HistoricalEvent]:
        """Retrieve historical events related to the topic."""
        
        # Use RAG system to find relevant events
        rag_results = await self.retriever.retrieve(
            query=f"historical events related to {topic}",
            subject="history",
            limit=limit
        )
        
        events = []
        for result in rag_results.get("sources", []):
            # Parse historical event from RAG result
            event = await self.events_processor.parse_event_from_source(
                result, topic
            )
            
            if event and self._event_in_time_range(event, time_range):
                events.append(event)
        
        # Supplement with pre-curated events if needed
        if len(events) < limit // 2:
            curated_events = await self._get_curated_events_for_topic(topic)
            events.extend(curated_events)
        
        return events
    
    def _event_in_time_range(
        self,
        event: HistoricalEvent,
        time_range: Optional[Tuple[date, date]]
    ) -> bool:
        """Check if event falls within specified time range."""
        if not time_range or not event.start_date:
            return True
        
        return (
            time_range[0] <= event.start_date <= time_range[1] or
            (event.end_date and time_range[0] <= event.end_date <= time_range[1])
        )
    
    async def _analyze_student_knowledge(
        self,
        student_id: str,
        topic: str
    ) -> Dict[str, float]:
        """Analyze student's prior knowledge of the topic."""
        
        # Get student's mastery data
        mastery_data = await self.memory.get_student_mastery(student_id, subject="History")
        
        prior_knowledge = {}
        for record in mastery_data:
            if topic.lower() in record["topic"].lower():
                prior_knowledge[record["topic"]] = record["mastery_score"] / 100.0
        
        return prior_knowledge
    
    def _filter_events_by_knowledge(
        self,
        events: List[HistoricalEvent],
        prior_knowledge: Dict[str, float],
        difficulty_level: float
    ) -> List[HistoricalEvent]:
        """Filter events based on student's knowledge and desired difficulty."""
        
        filtered_events = []
        
        for event in events:
            # Calculate if event is appropriate for student's level
            event_appropriate = True
            
            # Check prerequisite knowledge
            for prereq_event_id in event.prerequisite_events:
                prereq_mastery = prior_knowledge.get(prereq_event_id, 0.0)
                if prereq_mastery < 0.6:  # Prerequisite not mastered
                    event_appropriate = False
                    break
            
            # Check difficulty match
            difficulty_diff = abs(event.difficulty_level - difficulty_level)
            if difficulty_diff > 0.3:  # Too different from target difficulty
                event_appropriate = False
            
            if event_appropriate:
                filtered_events.append(event)
        
        return filtered_events
    
    async def _select_timeline_events(
        self,
        events: List[HistoricalEvent],
        max_events: int,
        focus_themes: Optional[List[str]] = None
    ) -> List[HistoricalEvent]:
        """Select the most important events for the timeline."""
        
        # Calculate importance scores for each event
        scored_events = []
        
        for event in events:
            score = self._calculate_event_importance(event, focus_themes)
            scored_events.append((event, score))
        
        # Sort by importance score
        scored_events.sort(key=lambda x: x[1], reverse=True)
        
        # Select top events while ensuring temporal distribution
        selected_events = self._ensure_temporal_distribution(
            scored_events, max_events
        )
        
        # Sort selected events chronologically
        selected_events.sort(key=lambda e: e.start_date or date.min)
        
        return selected_events
    
    def _calculate_event_importance(
        self,
        event: HistoricalEvent,
        focus_themes: Optional[List[str]] = None
    ) -> float:
        """Calculate importance score for an event."""
        
        # Base importance from curriculum
        base_score = event.importance_score
        
        # Theme relevance bonus
        theme_bonus = 0.0
        if focus_themes:
            matching_themes = set(event.themes) & set(focus_themes)
            theme_bonus = len(matching_themes) * 0.2
        
        # Causal centrality bonus (events that cause many other events)
        centrality_bonus = len(event.causal_relationships) * 0.1
        
        # Thematic weight adjustments
        thematic_weight = 1.0
        for theme in event.themes:
            theme_lower = theme.lower()
            for weight_category, weight in self.importance_weights.items():
                if weight_category in theme_lower:
                    thematic_weight *= weight
                    break
        
        total_score = (base_score + theme_bonus + centrality_bonus) * thematic_weight
        
        return min(1.0, total_score)  # Cap at 1.0
    
    def _ensure_temporal_distribution(
        self,
        scored_events: List[Tuple[HistoricalEvent, float]],
        max_events: int
    ) -> List[HistoricalEvent]:
        """Ensure selected events are well-distributed across time."""
        
        if len(scored_events) <= max_events:
            return [event for event, _ in scored_events]
        
        # Sort by date to analyze temporal distribution
        dated_events = [
            (event, score) for event, score in scored_events 
            if event.start_date is not None
        ]
        dated_events.sort(key=lambda x: x[0].start_date)
        
        if not dated_events:
            return [event for event, _ in scored_events[:max_events]]
        
        # Calculate time span
        start_date = dated_events[0][0].start_date
        end_date = dated_events[-1][0].start_date
        time_span_days = (end_date - start_date).days
        
        if time_span_days <= 0:
            return [event for event, _ in scored_events[:max_events]]
        
        # Create time buckets
        num_buckets = min(max_events, 10)
        bucket_size = time_span_days / num_buckets
        buckets = [[] for _ in range(num_buckets)]
        
        # Distribute events into buckets
        for event, score in dated_events:
            days_from_start = (event.start_date - start_date).days
            bucket_index = min(int(days_from_start / bucket_size), num_buckets - 1)
            buckets[bucket_index].append((event, score))
        
        # Select best event from each bucket
        selected_events = []
        events_per_bucket = max_events // num_buckets
        remaining_slots = max_events % num_buckets
        
        for i, bucket in enumerate(buckets):
            if not bucket:
                continue
                
            # Sort bucket by score
            bucket.sort(key=lambda x: x[1], reverse=True)
            
            # Select events from this bucket
            slots_for_bucket = events_per_bucket + (1 if i < remaining_slots else 0)
            for j in range(min(slots_for_bucket, len(bucket))):
                selected_events.append(bucket[j][0])
        
        # If we still have slots, fill with highest-scored remaining events
        if len(selected_events) < max_events:
            selected_ids = {event.id for event in selected_events}
            remaining_events = [
                (event, score) for event, score in scored_events
                if event.id not in selected_ids
            ]
            remaining_events.sort(key=lambda x: x[1], reverse=True)
            
            slots_remaining = max_events - len(selected_events)
            for i in range(min(slots_remaining, len(remaining_events))):
                selected_events.append(remaining_events[i][0])
        
        return selected_events
    
    def _calculate_timeline_boundaries(
        self,
        events: List[HistoricalEvent]
    ) -> Tuple[date, date]:
        """Calculate appropriate start and end dates for timeline."""
        
        if not events:
            return date.today() - timedelta(days=365), date.today()
        
        # Find earliest and latest dates
        dates = []
        for event in events:
            if event.start_date:
                dates.append(event.start_date)
            if event.end_date:
                dates.append(event.end_date)
        
        if not dates:
            return date.today() - timedelta(days=365), date.today()
        
        earliest = min(dates)
        latest = max(dates)
        
        # Add padding (10% of time span, minimum 1 year)
        time_span = latest - earliest
        padding_days = max(365, int(time_span.days * 0.1))
        
        start_date = earliest - timedelta(days=padding_days)
        end_date = latest + timedelta(days=padding_days)
        
        return start_date, end_date
    
    async def _generate_learning_objectives(
        self,
        topic: str,
        events: List[HistoricalEvent]
    ) -> List[str]:
        """Generate learning objectives for the timeline."""
        
        objectives = [
            f"Understand the chronological sequence of major events in {topic}",
            f"Identify cause-and-effect relationships in {topic}",
            f"Analyze the significance of key developments in {topic}"
        ]
        
        # Add theme-specific objectives
        all_themes = set()
        for event in events:
            all_themes.update(event.themes)
        
        for theme in all_themes:
            if theme.lower() in ["political", "government"]:
                objectives.append(f"Evaluate political changes and their impacts during {topic}")
            elif theme.lower() in ["social", "society"]:
                objectives.append(f"Examine social transformations in {topic}")
            elif theme.lower() in ["economic", "trade"]:
                objectives.append(f"Assess economic factors and developments in {topic}")
        
        return objectives[:6]  # Limit to 6 objectives
    
    async def generate_comparative_timeline(
        self,
        topics: List[str],
        student_id: Optional[str] = None,
        max_events_per_topic: int = 10
    ) -> TimelineView:
        """Generate a comparative timeline showing multiple topics simultaneously."""
        
        all_events = []
        all_themes = set()
        
        # Generate events for each topic
        for topic in topics:
            topic_events = await self._retrieve_events_for_topic(
                topic, limit=max_events_per_topic * 2
            )
            
            # Tag events with their source topic
            for event in topic_events:
                event.themes.append(f"topic_{topic.lower().replace(' ', '_')}")
                all_themes.update(event.themes)
            
            # Select best events for this topic
            selected_topic_events = await self._select_timeline_events(
                topic_events, max_events_per_topic
            )
            
            all_events.extend(selected_topic_events)
        
        # Remove duplicates based on title and date
        unique_events = self._deduplicate_events(all_events)
        
        # Calculate timeline boundaries
        time_range = self._calculate_timeline_boundaries(unique_events)
        
        # Create comparative timeline
        timeline_view = TimelineView(
            title=f"Comparative Timeline: {', '.join(topics)}",
            description=f"Comparative analysis of {', '.join(topics)} showing concurrent developments",
            start_date=time_range[0],
            end_date=time_range[1],
            focus_events=[event.id for event in unique_events],
            included_themes=list(all_themes),
            show_causal_connections=True,
            show_concurrent_events=True
        )
        
        # Add comparative learning objectives
        timeline_view.learning_objectives = [
            f"Compare and contrast developments in {', '.join(topics)}",
            "Identify concurrent events and their potential relationships",
            "Analyze how different regions/topics influenced each other",
            "Evaluate the relative significance of events across different contexts"
        ]
        
        return timeline_view
    
    def _deduplicate_events(self, events: List[HistoricalEvent]) -> List[HistoricalEvent]:
        """Remove duplicate events based on similarity."""
        
        unique_events = []
        seen_signatures = set()
        
        for event in events:
            # Create signature based on title and date
            title_lower = event.title.lower().strip()
            date_str = event.start_date.isoformat() if event.start_date else "unknown"
            signature = f"{title_lower}_{date_str}"
            
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                unique_events.append(event)
        
        return unique_events
    
    async def _get_curated_events_for_topic(self, topic: str) -> List[HistoricalEvent]:
        """Get pre-curated events for common topics."""
        
        # This would typically load from a curated database
        # For now, return sample events based on topic
        curated_events = []
        
        topic_lower = topic.lower()
        
        if "world war i" in topic_lower or "wwi" in topic_lower:
            curated_events = [
                HistoricalEvent(
                    title="Assassination of Archduke Franz Ferdinand",
                    description="The event that triggered World War I",
                    start_date=date(1914, 6, 28),
                    period=HistoricalPeriod.MODERN,
                    region="Europe",
                    themes=["political", "military", "assassination"],
                    importance_score=0.95,
                    key_concepts=["immediate cause", "alliance system", "nationalism"]
                ),
                HistoricalEvent(
                    title="Germany declares war on Russia",
                    description="Germany's declaration of war escalates the conflict",
                    start_date=date(1914, 8, 1),
                    period=HistoricalPeriod.MODERN,
                    region="Europe",
                    themes=["military", "political"],
                    importance_score=0.85,
                    key_concepts=["escalation", "alliance obligations"]
                )
            ]
        
        return curated_events
```

### 3. `src/history/sources/analyzer.py` - Primary Source Analysis System
```python
"""Primary source analysis system for historical documents and media."""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
import re
from datetime import datetime

from langchain_core.messages import SystemMessage, HumanMessage

from src.history.schemas import PrimarySource, SourceType, HistoricalThinkingSkill
from src.history.sources.bias_detector import BiasDetector
from src.history.sources.authenticity_checker import AuthenticityChecker
from src.llm.factory import LLMFactory
from src.rag.retriever import KnowledgeRetriever

logger = logging.getLogger(__name__)


class PrimarySourceAnalyzer:
    """Analyzes primary sources for educational use."""
    
    def __init__(
        self,
        knowledge_retriever: KnowledgeRetriever,
        bias_detector: BiasDetector = None,
        authenticity_checker: AuthenticityChecker = None
    ):
        self.retriever = knowledge_retriever
        self.bias_detector = bias_detector or BiasDetector()
        self.authenticity_checker = authenticity_checker or AuthenticityChecker()
        self.llm = LLMFactory.create(provider="openai", model="gpt-4")
        
        # Analysis question templates by source type
        self.question_templates = self._initialize_question_templates()
        
        # Historical thinking skills mapping
        self.skills_mapping = self._initialize_skills_mapping()
    
    def _initialize_question_templates(self) -> Dict[SourceType, List[str]]:
        """Initialize analysis question templates for different source types."""
        return {
            SourceType.PRIMARY_TEXT: [
                "Who wrote this document and what was their role/position?",
                "When and where was this document created?",
                "What was the intended audience for this document?",
                "What is the main message or argument of this document?",
                "What evidence of bias or perspective can you identify?",
                "How might the author's background have influenced this document?",
                "What does this document reveal about the time period?",
                "How does this document compare to other sources from the same period?"
            ],
            SourceType.PRIMARY_IMAGE: [
                "What do you see in this image? Describe the scene in detail.",
                "When and where do you think this image was created?",
                "Who might have created this image and for what purpose?",
                "What emotions or messages does this image convey?",
                "What details in the image tell us about the historical context?",
                "How might this image have been used or displayed originally?",
                "What perspective does this image represent?",
                "What might be missing or left out of this image?"
            ],
            SourceType.ARTIFACT: [
                "What is this object and what was it used for?",
                "What materials is it made from and what does that tell us?",
                "Who might have owned or used this object?",
                "What does this object reveal about daily life in this period?",
                "How does this object reflect the technology of its time?",
                "What social or economic status might its owner have had?",
                "How has this type of object changed over time?",
                "What questions does this object raise about the past?"
            ]
        }
    
    def _initialize_skills_mapping(self) -> Dict[str, HistoricalThinkingSkill]:
        """Map question types to historical thinking skills."""
        return {
            "authorship": HistoricalThinkingSkill.ANALYZING_SOURCES,
            "audience": HistoricalThinkingSkill.ANALYZING_SOURCES,
            "purpose": HistoricalThinkingSkill.ANALYZING_SOURCES,
            "bias": HistoricalThinkingSkill.ANALYZING_SOURCES,
            "context": HistoricalThinkingSkill.CONTEXTUALIZATION,
            "comparison": HistoricalThinkingSkill.CRAFTING_ARGUMENTS,
            "significance": HistoricalThinkingSkill.SYNTHESIS,
            "chronology": HistoricalThinkingSkill.CHRONOLOGICAL_REASONING
        }
    
    async def analyze_primary_source(
        self,
        source: PrimarySource,
        student_level: str = "intermediate",
        focus_skills: Optional[List[HistoricalThinkingSkill]] = None
    ) -> Dict[str, Any]:
        """Perform comprehensive analysis of a primary source."""
        
        logger.info(f"Analyzing primary source: {source.title}")
        
        analysis_results = {
            "source_id": source.id,
            "basic_analysis": {},
            "bias_analysis": {},
            "authenticity_check": {},
            "educational_analysis": {},
            "generated_questions": [],
            "teaching_suggestions": []
        }
        
        try:
            # 1. Basic source analysis
            analysis_results["basic_analysis"] = await self._perform_basic_analysis(source)
            
            # 2. Bias detection and analysis
            analysis_results["bias_analysis"] = await self.bias_detector.detect_bias(source)
            
            # 3. Authenticity verification
            analysis_results["authenticity_check"] = await self.authenticity_checker.verify_authenticity(source)
            
            # 4. Educational value analysis
            analysis_results["educational_analysis"] = await self._analyze_educational_value(
                source, student_level, focus_skills
            )
            
            # 5. Generate analysis questions
            analysis_results["generated_questions"] = await self._generate_analysis_questions(
                source, student_level, focus_skills
            )
            
            # 6. Generate teaching suggestions
            analysis_results["teaching_suggestions"] = await self._generate_teaching_suggestions(
                source, analysis_results, student_level
            )
            
            logger.info(f"Analysis complete for source: {source.title}")
            
        except Exception as e:
            logger.error(f"Error analyzing source {source.title}: {e}")
            analysis_results["error"] = str(e)
        
        return analysis_results
    
    async def _perform_basic_analysis(self, source: PrimarySource) -> Dict[str, Any]:
        """Perform basic source analysis using LLM."""
        
        analysis_prompt = f"""
        Analyze this primary source for basic information:

        Source Title: {source.title}
        Source Type: {source.source_type.value}
        Author: {source.author or "Unknown"}
        Date: {source.date_created or "Unknown"}
        Origin: {source.origin_location or "Unknown"}

        Content (first 500 characters):
        {(source.content_text or "")[:500]}...

        Provide analysis in the following categories:
        1. SOAPS Analysis:
           - Speaker: Who created this source?
           - Occasion: What was happening when this was created?
           - Audience: Who was the intended audience?
           - Purpose: Why was this source created?
           - Subject: What is the main topic/message?

        2. Historical Context:
           - Time period significance
           - Relevant historical events
           - Social/political climate

        3. Source Reliability:
           - Strengths as historical evidence
           - Potential limitations or weaknesses
           - Corroboration needs

        Format your response as JSON with the above categories.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert historian analyzing primary sources for educational use."),
                HumanMessage(content=analysis_prompt)
            ])
            
            # Parse LLM response (implement proper JSON parsing)
            basic_analysis = self._parse_llm_analysis(response.content)
            
            return basic_analysis
            
        except Exception as e:
            logger.error(f"Basic analysis failed: {e}")
            return {"error": str(e)}
    
    async def _analyze_educational_value(
        self,
        source: PrimarySource,
        student_level: str,
        focus_skills: Optional[List[HistoricalThinkingSkill]]
    ) -> Dict[str, Any]:
        """Analyze the educational value and appropriate use of the source."""
        
        educational_analysis = {
            "difficulty_assessment": {},
            "skill_development": {},
            "curriculum_alignment": {},
            "accessibility": {}
        }
        
        # Assess difficulty level
        educational_analysis["difficulty_assessment"] = await self._assess_source_difficulty(
            source, student_level
        )
        
        # Identify skill development opportunities
        educational_analysis["skill_development"] = self._identify_skill_opportunities(
            source, focus_skills
        )
        
        # Assess curriculum alignment
        educational_analysis["curriculum_alignment"] = await self._assess_curriculum_alignment(
            source
        )
        
        # Evaluate accessibility
        educational_analysis["accessibility"] = self._evaluate_accessibility(source)
        
        return educational_analysis
    
    async def _assess_source_difficulty(
        self,
        source: PrimarySource,
        student_level: str
    ) -> Dict[str, Any]:
        """Assess the difficulty level of the source for students."""
        
        difficulty_factors = {
            "vocabulary_complexity": 0.0,
            "sentence_structure": 0.0,
            "conceptual_complexity": 0.0,
            "cultural_distance": 0.0,
            "contextual_knowledge_required": 0.0
        }
        
        if source.content_text:
            text = source.content_text
            
            # Vocabulary complexity (based on word length and rarity)
            words = re.findall(r'\b\w+\b', text.lower())
            avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
            difficulty_factors["vocabulary_complexity"] = min(1.0, avg_word_length / 8.0)
            
            # Sentence structure complexity
            sentences = re.split(r'[.!?]+', text)
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
            difficulty_factors["sentence_structure"] = min(1.0, avg_sentence_length / 25.0)
        
        # Conceptual complexity based on source type and content
        if source.source_type == SourceType.PRIMARY_TEXT:
            if any(term in source.title.lower() for term in ["treaty", "constitution", "law"]):
                difficulty_factors["conceptual_complexity"] = 0.8
            elif any(term in source.title.lower() for term in ["letter", "diary"]):
                difficulty_factors["conceptual_complexity"] = 0.4
        
        # Cultural distance (how different from modern context)
        creation_year = source.date_created.year if source.date_created else 1900
        years_ago = 2024 - creation_year
        difficulty_factors["cultural_distance"] = min(1.0, years_ago / 500.0)
        
        # Overall difficulty score
        overall_difficulty = sum(difficulty_factors.values()) / len(difficulty_factors)
        
        return {
            "overall_score": overall_difficulty,
            "factors": difficulty_factors,
            "recommended_level": self._map_difficulty_to_level(overall_difficulty),
            "scaffolding_suggestions": self._suggest_scaffolding(difficulty_factors)
        }
    
    def _identify_skill_opportunities(
        self,
        source: PrimarySource,
        focus_skills: Optional[List[HistoricalThinkingSkill]]
    ) -> Dict[str, Any]:
        """Identify historical thinking skill development opportunities."""
        
        skill_opportunities = {}
        
        # All sources can develop source analysis skills
        skill_opportunities[HistoricalThinkingSkill.ANALYZING_SOURCES] = {
            "level": "high",
            "activities": [
                "Identify author, audience, and purpose",
                "Evaluate source reliability and bias",
                "Compare with other sources from the same period"
            ]
        }
        
        # Contextualization opportunities
        skill_opportunities[HistoricalThinkingSkill.CONTEXTUALIZATION] = {
            "level": "medium",
            "activities": [
                "Place source in its historical context",
                "Connect to broader historical patterns",
                "Analyze how context shapes the source"
            ]
        }
        
        # Specific opportunities based on source characteristics
        if len(source.related_events) > 1:
            skill_opportunities[HistoricalThinkingSkill.CHRONOLOGICAL_REASONING] = {
                "level": "high",
                "activities": [
                    "Create timeline of related events",
                    "Analyze change over time",
                    "Identify patterns of continuity and change"
                ]
            }
        
        if source.bias_indicators:
            skill_opportunities[HistoricalThinkingSkill.CRAFTING_ARGUMENTS] = {
                "level": "high",
                "activities": [
                    "Develop arguments about historical interpretations",
                    "Use evidence to support claims",
                    "Address counterarguments and bias"
                ]
            }
        
        # Filter by focus skills if provided
        if focus_skills:
            skill_opportunities = {
                skill: opportunities for skill, opportunities in skill_opportunities.items()
                if skill in focus_skills
            }
        
        return skill_opportunities
    
    async def _generate_analysis_questions(
        self,
        source: PrimarySource,
        student_level: str,
        focus_skills: Optional[List[HistoricalThinkingSkill]]
    ) -> List[Dict[str, Any]]:
        """Generate analysis questions appropriate for the source and student level."""
        
        # Get base questions for source type
        base_questions = self.question_templates.get(source.source_type, [])
        
        # Generate custom questions using LLM
        custom_questions_prompt = f"""
        Generate 5-7 analysis questions for this primary source, appropriate for {student_level} level students:

        Source: {source.title}
        Type: {source.source_type.value}
        Content summary: {source.description}
        Historical context: {source.historical_context}

        Requirements:
        - Questions should develop critical thinking skills
        - Appropriate difficulty for {student_level} students
        - Include both factual and analytical questions
        - Focus on historical thinking skills: {', '.join([skill.value for skill in focus_skills]) if focus_skills else 'all skills'}

        Format as numbered list with each question followed by its difficulty level (easy/medium/hard) and primary thinking skill.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert History teacher creating analysis questions for primary sources."),
                HumanMessage(content=custom_questions_prompt)
            ])
            
            custom_questions = self._parse_questions_from_response(response.content)
            
        except Exception as e:
            logger.warning(f"Custom question generation failed: {e}")
            custom_questions = []
        
        # Combine and organize questions
        all_questions = []
        
        # Add base questions
        for i, question in enumerate(base_questions[:4]):  # Limit base questions
            all_questions.append({
                "id": f"base_{i+1}",
                "question": question,
                "type": "base",
                "difficulty": "medium",
                "thinking_skill": self._infer_thinking_skill(question)
            })
        
        # Add custom questions
        all_questions.extend(custom_questions)
        
        # Sort by difficulty if student level is specified
        if student_level == "beginner":
            all_questions.sort(key=lambda q: {"easy": 1, "medium": 2, "hard": 3}.get(q.get("difficulty", "medium"), 2))
        elif student_level == "advanced":
            all_questions.sort(key=lambda q: {"hard": 1, "medium": 2, "easy": 3}.get(q.get("difficulty", "medium"), 2))
        
        return all_questions[:8]  # Limit to 8 questions total
    
    def _infer_thinking_skill(self, question: str) -> HistoricalThinkingSkill:
        """Infer the primary thinking skill developed by a question."""
        
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["who", "author", "wrote", "created", "audience", "purpose"]):
            return HistoricalThinkingSkill.ANALYZING_SOURCES
        elif any(word in question_lower for word in ["when", "chronology", "sequence", "before", "after"]):
            return HistoricalThinkingSkill.CHRONOLOGICAL_REASONING
        elif any(word in question_lower for word in ["context", "time period", "historical", "circumstances"]):
            return HistoricalThinkingSkill.CONTEXTUALIZATION
        elif any(word in question_lower for word in ["argument", "claim", "evidence", "support", "prove"]):
            return HistoricalThinkingSkill.CRAFTING_ARGUMENTS
        else:
            return HistoricalThinkingSkill.SYNTHESIS
    
    def _parse_questions_from_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse questions from LLM response."""
        
        questions = []
        lines = response_text.split('\n')
        
        question_pattern = r'^\d+\.\s*(.+?)(?:\s*\(([^)]+)\)\s*-\s*([^)]+))?$'
        
        for line in lines:
            line = line.strip()
            if not line or not re.match(r'^\d+\.', line):
                continue
            
            match = re.match(question_pattern, line)
            if match:
                question_text = match.group(1).strip()
                difficulty = match.group(2).strip() if match.group(2) else "medium"
                skill = match.group(3).strip() if match.group(3) else "analyzing_sources"
                
                # Map skill text to enum
                skill_mapping = {
                    "analyzing_sources": HistoricalThinkingSkill.ANALYZING_SOURCES,
                    "contextualization": HistoricalThinkingSkill.CONTEXTUALIZATION,
                    "chronological_reasoning": HistoricalThinkingSkill.CHRONOLOGICAL_REASONING,
                    "crafting_arguments": HistoricalThinkingSkill.CRAFTING_ARGUMENTS,
                    "synthesis": HistoricalThinkingSkill.SYNTHESIS
                }
                
                questions.append({
                    "id": f"custom_{len(questions)+1}",
                    "question": question_text,
                    "type": "custom",
                    "difficulty": difficulty.lower(),
                    "thinking_skill": skill_mapping.get(skill.lower(), HistoricalThinkingSkill.ANALYZING_SOURCES)
                })
        
        return questions
    
    def _parse_llm_analysis(self, response_text: str) -> Dict[str, Any]:
        """Parse structured analysis from LLM response."""
        
        # This would implement proper JSON parsing from LLM response
        # For now, return a basic structure
        return {
            "soaps": {
                "speaker": "Identified from response",
                "occasion": "Historical context extracted",
                "audience": "Target audience determined",
                "purpose": "Purpose analyzed",
                "subject": "Main topic identified"
            },
            "historical_context": {
                "significance": "Context significance",
                "events": "Related events",
                "climate": "Social/political climate"
            },
            "reliability": {
                "strengths": ["Source strengths"],
                "limitations": ["Source limitations"],
                "corroboration": "Corroboration needs"
            }
        }
    
    async def create_source_comparison_activity(
        self,
        sources: List[PrimarySource],
        comparison_theme: str,
        student_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """Create a comparative analysis activity using multiple sources."""
        
        activity = {
            "title": f"Comparative Analysis: {comparison_theme}",
            "sources": [source.id for source in sources],
            "comparison_framework": {},
            "analysis_questions": [],
            "synthesis_task": {}
        }
        
        # Create comparison framework
        activity["comparison_framework"] = {
            "categories": [
                "Perspective/Point of View",
                "Evidence Presented",
                "Bias/Limitations",
                "Historical Context",
                "Reliability"
            ],
            "comparison_matrix": self._create_comparison_matrix(sources)
        }
        
        # Generate comparative analysis questions
        comparative_questions = await self._generate_comparative_questions(
            sources, comparison_theme, student_level
        )
        activity["analysis_questions"] = comparative_questions
        
        # Create synthesis task
        activity["synthesis_task"] = {
            "prompt": f"Based on your analysis of these sources, write a {300 if student_level == 'beginner' else 500}-word essay addressing: {comparison_theme}",
            "requirements": [
                "Use evidence from at least 3 sources",
                "Acknowledge different perspectives",
                "Evaluate the reliability of your sources",
                "Develop a clear thesis statement"
            ],
            "rubric_categories": [
                "Use of Evidence",
                "Analysis of Sources", 
                "Historical Context",
                "Argument Development"
            ]
        }
        
        return activity
```

This comprehensive implementation provides the foundation for History-specific educational features including interactive timelines, sophisticated primary source analysis, and educational scaffolding systems. The remaining features (DBQ essays, thinking skills assessment, etc.) would follow similar patterns with detailed implementations focused on educational pedagogy and student learning outcomes.