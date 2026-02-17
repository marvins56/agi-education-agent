# LangGraph Workflows Implementation

**Document:** 02_LANGGRAPH_WORKFLOWS.md  
**Version:** 1.0  
**Date:** February 17, 2026  
**Dependencies:** LangGraph, existing orchestrator, context management  

---

## Overview

This document details the implementation of sophisticated LangGraph state machine workflows to replace the current simple orchestrator with intelligent tutoring flows that adapt to student needs and educational contexts.

## Current State Analysis

### Existing Orchestrator (src/agents/orchestrator.py)
```python
class MasterOrchestrator:
    """Routes messages to the appropriate specialist agent."""
    
    async def process(self, message: str, context: AgentContext) -> AgentResponse:
        """Route a message to the appropriate agent and return its response."""
        # For now, all messages go to the tutor agent.
        agent = self.agents["tutor"]
        return await agent.process(message, context)
```

### Problems with Current Implementation
1. **Linear Processing**: Every message goes directly to tutor agent
2. **No State Management**: No memory of conversation flow state
3. **No Conditional Logic**: Cannot branch based on student needs
4. **No Educational Workflows**: Missing scaffolded learning sequences
5. **Limited Adaptation**: Cannot adjust strategy based on student performance

### What We Keep
- Agent registration system (`self.agents` dictionary)
- Context enrichment with mastery data
- Memory manager integration
- Basic routing infrastructure

### What We Replace
- Simple linear message routing with sophisticated state machines
- Single-agent processing with multi-step educational workflows
- Static strategy selection with dynamic, context-aware flow control

---

## Architecture Design

### LangGraph State Machine Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH WORKFLOW SYSTEM                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  INPUT: Student message + Educational context                   │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              INTENT CLASSIFIER                          │   │
│  │  • Question about new topic                             │   │
│  │  • Request for clarification                            │   │
│  │  • Practice problem request                             │   │
│  │  • Assessment/quiz request                              │   │
│  │  • Casual conversation                                  │   │
│  └─────────────────────┬───────────────────────────────────┘   │
│                        │                                       │
│                        ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              WORKFLOW SELECTOR                          │   │
│  │  Based on:                                              │   │
│  │  • Student intent                                       │   │
│  │  • Prior knowledge level                               │   │
│  │  • Recent conversation context                          │   │
│  │  • Learning objectives                                  │   │
│  └─────────────────────┬───────────────────────────────────┘   │
│                        │                                       │
│                        ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              ACTIVE WORKFLOWS                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│  │  │  CONCEPT    │  │   PRACTICE  │  │ ASSESSMENT  │    │   │
│  │  │ EXPLANATION │  │  PROBLEMS   │  │   FLOW      │    │   │
│  │  │   FLOW      │  │    FLOW     │  │             │    │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│  │  │  SOCRATIC   │  │   REVIEW    │  │   HISTORY   │    │   │
│  │  │ QUESTIONING │  │    FLOW     │  │  SPECIFIC   │    │   │
│  │  │    FLOW     │  │             │  │   FLOWS     │    │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Structure and New Components

### New Directory Structure
```
src/workflows/
├── __init__.py
├── base.py              # Base workflow classes
├── state.py             # Workflow state definitions
├── orchestrator.py      # New workflow orchestrator
├── intent_classifier.py # Intent classification
├── flows/
│   ├── __init__.py
│   ├── concept_explanation.py
│   ├── practice_problems.py
│   ├── assessment.py
│   ├── socratic_questioning.py
│   ├── review_flow.py
│   └── history_specific/
│       ├── __init__.py
│       ├── timeline_exploration.py
│       ├── source_analysis.py
│       ├── cause_effect.py
│       └── dbq_essay.py
├── tools/
│   ├── __init__.py
│   ├── assessment_tool.py
│   ├── knowledge_retrieval_tool.py
│   ├── mastery_tracker_tool.py
│   └── feedback_generator_tool.py
└── conditions/
    ├── __init__.py
    ├── mastery_conditions.py
    ├── engagement_conditions.py
    └── time_conditions.py
```

---

## Core Implementation Files

