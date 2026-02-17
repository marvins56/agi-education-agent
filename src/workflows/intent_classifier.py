"""Intent classification for educational conversations."""
import json
import logging
from typing import List, Dict, Any, Optional
from langchain_core.prompts import PromptTemplate

from src.workflows.state import StudentIntent, WorkflowType
from src.llm.factory import LLMFactory
from src.context.schemas import TutoringContext

logger = logging.getLogger(__name__)


class IntentClassifier:
    """Classifies student intents to route to appropriate workflows."""
    
    INTENT_CLASSIFICATION_PROMPT = PromptTemplate.from_template("""
You are an expert educational AI that analyzes student messages to determine their learning intent.

STUDENT MESSAGE: "{message}"

CONVERSATION CONTEXT:
Recent messages:
{recent_conversation}

EDUCATIONAL CONTEXT:
- Current topic: {current_topic}
- Subject: {subject}
- Student's prior knowledge level: {knowledge_level}/10
- Recently covered concepts: {recent_concepts}
- Current engagement level: {engagement_level}/10

CLASSIFICATION TASK:
Analyze the student's message and classify their intent. Return a JSON object with:

{{
    "primary_intent": "one of: new_topic, clarification, practice, assessment, review, help_stuck, casual, meta_learning",
    "confidence": 0.85,
    "reasoning": "explanation of why this intent was chosen",
    "suggested_workflow": "concept_explanation|socratic_questioning|practice_problems|assessment_flow|review_session|history_timeline|source_analysis|cause_effect_analysis|dbq_essay",
    "urgency": "low|medium|high",
    "educational_markers": ["confused", "ready_for_challenge", "needs_scaffolding", "showing_insight"],
    "topic_keywords": ["keyword1", "keyword2"]
}}

INTENT DEFINITIONS:
- new_topic: Student asks about something they haven't learned yet
- clarification: Student doesn't understand current explanation/concept  
- practice: Student wants to try problems or apply knowledge
- assessment: Student wants to test their knowledge or be quizzed
- review: Student wants to go over previous material
- help_stuck: Student is stuck on a specific problem
- casual: General conversation, not directly educational
- meta_learning: Questions about how to learn or study

URGENCY LEVELS:
- high: Student is frustrated, confused, or explicitly asking for help
- medium: Student has a specific learning goal or question
- low: Casual exploration or general interest

Return only the JSON object, no additional text.
""")
    
    def __init__(self):
        self.llm_factory = LLMFactory()
        self.llm = None
        
        # Pattern-based fallbacks for when LLM is unavailable
        self.intent_patterns = {
            StudentIntent.NEW_TOPIC: [
                "what is", "tell me about", "explain", "how does", "what are",
                "I want to learn", "can you teach me"
            ],
            StudentIntent.CLARIFICATION: [
                "I don't understand", "confused", "what do you mean", "can you explain again",
                "I'm not sure", "clarify", "unclear"
            ],
            StudentIntent.PRACTICE: [
                "practice", "try", "exercise", "problem", "quiz", "test me",
                "can I do", "give me"
            ],
            StudentIntent.ASSESSMENT: [
                "test my knowledge", "assess me", "evaluate", "grade", "how well do I know",
                "am I ready"
            ],
            StudentIntent.REVIEW: [
                "review", "go over", "remind me", "what did we cover",
                "summary", "recap"
            ],
            StudentIntent.HELP_STUCK: [
                "stuck", "help", "hint", "I can't", "don't know how",
                "having trouble"
            ]
        }
    
    async def _get_llm(self):
        """Lazy load LLM to avoid initialization issues."""
        if self.llm is None:
            self.llm = await self.llm_factory.create_llm("anthropic", "claude-3-sonnet-20240229")
        return self.llm
    
    async def classify_intent(
        self, 
        message: str,
        tutoring_context: TutoringContext
    ) -> Dict[str, Any]:
        """Classify student intent from message and context."""
        
        try:
            # Prepare context data
            recent_conversation = self._format_recent_conversation(
                tutoring_context.active_messages[-5:] if tutoring_context.active_messages else []
            )
            
            current_topic = tutoring_context.learning_patterns.get("current_topic", "Unknown")
            subject = tutoring_context.learning_patterns.get("subject", "History")
            
            # Calculate knowledge level (0-10 scale)
            avg_mastery = sum(tutoring_context.topic_mastery.values()) / len(tutoring_context.topic_mastery) if tutoring_context.topic_mastery else 0.5
            knowledge_level = int(avg_mastery * 10)
            
            recent_concepts = list(tutoring_context.topic_mastery.keys())[-3:] if tutoring_context.topic_mastery else []
            engagement_level = 7  # Default, could be enhanced with actual engagement tracking
            
            # Get LLM classification
            llm = await self._get_llm()
            
            prompt = self.INTENT_CLASSIFICATION_PROMPT.format(
                message=message,
                recent_conversation=recent_conversation,
                current_topic=current_topic,
                subject=subject,
                knowledge_level=knowledge_level,
                recent_concepts=", ".join(recent_concepts) if recent_concepts else "None",
                engagement_level=engagement_level
            )
            
            response = await llm.ainvoke(prompt)
            classification = json.loads(response.content)
            
            # Validate and enhance classification
            classification = self._validate_classification(classification)
            
            logger.info(f"Classified intent: {classification['primary_intent']} (confidence: {classification['confidence']})")
            
            return classification
            
        except Exception as e:
            logger.warning(f"LLM intent classification failed: {e}. Using fallback.")
            return await self._fallback_classification(message, tutoring_context)
    
    def _format_recent_conversation(self, messages) -> str:
        """Format recent messages for context."""
        if not messages:
            return "No recent conversation"
        
        formatted = []
        for msg in messages:
            role = "Student" if msg.role == "user" else "Tutor"
            formatted.append(f"{role}: {msg.content}")
        
        return "\n".join(formatted)
    
    def _validate_classification(self, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance LLM classification results."""
        
        # Ensure required fields
        if "primary_intent" not in classification:
            classification["primary_intent"] = StudentIntent.CASUAL.value
        
        if "confidence" not in classification:
            classification["confidence"] = 0.5
        
        # Validate intent value
        valid_intents = [intent.value for intent in StudentIntent]
        if classification["primary_intent"] not in valid_intents:
            classification["primary_intent"] = StudentIntent.CASUAL.value
            classification["confidence"] = 0.3
        
        # Ensure confidence is in range
        classification["confidence"] = max(0.0, min(1.0, classification["confidence"]))
        
        # Add defaults for missing fields
        classification.setdefault("urgency", "medium")
        classification.setdefault("educational_markers", [])
        classification.setdefault("topic_keywords", [])
        classification.setdefault("reasoning", "Automated classification")
        classification.setdefault("suggested_workflow", self._suggest_workflow_for_intent(classification["primary_intent"]))
        
        return classification
    
    def _suggest_workflow_for_intent(self, intent: str) -> str:
        """Suggest appropriate workflow for classified intent."""
        intent_to_workflow = {
            StudentIntent.NEW_TOPIC.value: WorkflowType.CONCEPT_EXPLANATION.value,
            StudentIntent.CLARIFICATION.value: WorkflowType.SOCRATIC_QUESTIONING.value,
            StudentIntent.PRACTICE.value: WorkflowType.PRACTICE_PROBLEMS.value,
            StudentIntent.ASSESSMENT.value: WorkflowType.ASSESSMENT_FLOW.value,
            StudentIntent.REVIEW.value: WorkflowType.REVIEW_SESSION.value,
            StudentIntent.HELP_STUCK.value: WorkflowType.SOCRATIC_QUESTIONING.value,
            StudentIntent.META_LEARNING.value: WorkflowType.CONCEPT_EXPLANATION.value,
            StudentIntent.CASUAL.value: WorkflowType.CONCEPT_EXPLANATION.value
        }
        
        return intent_to_workflow.get(intent, WorkflowType.CONCEPT_EXPLANATION.value)
    
    async def _fallback_classification(
        self, 
        message: str, 
        tutoring_context: TutoringContext
    ) -> Dict[str, Any]:
        """Pattern-based fallback when LLM is unavailable."""
        
        message_lower = message.lower()
        
        # Check patterns for each intent
        best_intent = StudentIntent.CASUAL
        best_score = 0
        
        for intent, patterns in self.intent_patterns.items():
            score = sum(1 for pattern in patterns if pattern in message_lower)
            if score > best_score:
                best_score = score
                best_intent = intent
        
        # Determine urgency based on keywords
        urgency = "medium"
        if any(word in message_lower for word in ["help", "stuck", "confused", "don't understand"]):
            urgency = "high"
        elif any(word in message_lower for word in ["just wondering", "curious", "maybe"]):
            urgency = "low"
        
        # Educational markers based on patterns
        educational_markers = []
        if "confused" in message_lower or "don't understand" in message_lower:
            educational_markers.append("confused")
        if "challenging" in message_lower or "harder" in message_lower:
            educational_markers.append("ready_for_challenge")
        if "help" in message_lower or "guide" in message_lower:
            educational_markers.append("needs_scaffolding")
        
        return {
            "primary_intent": best_intent.value,
            "confidence": 0.6 if best_score > 0 else 0.3,
            "reasoning": f"Pattern-based fallback classification (matched {best_score} patterns)",
            "suggested_workflow": self._suggest_workflow_for_intent(best_intent.value),
            "urgency": urgency,
            "educational_markers": educational_markers,
            "topic_keywords": self._extract_topic_keywords(message)
        }
    
    def _extract_topic_keywords(self, message: str) -> List[str]:
        """Extract potential topic keywords from message."""
        # Simple keyword extraction - could be enhanced with NLP
        history_keywords = [
            "revolution", "war", "battle", "empire", "constitution", "democracy",
            "slavery", "independence", "colonization", "treaty", "president",
            "ancient", "medieval", "renaissance", "enlightenment", "industrial"
        ]
        
        message_lower = message.lower()
        found_keywords = [kw for kw in history_keywords if kw in message_lower]
        
        return found_keywords