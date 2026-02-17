# Context Window Management Implementation

**Document:** 01_CONTEXT_WINDOW_MANAGEMENT.md  
**Version:** 1.0  
**Date:** February 17, 2026  
**Dependencies:** Redis, PostgreSQL, ChromaDB  

---

## Overview

This document details the implementation of the hierarchical context management system that enables EduAGI to maintain educational context across multi-hour tutoring sessions while staying within LLM token limits.

## Current State Analysis

### Existing Implementation (src/memory/manager.py)
- **Working Memory (Redis)**: Basic session context storage with 50-message limit
- **Conversation History**: Simple FIFO queue in Redis with `ltrim(-50, -1)`
- **Session Context**: Basic JSON storage in Redis with TTL
- **Memory Issues**: No intelligent summarization, fixed 50-message window, no educational context preservation

```python
# Current implementation - basic and insufficient
async def add_to_conversation(self, session_id: str, role: str, content: str):
    key = f"session:{session_id}:messages"
    message = json.dumps({
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    await self._redis.rpush(key, message)
    await self._redis.ltrim(key, -50, -1)  # Only keeps last 50 messages
```

### Problems to Solve
1. **Context Loss**: Educational progress lost when conversation exceeds 50 messages
2. **No Summarization**: Raw messages don't capture learning insights
3. **No Context Prioritization**: All messages treated equally
4. **No Session Resume**: No way to resume learning sessions effectively

---

## Architecture Design

### Three-Tier Context Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    HIERARCHICAL CONTEXT SYSTEM                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Tier 1: Active Window (Redis)           Token Budget: ~2000     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ • Last 15-25 turns (adaptive based on token count)         │ │
│ │ • Raw conversation messages                                 │ │
│ │ • Real-time educational annotations                         │ │
│ │ • Student confusion/breakthrough markers                    │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                             ↓                                   │
│ Tier 2: Session Summaries (PostgreSQL)  Token Budget: ~1500     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ • Auto-generated every 30 minutes OR 40 turns              │ │
│ │ • Educational progress summaries                            │ │
│ │ • Concept mastery assessments                              │ │
│ │ • Teaching strategy effectiveness                           │ │
│ │ • Last 3-5 session summaries kept active                  │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                             ↓                                   │
│ Tier 3: Topic Memory (ChromaDB + PostgreSQL) Token Budget: ~1000 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ • Persistent cross-session learning state                  │ │
│ │ • Topic mastery levels and patterns                        │ │
│ │ • Effective teaching approaches for this student           │ │
│ │ • Long-term learning goals and progress                    │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ Total Context Budget: ~4500 tokens (fits in 8k context window) │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Structure and Changes

### New Files to Create

#### 1. `src/context/__init__.py`
```python
"""Context management system for educational conversations."""
from .manager import ContextManager
from .summarizer import EducationalSummarizer
from .window import SlidingContextWindow
from .schemas import ContextTier, TutoringContext, SummaryType

__all__ = [
    "ContextManager", 
    "EducationalSummarizer", 
    "SlidingContextWindow",
    "ContextTier", 
    "TutoringContext", 
    "SummaryType"
]
```

#### 2. `src/context/schemas.py`
```python
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
```

