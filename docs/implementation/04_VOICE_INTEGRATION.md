# Voice Integration Implementation

**Document:** 04_VOICE_INTEGRATION.md  
**Version:** 1.0  
**Date:** February 17, 2026  
**Dependencies:** ElevenLabs API, OpenAI Whisper, Deepgram, WebSocket, Redis  

---

## Overview

This document details the implementation of a professional voice interaction system that enables natural conversations between students and the History tutor AI using ElevenLabs TTS, Whisper/Deepgram STT, and real-time WebSocket communication.

## Architecture Design

### Voice Integration System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    VOICE INTEGRATION SYSTEM                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ STUDENT DEVICE                          SERVER INFRASTRUCTURE   │
│                                                                 │
│ ┌─────────────────────┐                ┌───────────────────────┐ │
│ │   BROWSER/APP       │   WebSocket    │    VOICE GATEWAY      │ │
│ │                     │◄──────────────►│                       │ │
│ │ ┌─────────────────┐ │                │ ┌───────────────────┐ │ │
│ │ │ Audio Recorder  │ │     Audio      │ │   STT Processor   │ │ │
│ │ │ • Microphone    │─┼────Chunks─────►│ │ • Whisper (1st)  │ │ │
│ │ │ • VAD Detection │ │    (binary)    │ │ • Deepgram (2nd) │ │ │
│ │ │ • Noise Cancel  │ │                │ │ • Audio Buffer    │ │ │
│ │ └─────────────────┘ │                │ └───────────────────┘ │ │
│ │                     │                │           │           │ │
│ │ ┌─────────────────┐ │                │           ▼           │ │
│ │ │ Audio Player    │ │    Audio       │ ┌───────────────────┐ │ │
│ │ │ • Speaker Out   │◄┼────Stream◄────│ │ CONVERSATION      │ │ │
│ │ │ • Volume Ctrl   │ │                │ │ ORCHESTRATOR      │ │ │
│ │ │ • Playback UI   │ │                │ │                   │ │ │
│ │ └─────────────────┘ │                │ │ Text→Workflow→    │ │ │
│ │                     │                │ │ Response Text     │ │ │
│ │ ┌─────────────────┐ │                │ └───────┬───────────┘ │ │
│ │ │ Visual Feedback │ │   WebSocket    │         │             │ │
│ │ │ • Speaking      │◄┼────Status◄────┤         ▼             │ │
│ │ │ • Listening     │ │                │ ┌───────────────────┐ │ │
│ │ │ • Thinking      │ │                │ │   TTS PROCESSOR   │ │ │
│ │ │ • Conversation  │ │                │ │ • ElevenLabs API  │ │ │
│ │ └─────────────────┘ │                │ │ • Voice Selection │ │ │
│ └─────────────────────┘                │ │ • Audio Cache     │ │ │
│                                        │ │ • Streaming       │ │ │
│                                        │ └───────────────────┘ │ │
│                                        │                       │ │
│ CONVERSATION FLOW STATE MACHINE        │   BACKGROUND TASKS    │ │
│                                        │                       │ │
│ [IDLE] → [LISTENING] → [TRANSCRIBING]  │ ┌───────────────────┐ │ │
│    ▲         │              │          │ │ • Audio Cleanup   │ │ │
│    │         ▼              ▼          │ │ • Cache Warming   │ │ │
│ [WAITING] ← [THINKING] ← [PROCESSING]  │ │ • Usage Analytics │ │ │
│    │                        │          │ │ • Cost Tracking   │ │ │
│    ▼                        ▼          │ └───────────────────┘ │ │
│ [SPEAKING] ← [GENERATING] ← [COMPLETE]  │                       │ │
│                                        └───────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Structure and Implementation

### Directory Structure
```
src/voice/
├── __init__.py
├── gateway.py               # Main voice WebSocket gateway
├── stt/
│   ├── __init__.py
│   ├── whisper_client.py    # OpenAI Whisper integration
│   ├── deepgram_client.py   # Deepgram fallback
│   ├── stt_manager.py       # STT orchestration and fallback
│   └── audio_processor.py   # Audio preprocessing
├── tts/
│   ├── __init__.py
│   ├── elevenlabs_client.py # ElevenLabs integration
│   ├── voice_manager.py     # Voice selection and caching
│   └── audio_optimizer.py   # Audio processing and compression
├── conversation/
│   ├── __init__.py
│   ├── state_machine.py     # Voice conversation flow
│   ├── session_manager.py   # Voice session management
│   └── interruption_handler.py # Handle interruptions gracefully
├── audio/
│   ├── __init__.py
│   ├── vad.py              # Voice Activity Detection
│   ├── formats.py          # Audio format conversion
│   └── noise_reduction.py  # Audio quality improvement
└── schemas.py              # Voice system data models
```

---

## Core Implementation