### 1. `src/workflows/state.py` - Workflow State Definitions
```python
"""Workflow state definitions for educational flows."""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, TypedDict, Annotated
from langgraph.graph import add_messages
from pydantic import BaseModel, Field


class StudentIntent(str, Enum):
    """Classified student intents."""
    NEW_TOPIC = "new_topic"                    # "Tell me about the French Revolution"
    CLARIFICATION = "clarification"            # "I don't understand what you mean"
    PRACTICE = "practice"                      # "Can I try some problems?"
    ASSESSMENT = "assessment"                  # "Test my knowledge"
    REVIEW = "review"                         # "Let's go over what we learned"
    HELP_STUCK = "help_stuck"                 # "I'm stuck on this problem"
    CASUAL = "casual"                         # General conversation
    META_LEARNING = "meta_learning"           # Questions about learning itself


class WorkflowType(str, Enum):
    """Types of educational workflows."""
    CONCEPT_EXPLANATION = "concept_explanation"
    SOCRATIC_QUESTIONING = "socratic_questioning"
    PRACTICE_PROBLEMS = "practice_problems"
    ASSESSMENT_FLOW = "assessment_flow"
    REVIEW_SESSION = "review_session"
    HISTORY_TIMELINE = "history_timeline"
    SOURCE_ANALYSIS = "source_analysis"
    CAUSE_EFFECT_ANALYSIS = "cause_effect_analysis"
    DBQ_ESSAY = "dbq_essay"


class LearningPhase(str, Enum):
    """Phases of learning process."""
    ASSESS_PRIOR_KNOWLEDGE = "assess_prior_knowledge"
    INTRODUCE_CONCEPT = "introduce_concept"
    GUIDED_PRACTICE = "guided_practice"
    INDEPENDENT_PRACTICE = "independent_practice"
    ASSESSMENT = "assessment"
    REVIEW_REINFORCE = "review_reinforce"
    APPLY_TRANSFER = "apply_transfer"


class HistoryThinkingSkill(str, Enum):
    """Historical thinking skills progression."""
    CHRONOLOGICAL_REASONING = "chronological_reasoning"
    CRAFTING_ARGUMENTS = "crafting_arguments"
    ANALYZING_SOURCES = "analyzing_sources"
    CONTEXTUALIZATION = "contextualization"
    SYNTHESIS = "synthesis"


class WorkflowState(TypedDict):
    """Base state for all educational workflows."""
    # Message handling
    messages: Annotated[List[Dict[str, str]], add_messages]
    
    # Student context
    student_id: str
    session_id: str
    student_intent: Optional[StudentIntent]
    
    # Educational context
    current_topic: Optional[str]
    subject: Optional[str]
    learning_objectives: List[str]
    prior_knowledge_level: float  # 0.0-1.0
    
    # Workflow control
    workflow_type: Optional[WorkflowType]
    current_phase: Optional[LearningPhase]
    phase_attempts: int
    max_phase_attempts: int
    
    # Educational tracking
    concepts_covered: List[str]
    misconceptions_identified: List[str]
    breakthrough_moments: List[str]
    engagement_level: float  # 0.0-1.0
    
    # Teaching strategy
    teaching_strategy: Optional[str]
    adaptation_history: List[Dict[str, Any]]
    
    # Flow control
    next_action: Optional[str]
    workflow_complete: bool
    should_exit: bool
    
    # Metadata
    workflow_start_time: datetime
    last_update_time: datetime
    debug_info: Dict[str, Any]


class ConceptExplanationState(WorkflowState):
    """State for concept explanation workflow."""
    concept_name: str
    explanation_depth: str  # "basic", "intermediate", "advanced"
    scaffolding_level: float  # 0.0-1.0, how much guidance to provide
    understanding_checks: List[Dict[str, Any]]
    visual_aids_used: List[str]


class SocraticQuestioningState(WorkflowState):
    """State for Socratic questioning workflow."""
    target_insight: str  # What we want student to discover
    question_sequence: List[str]
    current_question_index: int
    student_responses: List[str]
    discovery_level: float  # 0.0-1.0, how close to insight


class PracticeProblemsState(WorkflowState):
    """State for practice problems workflow."""
    problem_type: str
    difficulty_level: float  # 0.0-1.0
    problems_attempted: int
    problems_correct: int
    current_problem: Optional[Dict[str, Any]]
    hint_level: int  # 0 = no hints, increasing = more guidance
    mistakes_log: List[Dict[str, Any]]


class AssessmentFlowState(WorkflowState):
    """State for assessment workflow."""
    assessment_type: str  # "formative", "summative", "diagnostic"
    questions: List[Dict[str, Any]]
    current_question_index: int
    responses: List[Dict[str, Any]]
    scores: Dict[str, float]
    feedback_generated: bool


class HistoryTimelineState(WorkflowState):
    """State for History timeline exploration."""
    time_period: str  # "Ancient Rome", "World War I", etc.
    timeline_events: List[Dict[str, Any]]
    current_focus_event: Optional[Dict[str, Any]]
    connections_explored: List[str]
    thinking_skill_focus: HistoryThinkingSkill


class SourceAnalysisState(WorkflowState):
    """State for primary source analysis."""
    source_document: Dict[str, Any]
    analysis_questions: List[str]
    current_question_index: int
    student_analysis: List[str]
    source_context_provided: bool
    bias_discussion_completed: bool


class WorkflowResult(BaseModel):
    """Result of a workflow execution."""
    workflow_type: WorkflowType
    final_state: Dict[str, Any]
    learning_outcomes: List[str]
    concepts_mastered: List[str]
    areas_for_improvement: List[str]
    next_recommended_workflow: Optional[WorkflowType]
    session_summary: str
    metadata: Dict[str, Any]
```

