"""Text-to-Speech engine with Piper TTS for local CPU processing."""
import asyncio
import logging
import tempfile
import os
import re
import time
from typing import Optional, Dict, Any, List, AsyncGenerator, Union
from concurrent.futures import ThreadPoolExecutor
import json

from src.voice.schemas import VoiceResponse, VoicePersona, AudioFormat, VoiceProvider

logger = logging.getLogger(__name__)


class PiperTTSEngine:
    """Local Piper TTS engine optimized for CPU performance."""
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        voice_name: str = "en_US-amy-medium",
        sample_rate: int = 22050,
        use_cuda: bool = False
    ):
        """Initialize Piper TTS engine.
        
        Args:
            model_path: Path to Piper model (auto-download if None)
            voice_name: Voice model name
            sample_rate: Audio sample rate
            use_cuda: Use CUDA if available (False for CPU optimization)
        """
        self.model_path = model_path
        self.voice_name = voice_name
        self.sample_rate = sample_rate
        self.use_cuda = use_cuda
        
        # Voice persona mapping to Piper voices
        self.voice_mapping = {
            VoicePersona.SARAH_ENCOURAGING: "en_US-amy-medium",
            VoicePersona.ADAM_AUTHORITATIVE: "en_US-danny-low", 
            VoicePersona.DAVID_SCHOLARLY: "en_US-ryan-medium",
            VoicePersona.EMMA_ENGAGING: "en_US-kathleen-low"
        }
        
        # Model state
        self.synthesizer = None
        self.model_ready = False
        
        # Thread pool for CPU processing
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Streaming settings
        self.sentence_buffer = []
        self.stream_chunk_size = 4096
        
        # Performance stats
        self.stats = {
            "total_requests": 0,
            "total_characters": 0,
            "avg_generation_time_ms": 0,
            "model_load_time_ms": 0
        }
        
        # Speech rate adjustment for accessibility
        self.speed_multiplier = 1.0
        self.accessibility_mode = False
        
    async def initialize(self):
        """Initialize Piper TTS model."""
        if self.model_ready:
            return
        
        try:
            start_time = time.time()
            
            # Load model in thread pool
            await asyncio.get_event_loop().run_in_executor(
                self.executor, self._load_model
            )
            
            load_time = int((time.time() - start_time) * 1000)
            self.stats["model_load_time_ms"] = load_time
            
            logger.info(f"Piper TTS model loaded in {load_time}ms")
            
        except Exception as e:
            logger.error(f"Failed to initialize Piper TTS: {e}")
            # Continue with mock mode for development
            self.synthesizer = "mock"
            self.model_ready = True
    
    def _load_model(self):
        """Load Piper model (runs in thread)."""
        try:
            # Try to import piper_tts
            try:
                from piper import PiperVoice
                import onnxruntime
                
                # Set CPU-only for ONNX Runtime
                if not self.use_cuda:
                    os.environ["OMP_NUM_THREADS"] = "2"  # Optimize for i5-6500
                
                # Load voice model
                if self.model_path:
                    voice_path = self.model_path
                else:
                    voice_path = self._download_voice_model(self.voice_name)
                
                if voice_path and os.path.exists(voice_path):
                    self.synthesizer = PiperVoice.load(voice_path)
                    logger.info(f"Loaded Piper voice: {self.voice_name}")
                else:
                    raise FileNotFoundError(f"Voice model not found: {voice_path}")
                
                self.model_ready = True
                return
                
            except ImportError:
                logger.warning("piper-tts not available, trying alternative...")
            
            # Fallback to system TTS (espeak, etc.)
            try:
                import subprocess
                
                # Test if espeak is available
                result = subprocess.run(
                    ["espeak", "--version"], 
                    capture_output=True, 
                    timeout=5
                )
                
                if result.returncode == 0:
                    self.synthesizer = "espeak"
                    logger.info("Using espeak as TTS fallback")
                    self.model_ready = True
                    return
                    
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
            
            # Last resort: mock TTS
            self.synthesizer = "mock"
            self.model_ready = True
            logger.warning("Using mock TTS - install piper-tts for real functionality")
            
        except Exception as e:
            logger.error(f"TTS model loading failed: {e}")
            self.synthesizer = "mock"
            self.model_ready = True
    
    def _download_voice_model(self, voice_name: str) -> Optional[str]:
        """Download Piper voice model if not available."""
        
        # Create models directory
        models_dir = os.path.expanduser("~/.local/share/piper/voices")
        os.makedirs(models_dir, exist_ok=True)
        
        model_file = os.path.join(models_dir, f"{voice_name}.onnx")
        config_file = os.path.join(models_dir, f"{voice_name}.onnx.json")
        
        # Check if model already exists
        if os.path.exists(model_file) and os.path.exists(config_file):
            return model_file
        
        try:
            import urllib.request
            
            base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
            
            # Construct URLs
            model_url = f"{base_url}/en/en_US/{voice_name.split('-')[1]}/{voice_name}.onnx"
            config_url = f"{base_url}/en/en_US/{voice_name.split('-')[1]}/{voice_name}.onnx.json"
            
            logger.info(f"Downloading Piper voice model: {voice_name}")
            
            # Download model
            urllib.request.urlretrieve(model_url, model_file)
            urllib.request.urlretrieve(config_url, config_file)
            
            logger.info(f"Downloaded Piper voice model to {model_file}")
            return model_file
            
        except Exception as e:
            logger.error(f"Failed to download voice model: {e}")
            return None
    
    async def synthesize_speech(
        self,
        text: str,
        voice_persona: VoicePersona = VoicePersona.SARAH_ENCOURAGING,
        format: AudioFormat = AudioFormat.WAV,
        streaming: bool = False
    ) -> VoiceResponse:
        """Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            voice_persona: Voice persona to use
            format: Output audio format
            streaming: Enable streaming synthesis
            
        Returns:
            VoiceResponse with audio data
        """
        
        if not self.model_ready:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Clean and prepare text
            clean_text = self._preprocess_text(text)
            if not clean_text.strip():
                return self._create_empty_response(text, voice_persona)
            
            # Select voice for persona
            voice_name = self._get_voice_for_persona(voice_persona)
            
            # Synthesize in thread pool
            audio_data = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._synthesize_sync,
                clean_text,
                voice_name
            )
            
            generation_time = int((time.time() - start_time) * 1000)
            
            # Update stats
            self.stats["total_requests"] += 1
            self.stats["total_characters"] += len(text)
            self.stats["avg_generation_time_ms"] = (
                self.stats["avg_generation_time_ms"] * (self.stats["total_requests"] - 1) +
                generation_time
            ) // self.stats["total_requests"]
            
            # Estimate duration
            duration_ms = self._estimate_audio_duration(clean_text)
            
            return VoiceResponse(
                text=text,
                audio_data=audio_data,
                voice_persona=voice_persona,
                provider=VoiceProvider.ELEVENLABS,  # Keep as ElevenLabs in schema for compatibility
                duration_ms=duration_ms,
                format=format,
                sample_rate=self.sample_rate,
                generation_time_ms=generation_time,
                character_count=len(text)
            )
            
        except Exception as e:
            logger.error(f"Speech synthesis failed: {e}")
            generation_time = int((time.time() - start_time) * 1000)
            
            return VoiceResponse(
                text=text,
                audio_data=self._generate_silence(1000),  # 1 second of silence
                voice_persona=voice_persona,
                provider=VoiceProvider.ELEVENLABS,
                duration_ms=1000,
                format=format,
                generation_time_ms=generation_time,
                character_count=len(text)
            )
    
    def _synthesize_sync(self, text: str, voice_name: str) -> bytes:
        """Synchronous synthesis (runs in thread)."""
        
        if self.synthesizer == "mock":
            return self._mock_synthesize(text)
        
        elif self.synthesizer == "espeak":
            return self._espeak_synthesize(text)
        
        else:
            # Real Piper synthesis
            try:
                # Generate audio
                audio_generator = self.synthesizer.synthesize(text)
                
                # Collect audio chunks
                audio_chunks = []
                for audio_chunk in audio_generator:
                    audio_chunks.append(audio_chunk)
                
                # Combine chunks
                if audio_chunks:
                    import numpy as np
                    combined_audio = np.concatenate(audio_chunks)
                    
                    # Convert to bytes (16-bit PCM)
                    audio_int16 = (combined_audio * 32767).astype('int16')
                    return audio_int16.tobytes()
                else:
                    return b''
                    
            except Exception as e:
                logger.error(f"Piper synthesis error: {e}")
                return self._generate_silence(1000)
    
    def _mock_synthesize(self, text: str) -> bytes:
        """Mock synthesis for development."""
        
        # Simulate processing time
        char_processing_time = len(text) * 0.001  # 1ms per character
        time.sleep(min(char_processing_time, 2.0))  # Max 2 seconds
        
        # Generate simple tone based on text
        duration_seconds = max(1.0, len(text) / 150 * 60 / 60)  # ~150 WPM
        samples = int(self.sample_rate * duration_seconds)
        
        import numpy as np
        
        # Generate a simple tone
        t = np.linspace(0, duration_seconds, samples)
        frequency = 440 + (len(text) % 100)  # Vary frequency based on text
        tone = np.sin(2 * np.pi * frequency * t) * 0.1
        
        # Add some variation
        tone *= np.exp(-t / duration_seconds)  # Fade out
        
        # Convert to 16-bit PCM
        audio_int16 = (tone * 32767).astype('int16')
        return audio_int16.tobytes()
    
    def _espeak_synthesize(self, text: str) -> bytes:
        """Synthesize using espeak."""
        try:
            import subprocess
            
            # Adjust speech rate for accessibility
            speed = int(175 * self.speed_multiplier)  # Default ~175 WPM
            
            cmd = [
                "espeak", 
                "-s", str(speed),  # Speed in WPM
                "-a", "50",  # Amplitude
                "-p", "50",  # Pitch
                "--stdout",  # Output to stdout
                text
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                timeout=30,
                check=True
            )
            
            return result.stdout
            
        except Exception as e:
            logger.error(f"espeak synthesis failed: {e}")
            return self._generate_silence(2000)
    
    async def synthesize_streaming(
        self,
        text: str,
        voice_persona: VoicePersona = VoicePersona.SARAH_ENCOURAGING
    ) -> AsyncGenerator[bytes, None]:
        """Stream synthesis as text arrives (sentence-level chunking)."""
        
        if not self.model_ready:
            await self.initialize()
        
        try:
            # Split text into sentences
            sentences = self._split_into_sentences(text)
            
            for sentence in sentences:
                if sentence.strip():
                    # Synthesize sentence
                    response = await self.synthesize_speech(
                        sentence, 
                        voice_persona,
                        streaming=True
                    )
                    
                    # Yield audio in chunks
                    audio_data = response.audio_data
                    if audio_data:
                        for i in range(0, len(audio_data), self.stream_chunk_size):
                            chunk = audio_data[i:i + self.stream_chunk_size]
                            yield chunk
                            
                            # Small delay for natural pacing
                            await asyncio.sleep(0.01)
                            
        except Exception as e:
            logger.error(f"Streaming synthesis failed: {e}")
            yield b''
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and prepare text for TTS."""
        
        # Remove or replace problematic characters
        text = re.sub(r'[^\w\s\.\,\!\?\:\;\-\(\)]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Add natural pauses
        text = text.replace('.', '. ')
        text = text.replace('!', '! ')
        text = text.replace('?', '? ')
        text = text.replace(',', ', ')
        
        # Expand common abbreviations for better pronunciation
        expansions = {
            ' Dr.': ' Doctor',
            ' Mr.': ' Mister',
            ' Mrs.': ' Missus',
            ' Ms.': ' Miss',
            ' vs.': ' versus',
            ' etc.': ' etcetera',
            ' i.e.': ' that is',
            ' e.g.': ' for example'
        }
        
        for abbrev, expansion in expansions.items():
            text = text.replace(abbrev, expansion)
        
        return text.strip()
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences for streaming."""
        
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        
        # Clean up and filter empty sentences
        result = []
        for sentence in sentences:
            cleaned = sentence.strip()
            if cleaned and len(cleaned) > 3:  # Minimum sentence length
                result.append(cleaned + '.')
        
        return result
    
    def _get_voice_for_persona(self, persona: VoicePersona) -> str:
        """Get voice name for persona."""
        return self.voice_mapping.get(persona, self.voice_name)
    
    def _estimate_audio_duration(self, text: str) -> int:
        """Estimate audio duration in milliseconds."""
        
        # Average speaking rate with current speed multiplier
        wpm = int(150 / self.speed_multiplier)  # Words per minute
        words = len(text.split())
        
        # Add pause time for punctuation
        pauses = text.count('.') * 500 + text.count(',') * 200  # ms
        
        duration_ms = (words / wpm * 60 * 1000) + pauses
        return int(max(500, duration_ms))  # Minimum 500ms
    
    def _generate_silence(self, duration_ms: int) -> bytes:
        """Generate silence for given duration."""
        samples = int(self.sample_rate * duration_ms / 1000)
        import numpy as np
        silence = np.zeros(samples, dtype='int16')
        return silence.tobytes()
    
    def _create_empty_response(
        self,
        text: str,
        voice_persona: VoicePersona
    ) -> VoiceResponse:
        """Create empty response for invalid input."""
        
        return VoiceResponse(
            text=text,
            audio_data=self._generate_silence(100),  # 100ms silence
            voice_persona=voice_persona,
            provider=VoiceProvider.ELEVENLABS,
            duration_ms=100,
            format=AudioFormat.WAV,
            sample_rate=self.sample_rate,
            generation_time_ms=1,
            character_count=0
        )
    
    def set_accessibility_mode(
        self,
        enabled: bool,
        speed_multiplier: float = 0.8
    ):
        """Enable accessibility mode with slower speech."""
        
        self.accessibility_mode = enabled
        
        if enabled:
            self.speed_multiplier = max(0.3, min(1.0, speed_multiplier))
            logger.info(f"Accessibility mode enabled, speed: {self.speed_multiplier}x")
        else:
            self.speed_multiplier = 1.0
            logger.info("Accessibility mode disabled")
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices."""
        
        voices = []
        for persona, voice_name in self.voice_mapping.items():
            voices.append({
                "persona": persona.value,
                "name": persona.value.replace("_", " ").title(),
                "voice_model": voice_name,
                "language": "en-US",
                "gender": "female" if "sarah" in persona.value or "emma" in persona.value else "male",
                "style": persona.value.split("_")[1]
            })
        
        return voices
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine performance statistics."""
        return {
            **self.stats,
            "voice_name": self.voice_name,
            "sample_rate": self.sample_rate,
            "model_ready": self.model_ready,
            "accessibility_mode": self.accessibility_mode,
            "speed_multiplier": self.speed_multiplier,
            "synthesizer_type": str(type(self.synthesizer).__name__)
        }
    
    async def cleanup(self):
        """Clean up resources."""
        if self.executor:
            self.executor.shutdown(wait=True)
        
        self.synthesizer = None
        self.model_ready = False
        
        logger.info("TTS engine cleaned up")


