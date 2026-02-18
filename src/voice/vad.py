"""Voice Activity Detection using Silero VAD."""
import asyncio
import logging
import numpy as np
from typing import Optional, Callable, AsyncGenerator, Dict, Any
import torch

from src.voice.schemas import AudioChunk, AudioFormat

logger = logging.getLogger(__name__)


class VoiceActivityDetector:
    """Voice Activity Detection using Silero VAD with barge-in support."""
    
    def __init__(
        self,
        threshold: float = 0.5,
        min_speech_duration_ms: int = 250,
        min_silence_duration_ms: int = 500,
        padding_duration_ms: int = 100,
        sample_rate: int = 16000,
        energy_threshold: float = 0.01
    ):
        """Initialize VAD with configuration.
        
        Args:
            threshold: VAD confidence threshold (0-1)
            min_speech_duration_ms: Minimum speech duration to trigger
            min_silence_duration_ms: Minimum silence to end speech
            padding_duration_ms: Padding around speech segments
            sample_rate: Expected audio sample rate
            energy_threshold: Energy-based pre-filter threshold
        """
        self.threshold = threshold
        self.min_speech_duration_ms = min_speech_duration_ms
        self.min_silence_duration_ms = min_silence_duration_ms
        self.padding_duration_ms = padding_duration_ms
        self.sample_rate = sample_rate
        self.energy_threshold = energy_threshold
        
        # VAD model
        self.model = None
        self.model_ready = False
        
        # State tracking
        self.is_speaking = False
        self.speech_start_time = None
        self.silence_start_time = None
        self.current_energy = 0.0
        
        # Audio buffer for processing
        self.audio_buffer = []
        self.buffer_duration_ms = 0
        
        # Callbacks
        self.on_speech_start: Optional[Callable] = None
        self.on_speech_end: Optional[Callable] = None
        self.on_barge_in: Optional[Callable] = None
        
    async def initialize(self):
        """Initialize the VAD model."""
        try:
            # Import silero VAD - this might fail if packages aren't installed yet
            try:
                import silero_vad as vad
                
                # Load model
                self.model, utils = vad.load_model(
                    model_name="silero_vad_8k_v3",
                    force_reload=False
                )
                
                self.model_ready = True
                logger.info("Silero VAD model loaded successfully")
                
            except ImportError:
                logger.warning("Silero VAD not available, using energy-based detection")
                self.model_ready = False
                
        except Exception as e:
            logger.error(f"Failed to initialize VAD: {e}")
            self.model_ready = False
    
    async def process_chunk(self, audio_chunk: AudioChunk) -> Dict[str, Any]:
        """Process audio chunk and return VAD results.
        
        Returns:
            Dict with keys: is_speech, confidence, energy, timestamp_ms
        """
        
        # Convert audio data to numpy array
        if isinstance(audio_chunk.audio_data, bytes):
            # Assume 16-bit PCM
            audio_array = np.frombuffer(audio_chunk.audio_data, dtype=np.int16)
        else:
            audio_array = np.array(audio_chunk.audio_data)
        
        # Normalize to [-1, 1]
        audio_float = audio_array.astype(np.float32) / 32768.0
        
        # Calculate energy
        energy = float(np.mean(np.abs(audio_float)))
        self.current_energy = energy
        
        # Pre-filter: if energy is too low, definitely no speech
        if energy < self.energy_threshold:
            return {
                "is_speech": False,
                "confidence": 0.0,
                "energy": energy,
                "timestamp_ms": self._get_current_time_ms()
            }
        
        # Use VAD model if available
        if self.model_ready and self.model is not None:
            try:
                # Ensure correct format for Silero (16kHz)
                if self.sample_rate != 16000:
                    # Simple resampling (not ideal, but works for demo)
                    target_length = int(len(audio_float) * 16000 / self.sample_rate)
                    audio_float = np.interp(
                        np.linspace(0, len(audio_float), target_length),
                        np.arange(len(audio_float)),
                        audio_float
                    )
                
                # Convert to tensor
                audio_tensor = torch.from_numpy(audio_float)
                
                # Get VAD prediction
                confidence = self.model.predict(audio_tensor, 16000).item()
                is_speech = confidence > self.threshold
                
                return {
                    "is_speech": is_speech,
                    "confidence": confidence,
                    "energy": energy,
                    "timestamp_ms": self._get_current_time_ms()
                }
                
            except Exception as e:
                logger.error(f"VAD model prediction failed: {e}")
                # Fall back to energy-based detection
        
        # Energy-based fallback
        is_speech = energy > self.energy_threshold * 2  # Higher threshold for fallback
        confidence = min(1.0, energy / (self.energy_threshold * 4))
        
        return {
            "is_speech": is_speech,
            "confidence": confidence,
            "energy": energy,
            "timestamp_ms": self._get_current_time_ms()
        }
    
    async def detect_speech_segments(
        self,
        audio_chunks: AsyncGenerator[AudioChunk, None]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Detect speech segments from streaming audio chunks."""
        
        async for chunk in audio_chunks:
            result = await self.process_chunk(chunk)
            
            # Update state
            current_time = result["timestamp_ms"]
            
            if result["is_speech"]:
                if not self.is_speaking:
                    # Speech started
                    if self.speech_start_time is None:
                        self.speech_start_time = current_time
                    
                    # Check if we've had enough continuous speech
                    speech_duration = current_time - self.speech_start_time
                    if speech_duration >= self.min_speech_duration_ms:
                        self.is_speaking = True
                        self.silence_start_time = None
                        
                        # Trigger callback
                        if self.on_speech_start:
                            await self._safe_callback(self.on_speech_start, result)
                        
                        yield {
                            "event": "speech_start",
                            "timestamp_ms": current_time,
                            "confidence": result["confidence"],
                            "energy": result["energy"]
                        }
                
                # Reset silence timer
                self.silence_start_time = None
                
            else:
                # No speech detected
                if self.is_speaking:
                    # We were speaking, start silence timer
                    if self.silence_start_time is None:
                        self.silence_start_time = current_time
                    
                    # Check if we've had enough silence
                    silence_duration = current_time - self.silence_start_time
                    if silence_duration >= self.min_silence_duration_ms:
                        self.is_speaking = False
                        self.speech_start_time = None
                        
                        # Trigger callback
                        if self.on_speech_end:
                            await self._safe_callback(self.on_speech_end, result)
                        
                        yield {
                            "event": "speech_end",
                            "timestamp_ms": current_time,
                            "silence_duration_ms": silence_duration
                        }
                
                else:
                    # Reset speech timer
                    self.speech_start_time = None
            
            # Yield continuous updates
            yield {
                "event": "vad_update",
                "timestamp_ms": current_time,
                "is_speech": result["is_speech"],
                "confidence": result["confidence"],
                "energy": result["energy"],
                "speaking_state": self.is_speaking
            }
    
    async def detect_barge_in(self, audio_chunk: AudioChunk, tts_playing: bool = False) -> bool:
        """Detect if user is trying to interrupt during TTS playback.
        
        Args:
            audio_chunk: Audio chunk to analyze
            tts_playing: Whether TTS is currently playing
            
        Returns:
            True if barge-in detected
        """
        
        if not tts_playing:
            return False
        
        result = await self.process_chunk(audio_chunk)
        
        # More sensitive detection during TTS playback
        barge_in_threshold = max(0.3, self.threshold * 0.6)
        
        if result["confidence"] > barge_in_threshold and result["energy"] > self.energy_threshold:
            # Potential barge-in detected
            if self.on_barge_in:
                await self._safe_callback(self.on_barge_in, result)
            
            return True
        
        return False
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current VAD state."""
        return {
            "is_speaking": self.is_speaking,
            "current_energy": self.current_energy,
            "speech_start_time": self.speech_start_time,
            "silence_start_time": self.silence_start_time,
            "model_ready": self.model_ready,
            "threshold": self.threshold
        }
    
    def update_config(self, **kwargs):
        """Update VAD configuration."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.debug(f"Updated VAD config: {key} = {value}")
    
    def reset_state(self):
        """Reset VAD state."""
        self.is_speaking = False
        self.speech_start_time = None
        self.silence_start_time = None
        self.current_energy = 0.0
        logger.debug("VAD state reset")
    
    async def _safe_callback(self, callback: Callable, *args, **kwargs):
        """Safely execute callback without breaking VAD processing."""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)
        except Exception as e:
            logger.error(f"VAD callback error: {e}")
    
    def _get_current_time_ms(self) -> int:
        """Get current timestamp in milliseconds."""
        import time
        return int(time.time() * 1000)


class StreamingVAD:
    """Streaming Voice Activity Detection for real-time processing."""
    
    def __init__(self, vad: VoiceActivityDetector):
        self.vad = vad
        self.audio_queue = asyncio.Queue()
        self.result_queue = asyncio.Queue()
        self.processing_task = None
        self.running = False
    
    async def start(self):
        """Start streaming VAD processing."""
        if self.running:
            return
        
        self.running = True
        self.processing_task = asyncio.create_task(self._process_stream())
        logger.info("Streaming VAD started")
    
    async def stop(self):
        """Stop streaming VAD processing."""
        if not self.running:
            return
        
        self.running = False
        
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Streaming VAD stopped")
    
    async def add_audio(self, audio_chunk: AudioChunk):
        """Add audio chunk for processing."""
        if self.running:
            await self.audio_queue.put(audio_chunk)
    
    async def get_result(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """Get VAD result with timeout."""
        try:
            return await asyncio.wait_for(self.result_queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
    
    async def _process_stream(self):
        """Process audio stream continuously."""
        try:
            while self.running:
                try:
                    # Get audio chunk with timeout
                    audio_chunk = await asyncio.wait_for(
                        self.audio_queue.get(), 
                        timeout=0.1
                    )
                    
                    # Process with VAD
                    result = await self.vad.process_chunk(audio_chunk)
                    
                    # Put result in queue
                    await self.result_queue.put(result)
                    
                except asyncio.TimeoutError:
                    # No audio available, continue
                    continue
                except Exception as e:
                    logger.error(f"Streaming VAD processing error: {e}")
                    continue
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Streaming VAD task error: {e}")
        
        self.running = False