### 1. `src/voice/schemas.py` - Data Models
```python
"""Voice system data models and schemas."""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
import base64


class VoiceProvider(str, Enum):
    """Voice service providers."""
    ELEVENLABS = "elevenlabs"
    AZURE = "azure"
    OPENAI = "openai"


class STTProvider(str, Enum):
    """Speech-to-text service providers."""
    WHISPER = "whisper"
    DEEPGRAM = "deepgram"
    AZURE = "azure"


class ConversationState(str, Enum):
    """Voice conversation states."""
    IDLE = "idle"
    LISTENING = "listening"
    TRANSCRIBING = "transcribing"
    PROCESSING = "processing"
    THINKING = "thinking"
    GENERATING = "generating"
    SPEAKING = "speaking"
    WAITING = "waiting"
    COMPLETE = "complete"
    ERROR = "error"


class AudioFormat(str, Enum):
    """Supported audio formats."""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    WEBM = "webm"
    AAC = "aac"


class VoicePersona(str, Enum):
    """Pre-defined voice personas for History tutoring."""
    ADAM_AUTHORITATIVE = "adam_authoritative"      # Male, warm but authoritative
    SARAH_ENCOURAGING = "sarah_encouraging"        # Female, encouraging and patient
    DAVID_SCHOLARLY = "david_scholarly"            # Male, academic and thoughtful
    EMMA_ENGAGING = "emma_engaging"               # Female, enthusiastic and engaging


class AudioChunk(BaseModel):
    """Audio data chunk for streaming."""
    audio_data: bytes = Field(description="Raw audio bytes")
    format: AudioFormat = AudioFormat.WAV
    sample_rate: int = 16000
    channels: int = 1
    duration_ms: int = Field(description="Duration in milliseconds")
    sequence_number: int = Field(description="For ordering chunks")
    is_final: bool = False
    
    def to_base64(self) -> str:
        """Convert audio data to base64 for transmission."""
        return base64.b64encode(self.audio_data).decode('utf-8')
    
    @classmethod
    def from_base64(cls, b64_data: str, **kwargs) -> 'AudioChunk':
        """Create AudioChunk from base64 data."""
        audio_bytes = base64.b64decode(b64_data.encode('utf-8'))
        return cls(audio_data=audio_bytes, **kwargs)


class TranscriptionResult(BaseModel):
    """Result from speech-to-text processing."""
    text: str = Field(description="Transcribed text")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")
    provider: STTProvider = Field(description="STT provider used")
    processing_time_ms: int = Field(description="Processing time in milliseconds")
    language: str = "en"
    
    # Detailed transcription data
    words: Optional[List[Dict[str, Any]]] = None
    segments: Optional[List[Dict[str, Any]]] = None
    
    # Audio metrics
    audio_duration_ms: int = 0
    speech_detected: bool = True
    noise_level: float = Field(ge=0.0, le=1.0, default=0.0)


class VoiceResponse(BaseModel):
    """Generated voice response."""
    text: str = Field(description="Response text")
    audio_url: Optional[str] = None
    audio_data: Optional[bytes] = None
    voice_id: str = Field(description="ElevenLabs voice ID")
    voice_persona: VoicePersona
    
    # Audio properties
    duration_ms: int = 0
    sample_rate: int = 22050
    format: AudioFormat = AudioFormat.MP3
    
    # Generation metadata
    provider: VoiceProvider = VoiceProvider.ELEVENLABS
    generation_time_ms: int = 0
    cost_estimate: float = 0.0
    
    # Educational context
    speaking_rate: float = Field(ge=0.5, le=2.0, default=1.0)
    emotional_tone: str = "encouraging"
    emphasis_words: List[str] = Field(default_factory=list)


class VoiceSessionConfig(BaseModel):
    """Configuration for a voice conversation session."""
    session_id: str
    student_id: str
    
    # Voice preferences
    voice_persona: VoicePersona = VoicePersona.SARAH_ENCOURAGING
    speaking_rate: float = Field(ge=0.7, le=1.5, default=1.0)
    
    # STT preferences
    primary_stt: STTProvider = STTProvider.WHISPER
    fallback_stt: STTProvider = STTProvider.DEEPGRAM
    language: str = "en"
    
    # Audio quality
    noise_suppression: bool = True
    auto_gain_control: bool = True
    echo_cancellation: bool = True
    
    # Conversation flow
    max_silence_ms: int = 3000  # 3 seconds of silence before stopping
    max_speaking_time_ms: int = 300000  # 5 minutes max utterance
    interruption_handling: bool = True
    
    # Educational settings
    subject_context: str = "History"
    grade_level: Optional[str] = None
    learning_style: Optional[str] = None


class VoiceSessionState(BaseModel):
    """Current state of a voice session."""
    session_id: str
    current_state: ConversationState = ConversationState.IDLE
    
    # Timing
    session_start_time: datetime
    last_activity_time: datetime
    total_duration_ms: int = 0
    
    # Conversation tracking
    turn_count: int = 0
    student_speaking_time_ms: int = 0
    ai_speaking_time_ms: int = 0
    silence_time_ms: int = 0
    
    # Quality metrics
    avg_transcription_confidence: float = 0.0
    network_quality: float = 1.0
    audio_quality: float = 1.0
    
    # Current processing
    current_audio_buffer: Optional[bytes] = None
    transcription_in_progress: bool = False
    tts_generation_in_progress: bool = False
    
    # Error tracking
    error_count: int = 0
    last_error: Optional[str] = None
    
    # Cost tracking
    stt_cost: float = 0.0
    tts_cost: float = 0.0
    total_cost: float = 0.0


class WebSocketMessage(BaseModel):
    """WebSocket message format for voice communication."""
    type: str  # "audio_chunk", "transcription", "voice_response", "state_change", "error"
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any] = Field(default_factory=dict)


class VoiceAnalytics(BaseModel):
    """Analytics data for voice sessions."""
    session_id: str
    student_id: str
    
    # Session metrics
    total_duration_minutes: float
    conversation_turns: int
    words_spoken_by_student: int
    words_spoken_by_ai: int
    
    # Quality metrics
    average_response_time_ms: float
    transcription_accuracy: float
    student_engagement_score: float  # Based on response patterns
    
    # Educational effectiveness
    concepts_discussed: List[str]
    questions_asked_by_student: int
    clarifications_requested: int
    
    # Technical performance
    stt_provider_performance: Dict[STTProvider, Dict[str, float]]
    tts_generation_time_ms: float
    network_interruptions: int
    
    # Cost analysis
    total_cost: float
    cost_per_minute: float
    stt_cost_breakdown: Dict[STTProvider, float]
    tts_cost_breakdown: Dict[VoiceProvider, float]
```