#### 3. `src/context/manager.py`
```python
"""Main context manager orchestrating the three-tier system."""
import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any

from src.context.schemas import (
    TutoringContext, 
    AnnotatedMessage, 
    EducationalSummary,
    MessageAnnotation,
    SummaryType
)
from src.context.summarizer import EducationalSummarizer
from src.context.window import SlidingContextWindow
from src.memory.manager import MemoryManager

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages hierarchical context for educational conversations."""
    
    def __init__(
        self, 
        memory_manager: MemoryManager,
        summarization_interval_minutes: int = 30,
        max_active_summaries: int = 5
    ):
        self.memory = memory_manager
        self.summarizer = EducationalSummarizer()
        self.window = SlidingContextWindow()
        self.summarization_interval = summarization_interval_minutes
        self.max_active_summaries = max_active_summaries
        
        # Background tasks
        self._summarization_tasks: Dict[str, asyncio.Task] = {}
    
    async def get_tutoring_context(self, session_id: str) -> TutoringContext:
        """Build complete tutoring context from all three tiers."""
        # Get session context data
        context_data = await self.memory.get_session_context(session_id)
        if not context_data:
            logger.warning(f"No session context found for {session_id}")
            return TutoringContext(session_id=session_id, student_id="unknown")
        
        student_id = context_data.get("student_id", "unknown")
        
        # Tier 1: Active window messages
        active_messages = await self._get_active_window_messages(session_id)
        
        # Tier 2: Session summaries  
        session_summaries = await self._get_session_summaries(session_id)
        
        # Tier 3: Topic knowledge
        topic_mastery, learning_patterns = await self._get_topic_knowledge(student_id)
        
        context = TutoringContext(
            session_id=session_id,
            student_id=student_id,
            active_messages=active_messages,
            session_summaries=session_summaries[-self.max_active_summaries:],  # Keep recent
            topic_mastery=topic_mastery,
            learning_patterns=learning_patterns,
        )
        
        context.total_token_estimate = context.estimate_tokens()
        logger.info(f"Built context for {session_id}: {context.total_token_estimate} tokens")
        
        return context
    
    async def add_message_with_annotation(
        self, 
        session_id: str, 
        role: str, 
        content: str,
        annotations: List[MessageAnnotation] = None
    ) -> None:
        """Add message to active window with educational annotations."""
        # Create annotated message
        message = AnnotatedMessage(
            role=role,
            content=content,
            timestamp=datetime.now(timezone.utc),
            token_count=self._estimate_message_tokens(content),
            annotations=annotations or []
        )
        
        # Store in Redis with annotations
        await self._store_annotated_message(session_id, message)
        
        # Check if summarization needed
        await self._maybe_trigger_summarization(session_id)
        
        # Update sliding window
        await self.window.update_window(session_id, self.memory)
    
    async def _get_active_window_messages(self, session_id: str) -> List[AnnotatedMessage]:
        """Get messages from active window with annotations."""
        key = f"session:{session_id}:annotated_messages"
        raw_messages = await self.memory._redis.lrange(key, -25, -1)
        
        messages = []
        for raw_msg in raw_messages:
            try:
                msg_data = json.loads(raw_msg)
                messages.append(AnnotatedMessage(**msg_data))
            except Exception as e:
                logger.warning(f"Failed to parse annotated message: {e}")
                
        return messages
    
    async def _get_session_summaries(self, session_id: str) -> List[EducationalSummary]:
        """Get recent session summaries from PostgreSQL."""
        if not self.memory.db_session_factory:
            return []
            
        from src.models.context_summary import ContextSummary
        from sqlalchemy import select
        
        async with self.memory.db_session_factory() as db_session:
            stmt = (
                select(ContextSummary)
                .where(ContextSummary.session_id == session_id)
                .order_by(ContextSummary.created_at.desc())
                .limit(10)
            )
            result = await db_session.execute(stmt)
            db_summaries = result.scalars().all()
            
            summaries = []
            for db_summary in db_summaries:
                try:
                    summary = EducationalSummary(**json.loads(db_summary.summary_data))
                    summaries.append(summary)
                except Exception as e:
                    logger.warning(f"Failed to parse summary: {e}")
                    
            return summaries
    
    async def _get_topic_knowledge(self, student_id: str) -> tuple[Dict[str, float], Dict[str, Any]]:
        """Get topic mastery and learning patterns from long-term memory."""
        # Get mastery data from PostgreSQL
        mastery_data = await self.memory.get_student_mastery(student_id)
        topic_mastery = {
            record["topic"]: record["mastery_score"] 
            for record in mastery_data
        }
        
        # Get learning patterns from ChromaDB
        learning_patterns = await self._get_learning_patterns(student_id)
        
        return topic_mastery, learning_patterns
    
    async def _get_learning_patterns(self, student_id: str) -> Dict[str, Any]:
        """Query learning patterns from ChromaDB."""
        try:
            pattern_docs = await self.memory.search_knowledge(
                query=f"learning_patterns_for_student_{student_id}",
                collection_name="student_patterns",
                n_results=5
            )
            
            patterns = {}
            for doc in pattern_docs:
                metadata = doc.get("metadata", {})
                pattern_type = metadata.get("pattern_type")
                if pattern_type:
                    patterns[pattern_type] = json.loads(doc.get("document", "{}"))
                    
            return patterns
        except Exception as e:
            logger.warning(f"Failed to get learning patterns: {e}")
            return {}
    
    async def _store_annotated_message(self, session_id: str, message: AnnotatedMessage) -> None:
        """Store annotated message in Redis."""
        key = f"session:{session_id}:annotated_messages"
        message_json = message.json()
        
        await self.memory._redis.rpush(key, message_json)
        await self.memory._redis.ltrim(key, -50, -1)  # Keep last 50 for safety
        await self.memory._redis.expire(key, 86400)  # 24 hour TTL
    
    async def _maybe_trigger_summarization(self, session_id: str) -> None:
        """Check if it's time to summarize and trigger if needed."""
        # Check if summarization task already running
        if session_id in self._summarization_tasks:
            task = self._summarization_tasks[session_id]
            if not task.done():
                return  # Already summarizing
                
        # Check last summarization time
        last_summary_key = f"session:{session_id}:last_summary"
        last_summary_time = await self.memory._redis.get(last_summary_key)
        
        if last_summary_time:
            last_time = datetime.fromisoformat(last_summary_time)
            if datetime.now(timezone.utc) - last_time < timedelta(minutes=self.summarization_interval):
                return  # Too soon
        
        # Check message count threshold  
        key = f"session:{session_id}:annotated_messages"
        message_count = await self.memory._redis.llen(key)
        
        if message_count >= 40:  # Force summarization at 40 messages
            await self._trigger_background_summarization(session_id)
    
    async def _trigger_background_summarization(self, session_id: str) -> None:
        """Start background summarization task."""
        task = asyncio.create_task(self._background_summarize_session(session_id))
        self._summarization_tasks[session_id] = task
        logger.info(f"Started background summarization for session {session_id}")
    
    async def _background_summarize_session(self, session_id: str) -> None:
        """Background task to summarize a session."""
        try:
            # Get messages to summarize
            active_messages = await self._get_active_window_messages(session_id)
            
            if len(active_messages) < 10:  # Need minimum messages
                return
                
            # Generate summary
            summary = await self.summarizer.create_session_summary(
                session_id=session_id,
                messages=active_messages
            )
            
            # Store summary in PostgreSQL
            await self._store_session_summary(summary)
            
            # Update last summary timestamp
            last_summary_key = f"session:{session_id}:last_summary"
            await self.memory._redis.set(
                last_summary_key, 
                datetime.now(timezone.utc).isoformat(),
                ex=86400
            )
            
            logger.info(f"Completed summarization for session {session_id}")
            
        except Exception as e:
            logger.error(f"Summarization failed for session {session_id}: {e}")
        finally:
            # Clean up task reference
            self._summarization_tasks.pop(session_id, None)
    
    async def _store_session_summary(self, summary: EducationalSummary) -> None:
        """Store educational summary in PostgreSQL."""
        if not self.memory.db_session_factory:
            return
            
        from src.models.context_summary import ContextSummary
        
        async with self.memory.db_session_factory() as db_session:
            db_summary = ContextSummary(
                session_id=summary.session_id,
                student_id=summary.student_id,
                summary_type=summary.summary_type.value,
                summary_data=summary.json(),
                token_estimate=summary.total_tokens,
                created_at=summary.created_at
            )
            db_session.add(db_summary)
            await db_session.commit()
    
    async def end_session_summary(self, session_id: str) -> Optional[EducationalSummary]:
        """Create final session summary when session ends."""
        active_messages = await self._get_active_window_messages(session_id)
        
        if not active_messages:
            return None
            
        summary = await self.summarizer.create_session_end_summary(
            session_id=session_id,
            messages=active_messages
        )
        
        await self._store_session_summary(summary)
        
        # Also update topic knowledge in ChromaDB
        await self._update_topic_knowledge_from_summary(summary)
        
        return summary
    
    async def _update_topic_knowledge_from_summary(self, summary: EducationalSummary) -> None:
        """Update long-term topic knowledge based on session summary."""
        # Extract learning patterns to store in ChromaDB
        pattern_doc = {
            "student_id": summary.student_id,
            "effective_strategies": summary.effective_strategies,
            "engagement_pattern": summary.student_engagement_level,
            "mastery_gains": summary.mastery_assessments,
            "timestamp": summary.created_at.isoformat()
        }
        
        await self.memory.store_knowledge(
            documents=[json.dumps(pattern_doc)],
            metadatas=[{
                "student_id": summary.student_id,
                "pattern_type": "learning_effectiveness",
                "session_id": summary.session_id
            }],
            collection_name="student_patterns"
        )
    
    def _estimate_message_tokens(self, content: str) -> int:
        """Rough token estimation for a message."""
        # Rough approximation: ~4 characters per token
        return max(1, len(content) // 4)
    
    async def cleanup_old_context(self, session_id: str, days: int = 7) -> None:
        """Clean up old context data beyond retention period."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        if not self.memory.db_session_factory:
            return
            
        from src.models.context_summary import ContextSummary
        from sqlalchemy import delete
        
        async with self.memory.db_session_factory() as db_session:
            stmt = delete(ContextSummary).where(
                ContextSummary.session_id == session_id,
                ContextSummary.created_at < cutoff_date
            )
            await db_session.execute(stmt)
            await db_session.commit()
```

