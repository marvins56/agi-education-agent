"""Core voice pipeline orchestrating VAD → STT → LLM → TTS with real-time streaming."""
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, AsyncGenerator, Callable
import json

from src.voice.schemas import (
    AudioChunk, VoiceEvent, ConversationState, VoicePersona,
    TranscriptionResult, VoiceResponse
)
from src.voice.vad import VoiceActivityDetector, StreamingVAD
from src.voice.stt_engine import LocalWhisperSTTEngine
from src.voice.tts_engine import PiperTTSEngine, StreamingTTSBuffer
from src.voice.session import VoiceSessionManager
from src.agents.orchestrator import MasterOrchestrator
from src.memory.manager import MemoryManager

logger = logging.getLogger(__name__)


class VoiceAgentPipeline:
    """Real-time voice agent pipeline with streaming optimization."""
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        orchestrator: MasterOrchestrator,
        target_response_time_ms: int = 500,
        max_response_time_ms: int = 2000
    ):
        """Initialize voice agent pipeline.
        
        Args:
            memory_manager: Memory management system
            orchestrator: Master agent orchestrator
            target_response_time_ms: Target response time (300-700ms goal)
            max_response_time_ms: Maximum acceptable response time
        """
        self.memory_manager = memory_manager
        self.orchestrator = orchestrator
        self.target_response_time_ms = target_response_time_ms
        self.max_response_time_ms = max_response_time_ms
        
        # Voice processing components
        self.vad = None
        self.stt_engine = None
        self.tts_engine = None
        self.session_manager = None
        
        # Streaming components
        self.streaming_vad = None
        self.streaming_tts = None
        
        # Active pipelines
        self.active_pipelines: Dict[str, 'PipelineInstance'] = {}
        
        # Performance monitoring
        self.performance_stats = {
            "total_requests": 0,
            "avg_response_time_ms": 0,
            "response_time_p95_ms": 0,
            "pipeline_errors": 0,
            "streaming_sessions": 0
        }
        
        # Configuration
        self.config = {
            "vad_threshold": 0.5,
            "stt_model": "tiny",  # Fastest for CPU
            "tts_voice": "en_US-amy-medium",
            "enable_streaming": True,
            "parallel_processing": True,
            "audio_buffer_ms": 200,
            "response_timeout_ms": 5000
        }
        
        self.initialized = False
    
    async def initialize(self):
        """Initialize the voice pipeline."""
        if self.initialized:
            return
        
        try:
            start_time = time.time()
            
            # Initialize VAD with optimized settings
            self.vad = VoiceActivityDetector(
                threshold=self.config["vad_threshold"],
                min_speech_duration_ms=250,  # Quick trigger
                min_silence_duration_ms=400,  # Quick stop
                padding_duration_ms=50,      # Minimal padding
                energy_threshold=0.005       # Sensitive energy detection
            )
            await self.vad.initialize()
            
            # Initialize STT engine with CPU optimization
            self.stt_engine = LocalWhisperSTTEngine(
                model_name=self.config["stt_model"],  # "tiny" for speed
                device="cpu",
                compute_type="int8"  # Fastest inference
            )
            await self.stt_engine.initialize()
            
            # Initialize TTS engine 
            self.tts_engine = PiperTTSEngine(
                voice_name=self.config["tts_voice"],
                use_cuda=False  # CPU only for i5-6500
            )
            await self.tts_engine.initialize()
            
            # Initialize session manager with accessibility integration
            from src.tutor_personality import TutorPersonality
            from src.accessibility_engine import AccessibilityEngine
            
            tutor_personality = TutorPersonality()
            accessibility_engine = AccessibilityEngine()
            
            self.session_manager = VoiceSessionManager(
                tutor_personality=tutor_personality,
                accessibility_engine=accessibility_engine
            )
            await self.session_manager.initialize()
            
            # Initialize streaming components
            self.streaming_vad = StreamingVAD(self.vad)
            self.streaming_tts = StreamingTTSBuffer(self.tts_engine)
            
            init_time = int((time.time() - start_time) * 1000)
            self.initialized = True
            
            logger.info(f"Voice pipeline initialized in {init_time}ms")
            logger.info(f"Target response time: {self.target_response_time_ms}ms")
            
        except Exception as e:
            logger.error(f"Failed to initialize voice pipeline: {e}")
            raise
    
    async def create_session(
        self,
        session_id: str,
        student_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new voice session.
        
        Args:
            session_id: Unique session identifier
            student_id: Student identifier
            config: Session configuration
            
        Returns:
            Session creation result
        """
        
        if not self.initialized:
            await self.initialize()
        
        try:
            # Create session through session manager
            session = await self.session_manager.create_session(
                session_id, student_id, config
            )
            
            # Create pipeline instance
            pipeline_instance = PipelineInstance(
                session_id=session_id,
                pipeline=self,
                target_response_time=self.target_response_time_ms
            )
            
            self.active_pipelines[session_id] = pipeline_instance
            
            logger.info(f"Created voice pipeline session {session_id}")
            
            return {
                "session_id": session_id,
                "student_id": student_id,
                "state": session.state.value,
                "pipeline_ready": True,
                "target_response_time_ms": self.target_response_time_ms
            }
            
        except Exception as e:
            logger.error(f"Failed to create session {session_id}: {e}")
            raise
    
    async def process_audio_stream(
        self,
        session_id: str,
        audio_stream: AsyncGenerator[AudioChunk, None],
        response_callback: Optional[Callable] = None
    ) -> AsyncGenerator[VoiceEvent, None]:
        """Process streaming audio through the full voice pipeline.
        
        Args:
            session_id: Session identifier
            audio_stream: Stream of audio chunks
            response_callback: Optional callback for streaming responses
            
        Yields:
            VoiceEvent updates throughout processing
        """
        
        if session_id not in self.active_pipelines:
            yield VoiceEvent(
                event="error",
                session_id=session_id,
                data={"error": "Pipeline session not found"}
            )
            return
        
        pipeline_instance = self.active_pipelines[session_id]
        
        try:
            # Process audio stream through pipeline
            async for event in pipeline_instance.process_stream(audio_stream, response_callback):
                yield event
                
        except Exception as e:
            logger.error(f"Error processing audio stream: {e}")
            yield VoiceEvent(
                event="error",
                session_id=session_id,
                data={"error": str(e)}
            )
    
    async def process_single_audio(
        self,
        session_id: str,
        audio_chunk: AudioChunk
    ) -> VoiceEvent:
        """Process a single audio chunk.
        
        Args:
            session_id: Session identifier
            audio_chunk: Audio chunk to process
            
        Returns:
            VoiceEvent with processing result
        """
        
        if session_id not in self.active_pipelines:
            return VoiceEvent(
                event="error",
                session_id=session_id,
                data={"error": "Pipeline session not found"}
            )
        
        pipeline_instance = self.active_pipelines[session_id]
        
        try:
            return await pipeline_instance.process_chunk(audio_chunk)
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            return VoiceEvent(
                event="error",
                session_id=session_id,
                data={"error": str(e)}
            )
    
    async def interrupt_generation(self, session_id: str) -> bool:
        """Interrupt ongoing TTS generation for barge-in.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successfully interrupted
        """
        
        if session_id not in self.active_pipelines:
            return False
        
        pipeline_instance = self.active_pipelines[session_id]
        return await pipeline_instance.interrupt()
    
    async def end_session(self, session_id: str) -> bool:
        """End voice pipeline session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session ended successfully
        """
        
        try:
            # End session in session manager
            success = await self.session_manager.end_session(session_id)
            
            # Clean up pipeline instance
            if session_id in self.active_pipelines:
                pipeline_instance = self.active_pipelines[session_id]
                await pipeline_instance.cleanup()
                del self.active_pipelines[session_id]
            
            logger.info(f"Ended voice pipeline session {session_id}")
            return success
            
        except Exception as e:
            logger.error(f"Error ending session {session_id}: {e}")
            return False
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline performance statistics."""
        
        engine_stats = {}
        if self.stt_engine:
            engine_stats["stt"] = self.stt_engine.get_stats()
        if self.tts_engine:
            engine_stats["tts"] = self.tts_engine.get_stats()
        if self.vad:
            engine_stats["vad"] = self.vad.get_current_state()
        
        return {
            **self.performance_stats,
            "active_sessions": len(self.active_pipelines),
            "pipeline_ready": self.initialized,
            "config": self.config,
            "engines": engine_stats
        }
    
    async def update_config(self, new_config: Dict[str, Any]):
        """Update pipeline configuration."""
        
        self.config.update(new_config)
        
        # Apply config changes to components
        if "vad_threshold" in new_config and self.vad:
            self.vad.update_config(threshold=new_config["vad_threshold"])
        
        if "target_response_time_ms" in new_config:
            self.target_response_time_ms = new_config["target_response_time_ms"]
        
        logger.info(f"Updated pipeline config: {new_config}")
    
    async def cleanup(self):
        """Cleanup all pipeline resources."""
        
        # End all active sessions
        for session_id in list(self.active_pipelines.keys()):
            await self.end_session(session_id)
        
        # Cleanup session manager
        if self.session_manager:
            await self.session_manager.cleanup()
        
        # Cleanup engines
        if self.stt_engine:
            await self.stt_engine.cleanup()
        
        if self.tts_engine:
            await self.tts_engine.cleanup()
        
        # Stop streaming components
        if self.streaming_vad:
            await self.streaming_vad.stop()
        
        if self.streaming_tts:
            await self.streaming_tts.stop()
        
        self.initialized = False
        logger.info("Voice pipeline cleaned up")


class PipelineInstance:
    """Individual pipeline instance for a voice session."""
    
    def __init__(
        self,
        session_id: str,
        pipeline: VoiceAgentPipeline,
        target_response_time: int = 500
    ):
        """Initialize pipeline instance.
        
        Args:
            session_id: Session identifier
            pipeline: Parent pipeline
            target_response_time: Target response time in ms
        """
        self.session_id = session_id
        self.pipeline = pipeline
        self.target_response_time = target_response_time
        
        # Processing state
        self.current_state = ConversationState.IDLE
        self.processing_task = None
        self.interrupt_event = asyncio.Event()
        
        # Audio buffers
        self.audio_buffer = bytearray()
        self.buffer_lock = asyncio.Lock()
        
        # Performance tracking
        self.interaction_count = 0
        self.response_times = []
        
        logger.debug(f"Created pipeline instance for session {session_id}")
    
    async def process_stream(
        self,
        audio_stream: AsyncGenerator[AudioChunk, None],
        response_callback: Optional[Callable] = None
    ) -> AsyncGenerator[VoiceEvent, None]:
        """Process streaming audio."""
        
        try:
            # Start VAD processing
            await self.pipeline.streaming_vad.start()
            
            speech_buffer = bytearray()
            speech_detected = False
            silence_start = None
            
            async for audio_chunk in audio_stream:
                start_time = time.time()
                
                # Add to VAD
                await self.pipeline.streaming_vad.add_audio(audio_chunk)
                
                # Get VAD result
                vad_result = await self.pipeline.streaming_vad.get_result(timeout=0.01)
                
                if vad_result:
                    # Handle speech detection
                    if vad_result["is_speech"]:
                        if not speech_detected:
                            speech_detected = True
                            silence_start = None
                            yield VoiceEvent(
                                event="speech_start",
                                session_id=self.session_id,
                                data={"confidence": vad_result["confidence"]}
                            )
                        
                        # Buffer speech audio
                        speech_buffer.extend(audio_chunk.audio_data)
                        
                    else:
                        # No speech detected
                        if speech_detected:
                            if silence_start is None:
                                silence_start = time.time()
                            
                            # Check for end of speech
                            silence_duration = (time.time() - silence_start) * 1000
                            if silence_duration > 400:  # 400ms silence threshold
                                speech_detected = False
                                
                                # Process complete utterance
                                if speech_buffer:
                                    complete_chunk = AudioChunk(
                                        audio_data=bytes(speech_buffer),
                                        duration_ms=len(speech_buffer) // 32,  # Rough estimate
                                        is_final=True
                                    )
                                    
                                    # Process through full pipeline
                                    result = await self._process_complete_utterance(
                                        complete_chunk, 
                                        start_time
                                    )
                                    
                                    yield result
                                    
                                    # Stream TTS if callback provided
                                    if response_callback and result.data.get("audio_data"):
                                        asyncio.create_task(
                                            response_callback(result.data["audio_data"])
                                        )
                                
                                speech_buffer.clear()
                
                # Yield status update
                yield VoiceEvent(
                    event="processing",
                    session_id=self.session_id,
                    data={
                        "state": self.current_state.value,
                        "speech_detected": speech_detected,
                        "buffer_size": len(speech_buffer)
                    }
                )
                
        except Exception as e:
            logger.error(f"Stream processing error: {e}")
            yield VoiceEvent(
                event="error",
                session_id=self.session_id,
                data={"error": str(e)}
            )
        
        finally:
            # Stop VAD processing
            await self.pipeline.streaming_vad.stop()
    
    async def process_chunk(self, audio_chunk: AudioChunk) -> VoiceEvent:
        """Process a single audio chunk."""
        
        start_time = time.time()
        
        try:
            # Check for interruption
            if self.interrupt_event.is_set():
                self.interrupt_event.clear()
                return VoiceEvent(
                    event="interrupted",
                    session_id=self.session_id,
                    data={"message": "Processing interrupted"}
                )
            
            # Process if this is a final chunk
            if audio_chunk.is_final:
                return await self._process_complete_utterance(audio_chunk, start_time)
            
            # Otherwise, just update VAD state
            vad_result = await self.pipeline.vad.process_chunk(audio_chunk)
            
            return VoiceEvent(
                event="vad_update",
                session_id=self.session_id,
                data={
                    "is_speech": vad_result["is_speech"],
                    "confidence": vad_result["confidence"],
                    "energy": vad_result["energy"]
                }
            )
            
        except Exception as e:
            logger.error(f"Chunk processing error: {e}")
            return VoiceEvent(
                event="error",
                session_id=self.session_id,
                data={"error": str(e)}
            )
    
    async def _process_complete_utterance(
        self,
        audio_chunk: AudioChunk,
        start_time: float
    ) -> VoiceEvent:
        """Process complete utterance through the pipeline."""
        
        try:
            pipeline_start = time.time()
            
            # Step 1: STT
            self.current_state = ConversationState.TRANSCRIBING
            
            transcription = await self.pipeline.stt_engine.transcribe_audio(
                audio_chunk,
                enable_vad=False  # Already done VAD
            )
            
            stt_time = time.time()
            
            if not transcription.text.strip():
                return VoiceEvent(
                    event="no_speech",
                    session_id=self.session_id,
                    data={"message": "No speech detected"}
                )
            
            # Step 2: LLM Processing
            self.current_state = ConversationState.PROCESSING
            
            # Use session manager for personalized response
            session = await self.pipeline.session_manager.get_session(self.session_id)
            if not session:
                raise Exception("Session not found in session manager")
            
            # Generate response through session manager
            voice_event = await self.pipeline.session_manager.process_voice_interaction(
                self.session_id,
                audio_chunk,
                is_final=True
            )
            
            llm_time = time.time()
            
            # Check if we got a proper response
            if not voice_event or voice_event.event != "response_ready":
                raise Exception("Failed to generate response")
            
            # Update performance metrics
            total_time = int((time.time() - pipeline_start) * 1000)
            self.interaction_count += 1
            self.response_times.append(total_time)
            
            # Update pipeline stats
            self.pipeline.performance_stats["total_requests"] += 1
            
            prev_avg = self.pipeline.performance_stats["avg_response_time_ms"]
            total_requests = self.pipeline.performance_stats["total_requests"]
            self.pipeline.performance_stats["avg_response_time_ms"] = (
                prev_avg * (total_requests - 1) + total_time
            ) // total_requests
            
            # Calculate timing breakdown
            stt_time_ms = int((stt_time - pipeline_start) * 1000)
            llm_time_ms = int((llm_time - stt_time) * 1000)
            tts_time_ms = total_time - stt_time_ms - llm_time_ms
            
            # Add timing details to response
            voice_event.data["timing"] = {
                "total_ms": total_time,
                "stt_ms": stt_time_ms,
                "llm_ms": llm_time_ms,
                "tts_ms": tts_time_ms,
                "target_ms": self.target_response_time,
                "met_target": total_time <= self.target_response_time
            }
            
            # Log performance
            if total_time > self.target_response_time:
                logger.warning(f"Response time {total_time}ms exceeded target {self.target_response_time}ms")
            else:
                logger.debug(f"Response time {total_time}ms within target")
            
            self.current_state = ConversationState.SPEAKING
            return voice_event
            
        except Exception as e:
            self.current_state = ConversationState.ERROR
            logger.error(f"Complete utterance processing error: {e}")
            
            return VoiceEvent(
                event="error",
                session_id=self.session_id,
                data={"error": str(e)}
            )
    
    async def interrupt(self) -> bool:
        """Interrupt current processing."""
        
        try:
            self.interrupt_event.set()
            
            # Cancel processing task if running
            if self.processing_task and not self.processing_task.done():
                self.processing_task.cancel()
            
            # Reset state
            self.current_state = ConversationState.LISTENING
            
            logger.debug(f"Interrupted pipeline instance {self.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error interrupting pipeline: {e}")
            return False
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get instance performance statistics."""
        
        avg_response_time = 0
        if self.response_times:
            avg_response_time = sum(self.response_times) // len(self.response_times)
        
        return {
            "session_id": self.session_id,
            "interaction_count": self.interaction_count,
            "avg_response_time_ms": avg_response_time,
            "current_state": self.current_state.value,
            "target_response_time_ms": self.target_response_time
        }
    
    async def cleanup(self):
        """Cleanup pipeline instance."""
        
        # Cancel any running tasks
        if self.processing_task and not self.processing_task.done():
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        # Clear buffers
        async with self.buffer_lock:
            self.audio_buffer.clear()
        
        logger.debug(f"Cleaned up pipeline instance {self.session_id}")