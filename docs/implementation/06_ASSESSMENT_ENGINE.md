# Assessment Engine Implementation

**Document:** 06_ASSESSMENT_ENGINE.md  
**Version:** 1.0  
**Date:** February 17, 2026  
**Dependencies:** LangChain, PostgreSQL, Redis, NLP libraries, Statistics  

---

## Overview

This document details the implementation of a comprehensive assessment engine that provides formative and summative assessments, automated essay grading, question generation, spaced repetition scheduling, and detailed analytics for History education.

## Architecture Design

### Assessment Engine System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     ASSESSMENT ENGINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ FORMATIVE ASSESSMENT        SUMMATIVE ASSESSMENT               │
│                                                                 │
│ ┌─────────────────────┐    ┌─────────────────────┐              │
│ │ CONTINUOUS CHECKS   │    │ UNIT ASSESSMENTS    │              │
│ │ • Understanding     │    │ • Comprehensive     │              │
│ │ • Misconception     │    │ • Multi-format      │              │
│ │ • Progress Tracking │    │ • Standards-aligned │              │
│ │ • Real-time Feedback│    │ • Detailed Rubrics  │              │
│ └─────────────────────┘    └─────────────────────┘              │
│           │                          │                         │
│           └──────────┬───────────────┘                         │
│                      ▼                                         │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │              QUESTION GENERATION ENGINE                     │ │
│ │                                                             │ │
│ │ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │ │
│ │ │ MULTIPLE CHOICE │  │  SHORT ANSWER   │  │    ESSAY    │ │ │
│ │ │ • Distractor    │  │ • Key Points    │  │ • Prompts   │ │ │
│ │ │ • Plausible     │  │ • Rubric Items  │  │ • Rubrics   │ │ │
│ │ │ • Difficulty    │  │ • Sample Answers│  │ • Examples  │ │ │
│ │ └─────────────────┘  └─────────────────┘  └─────────────┘ │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                      ▼                                         │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │                GRADING ENGINE                               │ │
│ │                                                             │ │
│ │ ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │ │
│ │ │ AUTOMATIC   │  │  RUBRIC     │  │   ESSAY ANALYSIS    │ │ │
│ │ │ • Objective │  │ • Criteria  │  │ • Content Analysis  │ │ │
│ │ │ • Pattern   │  │ • Scoring   │  │ • Argument Eval     │ │ │
│ │ │ • Immediate │  │ • Holistic  │  │ • Source Usage     │ │ │
│ │ └─────────────┘  └─────────────┘  └─────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                      ▼                                         │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │              FEEDBACK GENERATION                            │ │
│ │                                                             │ │
│ │ • Personalized Comments    • Improvement Suggestions       │ │
│ │ • Strength Recognition     • Next Steps Guidance           │ │
│ │ • Error Pattern Analysis   • Resource Recommendations      │ │
│ │ • Growth Tracking         • Goal Setting                  │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                      ▼                                         │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │                ANALYTICS ENGINE                             │ │
│ │                                                             │ │
│ │ ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │ │
│ │ │ INDIVIDUAL  │  │   CLASS     │  │   PREDICTIVE        │ │ │
│ │ │ • Progress  │  │ • Trends    │  │ • Success Risk      │ │ │
│ │ │ • Patterns  │  │ • Gaps      │  │ • Intervention      │ │ │
│ │ │ • Growth    │  │ • Standards │  │ • Recommendations   │ │ │
│ │ └─────────────┘  └─────────────┘  └─────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Structure

### Directory Structure
```
src/assessment/
├── __init__.py
├── engine.py                # Main assessment orchestrator
├── formative/
│   ├── __init__.py
│   ├── continuous_checker.py    # Real-time understanding checks
│   ├── misconception_detector.py # Identify student misconceptions
│   ├── progress_tracker.py      # Track learning progress
│   └── intervention_suggester.py # Suggest interventions
├── summative/
│   ├── __init__.py
│   ├── unit_assessments.py      # Comprehensive unit tests
│   ├── standards_alignment.py   # Align with educational standards
│   └── comprehensive_evaluator.py # Multi-format evaluation
├── generation/
│   ├── __init__.py
│   ├── question_generator.py    # Generate various question types
│   ├── multiple_choice.py       # MC question generation
│   ├── short_answer.py         # Short answer generation
│   ├── essay_prompts.py        # Essay prompt creation
│   └── difficulty_calibrator.py # Calibrate question difficulty
├── grading/
│   ├── __init__.py
│   ├── automatic_grader.py     # Automated objective grading
│   ├── essay_grader.py         # Essay analysis and scoring
│   ├── rubric_engine.py        # Rubric-based assessment
│   └── feedback_generator.py   # Generate personalized feedback
├── analytics/
│   ├── __init__.py
│   ├── individual_analytics.py # Individual student analysis
│   ├── class_analytics.py      # Class-level insights
│   ├── predictive_analytics.py # Predictive modeling
│   └── reporting_engine.py     # Generate reports
├── spaced_repetition/
│   ├── __init__.py
│   ├── scheduler.py            # Schedule review sessions
│   ├── forgetting_curve.py     # Model forgetting patterns
│   └── retention_optimizer.py  # Optimize retention
└── schemas.py                  # Assessment data models
```

---

## Core Implementation