### 2. `src/voice/stt/whisper_client.py` - Whisper STT Integration
```python
"""OpenAI Whisper speech-to-text client with educational optimizations."""
import asyncio
import io
import logging
import time
from typing import Optional, Dict, Any
import openai
from openai import AsyncOpenAI
import httpx

from src.voice.schemas import TranscriptionResult, STTProvider, AudioChunk
from src.config import settings

logger = logging.getLogger(__name__)


class WhisperSTTClient:
    """OpenAI Whisper client optimized for educational conversations."""
    
    def __init__(self, api_key: str = None):
        self.client = AsyncOpenAI(api_key=api_key or settings.OPENAI_API_KEY)
        self.model = "whisper-1"
        
        # History-specific vocabulary hints for better accuracy
        self.history_prompt = (
            "This is an educational conversation about History. "
            "Common topics include World War I, World War II, French Revolution, "
            "American Revolution, Ancient Rome, Medieval period, Renaissance, "
            "Industrial Revolution, Cold War, Civil Rights Movement, "
            "imperialism, nationalism, democracy, monarchy, republic, "
            "primary sources, secondary sources, historiography, chronology."
        )
        
        # Performance tracking
        self.total_requests = 0
        self.total_processing_time = 0.0
        self.error_count = 0
    
    async def transcribe_audio(
        self,
        audio_chunk: AudioChunk,
        language: str = "en",
        context_hint: Optional[str] = None
    ) -> TranscriptionResult:
        """Transcribe audio chunk using Whisper."""
        start_time = time.time()
        
        try:
            # Prepare prompt with context
            prompt = self.history_prompt
            if context_hint:
                prompt += f" Current context: {context_hint}"
            
            # Create file-like object from audio data
            audio_file = io.BytesIO(audio_chunk.audio_data)
            audio_file.name = f"audio.{audio_chunk.format.value}"
            
            # Call Whisper API
            response = await self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                language=language,
                prompt=prompt,
                response_format="verbose_json",
                temperature=0.0  # Deterministic for educational content
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Extract transcription data
            transcription = TranscriptionResult(
                text=response.text.strip(),
                confidence=self._estimate_confidence(response),
                provider=STTProvider.WHISPER,
                processing_time_ms=processing_time,
                language=language,
                audio_duration_ms=audio_chunk.duration_ms,
                speech_detected=len(response.text.strip()) > 0
            )
            
            # Add detailed data if available
            if hasattr(response, 'segments'):
                transcription.segments = [
                    {
                        "start": segment.get("start", 0.0),
                        "end": segment.get("end", 0.0),
                        "text": segment.get("text", ""),
                        "confidence": segment.get("avg_logprob", 0.0)
                    }
                    for segment in response.segments
                ]
            
            if hasattr(response, 'words'):
                transcription.words = [
                    {
                        "word": word.get("word", ""),
                        "start": word.get("start", 0.0),
                        "end": word.get("end", 0.0),
                        "confidence": word.get("probability", 0.0)
                    }
                    for word in response.words
                ]
            
            # Update metrics
            self.total_requests += 1
            self.total_processing_time += processing_time
            
            logger.debug(
                f"Whisper transcription: '{transcription.text}' "
                f"(confidence: {transcription.confidence:.2f}, "
                f"time: {processing_time}ms)"
            )
            
            return transcription
            
        except openai.APIError as e:
            self.error_count += 1
            logger.error(f"Whisper API error: {e}")
            raise
        except Exception as e:
            self.error_count += 1
            logger.error(f"Whisper transcription failed: {e}")
            raise
    
    def _estimate_confidence(self, response) -> float:
        """Estimate confidence from Whisper response."""
        # Whisper doesn't provide direct confidence scores
        # We estimate based on available metrics
        
        if hasattr(response, 'segments') and response.segments:
            # Average log probability from segments
            avg_logprob = sum(
                segment.get("avg_logprob", -1.0) 
                for segment in response.segments
            ) / len(response.segments)
            
            # Convert log probability to confidence (0-1)
            confidence = max(0.0, min(1.0, (avg_logprob + 1.0)))
            return confidence
        
        # Fallback: estimate based on text length and common patterns
        text = response.text.strip()
        if not text:
            return 0.0
        
        # Basic heuristics for confidence estimation
        base_confidence = 0.8
        
        # Lower confidence for very short utterances
        if len(text) < 10:
            base_confidence *= 0.8
        
        # Lower confidence if many repeated characters (transcription artifacts)
        repeated_chars = sum(1 for i in range(1, len(text)) if text[i] == text[i-1])
        if repeated_chars > len(text) * 0.3:
            base_confidence *= 0.6
        
        # Higher confidence if contains educational terms
        educational_terms = [
            "history", "war", "revolution", "democracy", "government",
            "economy", "society", "culture", "timeline", "primary", "source"
        ]
        if any(term in text.lower() for term in educational_terms):
            base_confidence *= 1.1
        
        return min(1.0, base_confidence)
    
    async def transcribe_stream(
        self,
        audio_chunks: list[AudioChunk],
        language: str = "en",
        context_hint: Optional[str] = None
    ) -> TranscriptionResult:
        """Transcribe multiple audio chunks as a single stream."""
        
        if not audio_chunks:
            return TranscriptionResult(
                text="",
                confidence=0.0,
                provider=STTProvider.WHISPER,
                processing_time_ms=0,
                language=language,
                speech_detected=False
            )
        
        # Combine audio chunks
        combined_audio = b"".join(chunk.audio_data for chunk in audio_chunks)
        total_duration = sum(chunk.duration_ms for chunk in audio_chunks)
        
        combined_chunk = AudioChunk(
            audio_data=combined_audio,
            format=audio_chunks[0].format,
            sample_rate=audio_chunks[0].sample_rate,
            channels=audio_chunks[0].channels,
            duration_ms=total_duration,
            sequence_number=audio_chunks[0].sequence_number,
            is_final=True
        )
        
        return await self.transcribe_audio(combined_chunk, language, context_hint)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get client performance metrics."""
        avg_processing_time = (
            self.total_processing_time / self.total_requests 
            if self.total_requests > 0 else 0.0
        )
        
        error_rate = (
            self.error_count / self.total_requests 
            if self.total_requests > 0 else 0.0
        )
        
        return {
            "provider": "whisper",
            "total_requests": self.total_requests,
            "avg_processing_time_ms": avg_processing_time,
            "error_rate": error_rate,
            "error_count": self.error_count
        }
    
    async def check_health(self) -> bool:
        """Check if Whisper service is healthy."""
        try:
            # Create a tiny test audio file
            test_audio = b'\x00' * 1024  # 1KB of silence
            test_chunk = AudioChunk(
                audio_data=test_audio,
                duration_ms=100,
                sequence_number=0
            )
            
            # Set a short timeout for health check
            async with asyncio.timeout(5.0):
                result = await self.transcribe_audio(test_chunk)
                return True
        except Exception as e:
            logger.warning(f"Whisper health check failed: {e}")
            return False
```

