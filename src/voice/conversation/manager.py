"""Voice conversation manager orchestrating STT, TTS, and chat."""
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, AsyncGenerator
import json

from src.voice.schemas import (
    VoiceConversationSession, ConversationState, TranscriptionResult,
    VoiceResponse, STTConfig, TTSConfig, VoiceEvent, AudioChunk
)
from src.voice.stt.whisper_client import WhisperSTTClient
from src.voice.tts.elevenlabs_client import ElevenLabsClient
from src.agents.orchestrator import MasterOrchestrator
from src.memory.manager import MemoryManager

logger = logging.getLogger(__name__)


class VoiceConversationManager:
    """Manages voice conversations between students and the AI tutor."""
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        orchestrator: MasterOrchestrator
    ):
        self.memory = memory_manager
        self.orchestrator = orchestrator
        
        # Initialize voice clients
        self.stt_client = WhisperSTTClient()
        self.tts_client = ElevenLabsClient()
        
        # Active sessions
        self.active_sessions: Dict[str, VoiceConversationSession] = {}
        
        # Audio buffers for streaming
        self.audio_buffers: Dict[str, asyncio.Queue] = {}
        
        # Session locks for thread safety
        self.session_locks: Dict[str, asyncio.Lock] = {}
    
    async def initialize(self):
        """Initialize the voice conversation manager."""
        # Initialize clients in async context
        await self.stt_client.__aenter__()
        await self.tts_client.__aenter__()
        logger.info("Voice conversation manager initialized")
    
    async def close(self):
        """Clean up resources."""
        # Close all active sessions
        for session_id in list(self.active_sessions.keys()):
            await self.end_session(session_id)
        
        # Close clients
        await self.stt_client.__aexit__(None, None, None)
        await self.tts_client.__aexit__(None, None, None)
        
        logger.info("Voice conversation manager closed")
    
    async def create_session(
        self,
        session_id: str,
        student_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> VoiceConversationSession:
        """Create a new voice conversation session."""
        
        if session_id in self.active_sessions:
            logger.warning(f"Session {session_id} already exists")
            return self.active_sessions[session_id]
        
        # Create session
        session = VoiceConversationSession(
            session_id=session_id,
            student_id=student_id,
            state=ConversationState.IDLE
        )
        
        # Apply configuration
        if config:
            if "preferred_voice" in config:
                session.preferred_voice = config["preferred_voice"]
            if "language" in config:
                session.language = config["language"]
            if "auto_interrupt" in config:
                session.auto_interrupt = config["auto_interrupt"]
        
        # Initialize session resources
        self.active_sessions[session_id] = session
        self.audio_buffers[session_id] = asyncio.Queue()
        self.session_locks[session_id] = asyncio.Lock()
        
        # Store session in memory
        await self._store_session(session)
        
        logger.info(f"Created voice session {session_id} for student {student_id}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[VoiceConversationSession]:
        """Get active session."""
        return self.active_sessions.get(session_id)
    
    async def end_session(self, session_id: str) -> bool:
        """End voice conversation session."""
        
        if session_id not in self.active_sessions:
            return False
        
        async with self.session_locks[session_id]:
            session = self.active_sessions[session_id]
            session.state = ConversationState.COMPLETE
            
            # Calculate final metrics
            session.total_duration_ms = int(
                (datetime.now() - session.started_at).total_seconds() * 1000
            )
            
            # Store final session state
            await self._store_session(session)
            
            # Clean up resources
            del self.active_sessions[session_id]
            del self.audio_buffers[session_id]
            del self.session_locks[session_id]
        
        logger.info(f"Ended voice session {session_id}")
        return True
    
    async def process_audio(
        self,
        session_id: str,
        audio_chunk: AudioChunk
    ) -> Optional[VoiceEvent]:
        """Process incoming audio chunk."""
        
        if session_id not in self.active_sessions:
            return VoiceEvent(
                event="error",
                session_id=session_id,
                data={"error": "Session not found"}
            )
        
        session = self.active_sessions[session_id]
        
        # Add to buffer
        await self.audio_buffers[session_id].put(audio_chunk)
        
        # If session is idle, start listening
        if session.state == ConversationState.IDLE:
            await self._change_state(session_id, ConversationState.LISTENING)
        
        # Process audio if we're listening
        if session.state == ConversationState.LISTENING:
            # Check if this is the final chunk
            if audio_chunk.is_final:
                return await self._process_complete_audio(session_id)
        
        return None
    
    async def _process_complete_audio(self, session_id: str) -> VoiceEvent:
        """Process complete audio input."""
        
        session = self.active_sessions[session_id]
        await self._change_state(session_id, ConversationState.TRANSCRIBING)
        
        try:
            # Collect all audio chunks from buffer
            audio_data = b""
            total_duration = 0
            
            while not self.audio_buffers[session_id].empty():
                chunk = await self.audio_buffers[session_id].get()
                audio_data += chunk.audio_data
                total_duration += chunk.duration_ms
            
            # Transcribe audio
            stt_config = STTConfig(language=session.language)
            transcription = await self.stt_client.transcribe_audio(audio_data, stt_config)
            
            if not transcription.text.strip():
                # No speech detected
                await self._change_state(session_id, ConversationState.IDLE)
                return VoiceEvent(
                    event="no_speech",
                    session_id=session_id,
                    data={"message": "No speech detected"}
                )
            
            # Add transcription to session
            session.messages.append({
                "role": "user",
                "content": transcription.text,
                "timestamp": datetime.now().isoformat(),
                "audio_duration_ms": total_duration,
                "transcription_confidence": transcription.confidence
            })
            
            session.total_interactions += 1
            session.last_activity = datetime.now()
            
            # Generate response
            await self._change_state(session_id, ConversationState.PROCESSING)
            response_text = await self._generate_response(session_id, transcription.text)
            
            # Convert to speech
            await self._change_state(session_id, ConversationState.GENERATING)
            voice_response = await self._generate_speech(session_id, response_text)
            
            # Add response to session
            session.messages.append({
                "role": "assistant",
                "content": response_text,
                "timestamp": datetime.now().isoformat(),
                "audio_duration_ms": voice_response.duration_ms,
                "voice_persona": voice_response.voice_persona.value
            })
            
            await self._change_state(session_id, ConversationState.SPEAKING)
            
            return VoiceEvent(
                event="response_ready",
                session_id=session_id,
                data={
                    "transcription": transcription.text,
                    "response": response_text,
                    "audio_url": voice_response.audio_url,
                    "audio_data": voice_response.to_base64_audio(),
                    "duration_ms": voice_response.duration_ms
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing audio for session {session_id}: {e}")
            await self._change_state(session_id, ConversationState.ERROR)
            
            return VoiceEvent(
                event="error",
                session_id=session_id,
                data={"error": str(e)}
            )
    
    async def _generate_response(self, session_id: str, user_message: str) -> str:
        """Generate AI response to user message."""
        
        session = self.active_sessions[session_id]
        
        try:
            # Create agent context
            from src.agents.base import AgentContext
            
            context = AgentContext(
                student_id=session.student_id,
                session_id=session_id,
                message=user_message,
                metadata={
                    "conversation_history": session.messages[-5:],  # Last 5 messages
                    "voice_mode": True,
                    "preferred_voice": session.preferred_voice.value
                }
            )
            
            # Generate response using orchestrator
            response = await self.orchestrator.process_message(context)
            
            return response.text if response else "I'm sorry, I didn't understand that. Could you please rephrase?"
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I'm having trouble processing that right now. Could you try again?"
    
    async def _generate_speech(self, session_id: str, text: str) -> VoiceResponse:
        """Generate speech from text."""
        
        session = self.active_sessions[session_id]
        
        try:
            # Configure TTS
            tts_config = TTSConfig(
                voice_persona=session.preferred_voice,
                format=session.output_format
            )
            
            # Generate speech
            voice_response = await self.tts_client.synthesize_speech(text, tts_config)
            
            return voice_response
            
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            # Return mock response
            return VoiceResponse(
                text=text,
                voice_persona=session.preferred_voice,
                duration_ms=len(text) * 50  # Rough estimate
            )
    
    async def _change_state(self, session_id: str, new_state: ConversationState):
        """Change session state and emit event."""
        
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        old_state = session.state
        session.state = new_state
        session.last_activity = datetime.now()
        
        logger.debug(f"Session {session_id} state: {old_state.value} -> {new_state.value}")
        
        # Update in storage
        await self._store_session(session)
    
    async def handle_interruption(
        self,
        session_id: str,
        interruption_type: str = "user_speech"
    ) -> VoiceEvent:
        """Handle conversation interruption."""
        
        if session_id not in self.active_sessions:
            return VoiceEvent(
                event="error",
                session_id=session_id,
                data={"error": "Session not found"}
            )
        
        session = self.active_sessions[session_id]
        
        # Stop current processing
        if session.state in [ConversationState.GENERATING, ConversationState.SPEAKING]:
            await self._change_state(session_id, ConversationState.LISTENING)
            
            return VoiceEvent(
                event="interrupted",
                session_id=session_id,
                data={
                    "interruption_type": interruption_type,
                    "previous_state": session.state.value
                }
            )
        
        return VoiceEvent(
            event="no_interruption",
            session_id=session_id,
            data={"current_state": session.state.value}
        )
    
    async def get_session_analytics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics for a session."""
        
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        
        # Calculate metrics
        total_duration = (datetime.now() - session.started_at).total_seconds() * 1000
        
        user_messages = [m for m in session.messages if m["role"] == "user"]
        assistant_messages = [m for m in session.messages if m["role"] == "assistant"]
        
        total_audio_input = sum(m.get("audio_duration_ms", 0) for m in user_messages)
        total_audio_output = sum(m.get("audio_duration_ms", 0) for m in assistant_messages)
        
        avg_confidence = 0.0
        if user_messages:
            confidences = [m.get("transcription_confidence", 0.0) for m in user_messages]
            avg_confidence = sum(confidences) / len(confidences)
        
        return {
            "session_id": session_id,
            "student_id": session.student_id,
            "duration_ms": int(total_duration),
            "total_interactions": session.total_interactions,
            "current_state": session.state.value,
            "audio_input_ms": total_audio_input,
            "audio_output_ms": total_audio_output,
            "avg_transcription_confidence": avg_confidence,
            "message_count": len(session.messages),
            "started_at": session.started_at.isoformat(),
            "last_activity": session.last_activity.isoformat()
        }
    
    async def _store_session(self, session: VoiceConversationSession):
        """Store session state in memory."""
        try:
            session_key = f"voice_session:{session.session_id}"
            session_data = session.dict()
            
            # Convert datetime objects to strings for JSON serialization
            session_data["started_at"] = session.started_at.isoformat()
            session_data["last_activity"] = session.last_activity.isoformat()
            
            await self.memory._redis.setex(
                session_key,
                3600,  # 1 hour TTL
                json.dumps(session_data, default=str)
            )
            
        except Exception as e:
            logger.error(f"Error storing session: {e}")
    
    async def stream_audio_response(
        self,
        session_id: str,
        text: str
    ) -> AsyncGenerator[bytes, None]:
        """Stream audio response in real-time."""
        
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        
        try:
            tts_config = TTSConfig(
                voice_persona=session.preferred_voice,
                optimize_streaming_latency=1
            )
            
            async for audio_chunk in self.tts_client.stream_synthesis(text, tts_config):
                yield audio_chunk
                
        except Exception as e:
            logger.error(f"Error streaming audio: {e}")
            yield b"error"
    
    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all active sessions."""
        return {
            session_id: {
                "student_id": session.student_id,
                "state": session.state.value,
                "duration_ms": int((datetime.now() - session.started_at).total_seconds() * 1000),
                "interactions": session.total_interactions,
                "last_activity": session.last_activity.isoformat()
            }
            for session_id, session in self.active_sessions.items()
        }