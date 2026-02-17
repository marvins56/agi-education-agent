"""Tests for the LangGraph workflow system."""
import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock

from src.workflows.orchestrator import WorkflowOrchestrator
from src.workflows.intent_classifier import IntentClassifier
from src.workflows.flows.concept_explanation import ConceptExplanationFlow
from src.workflows.state import StudentIntent, WorkflowType, LearningPhase
from src.context.schemas import TutoringContext, AnnotatedMessage
from src.agents.base import AgentContext


@pytest.fixture
def tutoring_context():
    """Create a sample tutoring context for testing."""
    return TutoringContext(
        session_id="test_session_123",
        student_id="test_student_456",
        active_messages=[
            AnnotatedMessage(
                role="user",
                content="What is the American Revolution?",
                timestamp=datetime.now(timezone.utc),
                token_count=6,
                annotations=[]
            )
        ],
        session_summaries=[],
        topic_mastery={"american_revolution": 0.3, "colonial_period": 0.6},
        learning_patterns={"subject": "History", "learning_style": "visual"},
        effective_teaching_methods=["scaffolding", "examples"]
    )


@pytest.fixture
def agent_context():
    """Create a sample agent context for testing."""
    return AgentContext(
        student_id="test_student_456",
        session_id="test_session_123",
        conversation_history=[],
        student_profile={}
    )


@pytest.mark.asyncio
async def test_intent_classifier_basic_functionality():
    """Test basic intent classification functionality."""
    classifier = IntentClassifier()
    
    # Create minimal context
    context = TutoringContext(
        session_id="test",
        student_id="test",
        active_messages=[],
        topic_mastery={"revolution": 0.5}
    )
    
    # Test fallback classification (since LLM might not be available)
    classification = await classifier._fallback_classification(
        "What is the American Revolution?",
        context
    )
    
    assert "primary_intent" in classification
    assert "confidence" in classification
    assert classification["primary_intent"] in [intent.value for intent in StudentIntent]
    assert 0.0 <= classification["confidence"] <= 1.0


@pytest.mark.asyncio
async def test_concept_explanation_workflow_initialization():
    """Test concept explanation workflow initialization."""
    workflow = ConceptExplanationFlow()
    
    # Verify workflow is properly initialized
    assert workflow.workflow_type == WorkflowType.CONCEPT_EXPLANATION
    assert workflow.graph is not None
    
    # Test state initialization
    context = TutoringContext(
        session_id="test",
        student_id="test_student",
        active_messages=[],
        topic_mastery={"american_revolution": 0.4}
    )
    
    initial_state = await workflow.initialize_state(
        message="Tell me about the American Revolution",
        tutoring_context=context
    )
    
    assert initial_state["student_id"] == "test_student"
    assert initial_state["session_id"] == "test"
    assert initial_state["workflow_type"] == WorkflowType.CONCEPT_EXPLANATION
    assert "American Revolution" in initial_state["concept_name"]
    assert initial_state["current_phase"] == LearningPhase.ASSESS_PRIOR_KNOWLEDGE


@pytest.mark.asyncio
async def test_concept_explanation_concept_extraction():
    """Test concept extraction from various message formats."""
    workflow = ConceptExplanationFlow()
    
    # Test "what is" pattern
    concept1 = workflow._extract_concept_from_message("What is the French Revolution?")
    assert "French Revolution" in concept1
    
    # Test "tell me about" pattern  
    concept2 = workflow._extract_concept_from_message("Tell me about World War I")
    assert "World War I" in concept2
    
    # Test fallback
    concept3 = workflow._extract_concept_from_message("I'm confused about stuff")
    assert concept3 == "Historical Topic"


@pytest.mark.asyncio
async def test_workflow_orchestrator_initialization():
    """Test workflow orchestrator initialization."""
    orchestrator = WorkflowOrchestrator()
    
    # Verify orchestrator is properly initialized
    assert isinstance(orchestrator.intent_classifier, IntentClassifier)
    assert len(orchestrator.workflows) > 0
    assert WorkflowType.CONCEPT_EXPLANATION in orchestrator.workflows
    
    # Test available workflows
    available_workflows = await orchestrator.get_available_workflows()
    assert WorkflowType.CONCEPT_EXPLANATION in available_workflows


