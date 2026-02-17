"""ElevenLabs TTS client with streaming support."""
import asyncio
import logging
import os
from typing import Optional, AsyncGenerator, Dict, Any
import aiohttp
import json

from src.voice.schemas import VoiceResponse, TTSConfig, VoicePersona, AudioFormat, VoiceProvider

logger = logging.getLogger(__name__)


class ElevenLabsClient:
    """ElevenLabs text-to-speech client with streaming support."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1"
        
        # Voice persona to ElevenLabs voice ID mapping
        self.voice_mapping = {
            VoicePersona.SARAH_ENCOURAGING: "EXAVITQu4vr4xnSDxMaL",  # Bella - warm female
            VoicePersona.ADAM_AUTHORITATIVE: "pNInz6obpgDQGcFmaJgB",  # Adam - clear male
            VoicePersona.DAVID_SCHOLARLY: "29vD33N1CtxCmqQRPOHJ",    # Drew - thoughtful male
            VoicePersona.EMMA_ENGAGING: "ThT5KcBeYPX3keUQqHPh",     # Dorothy - engaging female
        }
        
        # Default settings
        self.default_model = "eleven_multilingual_v2"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _get_voice_id(self, persona: VoicePersona) -> str:
        """Get ElevenLabs voice ID for persona."""
        return self.voice_mapping.get(persona, self.voice_mapping[VoicePersona.SARAH_ENCOURAGING])
    
    def _check_api_key(self) -> bool:
        """Check if API key is available."""
        return bool(self.api_key and self.api_key != "your_elevenlabs_api_key_here")
    
    async def synthesize_speech(
        self,
        text: str,
        config: TTSConfig = None,
        stream: bool = False
    ) -> VoiceResponse:
        """Synthesize speech from text."""
        
        if not self._check_api_key():
            logger.warning("ElevenLabs API key not configured, returning mock response")
            return self._create_mock_response(text, config)
        
        config = config or TTSConfig()
        
        try:
            voice_id = config.voice_id or self._get_voice_id(config.voice_persona)
            
            if stream:
                return await self._synthesize_streaming(text, voice_id, config)
            else:
                return await self._synthesize_standard(text, voice_id, config)
                
        except Exception as e:
            logger.error(f"ElevenLabs synthesis failed: {e}")
            return self._create_mock_response(text, config)
    
    async def _synthesize_standard(
        self,
        text: str,
        voice_id: str,
        config: TTSConfig
    ) -> VoiceResponse:
        """Standard (non-streaming) synthesis."""
        
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text,
            "model_id": config.model_id,
            "voice_settings": {
                "stability": config.stability,
                "similarity_boost": config.similarity_boost,
                "style": config.style,
                "use_speaker_boost": config.use_speaker_boost
            }
        }
        
        import time
        start_time = time.time()
        
        async with self.session.post(url, json=data, headers=headers) as response:
            if response.status == 200:
                audio_data = await response.read()
                generation_time = int((time.time() - start_time) * 1000)
                
                return VoiceResponse(
                    text=text,
                    audio_data=audio_data,
                    voice_persona=config.voice_persona,
                    provider=VoiceProvider.ELEVENLABS,
                    duration_ms=self._estimate_duration(text),
                    format=AudioFormat.MP3,
                    sample_rate=44100,
                    generation_time_ms=generation_time,
                    character_count=len(text)
                )
            else:
                error_text = await response.text()
                logger.error(f"ElevenLabs API error {response.status}: {error_text}")
                raise Exception(f"ElevenLabs API error: {response.status}")
    
    async def _synthesize_streaming(
        self,
        text: str,
        voice_id: str,
        config: TTSConfig
    ) -> VoiceResponse:
        """Streaming synthesis (returns URL for streaming endpoint)."""
        
        url = f"{self.base_url}/text-to-speech/{voice_id}/stream"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json", 
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text,
            "model_id": config.model_id,
            "voice_settings": {
                "stability": config.stability,
                "similarity_boost": config.similarity_boost,
                "style": config.style,
                "use_speaker_boost": config.use_speaker_boost
            },
            "optimize_streaming_latency": config.optimize_streaming_latency
        }
        
        # For streaming, we return a response that can be used to start streaming
        return VoiceResponse(
            text=text,
            audio_url=url,  # Client can use this to stream
            voice_persona=config.voice_persona,
            provider=VoiceProvider.ELEVENLABS,
            duration_ms=self._estimate_duration(text),
            format=AudioFormat.MP3,
            character_count=len(text)
        )
    
    async def stream_synthesis(
        self,
        text: str,
        config: TTSConfig = None
    ) -> AsyncGenerator[bytes, None]:
        """Stream synthesis as audio chunks."""
        
        if not self._check_api_key():
            logger.warning("ElevenLabs API key not configured, yielding mock audio")
            yield b"mock_audio_data"
            return
        
        config = config or TTSConfig()
        voice_id = config.voice_id or self._get_voice_id(config.voice_persona)
        
        url = f"{self.base_url}/text-to-speech/{voice_id}/stream"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text,
            "model_id": config.model_id,
            "voice_settings": {
                "stability": config.stability,
                "similarity_boost": config.similarity_boost,
                "style": config.style,
                "use_speaker_boost": config.use_speaker_boost
            },
            "optimize_streaming_latency": config.optimize_streaming_latency
        }
        
        try:
            async with self.session.post(url, json=data, headers=headers) as response:
                if response.status == 200:
                    async for chunk in response.content.iter_chunked(1024):
                        yield chunk
                else:
                    error_text = await response.text()
                    logger.error(f"ElevenLabs streaming error {response.status}: {error_text}")
                    yield b"error_occurred"
        except Exception as e:
            logger.error(f"ElevenLabs streaming failed: {e}")
            yield b"error_occurred"
    
    async def get_voices(self) -> Dict[str, Any]:
        """Get available voices from ElevenLabs."""
        
        if not self._check_api_key():
            return self._get_mock_voices()
        
        url = f"{self.base_url}/voices"
        headers = {"xi-api-key": self.api_key}
        
        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get voices: {response.status}")
                    return self._get_mock_voices()
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            return self._get_mock_voices()
    
    async def get_voice_settings(self, voice_id: str) -> Dict[str, Any]:
        """Get voice settings for a specific voice."""
        
        if not self._check_api_key():
            return {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        
        url = f"{self.base_url}/voices/{voice_id}/settings"
        headers = {"xi-api-key": self.api_key}
        
        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                        "style": 0.0,
                        "use_speaker_boost": True
                    }
        except Exception as e:
            logger.error(f"Error getting voice settings: {e}")
            return {}
    
    def _estimate_duration(self, text: str) -> int:
        """Estimate audio duration in milliseconds based on text length."""
        # Average speaking rate is about 150 words per minute
        # Average word length is about 5 characters
        words = len(text) / 5
        duration_seconds = (words / 150) * 60
        return int(duration_seconds * 1000)
    
    def _create_mock_response(self, text: str, config: TTSConfig = None) -> VoiceResponse:
        """Create mock response when API key is not available."""
        config = config or TTSConfig()
        
        # Create a small mock audio data (silence)
        mock_audio = b'\x00' * 1024  # 1KB of silence
        
        return VoiceResponse(
            text=text,
            audio_data=mock_audio,
            voice_persona=config.voice_persona,
            provider=VoiceProvider.ELEVENLABS,
            duration_ms=self._estimate_duration(text),
            format=AudioFormat.MP3,
            sample_rate=44100,
            generation_time_ms=100,
            character_count=len(text)
        )
    
    def _get_mock_voices(self) -> Dict[str, Any]:
        """Get mock voices for development/testing."""
        return {
            "voices": [
                {
                    "voice_id": "EXAVITQu4vr4xnSDxMaL",
                    "name": "Bella (Sarah Encouraging)",
                    "category": "premade",
                    "description": "Warm and encouraging female voice"
                },
                {
                    "voice_id": "pNInz6obpgDQGcFmaJgB",
                    "name": "Adam (Adam Authoritative)",
                    "category": "premade",
                    "description": "Clear and authoritative male voice"
                },
                {
                    "voice_id": "29vD33N1CtxCmqQRPOHJ",
                    "name": "Drew (David Scholarly)",
                    "category": "premade",
                    "description": "Thoughtful and scholarly male voice"
                },
                {
                    "voice_id": "ThT5KcBeYPX3keUQqHPh",
                    "name": "Dorothy (Emma Engaging)",
                    "category": "premade",
                    "description": "Engaging and enthusiastic female voice"
                }
            ]
        }
    
    async def check_quota(self) -> Dict[str, Any]:
        """Check API usage and quota."""
        
        if not self._check_api_key():
            return {
                "character_count": 0,
                "character_limit": 10000,
                "can_extend_character_limit": True,
                "allowed_to_extend_character_limit": True,
                "status": "mock"
            }
        
        url = f"{self.base_url}/user"
        headers = {"xi-api-key": self.api_key}
        
        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"Failed to check quota: {response.status}"}
        except Exception as e:
            logger.error(f"Error checking quota: {e}")
            return {"error": str(e)}