### 3. `src/voice/tts/elevenlabs_client.py` - ElevenLabs TTS Integration
```python
"""ElevenLabs text-to-speech client for professional History tutoring."""
import asyncio
import logging
import time
import io
from typing import Dict, List, Optional, Any, Union
import httpx
import json

from src.voice.schemas import (
    VoiceResponse, VoicePersona, VoiceProvider, AudioFormat
)
from src.config import settings

logger = logging.getLogger(__name__)


class ElevenLabsVoiceConfig:
    """ElevenLabs voice configurations for History tutoring personas."""
    
    VOICE_PERSONAS = {
        VoicePersona.ADAM_AUTHORITATIVE: {
            "voice_id": "pNInz6obpgDQGcFmaJgB",  # Adam - warm, authoritative
            "model": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.75,
                "similarity_boost": 0.85,
                "style": 0.2,
                "use_speaker_boost": True
            },
            "description": "Warm but authoritative male voice, ideal for explaining complex historical concepts"
        },
        VoicePersona.SARAH_ENCOURAGING: {
            "voice_id": "EXAVITQu4vr4xnSDxMaL",  # Sarah - encouraging, patient
            "model": "eleven_multilingual_v2", 
            "voice_settings": {
                "stability": 0.8,
                "similarity_boost": 0.8,
                "style": 0.3,
                "use_speaker_boost": True
            },
            "description": "Encouraging female voice, perfect for patient tutoring and support"
        },
        VoicePersona.DAVID_SCHOLARLY: {
            "voice_id": "AZnzlk1XvdvUeBnXmlld",  # David - academic, thoughtful
            "model": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.85,
                "similarity_boost": 0.9,
                "style": 0.1,
                "use_speaker_boost": True
            },
            "description": "Scholarly male voice with academic tone for advanced discussions"
        },
        VoicePersona.EMMA_ENGAGING: {
            "voice_id": "ThT5KcBeYPX3keUQqHPh",  # Emma - enthusiastic, engaging
            "model": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.7,
                "similarity_boost": 0.8,
                "style": 0.4,
                "use_speaker_boost": True
            },
            "description": "Enthusiastic female voice that makes history exciting and engaging"
        }
    }


class ElevenLabsTTSClient:
    """ElevenLabs TTS client optimized for educational conversations."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.ELEVENLABS_API_KEY
        self.base_url = "https://api.elevenlabs.io/v1"
        
        # HTTP client with retries and timeouts
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        
        # Audio cache for common phrases
        self._audio_cache: Dict[str, bytes] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Performance tracking
        self.total_requests = 0
        self.total_characters = 0
        self.total_cost = 0.0
        self.total_generation_time = 0.0
        
        # Common History education phrases for caching
        self._warmup_phrases = [
            "That's a great question!",
            "Let me explain that concept.",
            "Can you tell me more about what you're thinking?",
            "You're on the right track.",
            "That's correct! Well done.",
            "Let's explore this topic together.",
            "What do you think happened next?",
            "This is an important historical concept.",
            "Let's look at the primary sources.",
            "Consider the cause and effect relationship here."
        ]
    
    async def initialize(self):
        """Initialize the client and warm up the cache."""
        # Verify API key and connection
        await self._verify_connection()
        
        # Warm up cache with common phrases
        await self._warmup_cache()
        
        logger.info("ElevenLabs client initialized successfully")
    
    async def _verify_connection(self):
        """Verify API connection and get available voices."""
        try:
            response = await self.client.get(
                f"{self.base_url}/voices",
                headers={"xi-api-key": self.api_key}
            )
            response.raise_for_status()
            voices = response.json()
            logger.info(f"Connected to ElevenLabs - {len(voices['voices'])} voices available")
        except Exception as e:
            logger.error(f"Failed to connect to ElevenLabs: {e}")
            raise
    
    async def _warmup_cache(self):
        """Pre-generate and cache common educational phrases."""
        logger.info("Warming up TTS cache with common phrases...")
        
        # Use the default voice for warmup
        default_persona = VoicePersona.SARAH_ENCOURAGING
        
        warmup_tasks = [
            self.generate_speech(
                text=phrase,
                voice_persona=default_persona,
                skip_cache=False  # Allow caching
            )
            for phrase in self._warmup_phrases
        ]
        
        # Generate all phrases concurrently
        await asyncio.gather(*warmup_tasks, return_exceptions=True)
        
        logger.info(f"Cache warmed up with {len(self._warmup_phrases)} phrases")
    
    async def generate_speech(
        self,
        text: str,
        voice_persona: VoicePersona = VoicePersona.SARAH_ENCOURAGING,
        speaking_rate: float = 1.0,
        emotional_tone: str = "encouraging",
        skip_cache: bool = False
    ) -> VoiceResponse:
        """Generate speech audio from text."""
        start_time = time.time()
        
        # Create cache key
        cache_key = self._create_cache_key(text, voice_persona, speaking_rate)
        
        # Check cache first
        if not skip_cache and cache_key in self._audio_cache:
            self._cache_hits += 1
            audio_data = self._audio_cache[cache_key]
            
            return VoiceResponse(
                text=text,
                audio_data=audio_data,
                voice_id=ElevenLabsVoiceConfig.VOICE_PERSONAS[voice_persona]["voice_id"],
                voice_persona=voice_persona,
                duration_ms=self._estimate_audio_duration(text, speaking_rate),
                format=AudioFormat.MP3,
                provider=VoiceProvider.ELEVENLABS,
                generation_time_ms=int((time.time() - start_time) * 1000),
                cost_estimate=0.0,  # Cache hit - no cost
                speaking_rate=speaking_rate,
                emotional_tone=emotional_tone
            )
        
        self._cache_misses += 1
        
        try:
            # Get voice configuration
            voice_config = ElevenLabsVoiceConfig.VOICE_PERSONAS[voice_persona]
            
            # Adjust voice settings for speaking rate and emotion
            adjusted_settings = self._adjust_voice_settings(
                voice_config["voice_settings"], speaking_rate, emotional_tone
            )
            
            # Prepare request payload
            payload = {
                "text": self._preprocess_text_for_history(text),
                "model_id": voice_config["model"],
                "voice_settings": adjusted_settings
            }
            
            # Make API request
            response = await self.client.post(
                f"{self.base_url}/text-to-speech/{voice_config['voice_id']}",
                headers={
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg"
                },
                json=payload
            )
            
            response.raise_for_status()
            audio_data = response.content
            
            # Calculate cost (ElevenLabs charges per character)
            character_count = len(text)
            cost_per_character = 0.0003  # Approximate cost in USD
            cost_estimate = character_count * cost_per_character
            
            generation_time = int((time.time() - start_time) * 1000)
            
            # Cache the result (if text is short enough)
            if len(text) <= 100 and not skip_cache:
                self._audio_cache[cache_key] = audio_data
                
                # Limit cache size
                if len(self._audio_cache) > 1000:
                    # Remove oldest entries
                    keys_to_remove = list(self._audio_cache.keys())[:100]
                    for key in keys_to_remove:
                        del self._audio_cache[key]
            
            # Update metrics
            self.total_requests += 1
            self.total_characters += character_count
            self.total_cost += cost_estimate
            self.total_generation_time += generation_time
            
            voice_response = VoiceResponse(
                text=text,
                audio_data=audio_data,
                voice_id=voice_config["voice_id"],
                voice_persona=voice_persona,
                duration_ms=self._estimate_audio_duration(text, speaking_rate),
                format=AudioFormat.MP3,
                provider=VoiceProvider.ELEVENLABS,
                generation_time_ms=generation_time,
                cost_estimate=cost_estimate,
                speaking_rate=speaking_rate,
                emotional_tone=emotional_tone,
                emphasis_words=self._extract_emphasis_words(text)
            )
            
            logger.debug(
                f"Generated speech: {character_count} chars, "
                f"{generation_time}ms, ${cost_estimate:.4f}"
            )
            
            return voice_response
            
        except httpx.HTTPStatusError as e:
            logger.error(f"ElevenLabs API error {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Speech generation failed: {e}")
            raise
    
    def _preprocess_text_for_history(self, text: str) -> str:
        """Preprocess text for better History education speech."""
        
        # Add pauses for better pacing in educational content
        processed_text = text
        
        # Add slight pauses after important phrases
        important_phrases = [
            "Let me explain",
            "For example",
            "Consider this",
            "On the other hand", 
            "As a result",
            "In conclusion",
            "Remember that",
            "It's important to note"
        ]
        
        for phrase in important_phrases:
            processed_text = processed_text.replace(
                phrase, f"{phrase},"  # Add comma for natural pause
            )
        
        # Add emphasis to key historical terms
        historical_terms = [
            "World War", "revolution", "democracy", "imperialism", 
            "nationalism", "primary source", "cause and effect"
        ]
        
        for term in historical_terms:
            # ElevenLabs uses SSML-style emphasis
            processed_text = processed_text.replace(
                term, f"<emphasis level='moderate'>{term}</emphasis>"
            )
        
        # Slow down for dates and numbers
        import re
        
        # Find years (4-digit numbers)
        years_pattern = r'\b(1[0-9]{3}|20[0-2][0-9])\b'
        processed_text = re.sub(
            years_pattern, 
            r"<prosody rate='slow'>\1</prosody>", 
            processed_text
        )
        
        return processed_text
    
    def _adjust_voice_settings(
        self, 
        base_settings: Dict[str, Any],
        speaking_rate: float,
        emotional_tone: str
    ) -> Dict[str, Any]:
        """Adjust voice settings based on speaking rate and emotional tone."""
        settings = base_settings.copy()
        
        # Adjust stability based on speaking rate
        if speaking_rate < 0.8:  # Slow speech
            settings["stability"] = min(0.95, settings["stability"] + 0.1)
        elif speaking_rate > 1.2:  # Fast speech
            settings["stability"] = max(0.5, settings["stability"] - 0.1)
        
        # Adjust style based on emotional tone
        tone_adjustments = {
            "encouraging": {"style": 0.3},
            "authoritative": {"style": 0.1},
            "enthusiastic": {"style": 0.4},
            "calm": {"style": 0.2},
            "serious": {"style": 0.1}
        }
        
        if emotional_tone in tone_adjustments:
            settings.update(tone_adjustments[emotional_tone])
        
        return settings
    
    def _estimate_audio_duration(self, text: str, speaking_rate: float) -> int:
        """Estimate audio duration in milliseconds."""
        # Average speaking rate: 150 words per minute at normal speed
        base_wpm = 150
        word_count = len(text.split())
        
        # Adjust for speaking rate
        adjusted_wpm = base_wpm * speaking_rate
        
        # Calculate duration in milliseconds
        duration_minutes = word_count / adjusted_wpm
        duration_ms = int(duration_minutes * 60 * 1000)
        
        return max(1000, duration_ms)  # Minimum 1 second
    
    def _extract_emphasis_words(self, text: str) -> List[str]:
        """Extract words that should be emphasized in speech."""
        emphasis_words = []
        
        # Look for words in caps or with emphasis markers
        words = text.split()
        for word in words:
            # Words in ALL CAPS (but not common words)
            if word.isupper() and len(word) > 3:
                emphasis_words.append(word.lower())
            
            # Words marked with asterisks or other emphasis
            if word.startswith('*') and word.endswith('*'):
                emphasis_words.append(word.strip('*'))
        
        return emphasis_words
    
    def _create_cache_key(
        self, 
        text: str, 
        voice_persona: VoicePersona, 
        speaking_rate: float
    ) -> str:
        """Create cache key for audio caching."""
        import hashlib
        
        key_string = f"{text}:{voice_persona.value}:{speaking_rate:.2f}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def generate_streaming_speech(
        self,
        text: str,
        voice_persona: VoicePersona = VoicePersona.SARAH_ENCOURAGING,
        chunk_size: int = 1024
    ) -> AsyncGenerator[bytes, None]:
        """Generate streaming speech for real-time playback."""
        
        voice_config = ElevenLabsVoiceConfig.VOICE_PERSONAS[voice_persona]
        
        payload = {
            "text": self._preprocess_text_for_history(text),
            "model_id": voice_config["model"],
            "voice_settings": voice_config["voice_settings"]
        }
        
        async with self.client.stream(
            "POST",
            f"{self.base_url}/text-to-speech/{voice_config['voice_id']}/stream",
            headers={
                "xi-api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg"
            },
            json=payload
        ) as response:
            response.raise_for_status()
            
            async for chunk in response.aiter_bytes(chunk_size):
                yield chunk
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get client performance metrics."""
        cache_hit_rate = (
            self._cache_hits / (self._cache_hits + self._cache_misses)
            if (self._cache_hits + self._cache_misses) > 0 else 0.0
        )
        
        avg_generation_time = (
            self.total_generation_time / self.total_requests
            if self.total_requests > 0 else 0.0
        )
        
        return {
            "provider": "elevenlabs",
            "total_requests": self.total_requests,
            "total_characters": self.total_characters,
            "total_cost": self.total_cost,
            "avg_generation_time_ms": avg_generation_time,
            "cache_hit_rate": cache_hit_rate,
            "cache_size": len(self._audio_cache)
        }
    
    async def close(self):
        """Clean up client resources."""
        await self.client.aclose()
```