#### 4. `src/context/summarizer.py`
```python
"""Educational conversation summarizer using LLM."""
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage

from src.context.schemas import (
    AnnotatedMessage, 
    EducationalSummary, 
    SummaryType
)
from src.llm.factory import LLMFactory

logger = logging.getLogger(__name__)


class EducationalSummarizer:
    """Intelligent summarizer focused on educational progress."""
    
    def __init__(self):
        # Use a fast, cheap model for summarization
        self.llm = LLMFactory.create(provider="openai", model="gpt-3.5-turbo")
    
    async def create_session_summary(
        self, 
        session_id: str, 
        messages: List[AnnotatedMessage],
        summary_type: SummaryType = SummaryType.PROGRESS
    ) -> EducationalSummary:
        """Create educational summary of conversation segment."""
        if not messages:
            raise ValueError("No messages to summarize")
            
        student_id = self._extract_student_id(session_id)
        time_range = (messages[0].timestamp, messages[-1].timestamp)
        
        # Build summarization prompt
        conversation_text = self._format_messages_for_summary(messages)
        annotations_text = self._format_annotations_for_summary(messages)
        
        prompt = self._build_summarization_prompt(
            conversation_text, 
            annotations_text, 
            summary_type
        )
        
        # Generate summary via LLM
        response = await self.llm.ainvoke([
            SystemMessage(content="You are an expert educational analyst."),
            HumanMessage(content=prompt)
        ])
        
        # Parse LLM response into structured summary
        summary_data = self._parse_llm_summary(response.content)
        
        return EducationalSummary(
            summary_type=summary_type,
            session_id=session_id,
            student_id=student_id,
            time_range=time_range,
            message_count=len(messages),
            total_tokens=sum(msg.token_count for msg in messages),
            **summary_data
        )
    
    async def create_session_end_summary(
        self, 
        session_id: str, 
        messages: List[AnnotatedMessage]
    ) -> EducationalSummary:
        """Create comprehensive end-of-session summary."""
        return await self.create_session_summary(
            session_id, 
            messages, 
            SummaryType.SESSION_END
        )
    
    def _extract_student_id(self, session_id: str) -> str:
        """Extract student ID from session context or return session ID."""
        # In practice, this would query Redis or PostgreSQL
        return f"student_from_{session_id}"
    
    def _format_messages_for_summary(self, messages: List[AnnotatedMessage]) -> str:
        """Format conversation for LLM summarization."""
        formatted = []
        for msg in messages:
            role = "Student" if msg.role == "user" else "Tutor"
            formatted.append(f"{role}: {msg.content}")
        return "\n".join(formatted)
    
    def _format_annotations_for_summary(self, messages: List[AnnotatedMessage]) -> str:
        """Format educational annotations for analysis."""
        annotations = []
        for msg in messages:
            for annotation in msg.annotations:
                annotations.append(
                    f"- {annotation.type} (confidence: {annotation.confidence:.2f}): "
                    f"{', '.join(annotation.concepts)}"
                )
        return "\n".join(annotations) if annotations else "No specific annotations"
    
    def _build_summarization_prompt(
        self, 
        conversation: str, 
        annotations: str, 
        summary_type: SummaryType
    ) -> str:
        """Build LLM prompt for educational summarization."""
        base_prompt = f"""
Analyze this educational conversation and extract key learning insights.

CONVERSATION:
{conversation}

EDUCATIONAL ANNOTATIONS:
{annotations}

Generate a JSON summary with these fields:
- concepts_discussed: List of main concepts/topics covered
- mastery_assessments: Dict mapping concepts to confidence levels (0.0-1.0)
- misconceptions_identified: List of misconceptions the student showed
- breakthrough_moments: List of moments where student gained clear understanding
- effective_strategies: List of teaching approaches that worked well
- ineffective_approaches: List of approaches that didn't work
- student_engagement_level: Overall engagement score (0.0-1.0)
- suggested_next_topics: List of logical next topics to explore
- recommended_teaching_approach: Single best teaching method for this student
"""
        
        if summary_type == SummaryType.SESSION_END:
            base_prompt += """
This is an END-OF-SESSION summary. Focus on:
- Overall learning progress made this session
- Key concepts mastered vs still struggling with  
- Most effective teaching approaches used
- Recommended focus areas for next session
"""
        
        base_prompt += "\nRespond with only valid JSON, no additional text."
        
        return base_prompt
    
    def _parse_llm_summary(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM response into structured summary data."""
        try:
            # Extract JSON from response (handle cases where LLM adds extra text)
            start_idx = llm_response.find('{')
            end_idx = llm_response.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in LLM response")
                
            json_str = llm_response[start_idx:end_idx]
            summary_data = json.loads(json_str)
            
            # Validate and set defaults
            return {
                "concepts_discussed": summary_data.get("concepts_discussed", []),
                "mastery_assessments": summary_data.get("mastery_assessments", {}),
                "misconceptions_identified": summary_data.get("misconceptions_identified", []),
                "breakthrough_moments": summary_data.get("breakthrough_moments", []),
                "effective_strategies": summary_data.get("effective_strategies", []),
                "ineffective_approaches": summary_data.get("ineffective_approaches", []),
                "student_engagement_level": float(summary_data.get("student_engagement_level", 0.5)),
                "suggested_next_topics": summary_data.get("suggested_next_topics", []),
                "recommended_teaching_approach": summary_data.get("recommended_teaching_approach"),
            }
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse LLM summary: {e}, response: {llm_response[:200]}")
            
            # Return safe defaults
            return {
                "concepts_discussed": [],
                "mastery_assessments": {},
                "misconceptions_identified": [],
                "breakthrough_moments": [],
                "effective_strategies": [],
                "ineffective_approaches": [], 
                "student_engagement_level": 0.5,
                "suggested_next_topics": [],
                "recommended_teaching_approach": None,
            }
    
    async def annotate_message_with_educational_insights(
        self, 
        message_content: str, 
        conversation_context: List[str]
    ) -> List[MessageAnnotation]:
        """Add educational annotations to a message."""
        context_text = "\n".join(conversation_context[-5:])  # Last 5 messages for context
        
        prompt = f"""
Analyze this student message for educational insights:

RECENT CONTEXT:
{context_text}

STUDENT MESSAGE:
{message_content}

Identify any of these patterns and respond with JSON:
{{
  "annotations": [
    {{
      "type": "confusion|breakthrough|misconception|mastery|question",
      "confidence": 0.0-1.0,
      "concepts": ["concept1", "concept2"]
    }}
  ]
}}

Look for:
- Confusion: Student seems lost or asks repeated similar questions
- Breakthrough: "Oh I see!" moments, sudden understanding
- Misconception: Incorrect understanding of concepts  
- Mastery: Confident, correct application of concepts
- Question: Specific topics being asked about

Respond with only JSON, no additional text.
"""
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an educational analyst."),
                HumanMessage(content=prompt)
            ])
            
            data = json.loads(response.content)
            annotations = []
            
            for ann_data in data.get("annotations", []):
                annotation = MessageAnnotation(
                    type=ann_data["type"],
                    confidence=float(ann_data["confidence"]),
                    concepts=ann_data.get("concepts", []),
                    timestamp=datetime.now(timezone.utc)
                )
                annotations.append(annotation)
                
            return annotations
            
        except Exception as e:
            logger.warning(f"Failed to annotate message: {e}")
            return []
```

