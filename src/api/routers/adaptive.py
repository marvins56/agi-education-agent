"""API endpoints for adaptive learning engine."""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.adaptive.engine import AdaptiveLearningEngine
from src.adaptive.schemas import (
    AdaptiveRecommendation, StudentInteraction, KnowledgeState,
    FSRSCard, LearningStyleProfile
)
from src.api.dependencies import get_current_user, get_memory
from src.api.middleware.auth import get_current_student
from src.memory.manager import MemoryManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/adaptive", tags=["Adaptive Learning"])


# Response models
class StudentInteractionRequest(BaseModel):
    """Request model for recording student interactions."""
    concept_id: int
    concept_name: str
    question_type: str
    correctness: float = Field(ge=0.0, le=1.0)
    response_time_seconds: float
    hint_count: int = 0
    difficulty_level: float = Field(ge=0.0, le=1.0, default=0.5)
    context_features: Dict[str, Any] = Field(default_factory=dict)


class RecommendationRequest(BaseModel):
    """Request model for getting adaptive recommendations."""
    current_topic: Optional[str] = None
    session_time_budget_minutes: int = Field(default=30, ge=5, le=120)
    learning_objectives: Optional[List[str]] = None


class KnowledgeStateResponse(BaseModel):
    """Response model for knowledge state."""
    student_id: str
    concept_probabilities: Dict[str, float]
    knowledge_growth_rate: float
    forgetting_rate: float
    learning_efficiency: float
    interaction_count: int
    last_updated: datetime


class AdaptiveRecommendationResponse(BaseModel):
    """Response model for adaptive recommendations."""
    student_id: str
    next_concept: Optional[str]
    next_difficulty: float
    teaching_strategy: str
    concepts_to_review: List[Dict[str, Any]]
    recommended_sequence: List[str]
    recommendation_confidence: float
    reasoning: str


class LearningStyleResponse(BaseModel):
    """Response model for learning style profile."""
    student_id: str
    visual_preference: float
    auditory_preference: float
    kinesthetic_preference: float
    reading_preference: float
    sequential_vs_global: float
    active_vs_reflective: float
    sensing_vs_intuitive: float
    preferred_session_length_minutes: int
    last_updated: datetime


async def get_adaptive_engine(
    memory_manager: MemoryManager = Depends(get_memory),
) -> AdaptiveLearningEngine:
    """Dependency to get adaptive learning engine."""
    return AdaptiveLearningEngine(memory_manager)


@router.post("/interactions", response_model=KnowledgeStateResponse)
async def record_interaction(
    interaction_data: StudentInteractionRequest,
    session_id: str = Query(..., description="Current session ID"),
    current_student: dict = Depends(get_current_student),
    engine: AdaptiveLearningEngine = Depends(get_adaptive_engine)
):
    """Record a student learning interaction and update knowledge state."""
    
    try:
        student_id = str(current_student.id)
        
        # Create interaction object
        interaction = StudentInteraction(
            student_id=student_id,
            session_id=session_id,
            concept_id=interaction_data.concept_id,
            concept_name=interaction_data.concept_name,
            question_type=interaction_data.question_type,
            correctness=interaction_data.correctness,
            response_time_seconds=interaction_data.response_time_seconds,
            hint_count=interaction_data.hint_count,
            difficulty_level=interaction_data.difficulty_level,
            context_features=interaction_data.context_features,
            timestamp=datetime.now()
        )
        
        # Update student knowledge
        knowledge_state = await engine.update_student_knowledge(student_id, interaction)
        
        return KnowledgeStateResponse(
            student_id=knowledge_state.student_id,
            concept_probabilities=knowledge_state.concept_probabilities,
            knowledge_growth_rate=knowledge_state.knowledge_growth_rate,
            forgetting_rate=knowledge_state.forgetting_rate,
            learning_efficiency=knowledge_state.learning_efficiency,
            interaction_count=knowledge_state.interaction_count,
            last_updated=knowledge_state.last_updated
        )
        
    except Exception as e:
        logger.error(f"Error recording interaction: {e}")
        raise HTTPException(status_code=500, detail="Failed to record interaction")


@router.get("/knowledge-state", response_model=KnowledgeStateResponse)
async def get_knowledge_state(
    current_student: dict = Depends(get_current_student),
    engine: AdaptiveLearningEngine = Depends(get_adaptive_engine)
):
    """Get current student knowledge state."""
    
    try:
        student_id = str(current_student.id)
        knowledge_state = await engine._get_knowledge_state(student_id)
        
        return KnowledgeStateResponse(
            student_id=knowledge_state.student_id,
            concept_probabilities=knowledge_state.concept_probabilities,
            knowledge_growth_rate=knowledge_state.knowledge_growth_rate,
            forgetting_rate=knowledge_state.forgetting_rate,
            learning_efficiency=knowledge_state.learning_efficiency,
            interaction_count=knowledge_state.interaction_count,
            last_updated=knowledge_state.last_updated
        )
        
    except Exception as e:
        logger.error(f"Error getting knowledge state: {e}")
        raise HTTPException(status_code=500, detail="Failed to get knowledge state")