### 4. `src/voice/gateway.py` - Voice WebSocket Gateway
```python
"""WebSocket gateway for real-time voice communication."""
import asyncio
import json
import logging
import time
from typing import Dict, Set, Optional, Any
import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager

import websocket
from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from starlette.websockets import WebSocketState

from src.voice.schemas import (
    VoiceSessionConfig, VoiceSessionState, ConversationState,
    AudioChunk, TranscriptionResult, VoiceResponse, WebSocketMessage
)
from src.voice.stt.stt_manager import STTManager
from src.voice.tts.elevenlabs_client import ElevenLabsTTSClient
from src.voice.conversation.state_machine import VoiceStateMachine
from src.voice.audio.vad import VoiceActivityDetector
from src.memory.manager import MemoryManager
from src.agents.orchestrator import MasterOrchestrator

logger = logging.getLogger(__name__)


class VoiceGateway:
    """WebSocket gateway managing voice conversations."""
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        orchestrator: MasterOrchestrator,
        stt_manager: STTManager,
        tts_client: ElevenLabsTTSClient
    ):
        self.memory = memory_manager
        self.orchestrator = orchestrator
        self.stt_manager = stt_manager
        self.tts_client = tts_client
        
        # Active voice sessions
        self.active_sessions: Dict[str, VoiceSessionState] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
        
        # Voice activity detection
        self.vad = VoiceActivityDetector()
        
        # Session management
        self.session_cleanup_interval = 300  # 5 minutes
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        """Initialize the voice gateway."""
        await self.stt_manager.initialize()
        await self.tts_client.initialize()
        
        # Start session cleanup task
        self._cleanup_task = asyncio.create_task(self._session_cleanup_loop())
        
        logger.info("Voice gateway initialized")
    
    async def handle_websocket_connection(
        self,
        websocket: WebSocket,
        session_id: str,
        student_id: str,
        config: VoiceSessionConfig
    ):
        """Handle a new WebSocket voice connection."""
        
        # Accept WebSocket connection
        await websocket.accept()
        
        # Create voice session
        voice_session = VoiceSessionState(
            session_id=session_id,
            current_state=ConversationState.IDLE,
            session_start_time=datetime.now(timezone.utc),
            last_activity_time=datetime.now(timezone.utc)
        )
        
        # Store session and connection
        self.active_sessions[session_id] = voice_session
        self.websocket_connections[session_id] = websocket
        
        # Create state machine for this session
        state_machine = VoiceStateMachine(
            session_config=config,
            voice_session=voice_session,
            stt_manager=self.stt_manager,
            tts_client=self.tts_client,
            orchestrator=self.orchestrator
        )
        
        try:
            # Send initial state
            await self._send_state_update(session_id, ConversationState.IDLE)
            
            # Handle WebSocket messages
            async for message_data in websocket.iter_text():
                try:
                    await self._handle_websocket_message(
                        session_id, message_data, state_machine
                    )
                except Exception as e:
                    logger.error(f"Error handling message for {session_id}: {e}")
                    await self._send_error(session_id, str(e))
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for session {session_id}")
        except Exception as e:
            logger.error(f"WebSocket error for session {session_id}: {e}")
        finally:
            # Cleanup session
            await self._cleanup_session(session_id)
    
    async def _handle_websocket_message(
        self,
        session_id: str,
        message_data: str,
        state_machine: VoiceStateMachine
    ):
        """Handle incoming WebSocket message."""
        
        try:
            message = json.loads(message_data)
            message_type = message.get("type")
            data = message.get("data", {})
            
            # Update last activity
            if session_id in self.active_sessions:
                self.active_sessions[session_id].last_activity_time = datetime.now(timezone.utc)
            
            if message_type == "audio_chunk":
                await self._handle_audio_chunk(session_id, data, state_machine)
                
            elif message_type == "start_listening":
                await self._handle_start_listening(session_id, state_machine)
                
            elif message_type == "stop_listening":
                await self._handle_stop_listening(session_id, state_machine)
                
            elif message_type == "interrupt_speech":
                await self._handle_interrupt_speech(session_id, state_machine)
                
            elif message_type == "session_config_update":
                await self._handle_config_update(session_id, data, state_machine)
                
            elif message_type == "ping":
                await self._send_message(session_id, "pong", {"timestamp": time.time()})
                
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in WebSocket message: {e}")
            await self._send_error(session_id, "Invalid JSON format")
            
    async def _handle_audio_chunk(
        self,
        session_id: str,
        data: Dict[str, Any],
        state_machine: VoiceStateMachine
    ):
        """Handle incoming audio chunk."""
        
        try:
            # Parse audio chunk
            audio_chunk = AudioChunk(
                audio_data=AudioChunk.from_base64(data["audio_data"]).audio_data,
                format=data.get("format", "wav"),
                sample_rate=data.get("sample_rate", 16000),
                channels=data.get("channels", 1),
                duration_ms=data.get("duration_ms", 0),
                sequence_number=data.get("sequence_number", 0),
                is_final=data.get("is_final", False)
            )
            
            # Check for voice activity
            has_speech = self.vad.detect_speech(audio_chunk.audio_data)
            
            if not has_speech and not audio_chunk.is_final:
                # Silent chunk - just acknowledge
                return
            
            # Process through state machine
            result = await state_machine.process_audio_chunk(audio_chunk)
            
            # Handle different results
            if isinstance(result, TranscriptionResult):
                await self._send_message(session_id, "transcription", {
                    "text": result.text,
                    "confidence": result.confidence,
                    "is_final": audio_chunk.is_final
                })
                
                # If final transcription, process through orchestrator
                if audio_chunk.is_final and result.text.strip():
                    await self._process_student_message(session_id, result.text, state_machine)
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            await self._send_error(session_id, "Audio processing failed")
    
    async def _process_student_message(
        self,
        session_id: str,
        message_text: str,
        state_machine: VoiceStateMachine
    ):
        """Process student's transcribed message through the orchestrator."""
        
        try:
            # Update state to thinking
            await self._send_state_update(session_id, ConversationState.THINKING)
            
            # Process through orchestrator (existing chat system)
            # This integrates with the workflow orchestrator from doc 02
            agent_response = await state_machine.process_text_message(message_text)
            
            # Update state to generating speech
            await self._send_state_update(session_id, ConversationState.GENERATING)
            
            # Generate voice response
            voice_response = await state_machine.generate_voice_response(agent_response.text)
            
            # Update state to speaking
            await self._send_state_update(session_id, ConversationState.SPEAKING)
            
            # Send voice response to client
            await self._send_message(session_id, "voice_response", {
                "text": voice_response.text,
                "audio_data": voice_response.to_base64(),
                "duration_ms": voice_response.duration_ms,
                "voice_persona": voice_response.voice_persona.value
            })
            
            # Update session metrics
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.turn_count += 1
                session.ai_speaking_time_ms += voice_response.duration_ms
            
            # Return to waiting state
            await self._send_state_update(session_id, ConversationState.WAITING)
            
        except Exception as e:
            logger.error(f"Error processing student message: {e}")
            await self._send_state_update(session_id, ConversationState.ERROR)
            await self._send_error(session_id, "Message processing failed")
    
    async def _handle_start_listening(
        self,
        session_id: str,
        state_machine: VoiceStateMachine
    ):
        """Handle start listening command."""
        await state_machine.start_listening()
        await self._send_state_update(session_id, ConversationState.LISTENING)
    
    async def _handle_stop_listening(
        self,
        session_id: str,
        state_machine: VoiceStateMachine
    ):
        """Handle stop listening command."""
        await state_machine.stop_listening()
        await self._send_state_update(session_id, ConversationState.PROCESSING)
    
    async def _handle_interrupt_speech(
        self,
        session_id: str,
        state_machine: VoiceStateMachine
    ):
        """Handle speech interruption."""
        await state_machine.interrupt_speech()
        await self._send_state_update(session_id, ConversationState.LISTENING)
    
    async def _send_message(
        self,
        session_id: str,
        message_type: str,
        data: Dict[str, Any]
    ):
        """Send message to WebSocket client."""
        
        if session_id not in self.websocket_connections:
            return
            
        websocket = self.websocket_connections[session_id]
        
        if websocket.application_state != WebSocketState.CONNECTED:
            return
        
        message = WebSocketMessage(
            type=message_type,
            session_id=session_id,
            data=data
        )
        
        try:
            await websocket.send_text(message.json())
        except Exception as e:
            logger.error(f"Failed to send message to {session_id}: {e}")
    
    async def _send_state_update(self, session_id: str, new_state: ConversationState):
        """Send conversation state update."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].current_state = new_state
            
        await self._send_message(session_id, "state_change", {
            "state": new_state.value,
            "timestamp": time.time()
        })
    
    async def _send_error(self, session_id: str, error_message: str):
        """Send error message to client."""
        await self._send_message(session_id, "error", {
            "message": error_message,
            "timestamp": time.time()
        })
    
    async def _cleanup_session(self, session_id: str):
        """Clean up voice session resources."""
        
        # Remove from active sessions
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            
            # Log session analytics
            await self._log_session_analytics(session)
            
            del self.active_sessions[session_id]
        
        # Remove WebSocket connection
        if session_id in self.websocket_connections:
            del self.websocket_connections[session_id]
        
        logger.info(f"Cleaned up voice session: {session_id}")
    
    async def _log_session_analytics(self, session: VoiceSessionState):
        """Log session analytics for monitoring."""
        
        session_duration = (
            datetime.now(timezone.utc) - session.session_start_time
        ).total_seconds()
        
        analytics = {
            "session_id": session.session_id,
            "total_duration_seconds": session_duration,
            "conversation_turns": session.turn_count,
            "student_speaking_time_ms": session.student_speaking_time_ms,
            "ai_speaking_time_ms": session.ai_speaking_time_ms,
            "avg_transcription_confidence": session.avg_transcription_confidence,
            "error_count": session.error_count,
            "total_cost": session.total_cost
        }
        
        logger.info(f"Voice session analytics: {json.dumps(analytics)}")
        
        # Store in database for later analysis
        if self.memory:
            await self.memory.save_learning_event(
                student_id=session.session_id,  # This would need to be passed properly
                event_type="voice_session_complete",
                data=analytics,
                outcome="completed"
            )
    
    async def _session_cleanup_loop(self):
        """Periodic cleanup of inactive sessions."""
        
        while True:
            try:
                await asyncio.sleep(self.session_cleanup_interval)
                
                current_time = datetime.now(timezone.utc)
                inactive_sessions = []
                
                for session_id, session in self.active_sessions.items():
                    inactive_duration = (current_time - session.last_activity_time).total_seconds()
                    
                    # Clean up sessions inactive for more than 30 minutes
                    if inactive_duration > 1800:
                        inactive_sessions.append(session_id)
                
                # Clean up inactive sessions
                for session_id in inactive_sessions:
                    logger.info(f"Cleaning up inactive voice session: {session_id}")
                    await self._cleanup_session(session_id)
                    
            except Exception as e:
                logger.error(f"Error in session cleanup loop: {e}")
    
    async def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get information about active voice sessions."""
        
        session_info = {}
        for session_id, session in self.active_sessions.items():
            session_info[session_id] = {
                "state": session.current_state.value,
                "duration_seconds": (
                    datetime.now(timezone.utc) - session.session_start_time
                ).total_seconds(),
                "turn_count": session.turn_count,
                "error_count": session.error_count,
                "total_cost": session.total_cost
            }
        
        return session_info
    
    async def shutdown(self):
        """Shutdown the voice gateway."""
        
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            
        # Close all active sessions
        for session_id in list(self.active_sessions.keys()):
            await self._cleanup_session(session_id)
        
        # Close TTS client
        await self.tts_client.close()
        
        logger.info("Voice gateway shutdown complete")
```