#### 5. `src/context/window.py`
```python
"""Sliding context window implementation."""
import logging
from typing import List

from src.context.schemas import AnnotatedMessage, ContextWindow

logger = logging.getLogger(__name__)


class SlidingContextWindow:
    """Manages the active conversation window with adaptive sizing."""
    
    def __init__(self, window_config: ContextWindow = None):
        self.config = window_config or ContextWindow()
    
    async def update_window(self, session_id: str, memory_manager) -> None:
        """Update the sliding window to stay within token limits."""
        key = f"session:{session_id}:annotated_messages"
        
        # Get current messages
        raw_messages = await memory_manager._redis.lrange(key, 0, -1)
        
        if not raw_messages:
            return
            
        # Parse messages and calculate tokens
        messages = []
        total_tokens = 0
        
        for raw_msg in reversed(raw_messages):  # Start from most recent
            try:
                import json
                msg_data = json.loads(raw_msg)
                message = AnnotatedMessage(**msg_data)
                messages.append(message)
                total_tokens += message.token_count
                
                # Stop if we exceed limits
                if (len(messages) >= self.config.max_messages and 
                    len(messages) > self.config.min_messages):
                    break
                    
                if (total_tokens >= self.config.max_tokens and 
                    len(messages) > self.config.min_messages):
                    break
                    
            except Exception as e:
                logger.warning(f"Failed to parse message in window: {e}")
                continue
        
        # If we have more messages than needed, trim
        if len(messages) < len(raw_messages):
            # Keep the most recent N messages
            messages_to_keep = len(messages)
            await memory_manager._redis.ltrim(key, -messages_to_keep, -1)
            
            logger.info(
                f"Trimmed window for {session_id}: "
                f"kept {messages_to_keep} messages, {total_tokens} tokens"
            )
    
    def calculate_optimal_window_size(
        self, 
        messages: List[AnnotatedMessage],
        target_tokens: int = 2000
    ) -> int:
        """Calculate optimal number of messages for target token count."""
        if not messages:
            return self.config.min_messages
            
        total_tokens = 0
        count = 0
        
        for message in reversed(messages):  # Start from most recent
            if total_tokens + message.token_count > target_tokens:
                break
            total_tokens += message.token_count
            count += 1
            
        return max(count, self.config.min_messages)
```

