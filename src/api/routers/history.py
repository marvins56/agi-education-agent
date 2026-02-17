"""API endpoints for History-specific features."""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.history.timeline.generator import TimelineGenerator
from src.history.sources.analyzer import PrimarySourceAnalyzer
from src.history.dbq.workflow import DBQWorkflowManager
from src.history.schemas import (
    HistoricalPeriod, EventType, SourceType, HistoricalThinkingSkill
)
from src.api.middleware.auth import get_current_student

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["History"])


# Request/Response Models
class TimelineRequest(BaseModel):
    """Request to create a timeline."""
    title: str
    theme: str
    event_filters: Optional[Dict[str, Any]] = None
    date_range: Optional[tuple[str, str]] = None


class TimelineResponse(BaseModel):
    """Timeline response."""
    timeline_id: str
    title: str
    theme: str
    events_count: int
    date_range: Dict[str, str]
    difficulty: float
    study_time_minutes: int


class SourceAnalysisRequest(BaseModel):
    """Request for source analysis."""
    source_id: str
    student_response: Optional[str] = None
    guided_analysis: bool = True


class DBQSessionRequest(BaseModel):
    """Request to start DBQ session."""
    dbq_id: str
    session_config: Optional[Dict[str, Any]] = None


class DocumentAnalysisSubmission(BaseModel):
    """Document analysis submission."""
    session_id: str
    document_analyses: Dict[str, str]  # document_label -> analysis


class ThesisSubmission(BaseModel):
    """Thesis statement submission."""
    session_id: str
    thesis_statement: str


class EssaySubmission(BaseModel):
    """Essay submission."""
    session_id: str
    essay_text: str


# Dependencies
async def get_timeline_generator() -> TimelineGenerator:
    """Get timeline generator."""
    return TimelineGenerator()


async def get_source_analyzer() -> PrimarySourceAnalyzer:
    """Get source analyzer."""
    return PrimarySourceAnalyzer()


async def get_dbq_manager() -> DBQWorkflowManager:
    """Get DBQ workflow manager."""
    return DBQWorkflowManager()


# Timeline Endpoints
@router.get("/timelines/available")
async def get_available_timelines(
    generator: TimelineGenerator = Depends(get_timeline_generator)
):
    """Get list of available timelines."""
    
    try:
        timelines = generator.get_available_timelines()
        return {
            "timelines": timelines,
            "total_count": len(timelines)
        }
    except Exception as e:
        logger.error(f"Error getting available timelines: {e}")
        raise HTTPException(status_code=500, detail="Failed to get timelines")


@router.post("/timelines/create", response_model=TimelineResponse)
async def create_timeline(
    request: TimelineRequest,
    current_student: dict = Depends(get_current_student),
    generator: TimelineGenerator = Depends(get_timeline_generator)
):
    """Create a custom timeline."""
    
    try:
        timeline = generator.create_timeline(
            title=request.title,
            theme=request.theme,
            event_filters=request.event_filters,
            date_range=request.date_range
        )
        
        return TimelineResponse(
            timeline_id=timeline.timeline_id,
            title=timeline.title,
            theme=timeline.theme,
            events_count=len(timeline.events),
            date_range={
                "start": timeline.date_range_start,
                "end": timeline.date_range_end
            },
            difficulty=timeline.difficulty_level,
            study_time_minutes=timeline.estimated_study_time_minutes
        )
        
    except Exception as e:
        logger.error(f"Error creating timeline: {e}")
        raise HTTPException(status_code=500, detail="Failed to create timeline")