---

## API Integration

### Add to `src/api/routers/chat.py`
```python
from src.voice.gateway import VoiceGateway
from src.voice.schemas import VoiceSessionConfig, VoicePersona

# Voice endpoints
@router.websocket("/voice/{session_id}")
async def voice_chat_websocket(
    websocket: WebSocket,
    session_id: str,
    student_id: str,
    voice_persona: VoicePersona = VoicePersona.SARAH_ENCOURAGING,
    speaking_rate: float = 1.0,
    current_user: User = Depends(get_current_user),
    voice_gateway: VoiceGateway = Depends(get_voice_gateway)
):
    """WebSocket endpoint for voice conversations."""
    
    # Verify user permissions
    if str(current_user.id) != student_id and current_user.role != "teacher":
        await websocket.close(code=1000, reason="Unauthorized")
        return
    
    # Create session configuration
    config = VoiceSessionConfig(
        session_id=session_id,
        student_id=student_id,
        voice_persona=voice_persona,
        speaking_rate=speaking_rate,
        subject_context="History",
        grade_level=getattr(current_user.profile, 'grade_level', None)
    )
    
    # Handle the voice connection
    await voice_gateway.handle_websocket_connection(
        websocket=websocket,
        session_id=session_id,
        student_id=student_id,
        config=config
    )

@router.get("/voice/sessions/active")
async def get_active_voice_sessions(
    current_user: User = Depends(get_current_user),
    voice_gateway: VoiceGateway = Depends(get_voice_gateway)
):
    """Get information about active voice sessions."""
    
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return await voice_gateway.get_active_sessions()

@router.get("/voice/analytics/{session_id}")
async def get_voice_session_analytics(
    session_id: str,
    current_user: User = Depends(get_current_user),
    memory: MemoryManager = Depends(get_memory)
):
    """Get analytics for a completed voice session."""
    
    # Get voice session events
    events = await memory.get_student_history(
        student_id=str(current_user.id),
        limit=100
    )
    
    voice_events = [
        event for event in events 
        if event.get("event_type") == "voice_session_complete"
        and event.get("data", {}).get("session_id") == session_id
    ]
    
    if not voice_events:
        raise HTTPException(status_code=404, detail="Voice session not found")
    
    return voice_events[0]["data"]
```

