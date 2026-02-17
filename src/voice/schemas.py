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
    voice_persona: VoicePersona = VoicePersona.SARAH_ENCOURAGING
    provider: VoiceProvider = VoiceProvider.ELEVENLABS
    
    # Audio properties
    duration_ms: int = 0
    format: AudioFormat = AudioFormat.MP3
    sample_rate: int = 44100
    
    # Generation metrics
    generation_time_ms: int = 0
    character_count: int = 0
    
    def to_base64_audio(self) -> Optional[str]:
        """Convert audio data to base64."""
        if self.audio_data:
            return base64.b64encode(self.audio_data).decode('utf-8')
        return None


class VoiceConversationSession(BaseModel):
    """Voice conversation session state."""
    session_id: str
    student_id: str
    state: ConversationState = ConversationState.IDLE
    
    # Session configuration
    preferred_voice: VoicePersona = VoicePersona.SARAH_ENCOURAGING
    language: str = "en"
    auto_interrupt: bool = True
    
    # Conversation history
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Audio settings
    input_format: AudioFormat = AudioFormat.WAV
    output_format: AudioFormat = AudioFormat.MP3
    
    # Session metadata
    started_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    total_duration_ms: int = 0
    
    # Performance metrics
    avg_response_time_ms: int = 0
    total_interactions: int = 0
    transcription_accuracy: float = 0.0


class VoiceCommand(BaseModel):
    """Voice command from WebSocket client."""
    command: str  # start_listening, stop_listening, send_audio, etc.
    session_id: str
    data: Optional[Dict[str, Any]] = None
    audio_chunk: Optional[str] = None  # base64 encoded audio


class VoiceEvent(BaseModel):
    """Voice event to WebSocket client."""
    event: str  # state_change, transcription_ready, audio_ready, error
    session_id: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class STTConfig(BaseModel):
    """Speech-to-text configuration."""
    provider: STTProvider = STTProvider.WHISPER
    language: str = "en"
    model: str = "whisper-1"  # for OpenAI Whisper
    
    # Whisper specific
    temperature: float = 0.0
    prompt: Optional[str] = None
    
    # Deepgram specific
    smart_format: bool = True
    punctuate: bool = True
    diarize: bool = False
    
    # Audio processing
    vad_enabled: bool = True  # Voice Activity Detection
    noise_reduction: bool = True
    auto_gain_control: bool = True


class TTSConfig(BaseModel):
    """Text-to-speech configuration."""
    provider: VoiceProvider = VoiceProvider.ELEVENLABS
    voice_persona: VoicePersona = VoicePersona.SARAH_ENCOURAGING
    
    # ElevenLabs specific
    voice_id: Optional[str] = None
    model_id: str = "eleven_multilingual_v2"
    stability: float = 0.5
    similarity_boost: float = 0.75
    style: float = 0.0
    use_speaker_boost: bool = True
    
    # OpenAI specific
    model: str = "tts-1"
    voice: str = "alloy"  # alloy, echo, fable, onyx, nova, shimmer
    
    # Output settings
    format: AudioFormat = AudioFormat.MP3
    sample_rate: int = 44100
    optimize_streaming_latency: int = 0


class VoiceAnalytics(BaseModel):
    """Voice interaction analytics."""
    session_id: str
    student_id: str
    
    # Usage metrics
    total_audio_duration_ms: int = 0
    total_text_characters: int = 0
    interaction_count: int = 0
    
    # Quality metrics
    avg_transcription_confidence: float = 0.0
    avg_response_time_ms: int = 0
    error_rate: float = 0.0
    
    # Cost tracking
    stt_api_calls: int = 0
    tts_api_calls: int = 0
    estimated_cost_usd: float = 0.0
    
    # Performance
    avg_stt_latency_ms: int = 0
    avg_tts_latency_ms: int = 0
    
    # Engagement
    interruption_count: int = 0
    clarification_requests: int = 0
    session_completion_rate: float = 0.0
    
    # Calculated at session end
    calculated_at: datetime = Field(default_factory=datetime.now)


class VoiceError(BaseModel):
    """Voice system error."""
    error_type: str  # transcription_failed, tts_failed, connection_lost, etc.
    message: str
    session_id: str
    provider: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    retry_count: int = 0


class InterruptionEvent(BaseModel):
    """Voice interruption event."""
    session_id: str
    interrupted_at: datetime
    interruption_type: str  # user_speech, manual_stop, timeout
    context: Optional[Dict[str, Any]] = None
    
    # State when interrupted
    current_state: ConversationState
    partial_transcription: Optional[str] = None
    response_progress: Optional[float] = None  # 0.0-1.0


class VoiceCapabilities(BaseModel):
    """System voice capabilities."""
    stt_providers: List[STTProvider] = Field(default_factory=lambda: [STTProvider.WHISPER])
    tts_providers: List[VoiceProvider] = Field(default_factory=lambda: [VoiceProvider.ELEVENLABS])
    available_voices: List[VoicePersona] = Field(default_factory=lambda: list(VoicePersona))
    supported_languages: List[str] = Field(default_factory=lambda: ["en", "es", "fr", "de"])
    max_audio_duration_ms: int = 300000  # 5 minutes
    streaming_supported: bool = True
    real_time_processing: bool = True