### Files to Modify

#### 1. `src/memory/manager.py` - Extend existing MemoryManager
Add these methods to the existing MemoryManager class:

```python
# Add to existing MemoryManager class
async def get_context_summaries(
    self, 
    session_id: str, 
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Get recent context summaries for a session."""
    if not self.db_session_factory:
        return []
        
    from src.models.context_summary import ContextSummary
    from sqlalchemy import select
    
    async with self.db_session_factory() as session:
        stmt = (
            select(ContextSummary)
            .where(ContextSummary.session_id == session_id)
            .order_by(ContextSummary.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        summaries = result.scalars().all()
        
        return [
            {
                "id": str(s.id),
                "summary_type": s.summary_type,
                "summary_data": json.loads(s.summary_data) if s.summary_data else {},
                "token_estimate": s.token_estimate,
                "created_at": s.created_at.isoformat() if s.created_at else None
            }
            for s in summaries
        ]
```

#### 2. `src/agents/tutor.py` - Update to use new context system
Replace the `process` method in TutorAgent:

```python
async def process(self, input_text: str, context: AgentContext) -> AgentResponse:
    """Process student input with enhanced context management."""
    start = time.time()
    
    # Use new context manager instead of basic memory
    if hasattr(self.memory, 'context_manager'):
        context_manager = self.memory.context_manager
        tutoring_context = await context_manager.get_tutoring_context(context.session_id)
        
        # Add message with educational annotation
        from src.context.summarizer import EducationalSummarizer
        summarizer = EducationalSummarizer()
        
        # Get recent conversation for context
        recent_messages = [msg.content for msg in tutoring_context.active_messages[-5:]]
        annotations = await summarizer.annotate_message_with_educational_insights(
            input_text, recent_messages
        )
        
        await context_manager.add_message_with_annotation(
            context.session_id, "user", input_text, annotations
        )
        
        # Build enriched agent context from tutoring context
        enriched_context = self._build_enriched_context(tutoring_context)
    else:
        # Fallback to original implementation
        enriched_context = await self._build_legacy_context(context)
    
    # Rest of the method remains the same...
    # [Continue with existing strategy selection and LLM call logic]
```