class StreamingTTSBuffer:
    """Buffer for streaming TTS synthesis."""
    
    def __init__(self, tts_engine: PiperTTSEngine):
        self.tts_engine = tts_engine
        self.text_buffer = ""
        self.sentence_queue = asyncio.Queue()
        self.audio_queue = asyncio.Queue()
        
        self.processing_task = None
        self.running = False
    
    async def start(self):
        """Start streaming TTS processing."""
        if self.running:
            return
        
        self.running = True
        self.processing_task = asyncio.create_task(self._process_stream())
        logger.info("Streaming TTS buffer started")
    
    async def stop(self):
        """Stop streaming TTS processing."""
        if not self.running:
            return
        
        self.running = False
        
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Streaming TTS buffer stopped")
    
    async def add_text(self, text: str):
        """Add text for streaming synthesis."""
        if self.running:
            self.text_buffer += text
            await self._check_for_sentences()
    
    async def get_audio(self, timeout: float = 1.0) -> Optional[bytes]:
        """Get synthesized audio chunk."""
        try:
            return await asyncio.wait_for(self.audio_queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
    
    async def _check_for_sentences(self):
        """Check buffer for complete sentences."""
        
        # Look for sentence endings
        sentences = []
        remaining = self.text_buffer
        
        for delimiter in ['. ', '! ', '? ']:
            if delimiter in remaining:
                parts = remaining.split(delimiter)
                for i in range(len(parts) - 1):
                    sentences.append(parts[i] + delimiter.strip())
                remaining = parts[-1]
        
        # Update buffer with remaining text
        self.text_buffer = remaining
        
        # Queue sentences for processing
        for sentence in sentences:
            await self.sentence_queue.put(sentence)
    
    async def _process_stream(self):
        """Process text stream continuously."""
        try:
            while self.running:
                try:
                    # Get sentence to synthesize
                    sentence = await asyncio.wait_for(
                        self.sentence_queue.get(),
                        timeout=0.1
                    )
                    
                    # Synthesize sentence
                    async for audio_chunk in self.tts_engine.synthesize_streaming(sentence):
                        await self.audio_queue.put(audio_chunk)
                    
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Streaming TTS processing error: {e}")
                    continue
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Streaming TTS task error: {e}")
        
        self.running = False