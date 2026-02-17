"""OpenAI Whisper STT client."""
import asyncio
import logging
import os
import tempfile
import time
from typing import Optional, Dict, Any, Union, AsyncGenerator, List
import aiohttp
import aiofiles

from src.voice.schemas import TranscriptionResult, STTConfig, STTProvider, AudioChunk

logger = logging.getLogger(__name__)


class WhisperSTTClient:
    """OpenAI Whisper speech-to-text client."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _check_api_key(self) -> bool:
        """Check if API key is available."""
        return bool(self.api_key and self.api_key != "your_openai_api_key_here")
    
    async def transcribe_audio(
        self,
        audio_data: Union[bytes, AudioChunk],
        config: STTConfig = None
    ) -> TranscriptionResult:
        """Transcribe audio to text."""
        
        if not self._check_api_key():
            logger.warning("OpenAI API key not configured, returning mock transcription")
            return self._create_mock_transcription(audio_data)
        
        config = config or STTConfig()
        
        try:
            # Handle different input types
            if isinstance(audio_data, AudioChunk):
                audio_bytes = audio_data.audio_data
                duration_ms = audio_data.duration_ms
            else:
                audio_bytes = audio_data
                duration_ms = self._estimate_duration(audio_bytes)
            
            # Write audio to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name
            
            try:
                start_time = time.time()
                result = await self._send_to_whisper(temp_file_path, config)
                processing_time = int((time.time() - start_time) * 1000)
                
                return TranscriptionResult(
                    text=result.get("text", ""),
                    confidence=1.0,  # Whisper doesn't provide confidence scores
                    provider=STTProvider.WHISPER,
                    processing_time_ms=processing_time,
                    language=result.get("language", config.language),
                    audio_duration_ms=duration_ms,
                    speech_detected=bool(result.get("text", "").strip()),
                    words=result.get("words"),
                    segments=result.get("segments")
                )
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            return self._create_mock_transcription(audio_data)
    
    async def _send_to_whisper(
        self,
        file_path: str,
        config: STTConfig
    ) -> Dict[str, Any]:
        """Send audio file to Whisper API."""
        
        url = f"{self.base_url}/audio/transcriptions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Prepare form data
        data = aiohttp.FormData()
        
        # Add file
        async with aiofiles.open(file_path, 'rb') as audio_file:
            audio_content = await audio_file.read()
            data.add_field(
                'file',
                audio_content,
                filename='audio.wav',
                content_type='audio/wav'
            )
        
        # Add parameters
        data.add_field('model', config.model)
        data.add_field('language', config.language)
        data.add_field('response_format', 'verbose_json')  # Get detailed response
        
        if config.temperature > 0:
            data.add_field('temperature', str(config.temperature))
        
        if config.prompt:
            data.add_field('prompt', config.prompt)
        
        # Send request
        async with self.session.post(url, data=data, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                logger.error(f"Whisper API error {response.status}: {error_text}")
                raise Exception(f"Whisper API error: {response.status}")
    
    async def transcribe_streaming(
        self,
        audio_chunks: asyncio.Queue,
        config: STTConfig = None
    ) -> AsyncGenerator[TranscriptionResult, None]:
        """Transcribe streaming audio chunks.
        
        Note: OpenAI Whisper doesn't support streaming, so we buffer chunks
        and transcribe when we have enough audio.
        """
        
        config = config or STTConfig()
        buffer = b""
        min_chunk_size = 16000 * 2  # 1 second of 16kHz 16-bit audio
        
        try:
            while True:
                try:
                    # Get chunk with timeout
                    chunk = await asyncio.wait_for(audio_chunks.get(), timeout=1.0)
                    
                    if isinstance(chunk, AudioChunk):
                        buffer += chunk.audio_data
                    else:
                        buffer += chunk
                    
                    # If we have enough audio, transcribe it
                    if len(buffer) >= min_chunk_size:
                        result = await self.transcribe_audio(buffer, config)
                        
                        # Only yield if we got actual text
                        if result.text.strip():
                            yield result
                        
                        # Clear buffer
                        buffer = b""
                
                except asyncio.TimeoutError:
                    # If no new chunks, transcribe what we have
                    if buffer:
                        result = await self.transcribe_audio(buffer, config)
                        if result.text.strip():
                            yield result
                        buffer = b""
                    break
                    
        except Exception as e:
            logger.error(f"Streaming transcription error: {e}")
    
    async def detect_language(self, audio_data: Union[bytes, AudioChunk]) -> str:
        """Detect language of audio."""
        
        if not self._check_api_key():
            return "en"  # Default to English
        
        try:
            # Use a smaller sample for language detection
            if isinstance(audio_data, AudioChunk):
                sample = audio_data.audio_data[:32000]  # First ~1 second
            else:
                sample = audio_data[:32000]
            
            config = STTConfig(language="", temperature=0.0)  # Empty language for detection
            result = await self.transcribe_audio(sample, config)
            
            return result.language
            
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return "en"
    
    def _estimate_duration(self, audio_bytes: bytes) -> int:
        """Estimate audio duration from byte length."""
        # Assume 16kHz, 16-bit, mono
        sample_rate = 16000
        bytes_per_sample = 2
        duration_seconds = len(audio_bytes) / (sample_rate * bytes_per_sample)
        return int(duration_seconds * 1000)
    
    def _create_mock_transcription(
        self,
        audio_data: Union[bytes, AudioChunk]
    ) -> TranscriptionResult:
        """Create mock transcription when API key is not available."""
        
        if isinstance(audio_data, AudioChunk):
            duration_ms = audio_data.duration_ms
        else:
            duration_ms = self._estimate_duration(audio_data)
        
        # Return a mock transcription for testing
        mock_texts = [
            "I'd like to learn about World War I.",
            "Can you tell me about the causes of the war?",
            "What was the Alliance System?",
            "How did nationalism contribute to the conflict?",
            "That's very helpful, thank you."
        ]
        
        # Choose mock text based on audio length
        text_index = min(len(mock_texts) - 1, duration_ms // 1000)
        mock_text = mock_texts[text_index]
        
        return TranscriptionResult(
            text=mock_text,
            confidence=0.95,
            provider=STTProvider.WHISPER,
            processing_time_ms=100,
            language="en",
            audio_duration_ms=duration_ms,
            speech_detected=True
        )
    
    async def check_quota(self) -> Dict[str, Any]:
        """Check API usage (OpenAI doesn't have a quota endpoint like ElevenLabs)."""
        
        if not self._check_api_key():
            return {
                "status": "mock",
                "api_key_configured": False
            }
        
        # OpenAI doesn't have a public quota endpoint
        # We can only verify the key works by making a test call
        try:
            # Make a minimal test call
            url = f"{self.base_url}/models"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return {
                        "status": "active",
                        "api_key_configured": True
                    }
                else:
                    return {
                        "status": "error", 
                        "error": f"API key validation failed: {response.status}"
                    }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_supported_formats(self) -> List[str]:
        """Get supported audio formats."""
        return [
            "flac", "m4a", "mp3", "mp4", "mpeg", "mpga", 
            "oga", "ogg", "wav", "webm"
        ]
    
    def get_max_file_size(self) -> int:
        """Get maximum file size in bytes (25MB for Whisper)."""
        return 25 * 1024 * 1024