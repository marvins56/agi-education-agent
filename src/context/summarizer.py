"""Educational summarization for context management."""
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

from langchain_core.prompts import PromptTemplate

from src.context.schemas import (
    AnnotatedMessage, 
    EducationalSummary, 
    SummaryType,
    MessageAnnotation
)
from src.llm.factory import LLMFactory

logger = logging.getLogger(__name__)


class EducationalSummarizer:
    """Creates intelligent educational summaries of conversation segments."""
    
    SUMMARIZATION_PROMPT = PromptTemplate.from_template("""
You are an expert educational analyst. Analyze this tutoring conversation segment and create a structured educational summary.

CONVERSATION SEGMENT:
{conversation_text}

SESSION INFO:
- Session ID: {session_id}
- Student ID: {student_id} 
- Time Range: {start_time} to {end_time}
- Message Count: {message_count}

ANALYSIS REQUIREMENTS:
Create a JSON summary with these exact fields:

{{
    "concepts_discussed": ["concept1", "concept2"],
    "mastery_assessments": {{"concept1": 0.8, "concept2": 0.3}},
    "misconceptions_identified": ["specific misconception descriptions"],
    "breakthrough_moments": ["descriptions of learning breakthroughs"],
    "effective_strategies": ["teaching approaches that worked well"],
    "ineffective_approaches": ["teaching approaches that didn't work"],
    "student_engagement_level": 0.75,
    "suggested_next_topics": ["topics to explore next"],
    "recommended_teaching_approach": "description of best approach for this student"
}}

SCORING GUIDELINES:
- mastery_assessments: 0.0-1.0 where 1.0 = complete mastery
- student_engagement_level: 0.0-1.0 where 1.0 = highly engaged
- Focus on educational insights, not just conversation summary
- Be specific about concepts and strategies

Return only the JSON object, no additional text.
""")
    
    def __init__(self):
        self.llm_factory = LLMFactory()
        self.llm = None
    
    async def _get_llm(self):
        """Lazy load LLM to avoid initialization issues."""
        if self.llm is None:
            self.llm = await self.llm_factory.create_llm("anthropic", "claude-3-sonnet-20240229")
        return self.llm
    
    async def create_educational_summary(
        self, 
        messages: List[AnnotatedMessage],
        session_id: str,
        student_id: str,
        summary_type: SummaryType = SummaryType.PROGRESS
    ) -> EducationalSummary:
        """Create an educational summary from conversation messages."""
        
        if not messages:
            logger.warning("No messages provided for summarization")
            return self._empty_summary(session_id, student_id, summary_type)
        
        # Prepare conversation text
        conversation_text = self._format_conversation_for_analysis(messages)
        
        # Time range
        start_time = messages[0].timestamp
        end_time = messages[-1].timestamp
        
        # Token count
        total_tokens = sum(msg.token_count for msg in messages)
        
        # Create summary using LLM
        llm = await self._get_llm()
        
        try:
            prompt = self.SUMMARIZATION_PROMPT.format(
                conversation_text=conversation_text,
                session_id=session_id,
                student_id=student_id,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                message_count=len(messages)
            )
            
            response = await llm.ainvoke(prompt)
            
            # Parse JSON response
            summary_data = json.loads(response.content)
            
            # Create educational summary
            summary = EducationalSummary(
                summary_type=summary_type,
                session_id=session_id,
                student_id=student_id,
                time_range=(start_time, end_time),
                message_count=len(messages),
                total_tokens=total_tokens,
                **summary_data
            )
            
            logger.info(f"Created {summary_type} summary for session {session_id}")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to create educational summary: {e}")
            return self._empty_summary(session_id, student_id, summary_type)
    
    def _format_conversation_for_analysis(self, messages: List[AnnotatedMessage]) -> str:
        """Format messages for LLM analysis with annotations."""
        formatted_messages = []
        
        for msg in messages:
            # Basic message
            msg_text = f"{msg.role.upper()}: {msg.content}"
            
            # Add annotations if present
            if msg.annotations:
                annotation_texts = []
                for ann in msg.annotations:
                    concepts_str = ", ".join(ann.concepts) if ann.concepts else "general"
                    annotation_texts.append(
                        f"[{ann.type.upper()}: {concepts_str} (confidence: {ann.confidence:.2f})]"
                    )
                msg_text += " " + " ".join(annotation_texts)
            
            formatted_messages.append(msg_text)
        
        return "\n\n".join(formatted_messages)
    
    def _empty_summary(
        self, 
        session_id: str, 
        student_id: str, 
        summary_type: SummaryType
    ) -> EducationalSummary:
        """Create empty summary as fallback."""
        now = datetime.now(timezone.utc)
        return EducationalSummary(
            summary_type=summary_type,
            session_id=session_id,
            student_id=student_id,
            time_range=(now, now),
            message_count=0,
            total_tokens=0,
            student_engagement_level=0.0
        )
    
    async def analyze_message_for_annotations(
        self, 
        message_content: str,
        conversation_context: List[AnnotatedMessage]
    ) -> List[MessageAnnotation]:
        """Analyze a message and generate educational annotations."""
        
        ANNOTATION_PROMPT = PromptTemplate.from_template("""
Analyze this student message in context and identify educational annotations.

RECENT CONVERSATION CONTEXT:
{context}

CURRENT MESSAGE TO ANALYZE:
"{message}"

Identify educational markers in this message. Return a JSON array of annotations:

[
    {{
        "type": "confusion|breakthrough|misconception|mastery|question|insight",
        "confidence": 0.85,
        "concepts": ["concept_name1", "concept_name2"]
    }}
]

ANNOTATION TYPES:
- confusion: Student shows confusion or uncertainty
- breakthrough: Student has an "aha" moment or understanding
- misconception: Student displays a misunderstanding
- mastery: Student demonstrates solid understanding
- question: Student asks a meaningful question
- insight: Student shows deeper thinking or connections

Only include annotations with confidence > 0.6. Return empty array [] if no clear markers found.
""")
        
        try:
            # Format context (last 5 messages)
            context_messages = conversation_context[-5:] if conversation_context else []
            context_text = "\n".join([
                f"{msg.role}: {msg.content}" for msg in context_messages
            ])
            
            llm = await self._get_llm()
            
            prompt = ANNOTATION_PROMPT.format(
                context=context_text,
                message=message_content
            )
            
            response = await llm.ainvoke(prompt)
            annotations_data = json.loads(response.content)
            
            # Convert to MessageAnnotation objects
            annotations = []
            for ann_data in annotations_data:
                annotation = MessageAnnotation(
                    type=ann_data["type"],
                    confidence=ann_data["confidence"],
                    concepts=ann_data.get("concepts", []),
                    timestamp=datetime.now(timezone.utc)
                )
                annotations.append(annotation)
            
            return annotations
            
        except Exception as e:
            logger.warning(f"Failed to generate annotations: {e}")
            return []