### 1. `src/assessment/schemas.py` - Assessment Data Models
```python
"""Assessment system data models and schemas."""
from datetime import datetime, date
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple
from pydantic import BaseModel, Field
import uuid


class AssessmentType(str, Enum):
    """Types of assessments."""
    FORMATIVE = "formative"           # Ongoing assessment during learning
    SUMMATIVE = "summative"           # Assessment of learning (end of unit)
    DIAGNOSTIC = "diagnostic"         # Assess prior knowledge/gaps
    BENCHMARK = "benchmark"           # Periodic progress checkpoints


class QuestionType(str, Enum):
    """Types of assessment questions."""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    MATCHING = "matching"
    FILL_IN_BLANK = "fill_in_blank"
    DBQ = "dbq"                      # Document-Based Question
    TIMELINE_CONSTRUCTION = "timeline_construction"
    PRIMARY_SOURCE_ANALYSIS = "primary_source_analysis"


class DifficultyLevel(str, Enum):
    """Question difficulty levels."""
    VERY_EASY = "very_easy"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"


class HistoricalThinkingSkill(str, Enum):
    """Historical thinking skills being assessed."""
    CHRONOLOGICAL_REASONING = "chronological_reasoning"
    CRAFTING_ARGUMENTS = "crafting_arguments"
    ANALYZING_SOURCES = "analyzing_sources"
    CONTEXTUALIZATION = "contextualization"
    SYNTHESIS = "synthesis"


class BloomsTaxonomyLevel(str, Enum):
    """Bloom's taxonomy cognitive levels."""
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class AssessmentQuestion(BaseModel):
    """Individual assessment question."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: QuestionType
    prompt: str = Field(description="Question text")
    
    # Question options (for MC, matching, etc.)
    options: Optional[List[Dict[str, Any]]] = None
    correct_answer: Optional[Union[str, List[str]]] = None
    
    # Metadata
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    blooms_level: BloomsTaxonomyLevel = BloomsTaxonomyLevel.UNDERSTAND
    historical_thinking_skill: Optional[HistoricalThinkingSkill] = None
    
    # Content alignment
    topic: str = Field(description="Historical topic being assessed")
    subtopic: Optional[str] = None
    time_period: Optional[str] = None
    
    # Scoring
    points: int = 1
    rubric: Optional[Dict[str, Any]] = None
    
    # Educational metadata
    learning_objective: Optional[str] = None
    prerequisite_knowledge: List[str] = Field(default_factory=list)
    common_misconceptions: List[str] = Field(default_factory=list)
    
    # Usage tracking
    times_used: int = 0
    average_score: float = 0.0
    difficulty_rating: float = 0.5  # 0.0-1.0 based on student performance
    
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)


class Assessment(BaseModel):
    """Complete assessment containing multiple questions."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    type: AssessmentType
    
    # Questions
    questions: List[str] = Field(description="Question IDs in order")
    question_weights: Dict[str, float] = Field(default_factory=dict)
    
    # Configuration
    time_limit_minutes: Optional[int] = None
    attempts_allowed: int = 1
    shuffle_questions: bool = False
    shuffle_options: bool = False
    
    # Grading
    passing_score: float = 70.0
    max_points: float = 0.0
    auto_grade: bool = True
    
    # Alignment
    learning_objectives: List[str] = Field(default_factory=list)
    historical_thinking_skills: List[HistoricalThinkingSkill] = Field(default_factory=list)
    topics_covered: List[str] = Field(default_factory=list)
    
    # Availability
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    
    # Metadata
    created_by: Optional[str] = None
    course_id: Optional[str] = None
    unit_id: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class AssessmentSubmission(BaseModel):
    """Student's submission of an assessment."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    assessment_id: str
    student_id: str
    
    # Responses
    responses: Dict[str, Any] = Field(description="question_id -> response")
    
    # Timing
    started_at: datetime
    submitted_at: Optional[datetime] = None
    time_spent_seconds: int = 0
    
    # Grading
    scores: Dict[str, float] = Field(default_factory=dict, description="question_id -> score")
    total_score: Optional[float] = None
    percentage_score: Optional[float] = None
    grade: Optional[str] = None
    
    # Status
    is_completed: bool = False
    is_graded: bool = False
    attempt_number: int = 1
    
    # Feedback
    feedback: Optional[str] = None
    detailed_feedback: Dict[str, str] = Field(default_factory=dict)
    improvement_suggestions: List[str] = Field(default_factory=list)
    
    # Analytics
    question_confidence: Dict[str, float] = Field(default_factory=dict)
    time_per_question: Dict[str, int] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=datetime.now)


class RubricCriterion(BaseModel):
    """Individual criterion in a rubric."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    weight: float = Field(ge=0.0, le=1.0, default=1.0)
    
    # Performance levels
    performance_levels: Dict[str, Dict[str, Any]] = Field(
        description="level_name -> {description, points}"
    )
    
    # Historical thinking alignment
    historical_skill: Optional[HistoricalThinkingSkill] = None


class Rubric(BaseModel):
    """Assessment rubric for essay/performance tasks."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    
    # Criteria
    criteria: List[RubricCriterion] = Field(default_factory=list)
    
    # Scoring
    total_points: float = 0.0
    performance_levels: List[str] = Field(
        default=["Exemplary", "Proficient", "Developing", "Beginning"]
    )
    
    # Usage context
    applicable_question_types: List[QuestionType] = Field(default_factory=list)
    grade_levels: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.now)


class FormativeCheck(BaseModel):
    """Formative assessment check during learning."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    session_id: str
    
    # Context
    topic: str
    learning_context: str = Field(description="What student was learning about")
    trigger: str = Field(description="What triggered this check")
    
    # Check details
    check_type: str  # "understanding", "misconception", "confusion", "mastery"
    question_asked: Optional[str] = None
    student_response: Optional[str] = None
    
    # Assessment
    understanding_level: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    misconceptions_identified: List[str] = Field(default_factory=list)
    
    # Response
    feedback_given: Optional[str] = None
    intervention_suggested: Optional[str] = None
    next_action: Optional[str] = None
    
    timestamp: datetime = Field(default_factory=datetime.now)


class LearningAnalytics(BaseModel):
    """Analytics data for a student's learning progress."""
    student_id: str
    time_period: Tuple[datetime, datetime]
    
    # Performance metrics
    assessments_taken: int = 0
    average_score: float = 0.0
    score_trend: List[float] = Field(default_factory=list)
    
    # Skill development
    historical_thinking_skills: Dict[HistoricalThinkingSkill, float] = Field(default_factory=dict)
    skill_growth_rates: Dict[HistoricalThinkingSkill, float] = Field(default_factory=dict)
    
    # Knowledge mastery
    topic_mastery: Dict[str, float] = Field(default_factory=dict)
    knowledge_gaps: List[str] = Field(default_factory=list)
    strong_areas: List[str] = Field(default_factory=list)
    
    # Learning patterns
    preferred_question_types: List[QuestionType] = Field(default_factory=list)
    difficulty_comfort_zone: DifficultyLevel = DifficultyLevel.MEDIUM
    time_management: Dict[str, float] = Field(default_factory=dict)
    
    # Engagement
    participation_rate: float = Field(ge=0.0, le=1.0, default=1.0)
    help_seeking_frequency: float = 0.0
    persistence_score: float = Field(ge=0.0, le=1.0, default=0.5)
    
    # Predictions
    next_assessment_prediction: Optional[float] = None
    risk_factors: List[str] = Field(default_factory=list)
    recommended_interventions: List[str] = Field(default_factory=list)
    
    generated_at: datetime = Field(default_factory=datetime.now)


class SpacedRepetitionCard(BaseModel):
    """Spaced repetition card for knowledge retention."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    
    # Content
    topic: str
    subtopic: Optional[str] = None
    question_id: Optional[str] = None
    concept: str = Field(description="The concept being reinforced")
    
    # Spaced repetition algorithm parameters
    ease_factor: float = Field(ge=1.3, default=2.5)
    interval: int = Field(ge=1, default=1, description="Days until next review")
    repetition: int = Field(ge=0, default=0)
    
    # Performance tracking
    correct_streak: int = 0
    total_reviews: int = 0
    success_rate: float = Field(ge=0.0, le=1.0, default=0.0)
    
    # Scheduling
    next_review_date: datetime
    last_reviewed: Optional[datetime] = None
    
    # Metadata
    difficulty_rating: float = Field(ge=0.0, le=1.0, default=0.5)
    importance_weight: float = Field(ge=0.0, le=1.0, default=1.0)
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class AssessmentInsight(BaseModel):
    """Generated insight about assessment performance."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: Optional[str] = None  # None for class-level insights
    
    # Insight details
    type: str  # "strength", "weakness", "improvement", "concern", "achievement"
    category: str  # "knowledge", "skill", "engagement", "progress"
    title: str
    description: str
    
    # Evidence
    supporting_data: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Recommendations
    recommended_actions: List[str] = Field(default_factory=list)
    resources: List[str] = Field(default_factory=list)
    
    # Context
    topics_involved: List[str] = Field(default_factory=list)
    time_period: Optional[Tuple[datetime, datetime]] = None
    
    # Priority
    urgency: str = Field(default="medium")  # "low", "medium", "high", "critical"
    impact_potential: str = Field(default="medium")
    
    created_at: datetime = Field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = None
```