### 2. `src/workflows/orchestrator.py` - New Workflow Orchestrator
```python
"""LangGraph-based workflow orchestrator for educational flows."""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Any, List

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.agents.base import AgentContext, AgentResponse
from src.workflows.state import WorkflowState, StudentIntent, WorkflowType
from src.workflows.intent_classifier import IntentClassifier
from src.workflows.flows.concept_explanation import ConceptExplanationFlow
from src.workflows.flows.socratic_questioning import SocraticQuestioningFlow
from src.workflows.flows.practice_problems import PracticeProblemsFlow
from src.workflows.flows.assessment import AssessmentFlow
from src.workflows.flows.history_specific.timeline_exploration import TimelineExplorationFlow
from src.workflows.flows.history_specific.source_analysis import SourceAnalysisFlow
from src.memory.manager import MemoryManager

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """LangGraph-based orchestrator for educational workflows."""
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        context_builder=None,
    ):
        self.memory = memory_manager
        self.context_builder = context_builder
        self.intent_classifier = IntentClassifier()
        
        # Initialize workflow flows
        self.flows = {
            WorkflowType.CONCEPT_EXPLANATION: ConceptExplanationFlow(),
            WorkflowType.SOCRATIC_QUESTIONING: SocraticQuestioningFlow(),
            WorkflowType.PRACTICE_PROBLEMS: PracticeProblemsFlow(),
            WorkflowType.ASSESSMENT_FLOW: AssessmentFlow(),
            WorkflowType.HISTORY_TIMELINE: TimelineExplorationFlow(),
            WorkflowType.SOURCE_ANALYSIS: SourceAnalysisFlow(),
        }
        
        # Build the main state graph
        self.graph = self._build_state_graph()
        
        # Checkpoint manager for state persistence
        self.checkpointer = MemorySaver()
        
        # Compiled graph with checkpointing
        self.app = self.graph.compile(checkpointer=self.checkpointer)
    
    def _build_state_graph(self) -> StateGraph:
        """Build the main workflow state graph."""
        graph = StateGraph(WorkflowState)
        
        # Add nodes
        graph.add_node("classify_intent", self._classify_intent)
        graph.add_node("select_workflow", self._select_workflow)
        graph.add_node("execute_workflow", self._execute_workflow)
        graph.add_node("handle_continuation", self._handle_continuation)
        graph.add_node("finalize_response", self._finalize_response)
        
        # Set entry point
        graph.set_entry_point("classify_intent")
        
        # Add edges
        graph.add_edge("classify_intent", "select_workflow")
        
        # Conditional edge from workflow selection
        graph.add_conditional_edges(
            "select_workflow",
            self._should_start_new_workflow,
            {
                "new_workflow": "execute_workflow",
                "continue_existing": "handle_continuation",
                "direct_response": "finalize_response"
            }
        )
        
        # Conditional edge from workflow execution
        graph.add_conditional_edges(
            "execute_workflow",
            self._workflow_completion_check,
            {
                "complete": "finalize_response",
                "continue": "handle_continuation",
                "switch_workflow": "select_workflow"
            }
        )
        
        graph.add_edge("handle_continuation", "finalize_response")
        graph.add_edge("finalize_response", END)
        
        return graph
    
    async def process(self, message: str, context: AgentContext) -> AgentResponse:
        """Process student message through workflow system."""
        start_time = datetime.now(timezone.utc)
        
        # Initialize workflow state
        state = WorkflowState(
            messages=[{"role": "user", "content": message}],
            student_id=context.student_id,
            session_id=context.session_id,
            student_intent=None,
            current_topic=context.current_topic,
            subject=context.current_subject,
            learning_objectives=context.learning_objectives or [],
            prior_knowledge_level=0.5,  # Will be updated by context
            workflow_type=None,
            current_phase=None,
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
            workflow_start_time=start_time,
            last_update_time=start_time,
            debug_info={}
        )
        
        # Enrich state with educational context
        if self.context_builder:
            try:
                enriched_context = await self.context_builder.build_context(
                    student_id=context.student_id,
                    session_id=context.session_id,
                )
                state = await self._enrich_state_with_context(state, enriched_context)
            except Exception as e:
                logger.warning(f"Failed to enrich workflow state: {e}")
        
        # Execute workflow graph
        config = {"configurable": {"thread_id": context.session_id}}
        
        try:
            result = await self.app.ainvoke(state, config=config)
            
            # Extract final response
            final_messages = result.get("messages", [])
            assistant_message = None
            
            for msg in reversed(final_messages):
                if msg.get("role") == "assistant":
                    assistant_message = msg.get("content", "")
                    break
            
            if not assistant_message:
                assistant_message = "I'm here to help with your learning. What would you like to explore?"
            
            # Build metadata
            metadata = {
                "workflow_type": result.get("workflow_type"),
                "current_phase": result.get("current_phase"),
                "engagement_level": result.get("engagement_level", 0.5),
                "concepts_covered": result.get("concepts_covered", []),
                "teaching_strategy": result.get("teaching_strategy"),
                "next_recommended_action": result.get("next_action")
            }
            
            # Save learning event
            await self._save_workflow_event(context, result)
            
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            return AgentResponse(
                text=assistant_message,
                metadata=metadata,
                agent_name="workflow_orchestrator",
                processing_time=processing_time,
                suggested_actions=self._generate_suggested_actions(result)
            )
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            
            # Fallback response
            return AgentResponse(
                text="I encountered an issue processing your request. Could you rephrase what you'd like to learn about?",
                metadata={"error": "workflow_execution_failed"},
                agent_name="workflow_orchestrator",
                processing_time=(datetime.now(timezone.utc) - start_time).total_seconds()
            )
    
    async def _classify_intent(self, state: WorkflowState) -> WorkflowState:
        """Classify student intent from their message."""
        latest_message = state["messages"][-1]["content"]
        
        intent = await self.intent_classifier.classify_intent(
            message=latest_message,
            conversation_context=state["messages"][-5:],  # Last 5 messages for context
            current_topic=state.get("current_topic"),
            subject=state.get("subject")
        )
        
        state["student_intent"] = intent
        state["debug_info"]["classified_intent"] = intent.value
        
        return state
    
    async def _select_workflow(self, state: WorkflowState) -> WorkflowState:
        """Select appropriate workflow based on intent and context."""
        intent = state["student_intent"]
        current_topic = state.get("current_topic")
        subject = state.get("subject", "").lower()
        prior_knowledge = state.get("prior_knowledge_level", 0.5)
        
        # Intent-to-workflow mapping
        workflow_mapping = {
            StudentIntent.NEW_TOPIC: WorkflowType.CONCEPT_EXPLANATION,
            StudentIntent.CLARIFICATION: WorkflowType.SOCRATIC_QUESTIONING,
            StudentIntent.PRACTICE: WorkflowType.PRACTICE_PROBLEMS,
            StudentIntent.ASSESSMENT: WorkflowType.ASSESSMENT_FLOW,
            StudentIntent.REVIEW: WorkflowType.REVIEW_SESSION,
            StudentIntent.HELP_STUCK: WorkflowType.SOCRATIC_QUESTIONING,
        }
        
        # History-specific workflow selection
        if subject == "history" or "history" in (current_topic or "").lower():
            if "timeline" in state["messages"][-1]["content"].lower():
                workflow_type = WorkflowType.HISTORY_TIMELINE
            elif any(word in state["messages"][-1]["content"].lower() 
                    for word in ["source", "document", "primary"]):
                workflow_type = WorkflowType.SOURCE_ANALYSIS
            else:
                workflow_type = workflow_mapping.get(intent, WorkflowType.CONCEPT_EXPLANATION)
        else:
            workflow_type = workflow_mapping.get(intent, WorkflowType.CONCEPT_EXPLANATION)
        
        # Adapt workflow based on prior knowledge
        if prior_knowledge < 0.3:  # Low knowledge
            if workflow_type == WorkflowType.PRACTICE_PROBLEMS:
                workflow_type = WorkflowType.CONCEPT_EXPLANATION  # Explain first
        elif prior_knowledge > 0.8:  # High knowledge
            if workflow_type == WorkflowType.CONCEPT_EXPLANATION:
                workflow_type = WorkflowType.ASSESSMENT_FLOW  # Challenge them
        
        state["workflow_type"] = workflow_type
        state["debug_info"]["selected_workflow"] = workflow_type.value
        
        return state
    
    async def _execute_workflow(self, state: WorkflowState) -> WorkflowState:
        """Execute the selected workflow."""
        workflow_type = state["workflow_type"]
        
        if workflow_type not in self.flows:
            logger.error(f"Unknown workflow type: {workflow_type}")
            state["should_exit"] = True
            return state
        
        flow = self.flows[workflow_type]
        
        try:
            # Execute the workflow
            updated_state = await flow.execute(state, self.memory)
            
            # Update timestamps
            updated_state["last_update_time"] = datetime.now(timezone.utc)
            
            return updated_state
            
        except Exception as e:
            logger.error(f"Workflow execution failed for {workflow_type}: {e}")
            state["should_exit"] = True
            state["debug_info"]["workflow_error"] = str(e)
            return state
    
    async def _handle_continuation(self, state: WorkflowState) -> WorkflowState:
        """Handle workflow continuation logic."""
        # Check if workflow should continue or switch
        if state.get("workflow_complete", False):
            # Generate continuation recommendation
            next_workflow = await self._recommend_next_workflow(state)
            if next_workflow:
                state["next_action"] = f"transition_to_{next_workflow.value}"
            else:
                state["next_action"] = "session_complete"
        
        return state
    
    async def _finalize_response(self, state: WorkflowState) -> WorkflowState:
        """Finalize the response with educational insights."""
        # Add assistant message if not already present
        if not any(msg.get("role") == "assistant" for msg in state["messages"]):
            response_text = await self._generate_fallback_response(state)
            state["messages"].append({"role": "assistant", "content": response_text})
        
        # Add educational metadata to the last assistant message
        state["debug_info"]["finalization_time"] = datetime.now(timezone.utc).isoformat()
        
        return state
    
    def _should_start_new_workflow(self, state: WorkflowState) -> str:
        """Determine if we should start a new workflow or continue existing."""
        # Check if there's an active workflow in session
        # This is where we'd check session state for ongoing workflows
        
        if state.get("workflow_type") is None:
            return "direct_response"  # No workflow needed
        
        # For now, always start new workflow
        # In production, this would check for existing workflow state
        return "new_workflow"
    
    def _workflow_completion_check(self, state: WorkflowState) -> str:
        """Check if workflow is complete or needs to continue."""
        if state.get("should_exit", False):
            return "complete"
        
        if state.get("workflow_complete", False):
            return "complete"
        
        # Check if workflow should switch (e.g., student needs different approach)
        if state.get("phase_attempts", 0) > state.get("max_phase_attempts", 3):
            return "switch_workflow"
        
        return "continue"
    
    async def _recommend_next_workflow(self, state: WorkflowState) -> Optional[WorkflowType]:
        """Recommend next workflow based on learning progress."""
        current_workflow = state.get("workflow_type")
        mastery_level = state.get("prior_knowledge_level", 0.5)
        engagement = state.get("engagement_level", 0.5)
        
        # Learning progression logic
        progressions = {
            WorkflowType.CONCEPT_EXPLANATION: {
                "high_mastery": WorkflowType.PRACTICE_PROBLEMS,
                "medium_mastery": WorkflowType.SOCRATIC_QUESTIONING,
                "low_mastery": None  # Stay with explanation
            },
            WorkflowType.SOCRATIC_QUESTIONING: {
                "high_engagement": WorkflowType.PRACTICE_PROBLEMS,
                "low_engagement": WorkflowType.CONCEPT_EXPLANATION
            },
            WorkflowType.PRACTICE_PROBLEMS: {
                "high_success": WorkflowType.ASSESSMENT_FLOW,
                "low_success": WorkflowType.CONCEPT_EXPLANATION
            }
        }
        
        if current_workflow in progressions:
            progression_map = progressions[current_workflow]
            
            if mastery_level > 0.7:
                return progression_map.get("high_mastery")
            elif mastery_level < 0.4:
                return progression_map.get("low_mastery")
            elif engagement > 0.7:
                return progression_map.get("high_engagement")
            elif engagement < 0.4:
                return progression_map.get("low_engagement")
        
        return None
    
    async def _enrich_state_with_context(
        self, 
        state: WorkflowState, 
        enriched_context: Dict[str, Any]
    ) -> WorkflowState:
        """Enrich workflow state with educational context."""
        # Update mastery level
        mastery_scores = enriched_context.get("mastery_scores", [])
        if mastery_scores and state.get("current_topic"):
            for score in mastery_scores:
                if score.get("topic") == state["current_topic"]:
                    state["prior_knowledge_level"] = score.get("mastery_score", 50.0) / 100.0
                    break
        
        # Update struggle points
        struggle_points = enriched_context.get("struggle_points", [])
        if struggle_points:
            state["debug_info"]["struggle_areas"] = [s["topic"] for s in struggle_points[:3]]
        
        return state
    
    async def _generate_fallback_response(self, state: WorkflowState) -> str:
        """Generate a fallback response when workflow fails."""
        intent = state.get("student_intent")
        topic = state.get("current_topic", "this topic")
        
        fallback_responses = {
            StudentIntent.NEW_TOPIC: f"I'd love to help you learn about {topic}. What specifically interests you about this topic?",
            StudentIntent.CLARIFICATION: "I want to make sure I explain this clearly. What part would you like me to clarify?",
            StudentIntent.PRACTICE: f"Let's practice with {topic}. What type of problem would you like to try?",
            StudentIntent.ASSESSMENT: f"I can help assess your understanding of {topic}. Shall we start with some questions?",
            StudentIntent.REVIEW: f"Great idea to review {topic}. What aspects should we focus on?",
        }
        
        return fallback_responses.get(
            intent, 
            "I'm here to help with your learning. What would you like to explore today?"
        )
    
    def _generate_suggested_actions(self, state: WorkflowState) -> List[str]:
        """Generate suggested actions based on workflow state."""
        actions = []
        
        workflow_type = state.get("workflow_type")
        topic = state.get("current_topic", "this topic")
        
        if workflow_type == WorkflowType.CONCEPT_EXPLANATION:
            actions.extend([
                f"Practice problems with {topic}",
                f"Quiz me on {topic}",
                "Show me examples"
            ])
        elif workflow_type == WorkflowType.PRACTICE_PROBLEMS:
            actions.extend([
                "Try a harder problem",
                "Explain the concept again",
                "Show me the solution"
            ])
        elif workflow_type == WorkflowType.ASSESSMENT_FLOW:
            actions.extend([
                "Review incorrect answers",
                "Try more questions",
                "Move to next topic"
            ])
        
        # Always include general options
        actions.extend([
            "Ask a specific question",
            "Change topics",
            "Take a break"
        ])
        
        return actions[:4]  # Limit to 4 suggestions
    
    async def _save_workflow_event(self, context: AgentContext, result: Dict[str, Any]) -> None:
        """Save workflow execution as learning event."""
        if not self.memory:
            return
            
        try:
            await self.memory.save_learning_event(
                student_id=context.student_id,
                event_type="workflow_execution",
                subject=context.current_subject,
                topic=context.current_topic,
                data={
                    "workflow_type": result.get("workflow_type"),
                    "concepts_covered": result.get("concepts_covered", []),
                    "engagement_level": result.get("engagement_level", 0.5),
                    "teaching_strategy": result.get("teaching_strategy"),
                    "workflow_complete": result.get("workflow_complete", False)
                },
                outcome="completed" if result.get("workflow_complete") else "in_progress"
            )
        except Exception as e:
            logger.warning(f"Failed to save workflow event: {e}")
```