@router.post("/recommendations", response_model=AdaptiveRecommendationResponse)
async def get_recommendations(
    request: RecommendationRequest,
    current_student: dict = Depends(get_current_student),
    engine: AdaptiveLearningEngine = Depends(get_adaptive_engine)
):
    """Get personalized learning recommendations."""
    
    try:
        student_id = str(current_student.id)
        
        recommendation = await engine.get_adaptive_recommendations(
            student_id=student_id,
            current_topic=request.current_topic,
            session_time_budget_minutes=request.session_time_budget_minutes,
            learning_objectives=request.learning_objectives
        )
        
        # Format concepts_to_review for response
        concepts_to_review = [
            {
                "concept_name": concept_name,
                "due_date": due_date.isoformat()
            }
            for concept_name, due_date in recommendation.concepts_to_review
        ]
        
        return AdaptiveRecommendationResponse(
            student_id=recommendation.student_id,
            next_concept=recommendation.next_concept,
            next_difficulty=recommendation.next_difficulty,
            teaching_strategy=recommendation.teaching_strategy,
            concepts_to_review=concepts_to_review,
            recommended_sequence=recommendation.recommended_sequence,
            recommendation_confidence=recommendation.recommendation_confidence,
            reasoning=recommendation.reasoning
        )
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")


@router.get("/learning-style", response_model=LearningStyleResponse)
async def get_learning_style(
    current_student: dict = Depends(get_current_student),
    engine: AdaptiveLearningEngine = Depends(get_adaptive_engine)
):
    """Get student's learning style profile."""
    
    try:
        student_id = str(current_student.id)
        
        # Get interaction history
        interaction_history = await engine._get_interaction_history(student_id)
        
        # Detect learning style
        learning_style = await engine.learning_style_detector.detect_style(
            student_id, interaction_history
        )
        
        # Create full profile
        profile = await engine.learning_style_detector.create_learning_style_profile(
            student_id, interaction_history
        )
        
        return LearningStyleResponse(
            student_id=profile.student_id,
            visual_preference=profile.visual_preference,
            auditory_preference=profile.auditory_preference,
            kinesthetic_preference=profile.kinesthetic_preference,
            reading_preference=profile.reading_preference,
            sequential_vs_global=profile.sequential_vs_global,
            active_vs_reflective=profile.active_vs_reflective,
            sensing_vs_intuitive=profile.sensing_vs_intuitive,
            preferred_session_length_minutes=profile.preferred_session_length_minutes,
            last_updated=profile.last_updated
        )
        
    except Exception as e:
        logger.error(f"Error getting learning style: {e}")
        raise HTTPException(status_code=500, detail="Failed to get learning style")