@router.get("/timelines/{timeline_id}")
async def get_timeline(
    timeline_id: str,
    generator: TimelineGenerator = Depends(get_timeline_generator)
):
    """Get timeline data for visualization."""
    
    try:
        timeline_data = generator.export_timeline_data(timeline_id)
        
        if not timeline_data:
            raise HTTPException(status_code=404, detail="Timeline not found")
        
        return timeline_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting timeline {timeline_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get timeline")


@router.get("/timelines/{timeline_id}/events/{event_id}/relationships")
async def get_event_relationships(
    timeline_id: str,
    event_id: str,
    generator: TimelineGenerator = Depends(get_timeline_generator)
):
    """Get relationships for a specific event."""
    
    try:
        relationships = generator.get_event_relationships(event_id)
        
        if not relationships:
            raise HTTPException(status_code=404, detail="Event not found")
        
        return relationships
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting event relationships: {e}")
        raise HTTPException(status_code=500, detail="Failed to get relationships")


@router.post("/timelines/causal-chain")
async def create_causal_chain_timeline(
    root_event_id: str = Query(..., description="Root event ID for causal chain"),
    title: Optional[str] = Query("Cause and Effect Timeline", description="Timeline title"),
    generator: TimelineGenerator = Depends(get_timeline_generator)
):
    """Create a causal chain timeline starting from a root event."""
    
    try:
        timeline = generator.create_causal_chain_timeline(root_event_id, title)
        
        return TimelineResponse(
            timeline_id=timeline.timeline_id,
            title=timeline.title,
            theme=timeline.theme,
            events_count=len(timeline.events),
            date_range={
                "start": timeline.date_range_start,
                "end": timeline.date_range_end
            },
            difficulty=timeline.difficulty_level,
            study_time_minutes=timeline.estimated_study_time_minutes
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating causal chain timeline: {e}")
        raise HTTPException(status_code=500, detail="Failed to create causal timeline")


@router.post("/timelines/comparative")
async def create_comparative_timeline(
    themes: List[str] = Query(..., description="Themes to compare"),
    title: Optional[str] = Query("Comparative Timeline", description="Timeline title"),
    generator: TimelineGenerator = Depends(get_timeline_generator)
):
    """Create a comparative timeline for multiple themes."""
    
    try:
        timeline = generator.create_comparative_timeline(themes, title)
        
        return TimelineResponse(
            timeline_id=timeline.timeline_id,
            title=timeline.title,
            theme=timeline.theme,
            events_count=len(timeline.events),
            date_range={
                "start": timeline.date_range_start,
                "end": timeline.date_range_end
            },
            difficulty=timeline.difficulty_level,
            study_time_minutes=timeline.estimated_study_time_minutes
        )
        
    except Exception as e:
        logger.error(f"Error creating comparative timeline: {e}")
        raise HTTPException(status_code=500, detail="Failed to create comparative timeline")


# Primary Source Analysis Endpoints
@router.get("/sources/available")
async def get_available_sources(
    analyzer: PrimarySourceAnalyzer = Depends(get_source_analyzer)
):
    """Get available template sources for analysis."""
    
    try:
        sources = analyzer.get_template_sources()
        return {
            "sources": sources,
            "total_count": len(sources)
        }
    except Exception as e:
        logger.error(f"Error getting available sources: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sources")


@router.get("/sources/{source_id}")
async def get_source_details(
    source_id: str,
    analyzer: PrimarySourceAnalyzer = Depends(get_source_analyzer)
):
    """Get detailed information about a specific source."""
    
    try:
        source = analyzer.get_source_by_id(source_id)
        
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        
        return {
            "source_id": source.source_id,
            "title": source.title,
            "description": source.description,
            "source_type": source.source_type.value,
            "content": source.content,
            "author": source.author,
            "date_created": source.date_created,
            "origin_location": source.origin_location,
            "historical_period": source.historical_period.value,
            "intended_audience": source.intended_audience,
            "purpose": source.purpose,
            "key_concepts": source.key_concepts,
            "discussion_questions": source.discussion_questions,
            "complexity_level": source.complexity_level
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting source details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get source details")


@router.post("/sources/analyze")
async def analyze_primary_source(
    request: SourceAnalysisRequest,
    current_student: dict = Depends(get_current_student),
    analyzer: PrimarySourceAnalyzer = Depends(get_source_analyzer)
):
    """Analyze a primary source with optional student response."""
    
    try:
        source = analyzer.get_source_by_id(request.source_id)
        
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        
        analysis = analyzer.analyze_source(
            source=source,
            student_response=request.student_response,
            guided_analysis=request.guided_analysis
        )
        
        return {
            "source_id": request.source_id,
            "analysis": analysis,
            "student_id": current_student["id"],
            "analyzed_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing source: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze source")


# DBQ Endpoints
@router.get("/dbq/available")
async def get_available_dbqs(
    dbq_manager: DBQWorkflowManager = Depends(get_dbq_manager)
):
    """Get available DBQ sets."""
    
    try:
        dbqs = dbq_manager.get_dbq_templates()
        return {
            "dbqs": dbqs,
            "total_count": len(dbqs)
        }
    except Exception as e:
        logger.error(f"Error getting available DBQs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get DBQs")


@router.get("/dbq/{dbq_id}")
async def get_dbq_details(
    dbq_id: str,
    dbq_manager: DBQWorkflowManager = Depends(get_dbq_manager)
):
    """Get detailed information about a DBQ set."""
    
    try:
        dbq_set = dbq_manager.get_dbq_by_id(dbq_id)
        
        if not dbq_set:
            raise HTTPException(status_code=404, detail="DBQ not found")
        
        return {
            "dbq_id": dbq_set.dbq_id,
            "title": dbq_set.title,
            "prompt": {
                "historical_question": dbq_set.prompt.historical_question,
                "task_description": dbq_set.prompt.task_description,
                "historical_context": dbq_set.prompt.historical_context_provided,
                "time_period": dbq_set.prompt.time_period,
                "essay_length": dbq_set.prompt.essay_length_words,
                "minimum_documents": dbq_set.prompt.minimum_documents_required,
                "outside_evidence_required": dbq_set.prompt.outside_evidence_required
            },
            "documents": [
                {
                    "document_id": doc.document_id,
                    "document_label": doc.document_label,
                    "title": doc.source.title,
                    "description": doc.source.description,
                    "source_type": doc.source.source_type.value,
                    "content": doc.source.content,
                    "author": doc.source.author,
                    "date_created": doc.source.date_created,
                    "guiding_questions": doc.guiding_questions
                }
                for doc in dbq_set.documents
            ],
            "historical_period": dbq_set.historical_period.value,
            "theme": dbq_set.theme,
            "difficulty_level": dbq_set.difficulty_level,
            "estimated_time_minutes": dbq_set.estimated_time_minutes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting DBQ details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get DBQ details")


@router.post("/dbq/sessions/start")
async def start_dbq_session(
    request: DBQSessionRequest,
    current_student: dict = Depends(get_current_student),
    dbq_manager: DBQWorkflowManager = Depends(get_dbq_manager)
):
    """Start a new DBQ session."""
    
    try:
        student_id = current_student["id"]
        
        session = dbq_manager.start_dbq_session(
            student_id=student_id,
            dbq_id=request.dbq_id,
            session_config=request.session_config
        )
        
        return {
            "session_id": session["session_id"],
            "dbq_id": session["dbq_id"],
            "current_phase": session["current_phase"],
            "started_at": session["started_at"].isoformat(),
            "dbq_info": {
                "title": session["dbq_set"].title,
                "document_count": len(session["dbq_set"].documents),
                "estimated_time": session["dbq_set"].estimated_time_minutes
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting DBQ session: {e}")
        raise HTTPException(status_code=500, detail="Failed to start DBQ session")


@router.post("/dbq/sessions/analyze-documents")
async def submit_document_analyses(
    submission: DocumentAnalysisSubmission,
    current_student: dict = Depends(get_current_student),
    dbq_manager: DBQWorkflowManager = Depends(get_dbq_manager)
):
    """Submit document analyses for a DBQ session."""
    
    try:
        # In a real implementation, would retrieve session from database
        # For now, creating a mock session structure
        session = {
            "session_id": submission.session_id,
            "student_id": current_student["id"],
            "dbq_set": dbq_manager.get_dbq_by_id("wwi_causes"),  # Mock
            "current_phase": "document_analysis",
            "phases_completed": []
        }
        
        result = dbq_manager.analyze_documents_phase(
            session=session,
            document_analyses=submission.document_analyses
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing document analyses: {e}")
        raise HTTPException(status_code=500, detail="Failed to process document analyses")


@router.post("/dbq/sessions/submit-thesis")
async def submit_thesis(
    submission: ThesisSubmission,
    current_student: dict = Depends(get_current_student),
    dbq_manager: DBQWorkflowManager = Depends(get_dbq_manager)
):
    """Submit thesis statement for evaluation."""
    
    try:
        # Mock session - in real implementation would retrieve from database
        session = {
            "session_id": submission.session_id,
            "student_id": current_student["id"],
            "dbq_set": dbq_manager.get_dbq_by_id("wwi_causes"),  # Mock
            "current_phase": "thesis_development",
            "phases_completed": ["document_analysis"]
        }
        
        result = dbq_manager.thesis_development_phase(
            session=session,
            proposed_thesis=submission.thesis_statement
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing thesis submission: {e}")
        raise HTTPException(status_code=500, detail="Failed to process thesis")


@router.post("/dbq/sessions/submit-essay")
async def submit_essay(
    submission: EssaySubmission,
    current_student: dict = Depends(get_current_student),
    dbq_manager: DBQWorkflowManager = Depends(get_dbq_manager)
):
    """Submit complete DBQ essay for grading."""
    
    try:
        # Mock session - in real implementation would retrieve from database
        session = {
            "session_id": submission.session_id,
            "student_id": current_student["id"],
            "dbq_id": "wwi_causes",
            "dbq_set": dbq_manager.get_dbq_by_id("wwi_causes"),  # Mock
            "current_phase": "essay_writing",
            "phases_completed": ["document_analysis", "thesis_development"],
            "proposed_thesis": "The primary causes of World War I were...",  # Would be retrieved
            "essay_drafts": []
        }
        
        result = dbq_manager.essay_writing_phase(
            session=session,
            essay_draft=submission.essay_text
        )
        
        return {
            "essay_id": result["essay"].essay_id,
            "overall_score": result["essay"].score,
            "grade_level": result["grading_results"]["grade_level"],
            "rubric_scores": result["essay"].rubric_scores,
            "feedback": result["essay"].feedback,
            "word_count": result["essay"].word_count,
            "documents_used_count": len(result["essay"].documents_used),
            "next_steps": result["next_steps"]
        }
        
    except Exception as e:
        logger.error(f"Error processing essay submission: {e}")
        raise HTTPException(status_code=500, detail="Failed to process essay")


# Historical Thinking Skills Endpoints
@router.get("/thinking-skills")
async def get_thinking_skills():
    """Get list of historical thinking skills."""
    
    skills = [
        {
            "skill": skill.value,
            "name": skill.value.replace("_", " ").title(),
            "description": f"Practice {skill.value.replace('_', ' ')} skills"
        }
        for skill in HistoricalThinkingSkill
    ]
    
    return {
        "thinking_skills": skills,
        "total_count": len(skills)
    }


@router.get("/periods")
async def get_historical_periods():
    """Get list of historical periods."""
    
    periods = [
        {
            "period": period.value,
            "name": period.value.replace("_", " ").title(),
            "description": f"Study the {period.value.replace('_', ' ')} period"
        }
        for period in HistoricalPeriod
    ]
    
    return {
        "periods": periods,
        "total_count": len(periods)
    }


@router.get("/events/types")
async def get_event_types():
    """Get list of event types."""
    
    types = [
        {
            "type": event_type.value,
            "name": event_type.value.title(),
            "description": f"Focus on {event_type.value} events"
        }
        for event_type in EventType
    ]
    
    return {
        "event_types": types,
        "total_count": len(types)
    }


@router.get("/sources/types")
async def get_source_types():
    """Get list of source types."""
    
    types = [
        {
            "type": source_type.value,
            "name": source_type.value.replace("_", " ").title(),
            "description": f"Analyze {source_type.value.replace('_', ' ')} sources"
        }
        for source_type in SourceType
    ]
    
    return {
        "source_types": types,
        "total_count": len(types)
    }


@router.get("/analytics/history-learning")
async def get_history_learning_analytics(
    current_student: dict = Depends(get_current_student),
    days_back: int = Query(30, ge=1, le=365)
):
    """Get History-specific learning analytics."""
    
    try:
        student_id = current_student["id"]
        
        # This would integrate with the adaptive learning system and assessment data
        # For now, return mock analytics structure
        
        analytics = {
            "student_id": student_id,
            "time_period_analyzed": f"Last {days_back} days",
            
            "thinking_skills_progress": {
                skill.value: {
                    "current_level": 3,  # Mock data
                    "assessments_completed": 5,
                    "improvement_trend": "improving"
                }
                for skill in HistoricalThinkingSkill
            },
            
            "period_mastery": {
                period.value: {
                    "mastery_score": 0.75,  # Mock data
                    "events_studied": 12,
                    "sources_analyzed": 8
                }
                for period in HistoricalPeriod
            },
            
            "source_analysis_skills": {
                "total_sources_analyzed": 25,
                "average_analysis_score": 82.5,
                "bias_detection_accuracy": 0.78,
                "reliability_assessment_quality": 0.85
            },
            
            "dbq_performance": {
                "dbqs_completed": 3,
                "average_score": 78.3,
                "strongest_area": "document_usage",
                "area_for_improvement": "outside_evidence",
                "thesis_quality_trend": "improving"
            },
            
            "timeline_engagement": {
                "timelines_created": 8,
                "events_explored": 156,
                "causal_connections_made": 34
            },
            
            "recommendations": [
                "Focus on incorporating more outside evidence in DBQ essays",
                "Practice analyzing source bias and reliability",
                "Explore cause-and-effect relationships in more depth"
            ],
            
            "calculated_at": datetime.now().isoformat()
        }
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting history learning analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")