### 3. `src/workflows/intent_classifier.py` - Intent Classification
```python
"""Intent classification for educational conversations."""
import re
from typing import List, Dict, Optional

from langchain_core.messages import SystemMessage, HumanMessage

from src.workflows.state import StudentIntent
from src.llm.factory import LLMFactory


class IntentClassifier:
    """Classifies student intent from conversation context."""
    
    def __init__(self):
        # Use fast, cheap model for classification
        self.llm = LLMFactory.create(provider="openai", model="gpt-3.5-turbo")
        
        # Pattern-based classification for common cases (faster)
        self.intent_patterns = {
            StudentIntent.NEW_TOPIC: [
                r'\b(tell me about|explain|what is|what are)\b',
                r'\b(how does|how do|why does|why do)\b',
                r'\b(I want to learn|teach me|help me understand)\b'
            ],
            StudentIntent.CLARIFICATION: [
                r'\b(I don\'t understand|clarify|confused|unclear)\b',
                r'\b(what do you mean|can you explain|rephrase)\b',
                r'\b(I\'m lost|not clear|doesn\'t make sense)\b'
            ],
            StudentIntent.PRACTICE: [
                r'\b(practice|try|exercise|problem|quiz)\b',
                r'\b(can I|let me|want to practice)\b',
                r'\b(work on|solve|attempt)\b'
            ],
            StudentIntent.ASSESSMENT: [
                r'\b(test me|quiz me|check my understanding)\b',
                r'\b(how am I doing|assess|evaluate)\b',
                r'\b(ready for test|want a quiz)\b'
            ],
            StudentIntent.REVIEW: [
                r'\b(review|go over|revisit|recap)\b',
                r'\b(what did we cover|summary|what have we learned)\b'
            ],
            StudentIntent.HELP_STUCK: [
                r'\b(stuck|help|hint|don\'t know how)\b',
                r'\b(can\'t figure out|struggling with)\b'
            ]
        }
    
    async def classify_intent(
        self,
        message: str,
        conversation_context: List[Dict[str, str]],
        current_topic: Optional[str] = None,
        subject: Optional[str] = None
    ) -> StudentIntent:
        """Classify student intent from message and context."""
        
        # First try pattern-based classification (fast)
        pattern_intent = self._classify_with_patterns(message)
        if pattern_intent:
            return pattern_intent
        
        # Fall back to LLM classification for complex cases
        return await self._classify_with_llm(
            message, conversation_context, current_topic, subject
        )
    
    def _classify_with_patterns(self, message: str) -> Optional[StudentIntent]:
        """Fast pattern-based intent classification."""
        message_lower = message.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent
        
        return None
    
    async def _classify_with_llm(
        self,
        message: str,
        conversation_context: List[Dict[str, str]],
        current_topic: Optional[str],
        subject: Optional[str]
    ) -> StudentIntent:
        """LLM-based intent classification for complex cases."""
        
        context_text = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in conversation_context[-5:]  # Last 5 messages
        ])
        
        topic_context = ""
        if current_topic:
            topic_context = f"Current topic: {current_topic}"
        if subject:
            topic_context += f" (Subject: {subject})"
        
        prompt = f"""
Classify the student's intent from this educational conversation:

{topic_context}

Recent conversation:
{context_text}

Student's latest message:
"{message}"

Classify the intent as ONE of these categories:
- new_topic: Student wants to learn about a new concept/topic
- clarification: Student is confused and needs clarification
- practice: Student wants to practice problems or exercises
- assessment: Student wants to be tested or assessed
- review: Student wants to review previously learned material
- help_stuck: Student is stuck on current problem and needs help
- casual: General conversation, not specific learning intent
- meta_learning: Questions about learning process itself

Respond with only the category name, no explanation.
"""
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert at understanding student learning intentions."),
                HumanMessage(content=prompt)
            ])
            
            intent_text = response.content.strip().lower()
            
            # Map response to enum
            intent_mapping = {
                "new_topic": StudentIntent.NEW_TOPIC,
                "clarification": StudentIntent.CLARIFICATION,
                "practice": StudentIntent.PRACTICE,
                "assessment": StudentIntent.ASSESSMENT,
                "review": StudentIntent.REVIEW,
                "help_stuck": StudentIntent.HELP_STUCK,
                "casual": StudentIntent.CASUAL,
                "meta_learning": StudentIntent.META_LEARNING
            }
            
            return intent_mapping.get(intent_text, StudentIntent.CASUAL)
            
        except Exception as e:
            # Fallback to pattern matching or default
            return StudentIntent.CASUAL
```

