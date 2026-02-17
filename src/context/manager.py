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
    
    async def add_message_with_auto_annotation(
        self, 
        session_id: str, 
        role: str, 
        content: str
    ) -> None:
        """Add message and automatically generate educational annotations."""
        
        # Get recent context for annotation
        recent_messages = await self._get_active_window_messages(session_id)
        
        # Generate annotations for student messages
        annotations = []
        if role == "user":  # Only annotate student messages
            annotations = await self.summarizer.analyze_message_for_annotations(
                content, recent_messages
            )
        
        await self.add_message_with_annotation(session_id, role, content, annotations)
    
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
        if not hasattr(self.memory, 'db_session_factory') or not self.memory.db_session_factory:
            return []
            
        try:
            from src.models.database import get_db_session
            from sqlalchemy import text
            
            async with get_db_session() as db_session:
                # Query context summaries table  
                stmt = text("""
                    SELECT summary_data, created_at 
                    FROM context_summaries 
                    WHERE session_id = :session_id 
                    ORDER BY created_at DESC 
                    LIMIT 10
                """)
                result = await db_session.execute(stmt, {"session_id": session_id})
                rows = result.fetchall()
                
                summaries = []
                for row in rows:
                    try:
                        summary_data = json.loads(row[0])
                        summary = EducationalSummary(**summary_data)
                        summaries.append(summary)
                    except Exception as e:
                        logger.warning(f"Failed to parse summary: {e}")
                        
                return summaries
                
        except Exception as e:
            logger.warning(f"Failed to get session summaries: {e}")
            return []
    
    async def _get_topic_knowledge(self, student_id: str) -> tuple[Dict[str, float], Dict[str, Any]]:
        """Get topic mastery and learning patterns from long-term memory."""
        # Get mastery data from PostgreSQL
        try:
            mastery_data = await self.memory.get_student_mastery(student_id)
            topic_mastery = {
                record["topic"]: record["mastery_score"] 
                for record in mastery_data
            }
        except Exception as e:
            logger.warning(f"Failed to get mastery data: {e}")
            topic_mastery = {}
        
        # Get learning patterns from ChromaDB
        learning_patterns = await self._get_learning_patterns(student_id)
        
        return topic_mastery, learning_patterns
    
    async def _get_learning_patterns(self, student_id: str) -> Dict[str, Any]:
        """Query learning patterns from ChromaDB."""
        try:
            if hasattr(self.memory, 'search_knowledge'):
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
            else:
                return {}
        except Exception as e:
            logger.warning(f"Failed to get learning patterns: {e}")
            return {}
    
    async def _store_annotated_message(self, session_id: str, message: AnnotatedMessage) -> None:
        """Store annotated message in Redis."""
        key = f"session:{session_id}:annotated_messages"
        message_json = message.model_dump_json()
        
        await self.memory._redis.rpush(key, message_json)
        await self.memory._redis.ltrim(key, -50, -1)  # Keep last 50 for safety
        await self.memory._redis.expire(key, 86400 * 7)  # 7 day expiry
        
        logger.debug(f"Stored annotated message for session {session_id}")
    
    async def _maybe_trigger_summarization(self, session_id: str) -> None:
        """Check if we need to trigger summarization."""
        
        # Check if already running summarization for this session
        if session_id in self._summarization_tasks:
            if not self._summarization_tasks[session_id].done():
                return  # Already running
        
        # Check time-based trigger
        last_summary_time = await self._get_last_summary_time(session_id)
        now = datetime.now(timezone.utc)
        
        if last_summary_time:
            time_diff = (now - last_summary_time).total_seconds() / 60
            if time_diff < self.summarization_interval:
                # Check if window pressure forces summarization
                force_summarize = await self.window.force_summarization_trigger(
                    session_id, self.memory
                )
                if not force_summarize:
                    return
        
        # Trigger background summarization
        task = asyncio.create_task(self._background_summarization(session_id))
        self._summarization_tasks[session_id] = task
        
        logger.info(f"Triggered summarization for session {session_id}")
    
    async def _background_summarization(self, session_id: str) -> None:
        """Background task to create and store session summary."""
        try:
            # Get messages for summarization
            messages = await self._get_active_window_messages(session_id)
            
            if len(messages) < 3:  # Need minimum conversation for summary
                return
            
            # Get student ID
            context_data = await self.memory.get_session_context(session_id)
            student_id = context_data.get("student_id", "unknown") if context_data else "unknown"
            
            # Create educational summary
            summary = await self.summarizer.create_educational_summary(
                messages=messages,
                session_id=session_id,
                student_id=student_id,
                summary_type=SummaryType.PROGRESS
            )
            
            # Store summary in PostgreSQL
            await self._store_educational_summary(summary)
            
            logger.info(f"Completed background summarization for session {session_id}")
            
        except Exception as e:
            logger.error(f"Background summarization failed for {session_id}: {e}")
        finally:
            # Clean up task reference
            if session_id in self._summarization_tasks:
                del self._summarization_tasks[session_id]
    
    async def _store_educational_summary(self, summary: EducationalSummary) -> None:
        """Store educational summary in PostgreSQL."""
        try:
            from src.models.database import get_db_session
            from sqlalchemy import text
            
            summary_json = summary.model_dump_json()
            
            async with get_db_session() as db_session:
                stmt = text("""
                    INSERT INTO context_summaries (
                        session_id, student_id, summary_type, 
                        summary_data, created_at
                    ) VALUES (
                        :session_id, :student_id, :summary_type,
                        :summary_data, :created_at
                    )
                """)
                
                await db_session.execute(stmt, {
                    "session_id": summary.session_id,
                    "student_id": summary.student_id,
                    "summary_type": summary.summary_type.value,
                    "summary_data": summary_json,
                    "created_at": summary.created_at
                })
                await db_session.commit()
                
            logger.debug(f"Stored educational summary for session {summary.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to store educational summary: {e}")
    
    async def _get_last_summary_time(self, session_id: str) -> Optional[datetime]:
        """Get timestamp of last summary for this session."""
        try:
            from src.models.database import get_db_session
            from sqlalchemy import text
            
            async with get_db_session() as db_session:
                stmt = text("""
                    SELECT created_at 
                    FROM context_summaries 
                    WHERE session_id = :session_id 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """)
                result = await db_session.execute(stmt, {"session_id": session_id})
                row = result.fetchone()
                
                return row[0] if row else None
                
        except Exception as e:
            logger.warning(f"Failed to get last summary time: {e}")
            return None
    
    def _estimate_message_tokens(self, content: str) -> int:
        """Rough token estimation for message content."""
        # Approximate: 4 characters per token
        return max(1, len(content) // 4)
    
    async def cleanup_old_summaries(self, retention_days: int = 30) -> int:
        """Clean up old educational summaries."""
        try:
            from src.models.database import get_db_session
            from sqlalchemy import text
            
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
            
            async with get_db_session() as db_session:
                stmt = text("""
                    DELETE FROM context_summaries 
                    WHERE created_at < :cutoff_date
                """)
                result = await db_session.execute(stmt, {"cutoff_date": cutoff_date})
                await db_session.commit()
                
                deleted_count = result.rowcount
                logger.info(f"Cleaned up {deleted_count} old context summaries")
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old summaries: {e}")
            return 0