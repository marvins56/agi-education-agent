"""Speech-to-Text engine with local Whisper optimization for CPU."""
import asyncio
import logging
import tempfile
import os
import time
import numpy as np
from typing import Optional, Dict, Any, List, Union, AsyncGenerator
from concurrent.futures import ThreadPoolExecutor

from src.voice.schemas import TranscriptionResult, STTProvider, AudioChunk

logger = logging.getLogger(__name__)


class LocalWhisperSTTEngine:
    """Local Whisper STT engine optimized for CPU performance."""
    
    def __init__(
        self,
        model_name: str = "tiny",  # tiny, base, small for CPU
        language: str = "en",
        device: str = "cpu",
        compute_type: str = "int8"  # int8 for CPU optimization
    ):
        """Initialize local Whisper engine.
        
        Args:
            model_name: Whisper model size (tiny, base, small)
            language: Primary language for optimization
            device: Device to run on (cpu recommended for i5-6500)
            compute_type: Computation type for speed/accuracy tradeoff
        """
        self.model_name = model_name
        self.language = language
        self.device = device
        self.compute_type = compute_type
        
        # Model state
        self.model = None
        self.model_ready = False
        
        # Performance optimization
        self.executor = ThreadPoolExecutor(max_workers=1)
        
        # Audio buffer for streaming
        self.audio_buffer = bytearray()
        self.buffer_lock = asyncio.Lock()
        
        # Language detection cache
        self.language_cache = {}
        
        # Performance stats
        self.stats = {
            "total_requests": 0,
            "avg_processing_time_ms": 0,
            "model_load_time_ms": 0
        }
        
    async def initialize(self):
        """Initialize Whisper model in thread pool."""
        if self.model_ready:
            return
        
        try:
            start_time = time.time()
            
            # Load model in thread to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                self.executor, self._load_model
            )
            
            load_time = int((time.time() - start_time) * 1000)
            self.stats["model_load_time_ms"] = load_time
            
            logger.info(f"Local Whisper {self.model_name} model loaded in {load_time}ms")
            
        except Exception as e:
            logger.error(f"Failed to initialize Whisper model: {e}")
            raise
    
    def _load_model(self):
        """Load Whisper model (runs in thread)."""
        try:
            # Try whisper-cpp first (faster), fallback to openai-whisper
            try:
                import faster_whisper
                
                self.model = faster_whisper.WhisperModel(
                    self.model_name,
                    device=self.device,
                    compute_type=self.compute_type
                )
                
                self.model_ready = True
                logger.info(f"Using faster-whisper with {self.model_name} model")
                return
                
            except ImportError:
                logger.info("faster-whisper not available, trying openai-whisper")
            
            # Fallback to openai-whisper
            try:
                import whisper
                
                self.model = whisper.load_model(
                    self.model_name,
                    device=self.device
                )
                
                self.model_ready = True
                logger.info(f"Using openai-whisper with {self.model_name} model")
                return
                
            except ImportError:
                logger.error("Neither faster-whisper nor openai-whisper available")
                
            # Last resort: use mock model
            self.model = "mock"
            self.model_ready = True
            logger.warning("Using mock STT model - install whisper for real functionality")
            
        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            self.model = "mock"
            self.model_ready = True
    
    async def transcribe_audio(
        self,
        audio_data: Union[bytes, AudioChunk],
        language: Optional[str] = None,
        enable_vad: bool = True
    ) -> TranscriptionResult:
        """Transcribe audio data to text.
        
        Args:
            audio_data: Raw audio bytes or AudioChunk
            language: Language code (None for auto-detection)
            enable_vad: Enable voice activity detection
            
        Returns:
            TranscriptionResult with text and metadata
        """
        
        if not self.model_ready:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Extract audio bytes and metadata
            if isinstance(audio_data, AudioChunk):
                audio_bytes = audio_data.audio_data
                duration_ms = audio_data.duration_ms
                sample_rate = audio_data.sample_rate
            else:
                audio_bytes = audio_data
                duration_ms = self._estimate_duration(audio_bytes)
                sample_rate = 16000  # Assume default
            
            # Pre-process audio
            audio_array = self._preprocess_audio(audio_bytes, sample_rate)
            
            # Check if audio contains speech
            if enable_vad and not self._has_speech(audio_array):
                return TranscriptionResult(
                    text="",
                    confidence=0.0,
                    provider=STTProvider.WHISPER,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    language=language or self.language,
                    audio_duration_ms=duration_ms,
                    speech_detected=False
                )
            
            # Transcribe in thread pool
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._transcribe_sync,
                audio_array,
                language or self.language
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Update stats
            self.stats["total_requests"] += 1
            self.stats["avg_processing_time_ms"] = (
                self.stats["avg_processing_time_ms"] * (self.stats["total_requests"] - 1) +
                processing_time
            ) // self.stats["total_requests"]
            
            return TranscriptionResult(
                text=result.get("text", ""),
                confidence=self._calculate_confidence(result),
                provider=STTProvider.WHISPER,
                processing_time_ms=processing_time,
                language=result.get("language", language or self.language),
                audio_duration_ms=duration_ms,
                speech_detected=bool(result.get("text", "").strip()),
                words=result.get("words"),
                segments=result.get("segments"),
                noise_level=self._estimate_noise_level(audio_array)
            )
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"Transcription failed: {e}")
            
            return TranscriptionResult(
                text="",
                confidence=0.0,
                provider=STTProvider.WHISPER,
                processing_time_ms=processing_time,
                language=language or self.language,
                audio_duration_ms=duration_ms or 0,
                speech_detected=False
            )
    
    def _transcribe_sync(self, audio_array: np.ndarray, language: str) -> Dict[str, Any]:
        """Synchronous transcription (runs in thread)."""
        
        if self.model == "mock":
            return self._mock_transcribe(audio_array, language)
        
        try:
            # Check if using faster-whisper
            if hasattr(self.model, 'transcribe'):
                if isinstance(self.model, type(None)):
                    return {"text": "", "language": language}
                
                # faster-whisper
                segments, info = self.model.transcribe(
                    audio_array,
                    language=language if language != "auto" else None,
                    vad_filter=True,
                    vad_parameters=dict(
                        min_silence_duration_ms=500,
                        max_speech_duration_s=30
                    )
                )
                
                # Combine segments
                text = " ".join([segment.text for segment in segments])
                
                return {
                    "text": text.strip(),
                    "language": info.language,
                    "segments": [
                        {
                            "start": s.start,
                            "end": s.end,
                            "text": s.text
                        } for s in segments
                    ]
                }
            
            else:
                # openai-whisper
                result = self.model.transcribe(
                    audio_array,
                    language=language if language != "auto" else None,
                    word_timestamps=True
                )
                
                return {
                    "text": result.get("text", "").strip(),
                    "language": result.get("language", language),
                    "segments": result.get("segments", []),
                    "words": []  # Extract from segments if needed
                }
                
        except Exception as e:
            logger.error(f"Sync transcription error: {e}")
            return {"text": "", "language": language}
    
    def _mock_transcribe(self, audio_array: np.ndarray, language: str) -> Dict[str, Any]:
        """Mock transcription for development/testing."""
        
        # Simulate processing time based on audio length
        duration = len(audio_array) / 16000  # Assume 16kHz
        processing_time = min(duration * 0.1, 0.5)  # 10% of audio duration, max 500ms
        time.sleep(processing_time)
        
        # Return mock text based on audio characteristics
        energy = float(np.mean(np.abs(audio_array)))
        
        if energy < 0.01:
            return {"text": "", "language": language}
        
        mock_phrases = [
            "Can you tell me about the causes of World War One?",
            "What was the Alliance System in Europe?",
            "How did nationalism contribute to the conflict?",
            "I'd like to learn more about the Eastern Front.",
            "That's very helpful, thank you for explaining."
        ]
        
        # Choose phrase based on audio characteristics
        phrase_index = int(energy * 1000) % len(mock_phrases)
        text = mock_phrases[phrase_index]
        
        return {
            "text": text,
            "language": language,
            "segments": [{"start": 0.0, "end": duration, "text": text}]
        }
    
    async def transcribe_streaming(
        self,
        audio_stream: AsyncGenerator[AudioChunk, None],
        language: Optional[str] = None,
        chunk_duration_ms: int = 1000
    ) -> AsyncGenerator[TranscriptionResult, None]:
        """Transcribe streaming audio with buffering.
        
        Args:
            audio_stream: Stream of audio chunks
            language: Language for transcription
            chunk_duration_ms: Buffer duration before transcribing
        """
        
        buffer_size = (16000 * 2 * chunk_duration_ms) // 1000  # 16kHz, 16-bit
        
        async with self.buffer_lock:
            self.audio_buffer.clear()
        
        try:
            async for chunk in audio_stream:
                async with self.buffer_lock:
                    self.audio_buffer.extend(chunk.audio_data)
                
                # Check if buffer is full enough to transcribe
                if len(self.audio_buffer) >= buffer_size:
                    # Copy buffer and clear
                    async with self.buffer_lock:
                        audio_data = bytes(self.audio_buffer)
                        self.audio_buffer.clear()
                    
                    # Transcribe buffer
                    if audio_data:
                        result = await self.transcribe_audio(audio_data, language)
                        
                        # Only yield if we got actual text
                        if result.text.strip():
                            yield result
                            
        except Exception as e:
            logger.error(f"Streaming transcription error: {e}")
    
    async def detect_language(
        self,
        audio_data: Union[bytes, AudioChunk],
        cache_result: bool = True
    ) -> str:
        """Detect language from audio sample.
        
        Args:
            audio_data: Audio sample for language detection
            cache_result: Cache result for performance
            
        Returns:
            Detected language code
        """
        
        try:
            # Use smaller sample for faster detection
            if isinstance(audio_data, AudioChunk):
                audio_bytes = audio_data.audio_data[:32000]  # ~1 second
            else:
                audio_bytes = audio_data[:32000]
            
            # Check cache first
            audio_hash = hash(audio_bytes) if cache_result else None
            if audio_hash and audio_hash in self.language_cache:
                return self.language_cache[audio_hash]
            
            # Transcribe with language detection
            result = await self.transcribe_audio(audio_bytes, language="auto")
            detected_lang = result.language
            
            # Cache result
            if cache_result and audio_hash:
                self.language_cache[audio_hash] = detected_lang
            
            return detected_lang
            
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return self.language  # Default language
    
    def _preprocess_audio(self, audio_bytes: bytes, sample_rate: int = 16000) -> np.ndarray:
        """Preprocess raw audio for Whisper."""
        
        # Convert to numpy array
        if len(audio_bytes) == 0:
            return np.array([], dtype=np.float32)
        
        try:
            # Assume 16-bit PCM
            audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
            
            # Convert to float32 and normalize
            audio_float32 = audio_int16.astype(np.float32) / 32768.0
            
            # Resample to 16kHz if needed (simple, not ideal)
            if sample_rate != 16000:
                target_length = int(len(audio_float32) * 16000 / sample_rate)
                if target_length > 0:
                    audio_float32 = np.interp(
                        np.linspace(0, len(audio_float32), target_length),
                        np.arange(len(audio_float32)),
                        audio_float32
                    )
            
            return audio_float32
            
        except Exception as e:
            logger.error(f"Audio preprocessing failed: {e}")
            return np.array([], dtype=np.float32)
    
    def _has_speech(self, audio_array: np.ndarray, threshold: float = 0.005) -> bool:
        """Quick check if audio contains speech."""
        if len(audio_array) == 0:
            return False
        
        # Simple energy-based check
        energy = float(np.mean(np.abs(audio_array)))
        return energy > threshold
    
    def _calculate_confidence(self, result: Dict[str, Any]) -> float:
        """Calculate confidence score from transcription result."""
        
        # Whisper doesn't provide confidence directly
        # Use text length and segment consistency as proxy
        
        text = result.get("text", "")
        segments = result.get("segments", [])
        
        if not text.strip():
            return 0.0
        
        # Base confidence on text characteristics
        confidence = 0.5  # Base confidence
        
        # Longer text is often more reliable
        text_length_bonus = min(0.3, len(text) / 200)
        confidence += text_length_bonus
        
        # Multiple segments suggest structured speech
        if len(segments) > 1:
            confidence += 0.1
        
        # Check for common speech patterns
        if any(word in text.lower() for word in ["the", "and", "is", "was", "can", "what"]):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _estimate_duration(self, audio_bytes: bytes) -> int:
        """Estimate audio duration from byte length."""
        # Assume 16kHz, 16-bit, mono
        sample_rate = 16000
        bytes_per_sample = 2
        duration_seconds = len(audio_bytes) / (sample_rate * bytes_per_sample)
        return int(duration_seconds * 1000)
    
    def _estimate_noise_level(self, audio_array: np.ndarray) -> float:
        """Estimate background noise level."""
        if len(audio_array) == 0:
            return 0.0
        
        # Use quietest 10% of samples as noise estimate
        sorted_abs = np.sort(np.abs(audio_array))
        noise_samples = sorted_abs[:max(1, len(sorted_abs) // 10)]
        return float(np.mean(noise_samples))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine performance statistics."""
        return {
            **self.stats,
            "model_name": self.model_name,
            "language": self.language,
            "device": self.device,
            "model_ready": self.model_ready,
            "cache_size": len(self.language_cache)
        }
    
    def clear_cache(self):
        """Clear language detection cache."""
        self.language_cache.clear()
        logger.info("STT engine cache cleared")
    
    async def cleanup(self):
        """Clean up resources."""
        if self.executor:
            self.executor.shutdown(wait=True)
        
        self.model = None
        self.model_ready = False
        self.language_cache.clear()
        
        logger.info("STT engine cleaned up")