### 4. `src/workflows/flows/concept_explanation.py` - Concept Explanation Workflow
```python
"""Concept explanation workflow with scaffolded learning."""
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage

from src.workflows.state import WorkflowState, LearningPhase, ConceptExplanationState
from src.workflows.base import BaseWorkflow
from src.llm.factory import LLMFactory

logger = logging.getLogger(__name__)


class ConceptExplanationFlow(BaseWorkflow):
    """Scaffolded concept explanation workflow."""
    
    def __init__(self):
        super().__init__()
        self.llm = LLMFactory.create(provider="openai", model="gpt-4")
    
    async def execute(self, state: WorkflowState, memory_manager) -> WorkflowState:
        """Execute concept explanation workflow."""
        
        # Convert to specific state type
        concept_state = ConceptExplanationState(**state)
        
        # Determine concept name if not set
        if not concept_state.get("concept_name"):
            concept_state["concept_name"] = await self._extract_concept_name(
                concept_state["messages"][-1]["content"]
            )
        
        # Set initial phase if not set
        if not concept_state.get("current_phase"):
            concept_state["current_phase"] = LearningPhase.ASSESS_PRIOR_KNOWLEDGE
            concept_state["explanation_depth"] = "basic"
            concept_state["scaffolding_level"] = 0.8  # High scaffolding initially
            concept_state["understanding_checks"] = []
            concept_state["visual_aids_used"] = []
        
        # Execute current phase
        if concept_state["current_phase"] == LearningPhase.ASSESS_PRIOR_KNOWLEDGE:
            concept_state = await self._assess_prior_knowledge(concept_state)
        elif concept_state["current_phase"] == LearningPhase.INTRODUCE_CONCEPT:
            concept_state = await self._introduce_concept(concept_state, memory_manager)
        elif concept_state["current_phase"] == LearningPhase.GUIDED_PRACTICE:
            concept_state = await self._guided_practice(concept_state)
        elif concept_state["current_phase"] == LearningPhase.ASSESSMENT:
            concept_state = await self._assess_understanding(concept_state)
        
        # Update workflow completion status
        if concept_state["current_phase"] == LearningPhase.ASSESSMENT:
            if concept_state.get("prior_knowledge_level", 0.0) > 0.7:
                concept_state["workflow_complete"] = True
        
        return concept_state
    
    async def _extract_concept_name(self, message: str) -> str:
        """Extract the main concept from student's message."""
        prompt = f"""
Extract the main concept or topic the student wants to learn about:

Student message: "{message}"

Examples:
- "Tell me about the French Revolution" → "French Revolution"
- "How does photosynthesis work?" → "photosynthesis"
- "Explain quadratic equations" → "quadratic equations"

Respond with only the concept name, no additional text.
"""
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You extract key concepts from student questions."),
                HumanMessage(content=prompt)
            ])
            return response.content.strip()
        except Exception:
            return "the concept you asked about"
    
    async def _assess_prior_knowledge(self, state: ConceptExplanationState) -> ConceptExplanationState:
        """Assess student's prior knowledge of the concept."""
        concept_name = state["concept_name"]
        
        # Generate assessment question
        assessment_prompt = f"""
Create a brief, friendly question to assess what the student already knows about {concept_name}.

Requirements:
- Open-ended question that reveals existing knowledge
- Appropriate for educational level
- Encouraging tone
- Should take 1-2 sentences to answer

Example: "Before we dive into {concept_name}, what do you already know about it? Even if it's just something you've heard, I'd love to hear your thoughts!"

Generate only the question, no additional text.
"""
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a friendly tutor assessing prior knowledge."),
                HumanMessage(content=assessment_prompt)
            ])
            
            assessment_question = response.content.strip()
            
            # Add to messages and update state
            state["messages"].append({
                "role": "assistant",
                "content": assessment_question
            })
            
            # Move to next phase
            state["current_phase"] = LearningPhase.INTRODUCE_CONCEPT
            state["phase_attempts"] += 1
            
        except Exception as e:
            logger.error(f"Prior knowledge assessment failed: {e}")
            # Skip to introduction
            state["current_phase"] = LearningPhase.INTRODUCE_CONCEPT
        
        return state
    
    async def _introduce_concept(
        self, 
        state: ConceptExplanationState, 
        memory_manager
    ) -> ConceptExplanationState:
        """Introduce the concept with appropriate scaffolding."""
        concept_name = state["concept_name"]
        depth = state.get("explanation_depth", "basic")
        scaffolding = state.get("scaffolding_level", 0.8)
        
        # Get relevant knowledge from RAG if available
        rag_context = ""
        if hasattr(memory_manager, 'search_knowledge'):
            try:
                knowledge_docs = await memory_manager.search_knowledge(
                    query=concept_name,
                    n_results=3
                )
                if knowledge_docs:
                    rag_context = "\n".join([
                        doc.get("document", "")
                        for doc in knowledge_docs[:2]
                    ])
            except Exception as e:
                logger.warning(f"RAG retrieval failed: {e}")
        
        # Build explanation prompt
        explanation_prompt = f"""
Explain {concept_name} to a student with the following requirements:

Explanation depth: {depth}
Scaffolding level: {scaffolding:.1f}/1.0 (higher = more guidance and structure)
Student's subject context: {state.get('subject', 'general')}

Guidelines:
- Start with a clear, simple definition
- Use relatable analogies and examples
- Break down complex ideas into smaller parts
- Include why this concept is important/useful
- End with a check for understanding

{f"Knowledge context (use to inform explanation): {rag_context}" if rag_context else ""}

Student's prior knowledge level: {state.get('prior_knowledge_level', 0.5):.1f}/1.0

Generate a clear, engaging explanation that builds understanding step by step.
"""
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert tutor explaining concepts clearly."),
                HumanMessage(content=explanation_prompt)
            ])
            
            explanation = response.content.strip()
            
            # Add explanation to messages
            state["messages"].append({
                "role": "assistant", 
                "content": explanation
            })
            
            # Update state
            state["concepts_covered"].append(concept_name)
            state["current_phase"] = LearningPhase.GUIDED_PRACTICE
            state["phase_attempts"] += 1
            
            # Track explanation metrics
            state["understanding_checks"].append({
                "phase": "introduction",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "scaffolding_used": scaffolding
            })
            
        except Exception as e:
            logger.error(f"Concept introduction failed: {e}")
            state["should_exit"] = True
        
        return state
    
    async def _guided_practice(self, state: ConceptExplanationState) -> ConceptExplanationState:
        """Provide guided practice opportunity."""
        concept_name = state["concept_name"]
        
        practice_prompt = f"""
Create a guided practice activity for {concept_name} that helps the student apply what they just learned.

Requirements:
- Interactive question or scenario
- Allows student to demonstrate understanding
- Provides scaffolding if they struggle
- Builds confidence
- Takes 2-3 minutes to complete

Subject context: {state.get('subject', 'general')}

Generate the practice activity with clear instructions.
"""
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You create engaging practice activities."),
                HumanMessage(content=practice_prompt)
            ])
            
            practice_activity = response.content.strip()
            
            # Add practice to messages
            state["messages"].append({
                "role": "assistant",
                "content": practice_activity
            })
            
            # Move to assessment phase
            state["current_phase"] = LearningPhase.ASSESSMENT
            state["phase_attempts"] += 1
            
        except Exception as e:
            logger.error(f"Guided practice creation failed: {e}")
            # Skip to assessment
            state["current_phase"] = LearningPhase.ASSESSMENT
        
        return state
    
    async def _assess_understanding(self, state: ConceptExplanationState) -> ConceptExplanationState:
        """Assess student's understanding of the concept."""
        concept_name = state["concept_name"]
        
        assessment_prompt = f"""
Create a brief assessment question to check if the student understands {concept_name}.

Requirements:
- Tests application, not just memorization
- Appropriate difficulty level
- Clear success criteria
- Encouraging tone
- Can be answered in 1-2 sentences

Generate the assessment question.
"""
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You create effective assessment questions."),
                HumanMessage(content=assessment_prompt)
            ])
            
            assessment_question = response.content.strip()
            
            # Add assessment to messages
            state["messages"].append({
                "role": "assistant",
                "content": assessment_question
            })
            
            # Update understanding check
            state["understanding_checks"].append({
                "phase": "final_assessment",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "question": assessment_question
            })
            
            # Estimate knowledge gain (this would be updated based on student response)
            state["prior_knowledge_level"] = min(1.0, state.get("prior_knowledge_level", 0.5) + 0.3)
            
            # Mark workflow as ready to complete
            state["workflow_complete"] = True
            
        except Exception as e:
            logger.error(f"Assessment creation failed: {e}")
            state["workflow_complete"] = True
        
        return state
```

