"""Advanced workflow orchestrator using LangGraph state machines."""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from src.workflows.base import BaseWorkflow
from src.workflows.intent_classifier import IntentClassifier
from src.workflows.state import WorkflowType, WorkflowResult, StudentIntent
from src.workflows.flows.concept_explanation import ConceptExplanationFlow
from src.context.schemas import TutoringContext
from src.agents.base import AgentContext, AgentResponse

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """Orchestrates educational workflows using LangGraph state machines."""
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.workflows: Dict[WorkflowType, BaseWorkflow] = {}
        
        # Initialize available workflows
        self._initialize_workflows()
        
        # Workflow selection strategy
        self.workflow_selection_strategies = {
            StudentIntent.NEW_TOPIC: self._select_new_topic_workflow,
            StudentIntent.CLARIFICATION: self._select_clarification_workflow,
            StudentIntent.PRACTICE: self._select_practice_workflow,
            StudentIntent.ASSESSMENT: self._select_assessment_workflow,
            StudentIntent.REVIEW: self._select_review_workflow,
            StudentIntent.HELP_STUCK: self._select_help_stuck_workflow,
            StudentIntent.CASUAL: self._select_casual_workflow,
            StudentIntent.META_LEARNING: self._select_meta_learning_workflow
        }
    
    def _initialize_workflows(self):
        """Initialize available workflow implementations."""
        self.workflows = {
            WorkflowType.CONCEPT_EXPLANATION: ConceptExplanationFlow(),
            # Additional workflows will be added as they are implemented
            # WorkflowType.SOCRATIC_QUESTIONING: SocraticQuestioningFlow(),
            # WorkflowType.PRACTICE_PROBLEMS: PracticeProblemsFlow(),
            # WorkflowType.ASSESSMENT_FLOW: AssessmentFlow(),
            # WorkflowType.REVIEW_SESSION: ReviewSessionFlow(),
        }
        
        logger.info(f"Initialized {len(self.workflows)} workflows")
    
    async def process(
        self, 
        message: str, 
        context: AgentContext,
        tutoring_context: Optional[TutoringContext] = None
    ) -> AgentResponse:
        """Process a message through the appropriate workflow."""
        
        try:
            # If no tutoring context provided, create a basic one
            if tutoring_context is None:
                tutoring_context = self._create_basic_tutoring_context(context)
            
            # Classify student intent
            intent_classification = await self.intent_classifier.classify_intent(
                message, tutoring_context
            )
            
            student_intent = StudentIntent(intent_classification["primary_intent"])
            confidence = intent_classification["confidence"]
            
            logger.info(
                f"Classified intent: {student_intent.value} "
                f"(confidence: {confidence:.2f})"
            )
            
            # Select appropriate workflow
            workflow_type = await self._select_workflow(
                student_intent, 
                intent_classification,
                tutoring_context
            )
            
            # Execute workflow
            if workflow_type in self.workflows:
                workflow_result = await self._execute_workflow(
                    workflow_type,
                    message,
                    tutoring_context,
                    intent_classification
                )
                
                # Convert workflow result to agent response
                agent_response = await self._convert_to_agent_response(
                    workflow_result, 
                    context
                )
                
                logger.info(
                    f"Completed {workflow_type.value} workflow. "
                    f"Engagement: {workflow_result.engagement_score:.2f}"
                )
                
                return agent_response
                
            else:
                # Fallback to simple response if workflow not implemented
                return await self._fallback_response(message, context)
                
        except Exception as e:
            logger.error(f"Workflow orchestration failed: {e}")
            return await self._error_response(str(e), context)
    
    async def _select_workflow(
        self,
        student_intent: StudentIntent,
        intent_classification: Dict[str, Any],
        tutoring_context: TutoringContext
    ) -> WorkflowType:
        """Select the most appropriate workflow for the student's intent."""
        
        # Use intent-specific selection strategy
        if student_intent in self.workflow_selection_strategies:
            strategy = self.workflow_selection_strategies[student_intent]
            return await strategy(intent_classification, tutoring_context)
        else:
            # Default to concept explanation
            return WorkflowType.CONCEPT_EXPLANATION
    
    async def _select_new_topic_workflow(
        self, 
        intent_classification: Dict[str, Any],
        tutoring_context: TutoringContext
    ) -> WorkflowType:
        """Select workflow for new topic requests."""
        
        # Check if this is a history-specific request
        topic_keywords = intent_classification.get("topic_keywords", [])
        
        if any(keyword in ["timeline", "chronology", "sequence"] for keyword in topic_keywords):
            return WorkflowType.HISTORY_TIMELINE  # When implemented
        elif any(keyword in ["source", "document", "primary"] for keyword in topic_keywords):
            return WorkflowType.SOURCE_ANALYSIS  # When implemented
        else:
            return WorkflowType.CONCEPT_EXPLANATION
    
    async def _select_clarification_workflow(
        self,
        intent_classification: Dict[str, Any],
        tutoring_context: TutoringContext
    ) -> WorkflowType:
        """Select workflow for clarification requests."""
        
        # Use Socratic questioning to guide understanding
        return WorkflowType.SOCRATIC_QUESTIONING  # When implemented, fallback to concept explanation
    
    async def _select_practice_workflow(
        self,
        intent_classification: Dict[str, Any],
        tutoring_context: TutoringContext
    ) -> WorkflowType:
        """Select workflow for practice requests."""
        
        return WorkflowType.PRACTICE_PROBLEMS  # When implemented, fallback to concept explanation
    
    async def _select_assessment_workflow(
        self,
        intent_classification: Dict[str, Any],
        tutoring_context: TutoringContext
    ) -> WorkflowType:
        """Select workflow for assessment requests."""
        
        return WorkflowType.ASSESSMENT_FLOW  # When implemented, fallback to concept explanation
    
    async def _select_review_workflow(
        self,
        intent_classification: Dict[str, Any],
        tutoring_context: TutoringContext
    ) -> WorkflowType:
        """Select workflow for review requests."""
        
        return WorkflowType.REVIEW_SESSION  # When implemented, fallback to concept explanation
    
    async def _select_help_stuck_workflow(
        self,
        intent_classification: Dict[str, Any], 
        tutoring_context: TutoringContext
    ) -> WorkflowType:
        """Select workflow for when student is stuck."""
        
        # Use Socratic questioning to help them work through it
        return WorkflowType.SOCRATIC_QUESTIONING  # When implemented, fallback to concept explanation
    
    async def _select_casual_workflow(
        self,
        intent_classification: Dict[str, Any],
        tutoring_context: TutoringContext
    ) -> WorkflowType:
        """Select workflow for casual conversation."""
        
        # Keep it educational with concept explanation
        return WorkflowType.CONCEPT_EXPLANATION
    
    async def _select_meta_learning_workflow(
        self,
        intent_classification: Dict[str, Any],
        tutoring_context: TutoringContext
    ) -> WorkflowType:
        """Select workflow for meta-learning questions."""
        
        # Concept explanation can handle learning strategy discussions
        return WorkflowType.CONCEPT_EXPLANATION
    
    async def _execute_workflow(
        self,
        workflow_type: WorkflowType,
        message: str,
        tutoring_context: TutoringContext,
        intent_classification: Dict[str, Any]
    ) -> WorkflowResult:
        """Execute the selected workflow."""
        
        # Get workflow implementation (fallback to concept explanation if not available)
        workflow = self.workflows.get(workflow_type, self.workflows[WorkflowType.CONCEPT_EXPLANATION])
        
        # Prepare workflow-specific kwargs
        workflow_kwargs = {
            "intent_classification": intent_classification,
            "subject": tutoring_context.learning_patterns.get("subject", "History")
        }
        
        # Add concept name for concept explanation workflow
        if workflow_type == WorkflowType.CONCEPT_EXPLANATION:
            workflow_kwargs["concept_name"] = self._extract_concept_name(
                message, intent_classification
            )
        
        # Execute the workflow
        result = await workflow.execute(
            message=message,
            tutoring_context=tutoring_context,
            thread_id=f"{tutoring_context.session_id}_{workflow_type.value}",
            **workflow_kwargs
        )
        
        return result
    
    def _extract_concept_name(self, message: str, intent_classification: Dict[str, Any]) -> str:
        """Extract concept name from message and intent classification."""
        
        # Try to get from topic keywords
        topic_keywords = intent_classification.get("topic_keywords", [])
        if topic_keywords:
            return " ".join(topic_keywords).title()
        
        # Try to extract from message patterns
        message_lower = message.lower()
        
        if "tell me about" in message_lower:
            parts = message_lower.split("tell me about")
            if len(parts) > 1:
                return parts[1].strip().split("?")[0].strip().title()
        
        if "what is" in message_lower:
            parts = message_lower.split("what is")
            if len(parts) > 1:
                return parts[1].strip().split("?")[0].strip().title()
        
        # Default concept name
        return "Historical Topic"
    
    async def _convert_to_agent_response(
        self,
        workflow_result: WorkflowResult,
        context: AgentContext
    ) -> AgentResponse:
        """Convert workflow result to agent response format."""
        
        # Extract the final tutor message from workflow
        final_state = workflow_result.final_state
        messages = final_state.get("messages", [])
        
        # Get the last assistant message
        tutor_messages = [msg for msg in messages if msg.get("role") == "assistant"]
        response_content = tutor_messages[-1]["content"] if tutor_messages else "I'm here to help you learn!"
        
        # Create metadata about the workflow execution
        metadata = {
            "workflow_type": workflow_result.workflow_type.value,
            "engagement_score": workflow_result.engagement_score,
            "concepts_mastered": workflow_result.concepts_mastered,
            "learning_outcomes": workflow_result.learning_outcomes,
            "time_spent_minutes": workflow_result.time_spent_minutes,
            "next_recommended_actions": workflow_result.next_recommended_actions
        }
        
        return AgentResponse(
            text=response_content,
            agent_name="WorkflowTutor",
            metadata=metadata,
            suggested_actions=workflow_result.next_recommended_actions
        )
    
    def _create_basic_tutoring_context(self, context: AgentContext) -> TutoringContext:
        """Create a basic tutoring context if none provided."""
        from src.context.schemas import TutoringContext
        
        return TutoringContext(
            session_id=context.session_id,
            student_id=context.student_id,
            active_messages=[],
            session_summaries=[],
            topic_mastery={},
            learning_patterns={"subject": "History"},
            effective_teaching_methods=[]
        )
    
    async def _fallback_response(self, message: str, context: AgentContext) -> AgentResponse:
        """Fallback response when workflow is not available."""
        
        return AgentResponse(
            text="I understand you're asking about that topic. Let me help you learn about it! "
                    "Could you tell me more specifically what you'd like to understand?",
            agent_name="WorkflowTutor",
            metadata={"fallback": True}
        )
    
    async def _error_response(self, error_message: str, context: AgentContext) -> AgentResponse:
        """Response when an error occurs."""
        
        return AgentResponse(
            text="I'm sorry, I encountered an issue while trying to help you. "
                    "Let's try again - what would you like to learn about?",
            agent_name="WorkflowTutor",
            metadata={"error": error_message}
        )
    
    async def get_available_workflows(self) -> List[WorkflowType]:
        """Get list of available workflow types."""
        return list(self.workflows.keys())
    
    async def get_workflow_info(self, workflow_type: WorkflowType) -> Dict[str, Any]:
        """Get information about a specific workflow."""
        
        if workflow_type not in self.workflows:
            return {"error": f"Workflow {workflow_type.value} not available"}
        
        workflow = self.workflows[workflow_type]
        
        return {
            "workflow_type": workflow_type.value,
            "description": workflow.__doc__ or "Educational workflow",
            "available": True,
            "class": workflow.__class__.__name__
        }