### 2. `src/assessment/generation/question_generator.py` - Intelligent Question Generation
```python
"""Intelligent question generation system for History assessments."""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
import random
from datetime import datetime

from langchain_core.messages import SystemMessage, HumanMessage

from src.assessment.schemas import (
    AssessmentQuestion, QuestionType, DifficultyLevel, BloomsTaxonomyLevel,
    HistoricalThinkingSkill
)
from src.assessment.generation.multiple_choice import MultipleChoiceGenerator
from src.assessment.generation.essay_prompts import EssayPromptGenerator
from src.history.schemas import HistoricalEvent, PrimarySource
from src.llm.factory import LLMFactory
from src.rag.retriever import KnowledgeRetriever

logger = logging.getLogger(__name__)


class QuestionGenerator:
    """Generates diverse assessment questions for History topics."""
    
    def __init__(
        self,
        knowledge_retriever: KnowledgeRetriever,
        mc_generator: MultipleChoiceGenerator = None,
        essay_generator: EssayPromptGenerator = None
    ):
        self.retriever = knowledge_retriever
        self.mc_generator = mc_generator or MultipleChoiceGenerator()
        self.essay_generator = essay_generator or EssayPromptGenerator()
        self.llm = LLMFactory.create(provider="openai", model="gpt-4")
        
        # Question templates for different History topics
        self.question_templates = self._initialize_question_templates()
        
        # Difficulty scaling parameters
        self.difficulty_parameters = self._initialize_difficulty_parameters()
        
        # Historical thinking skills mapping
        self.skills_question_types = self._initialize_skills_mapping()
    
    def _initialize_question_templates(self) -> Dict[QuestionType, List[str]]:
        """Initialize question templates for different types."""
        return {
            QuestionType.SHORT_ANSWER: [
                "Explain the causes of {event} and their relative importance.",
                "Describe the impact of {event} on {group/region}.",
                "Compare the perspectives of {group1} and {group2} regarding {issue}.",
                "Analyze the role of {factor} in {historical_process}.",
                "What were the immediate and long-term consequences of {event}?",
                "How did {event} change {aspect} in {time_period}?",
                "Identify three key factors that led to {outcome}.",
                "Explain why {person/group} made {decision} in {context}."
            ],
            QuestionType.ESSAY: [
                "To what extent did {factor} contribute to {outcome}? Use specific evidence to support your argument.",
                "Analyze the changing nature of {concept} from {time1} to {time2}.",
                "Evaluate the effectiveness of {policy/strategy} in achieving {goal}.",
                "\"Quote about historical topic.\" Assess the validity of this statement.",
                "Compare and contrast the approaches of {entity1} and {entity2} to {issue}.",
                "Analyze the causes and consequences of {event}, considering multiple perspectives."
            ],
            QuestionType.PRIMARY_SOURCE_ANALYSIS: [
                "Based on Source {letter}, what can you infer about {aspect} during {time_period}?",
                "How does the author's perspective in Source {letter} reflect {broader_context}?",
                "What evidence in Source {letter} supports the argument that {claim}?",
                "Compare the viewpoints presented in Sources {letter1} and {letter2}.",
                "What limitations should historians consider when using Source {letter}?"
            ],
            QuestionType.TIMELINE_CONSTRUCTION: [
                "Create a timeline showing the key events leading to {outcome}.",
                "Arrange these events in chronological order and explain their connections: {events}",
                "Develop a timeline showing how {process} evolved from {start} to {end}.",
                "Sequence these developments in {topic} and explain the causal relationships."
            ]
        }
    
    def _initialize_difficulty_parameters(self) -> Dict[DifficultyLevel, Dict[str, Any]]:
        """Initialize parameters for different difficulty levels."""
        return {
            DifficultyLevel.VERY_EASY: {
                "blooms_levels": [BloomsTaxonomyLevel.REMEMBER],
                "context_complexity": "simple",
                "vocabulary_level": "basic",
                "multiple_factors": 1,
                "time_periods": 1
            },
            DifficultyLevel.EASY: {
                "blooms_levels": [BloomsTaxonomyLevel.REMEMBER, BloomsTaxonomyLevel.UNDERSTAND],
                "context_complexity": "straightforward",
                "vocabulary_level": "accessible",
                "multiple_factors": 2,
                "time_periods": 1
            },
            DifficultyLevel.MEDIUM: {
                "blooms_levels": [BloomsTaxonomyLevel.UNDERSTAND, BloomsTaxonomyLevel.APPLY],
                "context_complexity": "moderate",
                "vocabulary_level": "standard",
                "multiple_factors": 3,
                "time_periods": 2
            },
            DifficultyLevel.HARD: {
                "blooms_levels": [BloomsTaxonomyLevel.ANALYZE, BloomsTaxonomyLevel.EVALUATE],
                "context_complexity": "complex",
                "vocabulary_level": "advanced",
                "multiple_factors": 4,
                "time_periods": 3
            },
            DifficultyLevel.VERY_HARD: {
                "blooms_levels": [BloomsTaxonomyLevel.EVALUATE, BloomsTaxonomyLevel.CREATE],
                "context_complexity": "highly complex",
                "vocabulary_level": "sophisticated",
                "multiple_factors": 5,
                "time_periods": 4
            }
        }
    
    def _initialize_skills_mapping(self) -> Dict[HistoricalThinkingSkill, List[QuestionType]]:
        """Map historical thinking skills to appropriate question types."""
        return {
            HistoricalThinkingSkill.CHRONOLOGICAL_REASONING: [
                QuestionType.TIMELINE_CONSTRUCTION,
                QuestionType.SHORT_ANSWER,
                QuestionType.MULTIPLE_CHOICE
            ],
            HistoricalThinkingSkill.CRAFTING_ARGUMENTS: [
                QuestionType.ESSAY,
                QuestionType.DBQ,
                QuestionType.SHORT_ANSWER
            ],
            HistoricalThinkingSkill.ANALYZING_SOURCES: [
                QuestionType.PRIMARY_SOURCE_ANALYSIS,
                QuestionType.DBQ,
                QuestionType.SHORT_ANSWER
            ],
            HistoricalThinkingSkill.CONTEXTUALIZATION: [
                QuestionType.ESSAY,
                QuestionType.SHORT_ANSWER,
                QuestionType.PRIMARY_SOURCE_ANALYSIS
            ],
            HistoricalThinkingSkill.SYNTHESIS: [
                QuestionType.ESSAY,
                QuestionType.DBQ,
                QuestionType.SHORT_ANSWER
            ]
        }
    
    async def generate_questions_for_topic(
        self,
        topic: str,
        question_count: int = 10,
        question_types: Optional[List[QuestionType]] = None,
        difficulty_distribution: Optional[Dict[DifficultyLevel, float]] = None,
        historical_thinking_skills: Optional[List[HistoricalThinkingSkill]] = None,
        student_level: str = "intermediate"
    ) -> List[AssessmentQuestion]:
        """Generate a set of questions for a specific History topic."""
        
        logger.info(f"Generating {question_count} questions for topic: {topic}")
        
        # Set default parameters
        if question_types is None:
            question_types = [
                QuestionType.MULTIPLE_CHOICE,
                QuestionType.SHORT_ANSWER,
                QuestionType.ESSAY
            ]
        
        if difficulty_distribution is None:
            difficulty_distribution = {
                DifficultyLevel.EASY: 0.2,
                DifficultyLevel.MEDIUM: 0.5,
                DifficultyLevel.HARD: 0.3
            }
        
        # Retrieve relevant content for the topic
        topic_content = await self._retrieve_topic_content(topic)
        
        # Plan question distribution
        question_plan = self._plan_question_distribution(
            question_count, question_types, difficulty_distribution, historical_thinking_skills
        )
        
        # Generate questions according to plan
        generated_questions = []
        
        for plan_item in question_plan:
            try:
                question = await self._generate_single_question(
                    topic=topic,
                    question_type=plan_item["type"],
                    difficulty=plan_item["difficulty"],
                    blooms_level=plan_item["blooms_level"],
                    thinking_skill=plan_item["thinking_skill"],
                    topic_content=topic_content,
                    student_level=student_level
                )
                
                if question:
                    generated_questions.append(question)
                    
            except Exception as e:
                logger.warning(f"Failed to generate question: {e}")
                continue
        
        logger.info(f"Successfully generated {len(generated_questions)} questions")
        return generated_questions
    
    async def _retrieve_topic_content(self, topic: str) -> Dict[str, Any]:
        """Retrieve relevant content for question generation."""
        
        # Use RAG to get comprehensive topic information
        rag_results = await self.retriever.retrieve(
            query=f"comprehensive information about {topic} for History education",
            subject="history",
            limit=20
        )
        
        topic_content = {
            "sources": rag_results.get("sources", []),
            "context": rag_results.get("context", ""),
            "key_events": [],
            "important_figures": [],
            "key_concepts": [],
            "time_periods": [],
            "primary_sources": []
        }
        
        # Extract structured information from RAG results
        for source in topic_content["sources"]:
            content = source.get("document", "")
            metadata = source.get("metadata", {})
            
            # Extract key information (this would be more sophisticated in practice)
            if "event" in content.lower():
                topic_content["key_events"].append(self._extract_events_from_content(content))
            
            if any(title in content.lower() for title in ["president", "king", "leader", "general"]):
                topic_content["important_figures"].extend(self._extract_figures_from_content(content))
        
        return topic_content
    
    def _plan_question_distribution(
        self,
        question_count: int,
        question_types: List[QuestionType],
        difficulty_distribution: Dict[DifficultyLevel, float],
        thinking_skills: Optional[List[HistoricalThinkingSkill]]
    ) -> List[Dict[str, Any]]:
        """Plan the distribution of questions to generate."""
        
        question_plan = []
        
        # Distribute question types
        type_counts = self._distribute_question_types(question_count, question_types)
        
        for question_type, count in type_counts.items():
            # Distribute difficulties for this question type
            type_difficulties = self._distribute_difficulties(count, difficulty_distribution)
            
            for difficulty, diff_count in type_difficulties.items():
                # Get parameters for this difficulty level
                diff_params = self.difficulty_parameters[difficulty]
                
                for i in range(diff_count):
                    # Select Bloom's level for this question
                    blooms_level = random.choice(diff_params["blooms_levels"])
                    
                    # Select thinking skill if specified
                    thinking_skill = None
                    if thinking_skills:
                        # Filter thinking skills by what's appropriate for this question type
                        applicable_skills = [
                            skill for skill in thinking_skills
                            if question_type in self.skills_question_types.get(skill, [])
                        ]
                        if applicable_skills:
                            thinking_skill = random.choice(applicable_skills)
                        else:
                            thinking_skill = random.choice(thinking_skills)
                    
                    question_plan.append({
                        "type": question_type,
                        "difficulty": difficulty,
                        "blooms_level": blooms_level,
                        "thinking_skill": thinking_skill,
                        "parameters": diff_params
                    })
        
        # Shuffle to distribute evenly
        random.shuffle(question_plan)
        
        return question_plan
    
    def _distribute_question_types(
        self, 
        total_count: int, 
        question_types: List[QuestionType]
    ) -> Dict[QuestionType, int]:
        """Distribute total questions across different types."""
        
        # Default weights for different question types
        type_weights = {
            QuestionType.MULTIPLE_CHOICE: 3,
            QuestionType.TRUE_FALSE: 2,
            QuestionType.SHORT_ANSWER: 4,
            QuestionType.ESSAY: 2,
            QuestionType.PRIMARY_SOURCE_ANALYSIS: 3,
            QuestionType.TIMELINE_CONSTRUCTION: 2,
            QuestionType.DBQ: 1,
            QuestionType.MATCHING: 2,
            QuestionType.FILL_IN_BLANK: 2
        }
        
        # Calculate weights for available types
        available_weights = {qt: type_weights.get(qt, 1) for qt in question_types}
        total_weight = sum(available_weights.values())
        
        # Distribute counts proportionally
        type_counts = {}
        remaining_count = total_count
        
        for i, (question_type, weight) in enumerate(available_weights.items()):
            if i == len(available_weights) - 1:  # Last type gets remainder
                type_counts[question_type] = remaining_count
            else:
                count = int(total_count * weight / total_weight)
                type_counts[question_type] = count
                remaining_count -= count
        
        # Ensure at least 1 of each type if total_count >= len(question_types)
        if total_count >= len(question_types):
            for question_type in question_types:
                if type_counts[question_type] == 0:
                    type_counts[question_type] = 1
                    # Reduce from largest group
                    largest_type = max(type_counts.items(), key=lambda x: x[1])[0]
                    type_counts[largest_type] -= 1
        
        return type_counts
    
    def _distribute_difficulties(
        self,
        count: int,
        difficulty_distribution: Dict[DifficultyLevel, float]
    ) -> Dict[DifficultyLevel, int]:
        """Distribute questions across difficulty levels."""
        
        difficulty_counts = {}
        remaining_count = count
        
        # Sort by difficulty level for consistent distribution
        sorted_difficulties = sorted(difficulty_distribution.items(), key=lambda x: x[1], reverse=True)
        
        for i, (difficulty, proportion) in enumerate(sorted_difficulties):
            if i == len(sorted_difficulties) - 1:  # Last difficulty gets remainder
                difficulty_counts[difficulty] = remaining_count
            else:
                diff_count = int(count * proportion)
                difficulty_counts[difficulty] = diff_count
                remaining_count -= diff_count
        
        return difficulty_counts
    
    async def _generate_single_question(
        self,
        topic: str,
        question_type: QuestionType,
        difficulty: DifficultyLevel,
        blooms_level: BloomsTaxonomyLevel,
        thinking_skill: Optional[HistoricalThinkingSkill],
        topic_content: Dict[str, Any],
        student_level: str
    ) -> Optional[AssessmentQuestion]:
        """Generate a single question based on specifications."""
        
        try:
            if question_type == QuestionType.MULTIPLE_CHOICE:
                return await self.mc_generator.generate_question(
                    topic, difficulty, blooms_level, thinking_skill, topic_content
                )
            
            elif question_type == QuestionType.ESSAY:
                return await self.essay_generator.generate_prompt(
                    topic, difficulty, blooms_level, thinking_skill, topic_content
                )
            
            elif question_type == QuestionType.SHORT_ANSWER:
                return await self._generate_short_answer_question(
                    topic, difficulty, blooms_level, thinking_skill, topic_content
                )
            
            elif question_type == QuestionType.PRIMARY_SOURCE_ANALYSIS:
                return await self._generate_source_analysis_question(
                    topic, difficulty, blooms_level, thinking_skill, topic_content
                )
            
            elif question_type == QuestionType.TIMELINE_CONSTRUCTION:
                return await self._generate_timeline_question(
                    topic, difficulty, blooms_level, thinking_skill, topic_content
                )
            
            else:
                logger.warning(f"Question type {question_type} not implemented")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate {question_type} question for {topic}: {e}")
            return None
    
    async def _generate_short_answer_question(
        self,
        topic: str,
        difficulty: DifficultyLevel,
        blooms_level: BloomsTaxonomyLevel,
        thinking_skill: Optional[HistoricalThinkingSkill],
        topic_content: Dict[str, Any]
    ) -> AssessmentQuestion:
        """Generate a short answer question."""
        
        # Get appropriate templates
        templates = self.question_templates[QuestionType.SHORT_ANSWER]
        template = random.choice(templates)
        
        # Get difficulty parameters
        diff_params = self.difficulty_parameters[difficulty]
        
        # Generate question using LLM
        generation_prompt = f"""
        Generate a {difficulty.value} difficulty short answer question about {topic} for History students.

        Requirements:
        - Bloom's taxonomy level: {blooms_level.value}
        - Historical thinking skill focus: {thinking_skill.value if thinking_skill else "general"}
        - Context complexity: {diff_params['context_complexity']}
        - Vocabulary level: {diff_params['vocabulary_level']}
        - Should involve {diff_params['multiple_factors']} main factors/aspects

        Available content context:
        {topic_content['context'][:500]}...

        Template pattern: {template}

        Generate:
        1. Question prompt (2-3 sentences)
        2. Key points expected in a good answer (3-5 bullet points)
        3. Sample acceptable answer (2-3 sentences)
        4. Common misconceptions students might have

        Format as JSON with keys: prompt, key_points, sample_answer, misconceptions
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert History teacher creating assessment questions."),
                HumanMessage(content=generation_prompt)
            ])
            
            # Parse response (implement proper JSON parsing)
            question_data = self._parse_question_response(response.content)
            
            # Create assessment question object
            question = AssessmentQuestion(
                type=QuestionType.SHORT_ANSWER,
                prompt=question_data.get("prompt", ""),
                difficulty=difficulty,
                blooms_level=blooms_level,
                historical_thinking_skill=thinking_skill,
                topic=topic,
                points=self._calculate_points_for_difficulty(difficulty),
                rubric=self._create_short_answer_rubric(question_data.get("key_points", [])),
                common_misconceptions=question_data.get("misconceptions", [])
            )
            
            return question
            
        except Exception as e:
            logger.error(f"Failed to generate short answer question: {e}")
            raise
    
    def _calculate_points_for_difficulty(self, difficulty: DifficultyLevel) -> int:
        """Calculate points based on difficulty level."""
        point_mapping = {
            DifficultyLevel.VERY_EASY: 1,
            DifficultyLevel.EASY: 2,
            DifficultyLevel.MEDIUM: 3,
            DifficultyLevel.HARD: 4,
            DifficultyLevel.VERY_HARD: 5
        }
        return point_mapping.get(difficulty, 3)
    
    def _create_short_answer_rubric(self, key_points: List[str]) -> Dict[str, Any]:
        """Create a rubric for short answer questions."""
        
        return {
            "type": "points_based",
            "total_points": len(key_points),
            "criteria": [
                {
                    "description": f"Addresses key point: {point}",
                    "points": 1
                }
                for point in key_points
            ],
            "bonus_criteria": [
                {
                    "description": "Provides specific historical examples",
                    "points": 1
                },
                {
                    "description": "Demonstrates clear understanding of historical context",
                    "points": 1
                }
            ]
        }
    
    def _parse_question_response(self, response_text: str) -> Dict[str, Any]:
        """Parse question data from LLM response."""
        
        # This would implement proper JSON parsing from LLM response
        # For now, return a basic structure
        return {
            "prompt": "Generated question prompt",
            "key_points": ["Key point 1", "Key point 2", "Key point 3"],
            "sample_answer": "Sample answer text",
            "misconceptions": ["Common misconception 1", "Common misconception 2"]
        }
    
    def _extract_events_from_content(self, content: str) -> List[str]:
        """Extract historical events from content."""
        # Simple implementation - would be more sophisticated in practice
        events = []
        
        # Look for event patterns
        import re
        event_patterns = [
            r'(\w+\s+War)',
            r'(\w+\s+Revolution)',
            r'(Battle\s+of\s+\w+)',
            r'(Treaty\s+of\s+\w+)',
            r'(\w+\s+Crisis)'
        ]
        
        for pattern in event_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            events.extend(matches)
        
        return list(set(events))[:5]  # Return up to 5 unique events
    
    def _extract_figures_from_content(self, content: str) -> List[str]:
        """Extract historical figures from content."""
        # Simple implementation - would use NER in practice
        figures = []
        
        # Look for common title patterns
        import re
        figure_patterns = [
            r'(President\s+\w+)',
            r'(King\s+\w+)',
            r'(Queen\s+\w+)',
            r'(General\s+\w+)',
            r'(Emperor\s+\w+)'
        ]
        
        for pattern in figure_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            figures.extend(matches)
        
        return list(set(figures))[:5]  # Return up to 5 unique figures
    
    async def generate_adaptive_follow_up_question(
        self,
        original_question: AssessmentQuestion,
        student_response: str,
        student_performance: float,
        student_id: str
    ) -> Optional[AssessmentQuestion]:
        """Generate an adaptive follow-up question based on student performance."""
        
        if student_performance >= 0.8:
            # Student did well - increase difficulty or explore deeper
            new_difficulty = self._increase_difficulty(original_question.difficulty)
            new_blooms = self._increase_blooms_level(original_question.blooms_level)
        elif student_performance <= 0.4:
            # Student struggled - provide scaffolding or decrease difficulty
            new_difficulty = self._decrease_difficulty(original_question.difficulty)
            new_blooms = self._decrease_blooms_level(original_question.blooms_level)
        else:
            # Similar level but different angle
            new_difficulty = original_question.difficulty
            new_blooms = original_question.blooms_level
        
        # Generate follow-up question
        follow_up_prompt = f"""
        Generate a follow-up question based on this student interaction:

        Original Question: {original_question.prompt}
        Student Response: {student_response}
        Student Performance: {student_performance:.2f}

        New question should:
        - Be at {new_difficulty.value} difficulty level
        - Target {new_blooms.value} cognitive level
        - Address the same topic: {original_question.topic}
        - {"Build on their success" if student_performance >= 0.8 else "Provide appropriate scaffolding"}

        Generate a question that helps the student {"advance their understanding" if student_performance >= 0.8 else "strengthen their foundational knowledge"}.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an adaptive History tutor creating personalized follow-up questions."),
                HumanMessage(content=follow_up_prompt)
            ])
            
            # Create follow-up question
            follow_up_question = AssessmentQuestion(
                type=original_question.type,
                prompt=response.content.strip(),
                difficulty=new_difficulty,
                blooms_level=new_blooms,
                historical_thinking_skill=original_question.historical_thinking_skill,
                topic=original_question.topic,
                points=self._calculate_points_for_difficulty(new_difficulty)
            )
            
            return follow_up_question
            
        except Exception as e:
            logger.error(f"Failed to generate adaptive follow-up question: {e}")
            return None
    
    def _increase_difficulty(self, current: DifficultyLevel) -> DifficultyLevel:
        """Increase difficulty level by one step."""
        levels = list(DifficultyLevel)
        current_index = levels.index(current)
        return levels[min(current_index + 1, len(levels) - 1)]
    
    def _decrease_difficulty(self, current: DifficultyLevel) -> DifficultyLevel:
        """Decrease difficulty level by one step."""
        levels = list(DifficultyLevel)
        current_index = levels.index(current)
        return levels[max(current_index - 1, 0)]
    
    def _increase_blooms_level(self, current: BloomsTaxonomyLevel) -> BloomsTaxonomyLevel:
        """Increase Bloom's taxonomy level."""
        levels = list(BloomsTaxonomyLevel)
        current_index = levels.index(current)
        return levels[min(current_index + 1, len(levels) - 1)]
    
    def _decrease_blooms_level(self, current: BloomsTaxonomyLevel) -> BloomsTaxonomyLevel:
        """Decrease Bloom's taxonomy level."""
        levels = list(BloomsTaxonomyLevel)
        current_index = levels.index(current)
        return levels[max(current_index - 1, 0)]
```