---

## Integration with Existing System

### Modified Files

#### 1. Update `src/agents/orchestrator.py`
Replace the simple orchestrator with workflow orchestrator:

```python
# In MasterOrchestrator.__init__
async def initialize(self) -> None:
    """Create and register all agents."""
    # Build a context builder if we have a memory manager
    if self.memory_manager:
        self.context_builder = StudentContextBuilder(
            memory_manager=self.memory_manager,
            db_session_factory=self.memory_manager.db_session_factory,
        )

    # Use new workflow orchestrator instead of simple tutor agent
    from src.workflows.orchestrator import WorkflowOrchestrator
    
    self.workflow_orchestrator = WorkflowOrchestrator(
        memory_manager=self.memory_manager,
        context_builder=self.context_builder
    )
    
    # Keep original tutor agent as fallback
    self.agents["tutor"] = TutorAgent(
        retriever=self.retriever,
        memory=self.memory_manager,
        context_builder=self.context_builder,
    )

async def process(self, message: str, context: AgentContext) -> AgentResponse:
    """Route to workflow orchestrator with fallback."""
    try:
        # Use workflow orchestrator as primary
        return await self.workflow_orchestrator.process(message, context)
    except Exception as e:
        logger.warning(f"Workflow orchestrator failed, falling back to tutor: {e}")
        
        # Fallback to original tutor agent
        agent = self.agents["tutor"]
        return await agent.process(message, context)
```

