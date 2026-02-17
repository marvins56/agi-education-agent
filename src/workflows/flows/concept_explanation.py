"""Concept explanation workflow using scaffolded learning."""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

from langgraph.graph import StateGraph, END

from src.workflows.base import BaseWorkflow
from src.workflows.state import (
    WorkflowType, 
    WorkflowState, 
    ConceptExplanationState,
    LearningPhase
)
from src.context.schemas import TutoringContext

logger = logging.getLogger(__name__)


class ConceptExplanationFlow(BaseWorkflow):
    """Workflow for explaining new concepts with scaffolded learning."""
    
    def __init__(self):
        super().__init__(WorkflowType.CONCEPT_EXPLANATION)
    
    def _build_graph(self) -> None:
        """Build the concept explanation workflow graph."""
        
        workflow = StateGraph(ConceptExplanationState)
        
        # Define workflow nodes
        workflow.add_node("assess_prior_knowledge", self._assess_prior_knowledge_node)
        workflow.add_node("determine_explanation_approach", self._determine_explanation_approach_node)
        workflow.add_node("provide_basic_explanation", self._provide_basic_explanation_node)
        workflow.add_node("provide_detailed_explanation", self._provide_detailed_explanation_node)
        workflow.add_node("check_understanding", self._check_understanding_node)
        workflow.add_node("provide_examples", self._provide_examples_node)
        workflow.add_node("address_misconceptions", self._address_misconceptions_node)
        workflow.add_node("consolidate_learning", self._consolidate_learning_node)
        
        # Define the workflow flow
        workflow.set_entry_point("assess_prior_knowledge")
        
        # From assess_prior_knowledge
        workflow.add_edge("assess_prior_knowledge", "determine_explanation_approach")
        
        # From determine_explanation_approach - conditional based on knowledge level
        workflow.add_conditional_edges(
            "determine_explanation_approach",
            self._route_explanation_complexity,
            {
                "basic": "provide_basic_explanation",
                "detailed": "provide_detailed_explanation"
            }
        )
        
        # From explanations to understanding check
        workflow.add_edge("provide_basic_explanation", "check_understanding")
        workflow.add_edge("provide_detailed_explanation", "check_understanding")
        
        # From check_understanding - conditional based on comprehension
        workflow.add_conditional_edges(
            "check_understanding",
            self._route_after_understanding_check,
            {
                "provide_examples": "provide_examples",
                "address_misconceptions": "address_misconceptions",
                "consolidate": "consolidate_learning",
                "retry_explanation": "determine_explanation_approach"
            }
        )
        
        # From examples and misconceptions
        workflow.add_edge("provide_examples", "check_understanding")
        workflow.add_edge("address_misconceptions", "check_understanding")
        
        # From consolidate_learning to end
        workflow.add_edge("consolidate_learning", END)
        
        # Compile the graph
        self.graph = workflow.compile(checkpointer=self.checkpointer)
    
    async def initialize_state(
        self, 
        message: str,
        tutoring_context: TutoringContext,
        **kwargs
    ) -> ConceptExplanationState:
        """Initialize concept explanation workflow state."""
        
        # Extract concept name from message or kwargs
        concept_name = kwargs.get("concept_name") or self._extract_concept_from_message(message)
        
        now = datetime.now(timezone.utc)
        
        # Create initial state
        state = ConceptExplanationState(
            # Base workflow state
            messages=[{"role": "user", "content": message}],
            student_id=tutoring_context.student_id,
            session_id=tutoring_context.session_id,
            student_intent=None,
            current_topic=concept_name,
            subject=kwargs.get("subject", "History"),
            learning_objectives=[f"Understand {concept_name}"],
            prior_knowledge_level=0.0,  # Will be assessed
            workflow_type=WorkflowType.CONCEPT_EXPLANATION,
            current_phase=LearningPhase.ASSESS_PRIOR_KNOWLEDGE,
            phase_attempts=0,
            max_phase_attempts=3,
            concepts_covered=[],
            misconceptions_identified=[],
            breakthrough_moments=[],
            engagement_level=0.5,
            teaching_strategy=None,
            adaptation_history=[],
            next_action=None,
            workflow_complete=False,
            should_exit=False,
            workflow_start_time=now,
            last_update_time=now,
            debug_info={},
            
            # Concept explanation specific
            concept_name=concept_name,
            explanation_depth="basic",
            scaffolding_level=0.8,  # High scaffolding initially
            understanding_checks=[],
            visual_aids_used=[]
        )
        
        # Set prior knowledge if available from context
        if concept_name in tutoring_context.topic_mastery:
            state["prior_knowledge_level"] = tutoring_context.topic_mastery[concept_name]
        
        return state
    
    def _extract_concept_from_message(self, message: str) -> str:
        """Extract the main concept from student's message."""
        # Simple extraction - could be enhanced with NLP
        message_lower = message.lower()
        
        # Common question patterns
        if "what is" in message_lower:
            parts = message_lower.split("what is")
            if len(parts) > 1:
                concept = parts[1].strip().split("?")[0].strip()
                return concept.title()
        
        if "tell me about" in message_lower:
            parts = message_lower.split("tell me about")
            if len(parts) > 1:
                concept = parts[1].strip().split("?")[0].strip()
                return concept.title()
        
        # Default to generic topic
        return "Historical Topic"
    
    async def _determine_explanation_approach_node(self, state: ConceptExplanationState) -> ConceptExplanationState:
        """Determine the appropriate explanation approach based on prior knowledge."""
        
        knowledge_level = state["prior_knowledge_level"]
        
        if knowledge_level < 0.3:
            state["explanation_depth"] = "basic"
            state["scaffolding_level"] = 0.9  # High scaffolding
        elif knowledge_level < 0.7:
            state["explanation_depth"] = "intermediate" 
            state["scaffolding_level"] = 0.6  # Medium scaffolding
        else:
            state["explanation_depth"] = "advanced"
            state["scaffolding_level"] = 0.3  # Low scaffolding
        
        state["teaching_strategy"] = f"Scaffolded explanation with {state['explanation_depth']} depth"
        state["current_phase"] = LearningPhase.INTRODUCE_CONCEPT
        state["last_update_time"] = datetime.now(timezone.utc)
        
        return state
    
    def _route_explanation_complexity(self, state: ConceptExplanationState) -> str:
        """Route to appropriate explanation based on complexity."""
        if state["prior_knowledge_level"] < 0.4:
            return "basic"
        else:
            return "detailed"
    
    async def _provide_basic_explanation_node(self, state: ConceptExplanationState) -> ConceptExplanationState:
        """Provide a basic, foundational explanation of the concept."""
        
        llm = await self._get_llm()
        
        concept_name = state["concept_name"]
        
        explanation_prompt = f"""
        You are an expert History tutor providing a basic, foundational explanation.
        
        CONCEPT TO EXPLAIN: {concept_name}
        STUDENT'S PRIOR KNOWLEDGE: {state['prior_knowledge_level']}/1.0 (low)
        
        Provide a clear, simple explanation that:
        1. Starts with the most basic definition
        2. Uses simple, concrete language
        3. Includes relatable analogies or examples
        4. Avoids complex terminology initially
        5. Builds understanding step by step
        
        Keep it conversational and encouraging. End with a simple question to check understanding.
        """
        
        response = await llm.ainvoke(explanation_prompt)
        
        # Add explanation to conversation
        explanation_message = {
            "role": "assistant",
            "content": response.content
        }
        
        state["messages"].append(explanation_message)
        state["concepts_covered"].append(concept_name)
        state["current_phase"] = LearningPhase.GUIDED_PRACTICE
        state["last_update_time"] = datetime.now(timezone.utc)
        
        return state
    
    async def _provide_detailed_explanation_node(self, state: ConceptExplanationState) -> ConceptExplanationState:
        """Provide a detailed explanation building on existing knowledge."""
        
        llm = await self._get_llm()
        
        concept_name = state["concept_name"]
        
        explanation_prompt = f"""
        You are an expert History tutor providing a detailed explanation.
        
        CONCEPT TO EXPLAIN: {concept_name}
        STUDENT'S PRIOR KNOWLEDGE: {state['prior_knowledge_level']}/1.0 (moderate to high)
        
        Provide a comprehensive explanation that:
        1. Builds on their existing knowledge
        2. Introduces more sophisticated terminology
        3. Explains multiple perspectives or interpretations
        4. Connects to broader historical themes
        5. Includes specific examples and evidence
        
        Make connections to what they likely already know. End with a thoughtful question.
        """
        
        response = await llm.ainvoke(explanation_prompt)
        
        # Add explanation to conversation
        explanation_message = {
            "role": "assistant",
            "content": response.content
        }
        
        state["messages"].append(explanation_message)
        state["concepts_covered"].append(concept_name)
        state["current_phase"] = LearningPhase.GUIDED_PRACTICE
        state["last_update_time"] = datetime.now(timezone.utc)
        
        return state
    
    async def _check_understanding_node(self, state: ConceptExplanationState) -> ConceptExplanationState:
        """Check student understanding and determine next steps."""
        
        # Simulate understanding check - in real implementation, this would analyze student response
        # For now, we'll use phase attempts and engagement level
        
        attempts = state.get("phase_attempts", 0)
        
        # Simulate understanding based on attempts (placeholder)
        if attempts == 0:
            # First check - assume some understanding but might need examples
            state["engagement_level"] = 0.6
            understanding_score = 0.6
        elif attempts == 1:
            # Second check - better understanding
            state["engagement_level"] = 0.8
            understanding_score = 0.8
        else:
            # Multiple attempts - assume understanding achieved
            state["engagement_level"] = 0.9
            understanding_score = 0.9
        
        # Record understanding check
        understanding_check = {
            "attempt": attempts + 1,
            "score": understanding_score,
            "phase": state["current_phase"],
            "timestamp": datetime.now(timezone.utc)
        }
        state["understanding_checks"].append(understanding_check)
        
        state["phase_attempts"] += 1
        state["last_update_time"] = datetime.now(timezone.utc)
        
        return state
    
    def _route_after_understanding_check(self, state: ConceptExplanationState) -> str:
        """Route after understanding check based on comprehension level."""
        
        if not state["understanding_checks"]:
            return "provide_examples"
        
        latest_check = state["understanding_checks"][-1]
        understanding_score = latest_check["score"]
        attempts = state["phase_attempts"]
        
        # Route based on understanding and attempts
        if understanding_score >= 0.8:
            return "consolidate"
        elif understanding_score >= 0.6:
            if attempts < 2:
                return "provide_examples"
            else:
                return "consolidate"
        elif attempts >= state.get("max_phase_attempts", 3):
            return "consolidate"  # Move on after max attempts
        else:
            # Check if there are misconceptions to address
            if state.get("misconceptions_identified"):
                return "address_misconceptions"
            else:
                return "retry_explanation"
    
    async def _provide_examples_node(self, state: ConceptExplanationState) -> ConceptExplanationState:
        """Provide concrete examples to reinforce understanding."""
        
        llm = await self._get_llm()
        
        concept_name = state["concept_name"]
        
        examples_prompt = f"""
        You are providing concrete examples to help a student understand {concept_name}.
        
        Based on the concept explanation already provided, give 2-3 specific, concrete examples that:
        1. Illustrate the concept clearly
        2. Are historically accurate
        3. Are relatable and memorable
        4. Show different aspects of the concept
        
        Make the examples engaging and help solidify understanding.
        """
        
        response = await llm.ainvoke(examples_prompt)
        
        examples_message = {
            "role": "assistant", 
            "content": response.content
        }
        
        state["messages"].append(examples_message)
        state["last_update_time"] = datetime.now(timezone.utc)
        
        return state
    
    async def _address_misconceptions_node(self, state: ConceptExplanationState) -> ConceptExplanationState:
        """Address identified misconceptions."""
        
        llm = await self._get_llm()
        
        misconceptions = state.get("misconceptions_identified", [])
        
        if misconceptions:
            misconception_prompt = f"""
            Address these student misconceptions about {state['concept_name']}:
            
            Misconceptions identified:
            {', '.join(misconceptions)}
            
            Provide a gentle correction that:
            1. Acknowledges the student's thinking
            2. Explains why the misconception is common
            3. Provides the correct understanding
            4. Uses a clear example to illustrate
            
            Be encouraging and focus on learning.
            """
            
            response = await llm.ainvoke(misconception_prompt)
            
            correction_message = {
                "role": "assistant",
                "content": response.content
            }
            
            state["messages"].append(correction_message)
        
        state["last_update_time"] = datetime.now(timezone.utc)
        
        return state
    
    async def _consolidate_learning_node(self, state: ConceptExplanationState) -> ConceptExplanationState:
        """Consolidate learning and prepare for next steps."""
        
        llm = await self._get_llm()
        
        consolidation_prompt = f"""
        Consolidate the student's learning about {state['concept_name']}.
        
        Provide a brief summary that:
        1. Highlights the key points covered
        2. Celebrates the student's progress
        3. Suggests how this concept connects to broader topics
        4. Asks what they'd like to explore next
        
        Be encouraging and forward-looking.
        """
        
        response = await llm.ainvoke(consolidation_prompt)
        
        consolidation_message = {
            "role": "assistant",
            "content": response.content
        }
        
        state["messages"].append(consolidation_message)
        
        # Mark workflow as complete
        state["workflow_complete"] = True
        state["current_phase"] = LearningPhase.APPLY_TRANSFER
        state["engagement_level"] = min(1.0, state["engagement_level"] + 0.1)
        
        # Record breakthrough if high engagement
        if state["engagement_level"] > 0.8:
            state["breakthrough_moments"].append(f"Successfully understood {state['concept_name']}")
        
        state["last_update_time"] = datetime.now(timezone.utc)
        
        return state