@pytest.mark.asyncio
async def test_workflow_selection_strategies():
    """Test workflow selection strategies."""
    orchestrator = WorkflowOrchestrator()
    
    context = TutoringContext(
        session_id="test",
        student_id="test",
        active_messages=[],
        topic_mastery={}
    )
    
    # Test new topic selection
    new_topic_workflow = await orchestrator._select_new_topic_workflow(
        intent_classification={"topic_keywords": ["revolution", "war"]},
        tutoring_context=context
    )
    assert new_topic_workflow == WorkflowType.CONCEPT_EXPLANATION
    
    # Test clarification selection
    clarification_workflow = await orchestrator._select_clarification_workflow(
        intent_classification={},
        tutoring_context=context
    )
    # Should fallback to concept explanation since Socratic questioning not implemented
    assert isinstance(clarification_workflow, WorkflowType)


@pytest.mark.asyncio
async def test_concept_extraction_from_orchestrator():
    """Test concept extraction in orchestrator."""
    orchestrator = WorkflowOrchestrator()
    
    # Test with topic keywords
    concept1 = orchestrator._extract_concept_name(
        "Tell me about it",
        {"topic_keywords": ["revolution", "american"]}
    )
    assert "Revolution American" in concept1
    
    # Test with message pattern
    concept2 = orchestrator._extract_concept_name(
        "What is photosynthesis?",
        {"topic_keywords": []}
    )
    assert "Photosynthesis" in concept2


def test_student_intent_enum():
    """Test StudentIntent enum values."""
    assert StudentIntent.NEW_TOPIC.value == "new_topic"
    assert StudentIntent.CLARIFICATION.value == "clarification"
    assert StudentIntent.PRACTICE.value == "practice"
    assert StudentIntent.ASSESSMENT.value == "assessment"


def test_workflow_type_enum():
    """Test WorkflowType enum values."""
    assert WorkflowType.CONCEPT_EXPLANATION.value == "concept_explanation"
    assert WorkflowType.SOCRATIC_QUESTIONING.value == "socratic_questioning"
    assert WorkflowType.PRACTICE_PROBLEMS.value == "practice_problems"


def test_learning_phase_enum():
    """Test LearningPhase enum values."""
    assert LearningPhase.ASSESS_PRIOR_KNOWLEDGE.value == "assess_prior_knowledge"
    assert LearningPhase.INTRODUCE_CONCEPT.value == "introduce_concept"
    assert LearningPhase.GUIDED_PRACTICE.value == "guided_practice"


@pytest.mark.asyncio
async def test_orchestrator_basic_tutoring_context_creation():
    """Test creation of basic tutoring context."""
    orchestrator = WorkflowOrchestrator()
    
    agent_context = AgentContext(
        student_id="test_student",
        session_id="test_session",
        conversation_history=[],
        student_profile={}
    )
    
    tutoring_context = orchestrator._create_basic_tutoring_context(agent_context)
    
    assert tutoring_context.student_id == "test_student"
    assert tutoring_context.session_id == "test_session"
    assert tutoring_context.learning_patterns.get("subject") == "History"


@pytest.mark.asyncio
async def test_workflow_orchestrator_fallback_response(agent_context):
    """Test fallback response when workflow isn't available."""
    orchestrator = WorkflowOrchestrator()
    
    response = await orchestrator._fallback_response("Hello", agent_context)
    
    assert response.agent_name == "WorkflowTutor"
    assert response.metadata.get("fallback") == True
    assert len(response.text) > 0


@pytest.mark.asyncio
async def test_workflow_orchestrator_error_response(agent_context):
    """Test error response handling."""
    orchestrator = WorkflowOrchestrator()
    
    response = await orchestrator._error_response("Test error", agent_context)
    
    assert response.agent_name == "WorkflowTutor" 
    assert response.metadata.get("error") == "Test error"
    assert "sorry" in response.text.lower()


@pytest.mark.asyncio
async def test_workflow_info_retrieval():
    """Test workflow information retrieval."""
    orchestrator = WorkflowOrchestrator()
    
    # Test available workflow
    info = await orchestrator.get_workflow_info(WorkflowType.CONCEPT_EXPLANATION)
    assert info["available"] == True
    assert info["workflow_type"] == "concept_explanation"
    assert "description" in info
    
    # Test unavailable workflow  
    info_unavailable = await orchestrator.get_workflow_info(WorkflowType.SOCRATIC_QUESTIONING)
    assert "error" in info_unavailable or info_unavailable.get("available") == True


if __name__ == "__main__":
    # Run tests
    asyncio.run(pytest.main([__file__, "-v"]))