#### 2. Update `src/api/routers/chat.py`
Add workflow status endpoint:

```python
@router.get("/workflow-status/{session_id}")
async def get_workflow_status(
    session_id: str,
    current_user: User = Depends(get_current_user),
    orchestrator: MasterOrchestrator = Depends(get_orchestrator),
):
    """Get current workflow status for debugging/analytics."""
    if hasattr(orchestrator, 'workflow_orchestrator'):
        # Get workflow state from checkpointer
        config = {"configurable": {"thread_id": session_id}}
        try:
            state = await orchestrator.workflow_orchestrator.app.aget_state(config)
            return {
                "session_id": session_id,
                "has_active_workflow": state is not None,
                "current_workflow": state.values.get("workflow_type") if state else None,
                "current_phase": state.values.get("current_phase") if state else None,
                "workflow_complete": state.values.get("workflow_complete", False) if state else None
            }
        except Exception as e:
            return {"error": f"Failed to get workflow state: {e}"}
    else:
        return {"message": "Workflow orchestrator not available"}
```

---

## Configuration

### Update `src/config.py`
```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Workflow settings
    WORKFLOW_ORCHESTRATOR_ENABLED: bool = True
    WORKFLOW_MAX_PHASE_ATTEMPTS: int = 3
    WORKFLOW_INTENT_CLASSIFICATION_MODEL: str = "gpt-3.5-turbo"
    WORKFLOW_EXECUTION_MODEL: str = "gpt-4"
    WORKFLOW_STATE_PERSISTENCE_ENABLED: bool = True
    WORKFLOW_FALLBACK_TO_TUTOR: bool = True
```

---

