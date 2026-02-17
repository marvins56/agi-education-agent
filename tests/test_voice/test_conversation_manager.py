"""Tests for voice conversation manager."""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from src.voice.conversation.manager import VoiceConversationManager
from src.voice.schemas import (
    VoiceConversationSession, ConversationState, AudioChunk,
    AudioFormat, VoicePersona, TranscriptionResult, VoiceResponse
)


@pytest.fixture
async def mock_memory_manager():
    """Mock memory manager for testing."""
    memory = Mock()
    memory._redis = Mock()
    memory._redis.setex = AsyncMock()
    return memory


@pytest.fixture
async def mock_orchestrator():
    """Mock orchestrator for testing."""
    orchestrator = Mock()
    orchestrator.process_message = AsyncMock()
    
    # Mock response
    mock_response = Mock()
    mock_response.text = "That's a great question about World War I! The main causes..."
    orchestrator.process_message.return_value = mock_response
    
    return orchestrator


@pytest.fixture
async def conversation_manager(mock_memory_manager, mock_orchestrator):
    """Create conversation manager for testing."""
    manager = VoiceConversationManager(mock_memory_manager, mock_orchestrator)
    
    # Mock the voice clients
    manager.stt_client = Mock()
    manager.stt_client.__aenter__ = AsyncMock(return_value=manager.stt_client)
    manager.stt_client.__aexit__ = AsyncMock()
    manager.stt_client.transcribe_audio = AsyncMock()
    
    manager.tts_client = Mock()
    manager.tts_client.__aenter__ = AsyncMock(return_value=manager.tts_client)
    manager.tts_client.__aexit__ = AsyncMock()
    manager.tts_client.synthesize_speech = AsyncMock()
    
    await manager.initialize()
    return manager


@pytest.mark.asyncio
async def test_create_session(conversation_manager):
    """Test creating a voice conversation session."""
    
    session_id = "test_session_123"
    student_id = "student_456"
    
    session = await conversation_manager.create_session(session_id, student_id)
    
    assert session.session_id == session_id
    assert session.student_id == student_id
    assert session.state == ConversationState.IDLE
    assert session_id in conversation_manager.active_sessions
    assert session_id in conversation_manager.audio_buffers


@pytest.mark.asyncio
async def test_create_session_with_config(conversation_manager):
    """Test creating session with custom configuration."""
    
    session_id = "test_session_123"
    student_id = "student_456"
    config = {
        "preferred_voice": VoicePersona.ADAM_AUTHORITATIVE,
        "language": "es",
        "auto_interrupt": False
    }
    
    session = await conversation_manager.create_session(session_id, student_id, config)
    
    assert session.preferred_voice == VoicePersona.ADAM_AUTHORITATIVE
    assert session.language == "es"
    assert session.auto_interrupt == False


@pytest.mark.asyncio
async def test_end_session(conversation_manager):
    """Test ending a voice conversation session."""
    
    session_id = "test_session_123"
    student_id = "student_456"
    
    # Create session first
    await conversation_manager.create_session(session_id, student_id)
    assert session_id in conversation_manager.active_sessions
    
    # End session
    success = await conversation_manager.end_session(session_id)
    
    assert success
    assert session_id not in conversation_manager.active_sessions
    assert session_id not in conversation_manager.audio_buffers


@pytest.mark.asyncio
async def test_process_audio_chunk(conversation_manager):
    """Test processing audio chunk."""
    
    session_id = "test_session_123"
    student_id = "student_456"
    
    # Create session
    await conversation_manager.create_session(session_id, student_id)
    
    # Create audio chunk
    audio_chunk = AudioChunk(
        audio_data=b"mock_audio_data",
        format=AudioFormat.WAV,
        sample_rate=16000,
        channels=1,
        duration_ms=1000,
        sequence_number=1,
        is_final=False
    )
    
    # Process audio
    event = await conversation_manager.process_audio(session_id, audio_chunk)
    
    # Should change state to listening
    session = conversation_manager.active_sessions[session_id]
    assert session.state == ConversationState.LISTENING
    
    # Event might be None for non-final chunks
    assert event is None or event.session_id == session_id


@pytest.mark.asyncio
async def test_complete_audio_processing(conversation_manager):
    """Test complete audio processing flow."""
    
    session_id = "test_session_123"
    student_id = "student_456"
    
    # Create session
    await conversation_manager.create_session(session_id, student_id)
    
    # Mock STT response
    conversation_manager.stt_client.transcribe_audio.return_value = TranscriptionResult(
        text="What were the causes of World War I?",
        confidence=0.95,
        provider="whisper",
        processing_time_ms=1500,
        language="en",
        audio_duration_ms=3000,
        speech_detected=True
    )
    
    # Mock TTS response
    conversation_manager.tts_client.synthesize_speech.return_value = VoiceResponse(
        text="The main causes of World War I were...",
        voice_persona=VoicePersona.SARAH_ENCOURAGING,
        duration_ms=5000,
        format=AudioFormat.MP3,
        generation_time_ms=800
    )
    
    # Send audio chunks
    for i in range(3):
        audio_chunk = AudioChunk(
            audio_data=b"mock_audio_data_" + str(i).encode(),
            format=AudioFormat.WAV,
            sample_rate=16000,
            channels=1,
            duration_ms=1000,
            sequence_number=i,
            is_final=(i == 2)  # Last chunk is final
        )
        
        event = await conversation_manager.process_audio(session_id, audio_chunk)
        
        if audio_chunk.is_final:
            # Should get response event
            assert event is not None
            assert event.event == "response_ready"
            assert "transcription" in event.data
            assert "response" in event.data
    
    # Check session messages
    session = conversation_manager.active_sessions[session_id]
    assert len(session.messages) == 2  # User message + assistant response
    assert session.messages[0]["role"] == "user"
    assert session.messages[1]["role"] == "assistant"
    assert session.total_interactions == 1