@router.get("/spaced-repetition/due")
async def get_due_reviews(
    current_student: dict = Depends(get_current_student),
    engine: AdaptiveLearningEngine = Depends(get_adaptive_engine)
):
    """Get concepts due for spaced repetition review."""
    
    try:
        student_id = str(current_student.id)
        fsrs_cards = await engine._get_student_fsrs_cards(student_id)
        
        # Get due cards
        due_cards = engine.fsrs_scheduler.get_due_cards(fsrs_cards)
        
        return {
            "student_id": student_id,
            "due_count": len(due_cards),
            "due_concepts": [
                {
                    "concept_name": card.concept_name,
                    "due_date": card.due_date.isoformat(),
                    "stability": card.stability,
                    "difficulty": card.difficulty,
                    "retrievability": card.retrievability,
                    "review_count": card.review_count,
                    "success_rate": card.success_rate
                }
                for card in due_cards
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting due reviews: {e}")
        raise HTTPException(status_code=500, detail="Failed to get due reviews")


@router.get("/knowledge-graph/concepts")
async def get_knowledge_graph_concepts(
    topic: Optional[str] = Query(None, description="Filter by topic"),
    difficulty_min: float = Query(0.0, ge=0.0, le=1.0),
    difficulty_max: float = Query(1.0, ge=0.0, le=1.0),
    engine: AdaptiveLearningEngine = Depends(get_adaptive_engine)
):
    """Get concepts from the knowledge graph."""
    
    try:
        concepts = []
        
        for concept_id, concept in engine.knowledge_graph.concepts.items():
            # Apply filters
            if topic and topic.lower() not in concept.concept_name.lower():
                continue
            
            if not (difficulty_min <= concept.difficulty <= difficulty_max):
                continue
            
            # Get prerequisites
            prereq_names = []
            for prereq_id in concept.prerequisites:
                prereq_concept = engine.knowledge_graph.concepts.get(prereq_id)
                if prereq_concept:
                    prereq_names.append(prereq_concept.concept_name)
            
            concepts.append({
                "concept_id": concept.concept_id,
                "concept_name": concept.concept_name,
                "subject": concept.subject,
                "difficulty": concept.difficulty,
                "importance": concept.importance,
                "prerequisites": prereq_names
            })
        
        return {
            "total_concepts": len(concepts),
            "concepts": concepts
        }
        
    except Exception as e:
        logger.error(f"Error getting knowledge graph concepts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get concepts")


@router.get("/analytics/learning-progress")
async def get_learning_progress(
    days_back: int = Query(30, ge=1, le=365),
    current_student: dict = Depends(get_current_student),
    engine: AdaptiveLearningEngine = Depends(get_adaptive_engine)
):
    """Get student learning progress analytics."""
    
    try:
        student_id = str(current_student.id)
        
        # Get recent interactions
        interactions = await engine._get_interaction_history(student_id)
        
        # Calculate progress metrics
        if not interactions:
            return {
                "student_id": student_id,
                "days_analyzed": days_back,
                "total_interactions": 0,
                "average_correctness": 0.0,
                "concepts_practiced": 0,
                "learning_efficiency": 0.0,
                "progress_trend": "insufficient_data"
            }
        
        # Filter to recent interactions
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_interactions = [
            i for i in interactions if i.timestamp >= cutoff_date
        ]
        
        if not recent_interactions:
            return {
                "student_id": student_id,
                "days_analyzed": days_back,
                "total_interactions": 0,
                "average_correctness": 0.0,
                "concepts_practiced": 0,
                "learning_efficiency": 0.0,
                "progress_trend": "no_recent_activity"
            }
        
        # Calculate metrics
        total_interactions = len(recent_interactions)
        average_correctness = sum(i.correctness for i in recent_interactions) / total_interactions
        concepts_practiced = len(set(i.concept_name for i in recent_interactions))
        
        # Calculate learning efficiency
        total_time = sum(i.response_time_seconds for i in recent_interactions)
        efficiency = (average_correctness * total_interactions) / max(total_time / 60, 1)  # Per minute
        
        # Determine trend
        first_half = recent_interactions[:total_interactions//2]
        second_half = recent_interactions[total_interactions//2:]
        
        if len(first_half) > 0 and len(second_half) > 0:
            first_avg = sum(i.correctness for i in first_half) / len(first_half)
            second_avg = sum(i.correctness for i in second_half) / len(second_half)
            
            if second_avg > first_avg + 0.1:
                trend = "improving"
            elif second_avg < first_avg - 0.1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "student_id": student_id,
            "days_analyzed": days_back,
            "total_interactions": total_interactions,
            "average_correctness": round(average_correctness, 3),
            "concepts_practiced": concepts_practiced,
            "learning_efficiency": round(efficiency, 3),
            "progress_trend": trend,
            "daily_breakdown": _calculate_daily_breakdown(recent_interactions)
        }
        
    except Exception as e:
        logger.error(f"Error getting learning progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to get learning progress")


def _calculate_daily_breakdown(interactions: List[StudentInteraction]) -> List[Dict[str, Any]]:
    """Calculate daily breakdown of learning activity."""
    
    daily_stats = {}
    
    for interaction in interactions:
        date_key = interaction.timestamp.date().isoformat()
        
        if date_key not in daily_stats:
            daily_stats[date_key] = {
                "date": date_key,
                "interaction_count": 0,
                "total_correctness": 0.0,
                "total_time_minutes": 0.0,
                "concepts_practiced": set()
            }
        
        stats = daily_stats[date_key]
        stats["interaction_count"] += 1
        stats["total_correctness"] += interaction.correctness
        stats["total_time_minutes"] += interaction.response_time_seconds / 60
        stats["concepts_practiced"].add(interaction.concept_name)
    
    # Convert to list and calculate averages
    breakdown = []
    for stats in daily_stats.values():
        breakdown.append({
            "date": stats["date"],
            "interaction_count": stats["interaction_count"],
            "average_correctness": stats["total_correctness"] / stats["interaction_count"],
            "total_time_minutes": round(stats["total_time_minutes"], 1),
            "unique_concepts": len(stats["concepts_practiced"])
        })
    
    # Sort by date
    breakdown.sort(key=lambda x: x["date"])
    
    return breakdown[-30:]  # Return last 30 days max