## History-Specific Workflow Example

### `src/workflows/flows/history_specific/timeline_exploration.py`
```python
"""History timeline exploration workflow."""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

from src.workflows.state import WorkflowState, HistoryTimelineState, HistoryThinkingSkill
from src.workflows.base import BaseWorkflow

logger = logging.getLogger(__name__)


class TimelineExplorationFlow(BaseWorkflow):
    """Interactive historical timeline exploration."""
    
    async def execute(self, state: WorkflowState, memory_manager) -> WorkflowState:
        """Execute timeline exploration workflow."""
        
        # Convert to timeline-specific state
        timeline_state = HistoryTimelineState(**state)
        
        # Initialize timeline if not set
        if not timeline_state.get("time_period"):
            timeline_state["time_period"] = await self._extract_time_period(
                timeline_state["messages"][-1]["content"]
            )
        
        if not timeline_state.get("timeline_events"):
            timeline_state["timeline_events"] = await self._generate_timeline_events(
                timeline_state["time_period"], memory_manager
            )
        
        if not timeline_state.get("thinking_skill_focus"):
            timeline_state["thinking_skill_focus"] = HistoryThinkingSkill.CHRONOLOGICAL_REASONING
        
        # Execute timeline interaction
        timeline_state = await self._interactive_timeline_exploration(timeline_state)
        
        return timeline_state
    
    async def _extract_time_period(self, message: str) -> str:
        """Extract historical time period from message."""
        # Pattern matching for common periods
        periods = {
            r'\bworld war i|wwi|first world war\b': "World War I (1914-1918)",
            r'\bworld war ii|wwii|second world war\b': "World War II (1939-1945)",
            r'\bfrench revolution\b': "French Revolution (1789-1799)",
            r'\bamerican revolution\b': "American Revolution (1775-1783)",
            r'\bcivil war\b': "American Civil War (1861-1865)",
            r'\bancient rome|roman empire\b': "Roman Empire (27 BC - 476 AD)",
            r'\bmedieval|middle ages\b': "Medieval Period (500-1500 AD)"
        }
        
        import re
        message_lower = message.lower()
        
        for pattern, period in periods.items():
            if re.search(pattern, message_lower):
                return period
        
        return "Historical Period"
    
    async def _generate_timeline_events(
        self, 
        time_period: str, 
        memory_manager
    ) -> List[Dict[str, Any]]:
        """Generate key events for the timeline."""
        # This would query the RAG system for historical events
        events = [
            {
                "date": "1914-06-28",
                "title": "Assassination of Archduke Franz Ferdinand",
                "description": "The event that triggered World War I",
                "significance": "immediate_cause",
                "connections": ["alliance_system", "nationalism"]
            }
            # More events would be generated based on RAG retrieval
        ]
        return events
    
    async def _interactive_timeline_exploration(
        self, 
        state: HistoryTimelineState
    ) -> HistoryTimelineState:
        """Create interactive timeline exploration."""
        
        response = f"""
Let's explore the timeline of {state['time_period']}! Here are key events:

"""
        
        # Add timeline events
        for i, event in enumerate(state["timeline_events"][:5], 1):
            response += f"{i}. **{event['date']}**: {event['title']}\n   {event['description']}\n\n"
        
        response += """
Which event would you like to explore in more detail? I can help you understand:
- What led to this event (causes)
- What happened as a result (effects)  
- How it connects to other events
- Why it was historically significant

Just tell me the number or name of the event that interests you!
"""
        
        state["messages"].append({
            "role": "assistant",
            "content": response
        })
        
        state["current_phase"] = "timeline_interaction"
        state["workflow_complete"] = False
        
        return state
```

---

## Testing Strategy

### Unit Tests
```python
# tests/test_workflows/test_orchestrator.py
import pytest
from src.workflows.orchestrator import WorkflowOrchestrator
from src.workflows.state import WorkflowState, StudentIntent

@pytest.mark.asyncio
async def test_workflow_selection():
    """Test that correct workflows are selected based on intent."""
    orchestrator = WorkflowOrchestrator(mock_memory, mock_context_builder)
    
    # Test concept explanation selection
    state = WorkflowState(
        messages=[{"role": "user", "content": "Tell me about photosynthesis"}],
        student_id="test_student",
        session_id="test_session",
        student_intent=StudentIntent.NEW_TOPIC
    )
    
    updated_state = await orchestrator._select_workflow(state)
    assert updated_state["workflow_type"] == WorkflowType.CONCEPT_EXPLANATION

@pytest.mark.asyncio
async def test_history_specific_workflow_selection():
    """Test that History-specific workflows are selected correctly."""
    state = WorkflowState(
        messages=[{"role": "user", "content": "Show me a timeline of World War I"}],
        student_id="test_student", 
        session_id="test_session",
        subject="History",
        student_intent=StudentIntent.NEW_TOPIC
    )
    
    updated_state = await orchestrator._select_workflow(state)
    assert updated_state["workflow_type"] == WorkflowType.HISTORY_TIMELINE
```

### Integration Tests
```python
# tests/integration/test_workflow_flows.py
@pytest.mark.asyncio
async def test_complete_concept_explanation_flow():
    """Test complete concept explanation workflow."""
    # Simulate student asking about new concept
    # Verify workflow progresses through all phases
    # Check that appropriate responses are generated
    # Ensure workflow completes successfully
```

---

## Performance Considerations

### Workflow State Persistence
- Use LangGraph's MemorySaver for development
- Implement PostgreSQL-backed checkpointer for production
- Cache workflow state in Redis for fast access

### LLM Call Optimization
- Use cheaper models (GPT-3.5) for intent classification and simple tasks
- Use premium models (GPT-4) only for complex educational content generation
- Implement response caching for common educational patterns

### Scalability
- Workflow state is isolated per session (thread_id)
- Background workflow processing for non-interactive steps
- Horizontal scaling through stateless workflow execution

---

This LangGraph implementation transforms EduAGI from simple message routing to sophisticated educational workflows that adapt to student needs and provide structured learning experiences.