---

## Database Schema Changes

### New Table: `context_summaries`

#### Migration: `migrations/versions/008_context_summaries.py`
```python
"""Add context summaries table.

Revision ID: 008
Revises: 007
Create Date: 2026-02-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


def upgrade() -> None:
    op.create_table(
        'context_summaries',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('session_id', sa.String(255), nullable=False, index=True),
        sa.Column('student_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('summary_type', sa.String(50), nullable=False),
        sa.Column('summary_data', JSONB, nullable=False),
        sa.Column('token_estimate', sa.Integer, default=0),
        sa.Column('message_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    
    # Indexes for efficient querying
    op.create_index('ix_context_summaries_session_student', 'context_summaries', 
                   ['session_id', 'student_id'])
    op.create_index('ix_context_summaries_created_at', 'context_summaries', 
                   ['created_at'])


def downgrade() -> None:
    op.drop_table('context_summaries')
```

#### Model: `src/models/context_summary.py`
```python
"""Context summary storage model."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.models.database import Base


class ContextSummary(Base):
    __tablename__ = "context_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    session_id = Column(String(255), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    summary_type = Column(String(50), nullable=False)  # "progress", "conceptual", "strategic", "session_end"
    summary_data = Column(JSONB, nullable=False)
    token_estimate = Column(Integer, default=0)
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
```

---

## Redis Key Structure

