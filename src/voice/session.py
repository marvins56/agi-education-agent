"""Voice Session Manager integrating with existing TutorPersonality and AccessibilityEngine."""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import json

from src.voice.schemas import (
    VoiceConversationSession, ConversationState, VoicePersona,
    AudioFormat, VoiceEvent, AudioChunk
)
from src.voice.vad import VoiceActivityDetector
from src.voice.stt_engine import LocalWhisperSTTEngine
from src.voice.tts_engine import PiperTTSEngine
from src.tutor_personality import TutorPersonality
from src.accessibility_engine import AccessibilityEngine

logger = logging.getLogger(__name__)


class VoiceSessionManager:
    """Manages voice sessions with personality and accessibility integration."""
    
    def __init__(
        self,
        tutor_personality: TutorPersonality,
        accessibility_engine: AccessibilityEngine
    ):
        """Initialize voice session manager.
        
        Args:
            tutor_personality: Tutor personality engine
            accessibility_engine: Accessibility support engine
        """
        self.tutor_personality = tutor_personality
        self.accessibility_engine = accessibility_engine
        
        # Voice processing engines
        self.vad = None
        self.stt_engine = None
        self.tts_engine = None
        
        # Active sessions
        self.sessions: Dict[str, VoiceConversationSession] = {}
        self.session_contexts: Dict[str, Dict[str, Any]] = {}
        
        # Session locks for thread safety
        self.session_locks: Dict[str, asyncio.Lock] = {}
        
        # Performance monitoring
        self.performance_metrics = {
            "total_sessions": 0,
            "avg_response_time_ms": 0,
            "accessibility_sessions": 0
        }
        
        self.initialized = False
    
    async def initialize(self):
        """Initialize voice engines."""
        if self.initialized:
            return
        
        try:
            # Initialize VAD
            self.vad = VoiceActivityDetector(
                threshold=0.5,
                min_speech_duration_ms=300,
                min_silence_duration_ms=600
            )
            await self.vad.initialize()
            
            # Initialize STT engine (CPU optimized)
            self.stt_engine = LocalWhisperSTTEngine(
                model_name="tiny",  # Fastest for i5-6500
                device="cpu"
            )
            await self.stt_engine.initialize()
            
            # Initialize TTS engine  
            self.tts_engine = PiperTTSEngine(
                voice_name="en_US-amy-medium",
                use_cuda=False  # CPU only
            )
            await self.tts_engine.initialize()
            
            self.initialized = True
            logger.info("Voice session manager initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize voice session manager: {e}")
            raise
    
    async def create_session(
        self,
        session_id: str,
        student_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> VoiceConversationSession:
        """Create a new voice session with personality and accessibility settings.
        
        Args:
            session_id: Unique session identifier
            student_id: Student identifier
            config: Session configuration
            
        Returns:
            VoiceConversationSession instance
        """
        
        if not self.initialized:
            await self.initialize()
        
        if session_id in self.sessions:
            logger.warning(f"Session {session_id} already exists")
            return self.sessions[session_id]
        
        try:
            # Get student profile for personalization
            student_profile = await self._get_student_profile(student_id)
            
            # Configure session based on profile
            session_config = await self._configure_session(student_profile, config)
            
            # Create session
            session = VoiceConversationSession(
                session_id=session_id,
                student_id=student_id,
                state=ConversationState.IDLE,
                preferred_voice=session_config.get("preferred_voice", VoicePersona.SARAH_ENCOURAGING),
                language=session_config.get("language", "en"),
                auto_interrupt=session_config.get("auto_interrupt", True),
                input_format=session_config.get("input_format", AudioFormat.WAV),
                output_format=session_config.get("output_format", AudioFormat.WAV)
            )
            
            # Store session
            self.sessions[session_id] = session
            self.session_locks[session_id] = asyncio.Lock()
            
            # Create session context
            self.session_contexts[session_id] = {
                "student_profile": student_profile,
                "tutor_context": await self._initialize_tutor_context(student_id),
                "accessibility_settings": session_config.get("accessibility", {}),
                "conversation_history": [],
                "performance_metrics": {
                    "start_time": datetime.now(),
                    "total_interactions": 0,
                    "avg_response_time_ms": 0
                }
            }
            
            # Apply accessibility settings
            await self._apply_accessibility_settings(session_id, session_config.get("accessibility", {}))
            
            # Update stats
            self.performance_metrics["total_sessions"] += 1
            if session_config.get("accessibility", {}).get("enabled", False):
                self.performance_metrics["accessibility_sessions"] += 1
            
            logger.info(f"Created voice session {session_id} for student {student_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to create session {session_id}: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[VoiceConversationSession]:
        """Get active voice session."""
        return self.sessions.get(session_id)
    
    async def process_voice_interaction(
        self,
        session_id: str,
        audio_chunk: AudioChunk,
        is_final: bool = False
    ) -> Optional[VoiceEvent]:
        """Process voice interaction with full pipeline.
        
        Args:
            session_id: Session identifier
            audio_chunk: Audio input chunk
            is_final: Whether this is the final chunk
            
        Returns:
            VoiceEvent with results or None
        """
        
        if session_id not in self.sessions:
            return VoiceEvent(
                event="error",
                session_id=session_id,
                data={"error": "Session not found"}
            )
        
        session = self.sessions[session_id]
        context = self.session_contexts[session_id]
        
        async with self.session_locks[session_id]:
            try:
                start_time = datetime.now()
                
                # Update session state
                if session.state == ConversationState.IDLE:
                    session.state = ConversationState.LISTENING
                
                # Voice Activity Detection
                vad_result = await self.vad.process_chunk(audio_chunk)
                
                # Check for barge-in if TTS is playing
                if session.state == ConversationState.SPEAKING:
                    barge_in = await self.vad.detect_barge_in(audio_chunk, tts_playing=True)
                    if barge_in:
                        session.state = ConversationState.LISTENING
                        return VoiceEvent(
                            event="barge_in_detected",
                            session_id=session_id,
                            data={"message": "User interrupted, stopping TTS"}
                        )
                
                # Process complete utterance
                if is_final and vad_result["is_speech"]:
                    return await self._process_complete_utterance(session_id, audio_chunk, start_time)
                
                # Return VAD status update
                return VoiceEvent(
                    event="vad_update",
                    session_id=session_id,
                    data={
                        "is_speech": vad_result["is_speech"],
                        "confidence": vad_result["confidence"],
                        "energy": vad_result["energy"],
                        "state": session.state.value
                    }
                )
                
            except Exception as e:
                logger.error(f"Error processing voice interaction: {e}")
                session.state = ConversationState.ERROR
                
                return VoiceEvent(
                    event="error",
                    session_id=session_id,
                    data={"error": str(e)}
                )
    
    async def _process_complete_utterance(
        self,
        session_id: str,
        audio_chunk: AudioChunk,
        start_time: datetime
    ) -> VoiceEvent:
        """Process complete utterance through STT → LLM → TTS pipeline."""
        
        session = self.sessions[session_id]
        context = self.session_contexts[session_id]
        
        try:
            # Speech-to-Text
            session.state = ConversationState.TRANSCRIBING
            
            transcription = await self.stt_engine.transcribe_audio(
                audio_chunk,
                language=session.language
            )
            
            if not transcription.text.strip():
                session.state = ConversationState.IDLE
                return VoiceEvent(
                    event="no_speech",
                    session_id=session_id,
                    data={"message": "No speech detected"}
                )
            
            # Add to conversation history
            context["conversation_history"].append({
                "role": "user",
                "content": transcription.text,
                "timestamp": datetime.now().isoformat(),
                "confidence": transcription.confidence,
                "processing_time_ms": transcription.processing_time_ms
            })
            
            # Generate response using tutor personality
            session.state = ConversationState.PROCESSING
            
            response_text = await self._generate_personalized_response(
                session_id,
                transcription.text
            )
            
            # Apply accessibility transformations
            response_text = await self._apply_accessibility_filters(
                session_id,
                response_text
            )
            
            # Text-to-Speech
            session.state = ConversationState.GENERATING
            
            voice_response = await self.tts_engine.synthesize_speech(
                response_text,
                voice_persona=session.preferred_voice,
                format=session.output_format
            )
            
            # Add to conversation history
            context["conversation_history"].append({
                "role": "assistant", 
                "content": response_text,
                "timestamp": datetime.now().isoformat(),
                "generation_time_ms": voice_response.generation_time_ms,
                "character_count": voice_response.character_count
            })
            
            # Update performance metrics
            total_time = int((datetime.now() - start_time).total_seconds() * 1000)
            context["performance_metrics"]["total_interactions"] += 1
            
            prev_avg = context["performance_metrics"]["avg_response_time_ms"]
            interactions = context["performance_metrics"]["total_interactions"]
            context["performance_metrics"]["avg_response_time_ms"] = (
                prev_avg * (interactions - 1) + total_time
            ) // interactions
            
            session.state = ConversationState.SPEAKING
            
            return VoiceEvent(
                event="response_ready",
                session_id=session_id,
                data={
                    "transcription": transcription.text,
                    "transcription_confidence": transcription.confidence,
                    "response": response_text,
                    "audio_data": voice_response.to_base64_audio(),
                    "duration_ms": voice_response.duration_ms,
                    "total_processing_time_ms": total_time,
                    "voice_persona": session.preferred_voice.value
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing complete utterance: {e}")
            session.state = ConversationState.ERROR
            raise
    
    async def _generate_personalized_response(
        self,
        session_id: str,
        user_message: str
    ) -> str:
        """Generate personalized response using tutor personality."""
        
        context = self.session_contexts[session_id]
        
        try:
            # Prepare tutor context
            tutor_context = context["tutor_context"]
            tutor_context.update({
                "student_message": user_message,
                "conversation_history": context["conversation_history"][-5:],  # Last 5 messages
                "voice_mode": True,
                "session_id": session_id
            })
            
            # Generate response using tutor personality
            response = await self.tutor_personality.generate_response(
                context=tutor_context,
                student_input=user_message
            )
            
            return response.get("text", "I understand. Could you tell me more about that?")
            
        except Exception as e:
            logger.error(f"Error generating personalized response: {e}")
            return "I'm having trouble processing that right now. Could you please rephrase?"
    
    async def _apply_accessibility_filters(
        self,
        session_id: str,
        text: str
    ) -> str:
        """Apply accessibility transformations to response text."""
        
        context = self.session_contexts[session_id]
        accessibility_settings = context.get("accessibility_settings", {})
        
        if not accessibility_settings.get("enabled", False):
            return text
        
        try:
            # Apply text simplification if needed
            if accessibility_settings.get("simplify_language", False):
                text = await self.accessibility_engine.simplify_text(text)
            
            # Add pronunciation guides if needed
            if accessibility_settings.get("pronunciation_guides", False):
                text = await self.accessibility_engine.add_pronunciation_guides(text)
            
            # Adjust for reading level
            reading_level = accessibility_settings.get("reading_level")
            if reading_level:
                text = await self.accessibility_engine.adjust_reading_level(text, reading_level)
            
            return text
            
        except Exception as e:
            logger.error(f"Error applying accessibility filters: {e}")
            return text  # Return original text if filtering fails
    
    async def _apply_accessibility_settings(
        self,
        session_id: str,
        accessibility_config: Dict[str, Any]
    ):
        """Apply accessibility settings to TTS engine."""
        
        if not accessibility_config.get("enabled", False):
            return
        
        try:
            # Adjust speech rate for disabilities
            speech_rate = accessibility_config.get("speech_rate", 1.0)
            if speech_rate != 1.0:
                self.tts_engine.set_accessibility_mode(
                    enabled=True,
                    speed_multiplier=speech_rate
                )
            
            # Adjust VAD sensitivity for motor impairments
            vad_sensitivity = accessibility_config.get("vad_sensitivity", 1.0)
            if vad_sensitivity != 1.0:
                new_threshold = max(0.1, min(0.9, self.vad.threshold / vad_sensitivity))
                self.vad.update_config(threshold=new_threshold)
            
            logger.info(f"Applied accessibility settings for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error applying accessibility settings: {e}")
    
    async def _get_student_profile(self, student_id: str) -> Dict[str, Any]:
        """Get student profile for personalization."""
        
        try:
            # This would typically fetch from database
            # For now, return a default profile
            return {
                "id": student_id,
                "learning_preferences": {
                    "pace": "moderate",
                    "style": "conversational"
                },
                "accessibility_needs": {
                    "enabled": False,
                    "speech_rate": 1.0,
                    "simplify_language": False
                },
                "voice_preferences": {
                    "persona": VoicePersona.SARAH_ENCOURAGING.value,
                    "language": "en"
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting student profile: {e}")
            return {"id": student_id}  # Minimal fallback
    
    async def _configure_session(
        self,
        student_profile: Dict[str, Any],
        config: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Configure session based on student profile and provided config."""
        
        # Start with defaults
        session_config = {
            "preferred_voice": VoicePersona.SARAH_ENCOURAGING,
            "language": "en",
            "auto_interrupt": True,
            "input_format": AudioFormat.WAV,
            "output_format": AudioFormat.WAV,
            "accessibility": {"enabled": False}
        }
        
        # Apply student profile preferences
        voice_prefs = student_profile.get("voice_preferences", {})
        if "persona" in voice_prefs:
            try:
                session_config["preferred_voice"] = VoicePersona(voice_prefs["persona"])
            except ValueError:
                pass  # Invalid persona, keep default
        
        if "language" in voice_prefs:
            session_config["language"] = voice_prefs["language"]
        
        # Apply accessibility needs
        accessibility_needs = student_profile.get("accessibility_needs", {})
        if accessibility_needs.get("enabled", False):
            session_config["accessibility"] = accessibility_needs
        
        # Override with provided config
        if config:
            session_config.update(config)
        
        return session_config
    
    async def _initialize_tutor_context(self, student_id: str) -> Dict[str, Any]:
        """Initialize tutor context for the session."""
        
        return {
            "student_id": student_id,
            "subject": "history",  # This could be dynamic
            "session_type": "voice_chat",
            "personality_mode": "encouraging",
            "adaptation_enabled": True
        }
    
    async def end_session(self, session_id: str) -> bool:
        """End voice session and cleanup resources."""
        
        if session_id not in self.sessions:
            return False
        
        try:
            async with self.session_locks[session_id]:
                session = self.sessions[session_id]
                context = self.session_contexts[session_id]
                
                # Update final metrics
                session.state = ConversationState.COMPLETE
                session.total_duration_ms = int(
                    (datetime.now() - session.started_at).total_seconds() * 1000
                )
                session.total_interactions = context["performance_metrics"]["total_interactions"]
                session.avg_response_time_ms = context["performance_metrics"]["avg_response_time_ms"]
                
                # Store final session data (this would go to database)
                await self._store_session_data(session, context)
                
                # Cleanup
                del self.sessions[session_id]
                del self.session_contexts[session_id]
                del self.session_locks[session_id]
                
                logger.info(f"Ended voice session {session_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error ending session {session_id}: {e}")
            return False
    
    async def _store_session_data(
        self,
        session: VoiceConversationSession,
        context: Dict[str, Any]
    ):
        """Store session data for analytics and learning."""
        
        try:
            session_data = {
                "session_id": session.session_id,
                "student_id": session.student_id,
                "duration_ms": session.total_duration_ms,
                "interactions": session.total_interactions,
                "avg_response_time_ms": session.avg_response_time_ms,
                "conversation_history": context["conversation_history"],
                "accessibility_used": context["accessibility_settings"].get("enabled", False),
                "voice_persona": session.preferred_voice.value,
                "language": session.language,
                "ended_at": datetime.now().isoformat()
            }
            
            # This would typically be stored in a database
            logger.info(f"Session data stored for {session.session_id}")
            
        except Exception as e:
            logger.error(f"Error storing session data: {e}")
    
    def get_session_analytics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics for a specific session."""
        
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        context = self.session_contexts[session_id]
        
        current_duration = int(
            (datetime.now() - session.started_at).total_seconds() * 1000
        )
        
        return {
            "session_id": session_id,
            "student_id": session.student_id,
            "duration_ms": current_duration,
            "state": session.state.value,
            "interactions": context["performance_metrics"]["total_interactions"],
            "avg_response_time_ms": context["performance_metrics"]["avg_response_time_ms"],
            "voice_persona": session.preferred_voice.value,
            "language": session.language,
            "accessibility_enabled": context["accessibility_settings"].get("enabled", False),
            "conversation_length": len(context["conversation_history"]),
            "started_at": session.started_at.isoformat(),
            "last_activity": session.last_activity.isoformat()
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get overall performance metrics."""
        return {
            **self.performance_metrics,
            "active_sessions": len(self.sessions),
            "engines_ready": {
                "vad": self.vad.model_ready if self.vad else False,
                "stt": self.stt_engine.model_ready if self.stt_engine else False,
                "tts": self.tts_engine.model_ready if self.tts_engine else False
            }
        }
    
    async def cleanup(self):
        """Cleanup all resources."""
        
        # End all active sessions
        for session_id in list(self.sessions.keys()):
            await self.end_session(session_id)
        
        # Cleanup engines
        if self.stt_engine:
            await self.stt_engine.cleanup()
        
        if self.tts_engine:
            await self.tts_engine.cleanup()
        
        self.initialized = False
        logger.info("Voice session manager cleaned up")