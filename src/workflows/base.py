"""Base workflow classes for educational flows."""
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.workflows.state import WorkflowState, WorkflowType, WorkflowResult, LearningPhase
from src.context.schemas import TutoringContext
from src.llm.factory import LLMFactory

logger = logging.getLogger(__name__)


class BaseWorkflow(ABC):
    """Base class for all educational workflows."""
    
    def __init__(self, workflow_type: WorkflowType):
        self.workflow_type = workflow_type
        self.llm_factory = LLMFactory()
        self.llm = None
        self.graph: Optional[StateGraph] = None
        self.checkpointer = MemorySaver()
        
        # Build the workflow graph
        self._build_graph()
    
    @abstractmethod
    def _build_graph(self) -> None:
        """Build the LangGraph state machine for this workflow."""
        pass
    
    @abstractmethod
    async def initialize_state(
        self, 
        message: str,
        tutoring_context: TutoringContext,
        **kwargs
    ) -> WorkflowState:
        """Initialize the workflow state."""
        pass
    
    async def _get_llm(self):
        """Lazy load LLM to avoid initialization issues."""
        if self.llm is None:
            self.llm = await self.llm_factory.create_llm("anthropic", "claude-3-sonnet-20240229")
        return self.llm
    
    async def execute(
        self, 
        message: str,
        tutoring_context: TutoringContext,
        thread_id: str = None,
        **kwargs
    ) -> WorkflowResult:
        """Execute the workflow."""
        
        try:
            # Initialize state
            initial_state = await self.initialize_state(message, tutoring_context, **kwargs)
            
            # Configure thread ID for state persistence
            config = {"configurable": {"thread_id": thread_id or f"{tutoring_context.session_id}_{self.workflow_type.value}"}}
            
            # Execute the workflow
            final_state = await self.graph.ainvoke(initial_state, config=config)
            
            # Create result
            result = await self._create_workflow_result(final_state, tutoring_context)
            
            logger.info(f"Completed {self.workflow_type.value} workflow for session {tutoring_context.session_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return await self._create_error_result(e, tutoring_context)
    
    async def _create_workflow_result(
        self, 
        final_state: WorkflowState, 
        tutoring_context: TutoringContext
    ) -> WorkflowResult:
        """Create a WorkflowResult from the final state."""
        
        time_spent = (final_state["last_update_time"] - final_state["workflow_start_time"]).total_seconds() / 60
        
        return WorkflowResult(
            workflow_type=self.workflow_type,
            final_state=dict(final_state),
            learning_outcomes=final_state.get("concepts_covered", []),
            concepts_mastered=self._identify_mastered_concepts(final_state),
            engagement_score=final_state.get("engagement_level", 0.5),
            time_spent_minutes=time_spent,
            next_recommended_actions=self._recommend_next_actions(final_state),
            assessment_scores=self._extract_assessment_scores(final_state),
            areas_needing_work=final_state.get("misconceptions_identified", []),
            strengths_identified=final_state.get("breakthrough_moments", [])
        )
    
    async def _create_error_result(
        self, 
        error: Exception, 
        tutoring_context: TutoringContext
    ) -> WorkflowResult:
        """Create an error result when workflow fails."""
        
        return WorkflowResult(
            workflow_type=self.workflow_type,
            final_state={
                "error": str(error),
                "workflow_complete": False,
                "should_exit": True
            },
            learning_outcomes=[],
            concepts_mastered=[],
            engagement_score=0.0,
            time_spent_minutes=0.0,
            next_recommended_actions=["Retry with simpler approach"],
            teacher_notes=f"Workflow failed: {error}"
        )
    
    def _identify_mastered_concepts(self, state: WorkflowState) -> List[str]:
        """Identify concepts that were mastered during this workflow."""
        # Override in specific workflows for more sophisticated logic
        return [concept for concept in state.get("concepts_covered", []) 
                if state.get("engagement_level", 0) > 0.7]
    
    def _recommend_next_actions(self, state: WorkflowState) -> List[str]:
        """Recommend next learning actions based on workflow outcome."""
        actions = []
        
        if state.get("workflow_complete", False):
            if state.get("engagement_level", 0) > 0.8:
                actions.append("Try more challenging material")
            elif state.get("engagement_level", 0) < 0.5:
                actions.append("Review fundamentals")
            else:
                actions.append("Continue with related topics")
        else:
            actions.append("Complete current learning objective")
        
        if state.get("misconceptions_identified"):
            actions.append("Address identified misconceptions")
        
        return actions
    
    def _extract_assessment_scores(self, state: WorkflowState) -> Dict[str, float]:
        """Extract assessment scores from workflow state."""
        # Override in assessment workflows
        return {}
    
    # Common workflow nodes that can be used by subclasses
    async def _assess_prior_knowledge_node(self, state: WorkflowState) -> WorkflowState:
        """Common node for assessing prior knowledge."""
        llm = await self._get_llm()
        
        current_topic = state.get("current_topic", "the topic")
        student_id = state["student_id"]
        
        assessment_prompt = f"""
        You are assessing a student's prior knowledge about {current_topic}.
        
        Recent conversation:
        {self._format_messages_for_llm(state["messages"][-3:])}
        
        Based on the student's responses, estimate their prior knowledge level (0.0-1.0)
        and identify any misconceptions. 
        
        Respond in this format:
        KNOWLEDGE_LEVEL: 0.7
        MISCONCEPTIONS: [list any identified misconceptions]
        STRENGTHS: [list what they know well]
        """
        
        response = await llm.ainvoke(assessment_prompt)
        
        # Parse response and update state
        knowledge_level = self._extract_knowledge_level(response.content)
        misconceptions = self._extract_misconceptions(response.content)
        
        state["prior_knowledge_level"] = knowledge_level
        state["misconceptions_identified"].extend(misconceptions)
        state["current_phase"] = LearningPhase.INTRODUCE_CONCEPT
        state["last_update_time"] = datetime.now(timezone.utc)
        
        return state
    
    async def _generate_response_node(self, state: WorkflowState) -> WorkflowState:
        """Common node for generating educational responses."""
        llm = await self._get_llm()
        
        # Get the last student message
        last_message = state["messages"][-1] if state["messages"] else {"content": "Hello"}
        
        response_prompt = f"""
        You are an expert History tutor using the {self.workflow_type.value} approach.
        
        Student message: "{last_message['content']}"
        Current topic: {state.get('current_topic', 'History')}
        Student's knowledge level: {state.get('prior_knowledge_level', 0.5)}/1.0
        Learning phase: {state.get('current_phase', 'unknown')}
        
        Provide an educational response that:
        1. Addresses the student's message
        2. Uses appropriate pedagogical techniques for this workflow
        3. Maintains engagement and understanding
        4. Guides toward learning objectives
        
        Keep responses conversational and encouraging.
        """
        
        response = await llm.ainvoke(response_prompt)
        
        # Add tutor response to messages
        tutor_message = {
            "role": "assistant",
            "content": response.content
        }
        
        state["messages"].append(tutor_message)
        state["last_update_time"] = datetime.now(timezone.utc)
        
        return state
    
    async def _check_understanding_node(self, state: WorkflowState) -> WorkflowState:
        """Common node for checking student understanding."""
        
        # Simple understanding check based on engagement
        engagement = state.get("engagement_level", 0.5)
        attempts = state.get("phase_attempts", 0)
        
        if engagement > 0.7 or attempts >= state.get("max_phase_attempts", 3):
            state["next_action"] = "advance_phase"
        else:
            state["next_action"] = "provide_scaffolding"
            
        state["phase_attempts"] += 1
        state["last_update_time"] = datetime.now(timezone.utc)
        
        return state
    
    def _determine_next_action(self, state: WorkflowState) -> str:
        """Determine next action based on state."""
        if state.get("should_exit", False):
            return END
        
        if state.get("workflow_complete", False):
            return END
        
        return state.get("next_action", "generate_response")
    
    def _format_messages_for_llm(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for LLM prompts."""
        if not messages:
            return "No previous messages"
        
        formatted = []
        for msg in messages:
            role = "Student" if msg["role"] == "user" else "Tutor"
            formatted.append(f"{role}: {msg['content']}")
        
        return "\n".join(formatted)
    
    def _extract_knowledge_level(self, response: str) -> float:
        """Extract knowledge level from LLM response."""
        try:
            for line in response.split("\n"):
                if "KNOWLEDGE_LEVEL:" in line:
                    return float(line.split(":")[1].strip())
        except:
            pass
        return 0.5  # Default
    
    def _extract_misconceptions(self, response: str) -> List[str]:
        """Extract misconceptions from LLM response."""
        misconceptions = []
        try:
            for line in response.split("\n"):
                if "MISCONCEPTIONS:" in line:
                    misconceptions_text = line.split(":")[1].strip()
                    # Simple parsing - could be enhanced
                    if misconceptions_text and misconceptions_text != "[]":
                        misconceptions.append(misconceptions_text)
        except:
            pass
        return misconceptions