### Enhanced Redis Schema
```
# Session context (enhanced)
session:{session_id}:context              # Original session metadata
session:{session_id}:annotated_messages   # NEW: Messages with annotations  
session:{session_id}:last_summary         # NEW: Last summarization timestamp
session:{session_id}:context_stats        # NEW: Token counts, message counts

# Context management
context:{session_id}:token_budget         # Current token usage across tiers
context:{session_id}:window_size          # Current active window size
context:{session_id}:summarization_lock   # Lock to prevent concurrent summarization
```

---

## API Endpoint Changes

### New Endpoint: Context Management

#### Add to `src/api/routers/chat.py`:
```python
@router.get("/context/{session_id}")
async def get_context_info(
    session_id: str,
    current_user: User = Depends(get_current_user),
    memory: MemoryManager = Depends(get_memory),
):
    """Get context information for debugging/analytics."""
    if hasattr(memory, 'context_manager'):
        context = await memory.context_manager.get_tutoring_context(session_id)
        
        return {
            "session_id": session_id,
            "active_message_count": len(context.active_messages),
            "session_summary_count": len(context.session_summaries),  
            "topic_mastery_count": len(context.topic_mastery),
            "total_token_estimate": context.total_token_estimate,
            "context_freshness": context.context_freshness.isoformat()
        }
    else:
        # Legacy context info
        context_data = await memory.get_session_context(session_id)
        history = await memory.get_conversation_history(session_id)
        
        return {
            "session_id": session_id,
            "message_count": len(history),
            "has_context": context_data is not None,
            "legacy_mode": True
        }

@router.post("/context/{session_id}/force-summarize")
async def force_summarization(
    session_id: str,
    current_user: User = Depends(get_current_user),
    memory: MemoryManager = Depends(get_memory),
):
    """Manually trigger summarization (for testing/admin)."""
    if not hasattr(memory, 'context_manager'):
        raise HTTPException(status_code=400, detail="Context manager not available")
        
    context_manager = memory.context_manager
    summary = await context_manager._background_summarize_session(session_id)
    
    return {"message": "Summarization completed", "session_id": session_id}
```

---

## Configuration Changes

### Update `src/config.py`:
```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Context management settings
    CONTEXT_SUMMARIZATION_INTERVAL_MINUTES: int = 30
    CONTEXT_MAX_ACTIVE_SUMMARIES: int = 5
    CONTEXT_ACTIVE_WINDOW_MAX_MESSAGES: int = 25
    CONTEXT_ACTIVE_WINDOW_MAX_TOKENS: int = 2000
    CONTEXT_ADAPTIVE_WINDOW_SIZING: bool = True
    CONTEXT_CLEANUP_DAYS: int = 7
```

---

## Error Handling and Edge Cases

### 1. Summarization Failures
```python
# In context/manager.py
async def _background_summarize_session(self, session_id: str) -> None:
    """Background task with comprehensive error handling."""
    try:
        # Main summarization logic...
        pass
    except Exception as e:
        logger.error(f"Summarization failed for {session_id}: {e}")
        
        # Fallback: Simple text truncation summary
        try:
            await self._create_fallback_summary(session_id)
        except Exception as fallback_error:
            logger.critical(f"Fallback summarization failed: {fallback_error}")
            
            # Last resort: Mark as failed and continue
            await self._mark_summarization_failed(session_id)
```

### 2. Context Corruption Recovery
```python
async def _recover_corrupted_context(self, session_id: str) -> TutoringContext:
    """Recover from corrupted context data."""
    logger.warning(f"Attempting context recovery for {session_id}")
    
    # Try to rebuild from conversation history
    basic_history = await self.memory.get_conversation_history(session_id)
    
    # Create minimal context
    context = TutoringContext(
        session_id=session_id,
        student_id="recovered",
        active_messages=[
            AnnotatedMessage(
                role=msg.get("role", "user"),
                content=msg.get("content", ""),
                timestamp=datetime.fromisoformat(msg.get("timestamp", datetime.now().isoformat())),
                token_count=len(msg.get("content", "")) // 4
            )
            for msg in basic_history[-20:]  # Last 20 messages
        ]
    )
    
    return context
```

### 3. Token Limit Overflow Protection
```python
def _enforce_hard_token_limit(self, context: TutoringContext, max_tokens: int = 8000) -> TutoringContext:
    """Emergency token limit enforcement."""
    if context.total_token_estimate <= max_tokens:
        return context
        
    logger.warning(f"Context exceeds {max_tokens} tokens, applying emergency truncation")
    
    # Aggressive truncation strategy
    # 1. Reduce active messages to minimum
    context.active_messages = context.active_messages[-10:]  # Keep only last 10
    
    # 2. Reduce session summaries
    context.session_summaries = context.session_summaries[-2:]  # Keep only last 2
    
    # 3. Reduce topic knowledge to most relevant
    if len(context.topic_mastery) > 20:
        # Keep top 20 by mastery score
        sorted_topics = sorted(
            context.topic_mastery.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        context.topic_mastery = dict(sorted_topics[:20])
    
    # Recalculate token estimate
    context.total_token_estimate = context.estimate_tokens()
    
    return context
```