@pytest.mark.asyncio
async def test_handle_interruption(conversation_manager):
    """Test handling conversation interruption."""
    
    session_id = "test_session_123"
    student_id = "student_456"
    
    # Create session
    session = await conversation_manager.create_session(session_id, student_id)
    
    # Set session to speaking state
    session.state = ConversationState.SPEAKING
    
    # Handle interruption
    event = await conversation_manager.handle_interruption(session_id, "user_speech")
    
    assert event.event == "interrupted"
    assert event.session_id == session_id
    assert event.data["interruption_type"] == "user_speech"
    
    # State should change to listening
    assert session.state == ConversationState.LISTENING


@pytest.mark.asyncio
async def test_session_analytics(conversation_manager):
    """Test getting session analytics."""
    
    session_id = "test_session_123"
    student_id = "student_456"
    
    # Create session
    session = await conversation_manager.create_session(session_id, student_id)
    
    # Add some mock data
    session.total_interactions = 5
    session.messages = [
        {
            "role": "user",
            "content": "Test message 1",
            "audio_duration_ms": 1500
        },
        {
            "role": "assistant", 
            "content": "Test response 1",
            "audio_duration_ms": 2500
        }
    ]
    
    # Get analytics
    analytics = await conversation_manager.get_session_analytics(session_id)
    
    assert analytics is not None
    assert analytics["session_id"] == session_id
    assert analytics["student_id"] == student_id
    assert analytics["total_interactions"] == 5
    assert analytics["audio_input_ms"] == 1500
    assert analytics["audio_output_ms"] == 2500
    assert analytics["message_count"] == 2


@pytest.mark.asyncio
async def test_nonexistent_session(conversation_manager):
    """Test operations on non-existent session."""
    
    # Try to process audio for non-existent session
    audio_chunk = AudioChunk(
        audio_data=b"test",
        duration_ms=1000,
        sequence_number=1
    )
    
    event = await conversation_manager.process_audio("nonexistent", audio_chunk)
    
    assert event.event == "error"
    assert "Session not found" in event.data["error"]
    
    # Try to end non-existent session
    success = await conversation_manager.end_session("nonexistent")
    assert not success
    
    # Try to get analytics for non-existent session
    analytics = await conversation_manager.get_session_analytics("nonexistent")
    assert analytics is None


@pytest.mark.asyncio
async def test_get_active_sessions(conversation_manager):
    """Test getting active sessions summary."""
    
    # Create multiple sessions
    session1_id = "session_1"
    session2_id = "session_2"
    
    await conversation_manager.create_session(session1_id, "student_1")
    await conversation_manager.create_session(session2_id, "student_2")
    
    # Get active sessions
    active = conversation_manager.get_active_sessions()
    
    assert len(active) == 2
    assert session1_id in active
    assert session2_id in active
    assert active[session1_id]["student_id"] == "student_1"
    assert active[session2_id]["student_id"] == "student_2"


@pytest.mark.asyncio
async def test_error_handling_in_audio_processing(conversation_manager):
    """Test error handling during audio processing."""
    
    session_id = "test_session_123"
    student_id = "student_456"
    
    # Create session
    await conversation_manager.create_session(session_id, student_id)
    
    # Mock STT to raise exception
    conversation_manager.stt_client.transcribe_audio.side_effect = Exception("STT failed")
    
    # Send final audio chunk
    audio_chunk = AudioChunk(
        audio_data=b"mock_audio_data",
        duration_ms=1000,
        sequence_number=1,
        is_final=True
    )
    
    event = await conversation_manager.process_audio(session_id, audio_chunk)
    
    # Should get error event
    assert event.event == "error"
    assert "STT failed" in event.data["error"]
    
    # Session state should be error
    session = conversation_manager.active_sessions[session_id]
    assert session.state == ConversationState.ERROR


@pytest.mark.asyncio
async def test_no_speech_detected(conversation_manager):
    """Test handling when no speech is detected."""
    
    session_id = "test_session_123"
    student_id = "student_456"
    
    # Create session
    await conversation_manager.create_session(session_id, student_id)
    
    # Mock STT to return empty transcription
    conversation_manager.stt_client.transcribe_audio.return_value = TranscriptionResult(
        text="",  # Empty transcription
        confidence=0.0,
        provider="whisper",
        processing_time_ms=500,
        language="en",
        speech_detected=False
    )
    
    # Send final audio chunk
    audio_chunk = AudioChunk(
        audio_data=b"silence",
        duration_ms=1000,
        sequence_number=1,
        is_final=True
    )
    
    event = await conversation_manager.process_audio(session_id, audio_chunk)
    
    assert event.event == "no_speech"
    assert event.data["message"] == "No speech detected"
    
    # Session should return to idle state
    session = conversation_manager.active_sessions[session_id]
    assert session.state == ConversationState.IDLE