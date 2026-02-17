"""API endpoints for voice integration."""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from pydantic import BaseModel, Field

from src.voice.conversation.manager import VoiceConversationManager
from src.voice.gateway import VoiceWebSocketGateway
from src.voice.schemas import (
    VoicePersona, AudioFormat, TTSConfig, STTConfig,
    TranscriptionResult, VoiceResponse
)
from src.voice.stt.whisper_client import WhisperSTTClient
from src.voice.tts.elevenlabs_client import ElevenLabsClient
from src.api.middleware.auth import get_current_student

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["Voice"])


# Request/Response Models
class VoiceSessionConfig(BaseModel):
    """Voice session configuration."""
    preferred_voice: VoicePersona = VoicePersona.SARAH_ENCOURAGING
    language: str = "en"
    auto_interrupt: bool = True


class VoiceSessionResponse(BaseModel):
    """Voice session response."""
    session_id: str
    student_id: str
    state: str
    preferred_voice: str
    language: str
    websocket_url: str


class TranscriptionRequest(BaseModel):
    """Request for audio transcription."""
    language: str = "en"
    provider: str = "whisper"


class TTSRequest(BaseModel):
    """Request for text-to-speech synthesis."""
    text: str = Field(max_length=5000)
    voice_persona: VoicePersona = VoicePersona.SARAH_ENCOURAGING
    format: AudioFormat = AudioFormat.MP3
    provider: str = "elevenlabs"


class VoiceCapabilitiesResponse(BaseModel):
    """Voice system capabilities."""
    stt_providers: list[str]
    tts_providers: list[str]
    supported_voices: list[str]
    supported_formats: list[str]
    max_audio_duration_ms: int
    streaming_supported: bool


# Dependency to get conversation manager
async def get_conversation_manager() -> VoiceConversationManager:
    """Get voice conversation manager."""
    # This should be injected properly in a real application
    from src.memory.manager import MemoryManager
    from src.agents.orchestrator import MasterOrchestrator
    
    # These would be dependency injected
    memory_manager = MemoryManager()
    orchestrator = MasterOrchestrator(memory_manager, None)
    
    manager = VoiceConversationManager(memory_manager, orchestrator)
    await manager.initialize()
    return manager


@router.get("/capabilities", response_model=VoiceCapabilitiesResponse)
async def get_voice_capabilities():
    """Get voice system capabilities."""
    return VoiceCapabilitiesResponse(
        stt_providers=["whisper", "deepgram"],
        tts_providers=["elevenlabs", "openai"],
        supported_voices=[persona.value for persona in VoicePersona],
        supported_formats=[fmt.value for fmt in AudioFormat],
        max_audio_duration_ms=300000,  # 5 minutes
        streaming_supported=True
    )


@router.post("/sessions", response_model=VoiceSessionResponse)
async def create_voice_session(
    config: VoiceSessionConfig = VoiceSessionConfig(),
    current_student: dict = Depends(get_current_student),
    manager: VoiceConversationManager = Depends(get_conversation_manager)
):
    """Create a new voice conversation session."""
    
    try:
        student_id = current_student["id"]
        session_id = str(uuid.uuid4())
        
        # Create session
        session = await manager.create_session(
            session_id=session_id,
            student_id=student_id,
            config=config.dict()
        )
        
        # Construct WebSocket URL
        websocket_url = f"/api/v1/voice/ws/{session_id}?student_id={student_id}"
        
        return VoiceSessionResponse(
            session_id=session.session_id,
            student_id=session.student_id,
            state=session.state.value,
            preferred_voice=session.preferred_voice.value,
            language=session.language,
            websocket_url=websocket_url
        )
        
    except Exception as e:
        logger.error(f"Error creating voice session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create voice session")


@router.get("/sessions/{session_id}/status")
async def get_session_status(
    session_id: str,
    current_student: dict = Depends(get_current_student),
    manager: VoiceConversationManager = Depends(get_conversation_manager)
):
    """Get voice session status."""
    
    try:
        analytics = await manager.get_session_analytics(session_id)
        
        if not analytics:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check if student owns the session
        if analytics["student_id"] != current_student["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get session status")