---

## Testing Strategy

### Unit Tests
```python
# tests/test_context/test_manager.py
import pytest
from src.context.manager import ContextManager
from src.context.schemas import AnnotatedMessage, MessageAnnotation

@pytest.mark.asyncio
async def test_context_window_management():
    """Test that context window stays within token limits."""
    # Setup
    context_manager = ContextManager(memory_manager=mock_memory)
    
    # Add many messages
    for i in range(100):
        await context_manager.add_message_with_annotation(
            "test_session", "user", f"Message {i} with some content"
        )
    
    # Verify window size constraint
    context = await context_manager.get_tutoring_context("test_session")
    assert context.total_token_estimate < 5000
    assert len(context.active_messages) <= 25

@pytest.mark.asyncio  
async def test_summarization_trigger():
    """Test that summarization is triggered at appropriate intervals."""
    # Setup session with 40 messages
    # Verify summarization task is created
    # Check that summary is stored in PostgreSQL

@pytest.mark.asyncio
async def test_context_recovery():
    """Test recovery from corrupted context data."""
    # Simulate corrupted Redis data
    # Verify system can recover minimal context
    # Ensure tutoring can continue
```

### Integration Tests
```python
# tests/integration/test_context_integration.py
@pytest.mark.asyncio
async def test_full_tutoring_session_with_context():
    """Test complete tutoring session with context management."""
    # Simulate 2-hour tutoring session (200+ messages)
    # Verify context is maintained throughout
    # Check that summaries are created
    # Ensure session can be resumed
```

---

## Performance Benchmarks

### Target Metrics
- **Context Retrieval Time**: < 100ms for complete tutoring context
- **Summarization Time**: < 30 seconds for 40-message window  
- **Token Budget Accuracy**: ±10% of actual token usage
- **Memory Usage**: < 50MB Redis memory per active session
- **Database Growth**: < 1MB per day per active student

### Monitoring
```python
# Add to context/manager.py
import time
import logging
from src.monitoring import metrics

async def get_tutoring_context(self, session_id: str) -> TutoringContext:
    """Build complete tutoring context with performance monitoring."""
    start_time = time.time()
    
    try:
        # ... context building logic ...
        
        # Record metrics
        metrics.record_timing("context.build_time", time.time() - start_time)
        metrics.record_gauge("context.token_estimate", context.total_token_estimate)
        metrics.record_gauge("context.active_messages", len(context.active_messages))
        
        return context
    except Exception as e:
        metrics.record_counter("context.build_errors")
        raise
```

---

## Deployment Considerations

### 1. Migration Strategy
```bash
# Deploy new context system alongside existing system
# Gradually migrate sessions to new system
# Monitor performance and rollback if needed

# Phase 1: Deploy code with feature flag OFF
CONTEXT_V2_ENABLED=false

# Phase 2: Enable for 10% of sessions
CONTEXT_V2_ENABLED=true
CONTEXT_V2_ROLLOUT_PERCENTAGE=10

# Phase 3: Full rollout
CONTEXT_V2_ROLLOUT_PERCENTAGE=100
```

### 2. Resource Scaling
```yaml
# Redis memory scaling
redis:
  memory_limit: 2GB  # Up from 1GB
  max_connections: 200

# PostgreSQL storage
postgres:
  storage_increase: +500GB  # For context summaries
  
# Background workers for summarization
summarization_workers: 3
```

### 3. Monitoring and Alerting
```yaml
alerts:
  - name: "Context Build Latency High"
    condition: "context.build_time > 200ms"
    action: "Scale Redis cluster"
    
  - name: "Summarization Queue Backlog" 
    condition: "summarization.queue_size > 10"
    action: "Scale background workers"
    
  - name: "Token Estimate Accuracy Low"
    condition: "abs(context.token_estimate - actual_tokens) > context.token_estimate * 0.2"
    action: "Review token estimation algorithm"
```

---

This comprehensive context management system will enable EduAGI to maintain rich educational context across hours of conversation while staying within LLM token limits. The three-tier architecture provides both immediate responsiveness and long-term learning continuity.