---

## Frontend Implementation

### WebSocket Voice Client (`frontend/src/lib/voice/VoiceClient.ts`)
```typescript
interface VoiceClientConfig {
  sessionId: string;
  voicePersona?: string;
  speakingRate?: number;
  sttLanguage?: string;
}

interface AudioChunk {
  audioData: string; // base64
  format: string;
  sampleRate: number;
  channels: number;
  durationMs: number;
  sequenceNumber: number;
  isFinal: boolean;
}

export class VoiceClient {
  private ws: WebSocket | null = null;
  private mediaRecorder: MediaRecorder | null = null;
  private audioContext: AudioContext | null = null;
  private isRecording = false;
  private sequenceNumber = 0;
  
  constructor(private config: VoiceClientConfig) {}
  
  async connect(): Promise<void> {
    const wsUrl = `ws://localhost:8000/api/voice/${this.config.sessionId}?` +
      `student_id=${this.config.sessionId}&` +
      `voice_persona=${this.config.voicePersona || 'sarah_encouraging'}&` +
      `speaking_rate=${this.config.speakingRate || 1.0}`;
    
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      console.log('Voice WebSocket connected');
      this.onConnectionOpen?.();
    };
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleIncomingMessage(message);
    };
    
    this.ws.onclose = () => {
      console.log('Voice WebSocket disconnected');
      this.onConnectionClose?.();
    };
    
    this.ws.onerror = (error) => {
      console.error('Voice WebSocket error:', error);
      this.onError?.(error);
    };
  }
  
  async startRecording(): Promise<void> {
    if (!this.ws || this.isRecording) return;
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      
      this.audioContext = new AudioContext({ sampleRate: 16000 });
      this.mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.sendAudioChunk(event.data, false);
        }
      };
      
      this.mediaRecorder.start(250); // 250ms chunks
      this.isRecording = true;
      
      // Send start listening message
      this.sendMessage('start_listening', {});
      
    } catch (error) {
      console.error('Failed to start recording:', error);
      this.onError?.(error);
    }
  }
  
  async stopRecording(): Promise<void> {
    if (!this.isRecording || !this.mediaRecorder) return;
    
    this.mediaRecorder.stop();
    this.isRecording = false;
    
    // Send final chunk
    this.sendMessage('stop_listening', {});
  }
  
  private async sendAudioChunk(audioBlob: Blob, isFinal: boolean) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
    
    const arrayBuffer = await audioBlob.arrayBuffer();
    const base64Audio = btoa(
      new Uint8Array(arrayBuffer).reduce(
        (data, byte) => data + String.fromCharCode(byte), ''
      )
    );
    
    const audioChunk: AudioChunk = {
      audioData: base64Audio,
      format: 'webm',
      sampleRate: 16000,
      channels: 1,
      durationMs: 250,
      sequenceNumber: this.sequenceNumber++,
      isFinal
    };
    
    this.sendMessage('audio_chunk', audioChunk);
  }
  
  private sendMessage(type: string, data: any) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
    
    this.ws.send(JSON.stringify({
      type,
      session_id: this.config.sessionId,
      timestamp: Date.now(),
      data
    }));
  }
  
  private handleIncomingMessage(message: any) {
    switch (message.type) {
      case 'transcription':
        this.onTranscription?.(message.data);
        break;
        
      case 'voice_response':
        this.playVoiceResponse(message.data);
        break;
        
      case 'state_change':
        this.onStateChange?.(message.data.state);
        break;
        
      case 'error':
        this.onError?.(new Error(message.data.message));
        break;
        
      case 'pong':
        // Handle ping/pong for connection health
        break;
    }
  }
  
  private async playVoiceResponse(responseData: any) {
    try {
      // Decode base64 audio
      const audioData = atob(responseData.audio_data);
      const audioArray = new Uint8Array(audioData.length);
      for (let i = 0; i < audioData.length; i++) {
        audioArray[i] = audioData.charCodeAt(i);
      }
      
      // Play audio
      const audioContext = new AudioContext();
      const audioBuffer = await audioContext.decodeAudioData(audioArray.buffer);
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContext.destination);
      source.start();
      
      this.onVoiceResponse?.(responseData);
      
    } catch (error) {
      console.error('Failed to play voice response:', error);
      this.onError?.(error);
    }
  }
  
  disconnect() {
    if (this.isRecording) {
      this.stopRecording();
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
  
  // Event handlers (to be set by the React component)
  onConnectionOpen?: () => void;
  onConnectionClose?: () => void;
  onTranscription?: (transcription: any) => void;
  onVoiceResponse?: (response: any) => void;
  onStateChange?: (state: string) => void;
  onError?: (error: any) => void;
}
```

---

## Configuration and Deployment

### Environment Variables
```bash
# ElevenLabs Configuration
ELEVENLABS_API_KEY=your_api_key_here
ELEVENLABS_MODEL=eleven_multilingual_v2

# Whisper Configuration  
OPENAI_API_KEY=your_openai_api_key_here
WHISPER_MODEL=whisper-1

# Deepgram Configuration (fallback)
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# Voice System Settings
VOICE_ENABLED=true
VOICE_MAX_SESSION_DURATION_MINUTES=120
VOICE_CACHE_SIZE=1000
VOICE_CLEANUP_INTERVAL_SECONDS=300

# Cost Controls
VOICE_DAILY_COST_LIMIT=50.00
VOICE_COST_ALERT_THRESHOLD=40.00
```

### Performance Monitoring
```python
# Add to monitoring system
async def log_voice_metrics():
    """Log voice system performance metrics."""
    metrics = {
        "stt_performance": stt_manager.get_performance_metrics(),
        "tts_performance": tts_client.get_performance_metrics(),
        "active_sessions": len(voice_gateway.active_sessions),
        "total_cost_today": calculate_daily_voice_cost(),
        "cache_hit_rate": tts_client.get_cache_hit_rate()
    }
    
    logger.info(f"Voice system metrics: {json.dumps(metrics)}")
```

This comprehensive voice integration system enables natural, real-time conversations between students and the History tutor AI, with professional-quality speech generation, reliable transcription, and seamless WebSocket communication.