### 3. `src/assessment/grading/essay_grader.py` - Automated Essay Grading
```python
"""Automated essay grading system for History assessments."""
import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from langchain_core.messages import SystemMessage, HumanMessage

from src.assessment.schemas import (
    AssessmentQuestion, AssessmentSubmission, Rubric, RubricCriterion
)
from src.llm.factory import LLMFactory

logger = logging.getLogger(__name__)


class HistoryEssayGrader:
    """Automated grading system for History essays with detailed feedback."""
    
    def __init__(self):
        self.llm = LLMFactory.create(provider="openai", model="gpt-4")
        
        # Standard History essay rubric
        self.standard_rubric = self._create_standard_history_rubric()
        
        # Essay analysis components
        self.analysis_components = [
            "thesis_quality",
            "evidence_usage",
            "historical_analysis",
            "organization_clarity",
            "source_integration",
            "argument_development"
        ]
    
    def _create_standard_history_rubric(self) -> Rubric:
        """Create standard rubric for History essays."""
        
        criteria = [
            RubricCriterion(
                name="Thesis and Argument",
                description="Clear thesis statement and coherent argument development",
                weight=0.25,
                performance_levels={
                    "Exemplary": {
                        "description": "Clear, sophisticated thesis with nuanced, well-developed argument",
                        "points": 4
                    },
                    "Proficient": {
                        "description": "Clear thesis with coherent argument development",
                        "points": 3
                    },
                    "Developing": {
                        "description": "Thesis present but argument development inconsistent",
                        "points": 2
                    },
                    "Beginning": {
                        "description": "Weak or unclear thesis with minimal argument development",
                        "points": 1
                    }
                }
            ),
            RubricCriterion(
                name="Use of Evidence",
                description="Integration and analysis of historical evidence",
                weight=0.25,
                performance_levels={
                    "Exemplary": {
                        "description": "Extensive, accurate evidence effectively integrated and analyzed",
                        "points": 4
                    },
                    "Proficient": {
                        "description": "Sufficient accurate evidence well-integrated into argument",
                        "points": 3
                    },
                    "Developing": {
                        "description": "Some evidence present but integration inconsistent",
                        "points": 2
                    },
                    "Beginning": {
                        "description": "Limited or inaccurate evidence with poor integration",
                        "points": 1
                    }
                }
            ),
            RubricCriterion(
                name="Historical Analysis",
                description="Demonstration of historical thinking and analysis skills",
                weight=0.25,
                performance_levels={
                    "Exemplary": {
                        "description": "Sophisticated historical analysis with complex reasoning",
                        "points": 4
                    },
                    "Proficient": {
                        "description": "Clear historical analysis with solid reasoning",
                        "points": 3
                    },
                    "Developing": {
                        "description": "Some analysis present but reasoning inconsistent",
                        "points": 2
                    },
                    "Beginning": {
                        "description": "Limited analysis with minimal historical reasoning",
                        "points": 1
                    }
                }
            ),
            RubricCriterion(
                name="Organization and Clarity",
                description="Clear organization and effective communication",
                weight=0.25,
                performance_levels={
                    "Exemplary": {
                        "description": "Excellent organization with clear, engaging writing",
                        "points": 4
                    },
                    "Proficient": {
                        "description": "Good organization with clear communication",
                        "points": 3
                    },
                    "Developing": {
                        "description": "Basic organization with adequate clarity",
                        "points": 2
                    },
                    "Beginning": {
                        "description": "Poor organization with unclear communication",
                        "points": 1
                    }
                }
            }
        ]
        
        return Rubric(
            name="Standard History Essay Rubric",
            description="Comprehensive rubric for History essay assessment",
            criteria=criteria,
            total_points=16.0
        )
    
    async def grade_essay(
        self,
        essay_text: str,
        question: AssessmentQuestion,
        rubric: Optional[Rubric] = None,
        student_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Grade a History essay and provide detailed feedback."""
        
        logger.info(f"Grading essay for question: {question.id}")
        
        if not rubric:
            rubric = self.standard_rubric
        
        grading_result = {
            "essay_analysis": {},
            "criterion_scores": {},
            "total_score": 0.0,
            "percentage_score": 0.0,
            "feedback": {
                "strengths": [],
                "areas_for_improvement": [],
                "specific_suggestions": [],
                "next_steps": []
            },
            "detailed_analysis": {}
        }
        
        try:
            # 1. Perform comprehensive essay analysis
            grading_result["essay_analysis"] = await self._analyze_essay_structure(
                essay_text, question
            )
            
            # 2. Grade against each rubric criterion
            for criterion in rubric.criteria:
                criterion_score = await self._grade_criterion(
                    essay_text, question, criterion, grading_result["essay_analysis"]
                )
                grading_result["criterion_scores"][criterion.name] = criterion_score
            
            # 3. Calculate total score
            total_score = self._calculate_total_score(
                grading_result["criterion_scores"], rubric
            )
            grading_result["total_score"] = total_score
            grading_result["percentage_score"] = (total_score / rubric.total_points) * 100
            
            # 4. Generate comprehensive feedback
            grading_result["feedback"] = await self._generate_comprehensive_feedback(
                essay_text, question, grading_result, rubric
            )
            
            # 5. Create detailed analysis for learning insights
            grading_result["detailed_analysis"] = await self._create_detailed_analysis(
                essay_text, question, grading_result
            )
            
            logger.info(f"Essay graded: {grading_result['percentage_score']:.1f}%")
            
        except Exception as e:
            logger.error(f"Essay grading failed: {e}")
            grading_result["error"] = str(e)
        
        return grading_result
    
    async def _analyze_essay_structure(
        self, 
        essay_text: str, 
        question: AssessmentQuestion
    ) -> Dict[str, Any]:
        """Analyze the structural components of the essay."""
        
        analysis_prompt = f"""
        Analyze this History essay's structure and components:

        Essay Question: {question.prompt}
        Essay Text: {essay_text}

        Provide analysis of:
        1. Thesis statement identification and quality
        2. Essay organization and paragraph structure
        3. Evidence usage and integration
        4. Historical reasoning and analysis
        5. Conclusion effectiveness

        Format your analysis as JSON with the following structure:
        {{
            "thesis": {{
                "present": true/false,
                "location": "paragraph number or 'unclear'",
                "clarity": "clear/somewhat clear/unclear",
                "specificity": "specific/general/vague",
                "arguability": "strong/moderate/weak"
            }},
            "organization": {{
                "paragraph_count": number,
                "introduction_effective": true/false,
                "body_paragraph_focus": "clear/mixed/unclear",
                "transitions": "smooth/adequate/choppy",
                "conclusion_effective": true/false
            }},
            "evidence": {{
                "specific_examples_count": number,
                "evidence_types": ["primary sources", "specific events", "statistics", etc.],
                "integration_quality": "excellent/good/fair/poor",
                "accuracy": "accurate/mostly accurate/some inaccuracies/many errors"
            }},
            "analysis": {{
                "cause_effect_reasoning": "sophisticated/adequate/basic/absent",
                "historical_context": "comprehensive/adequate/limited/absent",
                "multiple_perspectives": "considers multiple/some consideration/single perspective",
                "complexity_of_understanding": "nuanced/adequate/simplistic"
            }}
        }}
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert History teacher analyzing essay structure and content."),
                HumanMessage(content=analysis_prompt)
            ])
            
            # Parse the structured analysis (implement proper JSON parsing)
            analysis = self._parse_essay_analysis(response.content)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Essay structure analysis failed: {e}")
            return self._get_default_analysis()
    
    async def _grade_criterion(
        self,
        essay_text: str,
        question: AssessmentQuestion,
        criterion: RubricCriterion,
        essay_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Grade essay against a specific rubric criterion."""
        
        # Build performance level descriptions for this criterion
        level_descriptions = "\n".join([
            f"{level}: {details['description']} ({details['points']} points)"
            for level, details in criterion.performance_levels.items()
        ])
        
        grading_prompt = f"""
        Grade this History essay against the following criterion:

        Criterion: {criterion.name}
        Description: {criterion.description}
        Weight: {criterion.weight}

        Performance Levels:
        {level_descriptions}

        Essay Question: {question.prompt}
        Essay Text: {essay_text}

        Essay Analysis Context:
        {essay_analysis}

        Based on the essay content and the criterion requirements, determine:
        1. Which performance level best matches this essay
        2. Specific evidence from the essay that supports this assessment
        3. Key strengths related to this criterion
        4. Areas for improvement related to this criterion
        5. Specific suggestions for improvement

        Respond in JSON format:
        {{
            "performance_level": "level name",
            "points_awarded": number,
            "justification": "specific reasoning for this score",
            "evidence_from_essay": ["quote 1", "quote 2"],
            "strengths": ["strength 1", "strength 2"],
            "improvements": ["improvement 1", "improvement 2"],
            "suggestions": ["suggestion 1", "suggestion 2"]
        }}
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an experienced History teacher grading essays with detailed rubrics."),
                HumanMessage(content=grading_prompt)
            ])
            
            # Parse the grading result
            criterion_result = self._parse_criterion_grading(response.content, criterion)
            
            return criterion_result
            
        except Exception as e:
            logger.error(f"Criterion grading failed for {criterion.name}: {e}")
            return self._get_default_criterion_score(criterion)
    
    def _calculate_total_score(
        self,
        criterion_scores: Dict[str, Dict[str, Any]],
        rubric: Rubric
    ) -> float:
        """Calculate weighted total score from criterion scores."""
        
        total_score = 0.0
        
        for criterion in rubric.criteria:
            criterion_score = criterion_scores.get(criterion.name, {})
            points = criterion_score.get("points_awarded", 0.0)
            weighted_points = points * criterion.weight
            total_score += weighted_points
        
        return total_score
    
    async def _generate_comprehensive_feedback(
        self,
        essay_text: str,
        question: AssessmentQuestion,
        grading_result: Dict[str, Any],
        rubric: Rubric
    ) -> Dict[str, Any]:
        """Generate comprehensive, actionable feedback for the student."""
        
        # Collect all strengths and improvements from criteria
        all_strengths = []
        all_improvements = []
        all_suggestions = []
        
        for criterion_name, criterion_result in grading_result["criterion_scores"].items():
            all_strengths.extend(criterion_result.get("strengths", []))
            all_improvements.extend(criterion_result.get("improvements", []))
            all_suggestions.extend(criterion_result.get("suggestions", []))
        
        feedback_prompt = f"""
        Generate comprehensive, encouraging feedback for this History essay:

        Essay Score: {grading_result['percentage_score']:.1f}%
        Question: {question.prompt}

        Identified Strengths:
        {chr(10).join(f"- {strength}" for strength in all_strengths[:5])}

        Areas for Improvement:
        {chr(10).join(f"- {improvement}" for improvement in all_improvements[:5])}

        Create feedback that:
        1. Starts with positive recognition of strengths
        2. Provides specific, actionable improvement suggestions
        3. Offers concrete next steps for learning
        4. Maintains an encouraging, supportive tone
        5. Focuses on historical thinking skill development

        Format as JSON:
        {{
            "opening_comment": "encouraging opening that highlights main strengths",
            "strengths_detailed": ["strength 1 with specific example", "strength 2 with specific example"],
            "improvements_prioritized": ["most important improvement with explanation", "second priority improvement"],
            "specific_suggestions": ["actionable suggestion 1", "actionable suggestion 2", "actionable suggestion 3"],
            "next_steps": ["next learning step 1", "next learning step 2"],
            "encouragement": "encouraging closing comment about growth and learning"
        }}
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a supportive History teacher providing encouraging, specific feedback to help students improve."),
                HumanMessage(content=feedback_prompt)
            ])
            
            feedback = self._parse_feedback_response(response.content)
            
            return feedback
            
        except Exception as e:
            logger.error(f"Feedback generation failed: {e}")
            return self._get_default_feedback()
    
    async def _create_detailed_analysis(
        self,
        essay_text: str,
        question: AssessmentQuestion,
        grading_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create detailed analysis for learning analytics."""
        
        detailed_analysis = {
            "word_count": len(essay_text.split()),
            "sentence_count": len(re.split(r'[.!?]+', essay_text)),
            "paragraph_count": len([p for p in essay_text.split('\n\n') if p.strip()]),
            "historical_thinking_skills": {},
            "content_analysis": {},
            "language_quality": {},
            "improvement_priorities": []
        }
        
        # Analyze historical thinking skills demonstrated
        detailed_analysis["historical_thinking_skills"] = await self._analyze_thinking_skills(
            essay_text, question
        )
        
        # Analyze content depth and accuracy
        detailed_analysis["content_analysis"] = await self._analyze_content_depth(
            essay_text, question
        )
        
        # Assess language and writing quality
        detailed_analysis["language_quality"] = self._analyze_language_quality(essay_text)
        
        # Prioritize improvements based on impact
        detailed_analysis["improvement_priorities"] = self._prioritize_improvements(
            grading_result, detailed_analysis
        )
        
        return detailed_analysis
    
    def _parse_essay_analysis(self, response_text: str) -> Dict[str, Any]:
        """Parse essay analysis from LLM response."""
        # This would implement proper JSON parsing
        # For now, return a structured default
        return {
            "thesis": {
                "present": True,
                "location": "paragraph 1",
                "clarity": "clear",
                "specificity": "specific",
                "arguability": "strong"
            },
            "organization": {
                "paragraph_count": 5,
                "introduction_effective": True,
                "body_paragraph_focus": "clear",
                "transitions": "adequate",
                "conclusion_effective": True
            },
            "evidence": {
                "specific_examples_count": 3,
                "evidence_types": ["specific events", "primary sources"],
                "integration_quality": "good",
                "accuracy": "accurate"
            },
            "analysis": {
                "cause_effect_reasoning": "adequate",
                "historical_context": "adequate",
                "multiple_perspectives": "some consideration",
                "complexity_of_understanding": "adequate"
            }
        }
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """Return default analysis structure if parsing fails."""
        return {
            "thesis": {"present": True, "clarity": "unclear"},
            "organization": {"paragraph_count": 3, "transitions": "adequate"},
            "evidence": {"specific_examples_count": 1, "integration_quality": "fair"},
            "analysis": {"complexity_of_understanding": "basic"}
        }
    
    def _parse_criterion_grading(
        self, 
        response_text: str, 
        criterion: RubricCriterion
    ) -> Dict[str, Any]:
        """Parse criterion grading from LLM response."""
        # This would implement proper JSON parsing
        # For now, return a structured default
        return {
            "performance_level": "Proficient",
            "points_awarded": 3.0,
            "justification": "Essay meets most requirements for this criterion",
            "evidence_from_essay": ["Evidence quote 1", "Evidence quote 2"],
            "strengths": ["Strength related to criterion"],
            "improvements": ["Area for improvement"],
            "suggestions": ["Specific suggestion for improvement"]
        }
    
    def _get_default_criterion_score(self, criterion: RubricCriterion) -> Dict[str, Any]:
        """Return default criterion score if grading fails."""
        return {
            "performance_level": "Developing",
            "points_awarded": 2.0,
            "justification": "Unable to fully assess this criterion",
            "evidence_from_essay": [],
            "strengths": [],
            "improvements": ["Needs more development in this area"],
            "suggestions": ["Focus on improving this criterion"]
        }
```

This comprehensive assessment engine implementation provides intelligent question generation, automated grading with detailed feedback, formative assessment capabilities, and analytics for tracking student progress. The system is specifically designed for History education with appropriate pedagogical approaches and thinking skills assessment.