@router.delete("/sessions/{session_id}")
async def end_voice_session(
    session_id: str,
    current_student: dict = Depends(get_current_student),
    manager: VoiceConversationManager = Depends(get_conversation_manager)
):
    """End a voice conversation session."""
    
    try:
        # Verify session belongs to student
        session = await manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.student_id != current_student["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # End session
        success = await manager.end_session(session_id)
        
        if success:
            return {"message": "Session ended successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to end session")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending voice session: {e}")
        raise HTTPException(status_code=500, detail="Failed to end session")


@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    config: TranscriptionRequest = TranscriptionRequest(),
    current_student: dict = Depends(get_current_student)
):
    """Transcribe audio file to text."""
    
    try:
        # Validate file
        if not audio.content_type or not audio.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="Invalid audio file format")
        
        # Read audio data
        audio_data = await audio.read()
        
        # Initialize STT client
        async with WhisperSTTClient() as stt_client:
            # Configure STT
            stt_config = STTConfig(
                language=config.language,
                provider=config.provider
            )
            
            # Transcribe
            result = await stt_client.transcribe_audio(audio_data, stt_config)
            
            return {
                "text": result.text,
                "confidence": result.confidence,
                "language": result.language,
                "duration_ms": result.audio_duration_ms,
                "provider": result.provider.value,
                "processing_time_ms": result.processing_time_ms
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise HTTPException(status_code=500, detail="Audio transcription failed")


@router.post("/synthesize")
async def synthesize_speech(
    request: TTSRequest,
    current_student: dict = Depends(get_current_student)
):
    """Convert text to speech."""
    
    try:
        # Initialize TTS client
        async with ElevenLabsClient() as tts_client:
            # Configure TTS
            tts_config = TTSConfig(
                voice_persona=request.voice_persona,
                format=request.format
            )
            
            # Synthesize
            result = await tts_client.synthesize_speech(request.text, tts_config)
            
            return {
                "text": result.text,
                "audio_data": result.to_base64_audio(),
                "voice_persona": result.voice_persona.value,
                "format": result.format.value,
                "duration_ms": result.duration_ms,
                "generation_time_ms": result.generation_time_ms,
                "provider": result.provider.value
            }
            
    except Exception as e:
        logger.error(f"Error synthesizing speech: {e}")
        raise HTTPException(status_code=500, detail="Speech synthesis failed")


@router.get("/voices")
async def get_available_voices():
    """Get available voice personas and their details."""
    
    try:
        async with ElevenLabsClient() as tts_client:
            voices = await tts_client.get_voices()
            
            # Combine with persona information
            personas = []
            for persona in VoicePersona:
                personas.append({
                    "id": persona.value,
                    "name": persona.value.replace("_", " ").title(),
                    "description": f"{persona.value.split('_')[1].capitalize()} voice for History tutoring",
                    "gender": "female" if "sarah" in persona.value or "emma" in persona.value else "male",
                    "style": persona.value.split("_")[1]
                })
            
            return {
                "personas": personas,
                "provider_voices": voices.get("voices", [])
            }
            
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        return {
            "personas": [
                {
                    "id": persona.value,
                    "name": persona.value.replace("_", " ").title(),
                    "description": f"{persona.value.split('_')[1].capitalize()} voice",
                    "available": False
                }
                for persona in VoicePersona
            ],
            "provider_voices": []
        }


# WebSocket endpoint for real-time voice communication
voice_gateway: Optional[VoiceWebSocketGateway] = None

async def get_voice_gateway() -> VoiceWebSocketGateway:
    """Get or create voice WebSocket gateway."""
    global voice_gateway
    
    if voice_gateway is None:
        manager = await get_conversation_manager()
        voice_gateway = VoiceWebSocketGateway(manager)
    
    return voice_gateway


@router.websocket("/ws/{session_id}")
async def voice_websocket(
    websocket: WebSocket,
    session_id: str,
    student_id: str,
    gateway: VoiceWebSocketGateway = Depends(get_voice_gateway)
):
    """WebSocket endpoint for real-time voice communication."""
    
    connection_id = f"{student_id}_{session_id}_{uuid.uuid4()}"
    
    await gateway.handle_connection(websocket, connection_id, student_id)


@router.get("/sessions/{session_id}/analytics")
async def get_voice_analytics(
    session_id: str,
    current_student: dict = Depends(get_current_student),
    manager: VoiceConversationManager = Depends(get_conversation_manager)
):
    """Get detailed voice interaction analytics."""
    
    try:
        analytics = await manager.get_session_analytics(session_id)
        
        if not analytics:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if analytics["student_id"] != current_student["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Add additional computed metrics
        session = await manager.get_session(session_id)
        if session:
            # Calculate speaking time vs listening time
            user_audio_time = sum(
                msg.get("audio_duration_ms", 0) 
                for msg in session.messages 
                if msg["role"] == "user"
            )
            
            assistant_audio_time = sum(
                msg.get("audio_duration_ms", 0)
                for msg in session.messages
                if msg["role"] == "assistant"
            )
            
            analytics.update({
                "user_speaking_time_ms": user_audio_time,
                "assistant_speaking_time_ms": assistant_audio_time,
                "speaking_ratio": user_audio_time / max(assistant_audio_time, 1),
                "messages_breakdown": {
                    "user_messages": len([m for m in session.messages if m["role"] == "user"]),
                    "assistant_messages": len([m for m in session.messages if m["role"] == "assistant"])
                },
                "voice_settings": {
                    "preferred_voice": session.preferred_voice.value,
                    "language": session.language,
                    "auto_interrupt": session.auto_interrupt
                }
            })
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting voice analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")


@router.get("/gateway/status")
async def get_gateway_status(
    gateway: VoiceWebSocketGateway = Depends(get_voice_gateway)
):
    """Get voice gateway status."""
    
    try:
        stats = gateway.get_connection_stats()
        active_sessions = gateway.conversation_manager.get_active_sessions()
        
        return {
            "gateway_stats": stats,
            "active_sessions": active_sessions,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting gateway status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get gateway status")