"""
Real-time voice handler for bidirectional audio communication.
Handles WebSocket audio streams with barge-in detection and streaming LLM→TTS pipeline.
"""

import asyncio
import json
import logging
import struct
import time
from typing import Optional, Dict, Any, Callable
import websockets
from websockets.server import WebSocketServerProtocol

from .interruption import InterruptionDetector

logger = logging.getLogger(__name__)


class AudioBuffer:
    """Circular buffer for 16kHz mono PCM audio in 20ms chunks."""
    
    def __init__(self, chunk_size_ms: int = 20, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.chunk_size_ms = chunk_size_ms
        self.chunk_size_samples = (sample_rate * chunk_size_ms) // 1000
        self.chunk_size_bytes = self.chunk_size_samples * 2  # 16-bit PCM
        
        self.buffer = bytearray()
        self.max_buffer_ms = 5000  # 5 second max buffer
        self.max_buffer_bytes = (sample_rate * self.max_buffer_ms * 2) // 1000
        
    def write(self, audio_data: bytes) -> None:
        """Add audio data to buffer."""
        self.buffer.extend(audio_data)
        
        # Trim buffer if too large
        if len(self.buffer) > self.max_buffer_bytes:
            excess = len(self.buffer) - self.max_buffer_bytes
            self.buffer = self.buffer[excess:]
    
    def read_chunk(self) -> Optional[bytes]:
        """Read one 20ms chunk if available."""
        if len(self.buffer) >= self.chunk_size_bytes:
            chunk = bytes(self.buffer[:self.chunk_size_bytes])
            self.buffer = self.buffer[self.chunk_size_bytes:]
            return chunk
        return None
    
    def clear(self) -> None:
        """Clear the buffer."""
        self.buffer.clear()
    
    def get_duration_ms(self) -> int:
        """Get current buffer duration in milliseconds."""
        samples = len(self.buffer) // 2
        return (samples * 1000) // self.sample_rate


class VoiceSession:
    """Voice session state management."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = time.time()
        self.last_activity = time.time()
        self.state = "idle"  # idle, listening, speaking, processing
        self.context = ""  # Current conversation context
        self.interruption_count = 0
        self.speaking_start_time: Optional[float] = None
        self.is_streaming_tts = False
        
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = time.time()
    
    def set_state(self, state: str) -> None:
        """Set session state and update activity."""
        logger.info(f"Session {self.session_id}: {self.state} -> {state}")
        self.state = state
        self.update_activity()
        
        if state == "speaking":
            self.speaking_start_time = time.time()
            self.is_streaming_tts = True
        elif state != "speaking":
            self.is_streaming_tts = False
    
    def add_context(self, text: str, role: str = "user") -> None:
        """Add to conversation context."""
        timestamp = time.strftime("%H:%M:%S")
        self.context += f"[{timestamp}] {role}: {text}\n"
        # Keep last 50 lines
        lines = self.context.split('\n')
        if len(lines) > 50:
            self.context = '\n'.join(lines[-50:])


class RealtimeVoiceHandler:
    """Main handler for real-time voice communication."""
    
    def __init__(self, llm_callback: Callable, tts_callback: Callable):
        self.llm_callback = llm_callback  # async fn(text) -> async generator[str]
        self.tts_callback = tts_callback  # async fn(text) -> bytes (audio)
        
        self.sessions: Dict[str, VoiceSession] = {}
        self.audio_buffers: Dict[str, AudioBuffer] = {}
        self.interruption_detectors: Dict[str, InterruptionDetector] = {}
        self.active_streams: Dict[str, asyncio.Task] = {}
        
    async def handle_connection(self, websocket: WebSocketServerProtocol, session_id: str) -> None:
        """Handle a new WebSocket connection."""
        logger.info(f"New voice connection: {session_id}")
        
        # Initialize session
        session = VoiceSession(session_id)
        self.sessions[session_id] = session
        self.audio_buffers[session_id] = AudioBuffer()
        self.interruption_detectors[session_id] = InterruptionDetector()
        
        try:
            await self._handle_session(websocket, session)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Voice connection closed: {session_id}")
        except Exception as e:
            logger.error(f"Voice session error: {e}", exc_info=True)
        finally:
            await self._cleanup_session(session_id)
    
    async def _handle_session(self, websocket: WebSocketServerProtocol, session: VoiceSession) -> None:
        """Handle messages for a voice session."""
        session_id = session.session_id
        
        async for message in websocket:
            try:
                if isinstance(message, bytes):
                    await self._handle_audio_data(session_id, message)
                else:
                    data = json.loads(message)
                    await self._handle_control_message(websocket, session_id, data)
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": str(e)
                }))
    
    async def _handle_audio_data(self, session_id: str, audio_data: bytes) -> None:
        """Handle incoming audio data."""
        session = self.sessions[session_id]
        buffer = self.audio_buffers[session_id]
        detector = self.interruption_detectors[session_id]
        
        session.update_activity()
        buffer.write(audio_data)
        
        # Check for interruption during TTS output
        if session.is_streaming_tts:
            if detector.detect_speech_onset(audio_data):
                logger.info(f"Barge-in detected for session {session_id}")
                await self._handle_interruption(session_id)
        
        # Process audio chunks for speech recognition
        while chunk := buffer.read_chunk():
            if session.state == "listening":
                asyncio.create_task(self._process_audio_chunk(session_id, chunk))
    
    async def _handle_control_message(self, websocket: WebSocketServerProtocol, 
                                    session_id: str, data: Dict[str, Any]) -> None:
        """Handle control messages."""
        session = self.sessions[session_id]
        msg_type = data.get("type")
        
        if msg_type == "start_listening":
            session.set_state("listening")
            await websocket.send(json.dumps({"type": "listening_started"}))
            
        elif msg_type == "stop_listening":
            session.set_state("idle")
            await websocket.send(json.dumps({"type": "listening_stopped"}))
            
        elif msg_type == "text_input":
            text = data.get("text", "")
            session.add_context(text, "user")
            asyncio.create_task(self._process_text_input(session_id, text))
            
        elif msg_type == "set_interruption_sensitivity":
            sensitivity = data.get("sensitivity", "medium")
            detector = self.interruption_detectors[session_id]
            detector.set_sensitivity(sensitivity)
            
        else:
            logger.warning(f"Unknown message type: {msg_type}")
    
    async def _process_audio_chunk(self, session_id: str, audio_chunk: bytes) -> None:
        """Process audio chunk for speech recognition."""
        # Placeholder for speech-to-text processing
        # In a real implementation, this would call your STT service
        logger.debug(f"Processing audio chunk for {session_id}: {len(audio_chunk)} bytes")
    
    async def _process_text_input(self, session_id: str, text: str) -> None:
        """Process text input through LLM and generate TTS response."""
        session = self.sessions[session_id]
        
        try:
            session.set_state("processing")
            
            # Get streaming LLM response
            response_text = ""
            async for chunk in self.llm_callback(text):
                response_text += chunk
                
                # Stream partial responses for longer texts
                if len(response_text) > 100 and response_text.endswith(('.', '!', '?')):
                    await self._stream_tts_response(session_id, response_text)
                    response_text = ""
            
            # Send final chunk if any
            if response_text.strip():
                await self._stream_tts_response(session_id, response_text)
            
            session.add_context(text, "assistant")
            session.set_state("idle")
            
        except Exception as e:
            logger.error(f"Error processing text input: {e}")
            session.set_state("idle")
    
    async def _stream_tts_response(self, session_id: str, text: str) -> None:
        """Convert text to speech and stream to client."""
        session = self.sessions[session_id]
        
        try:
            session.set_state("speaking")
            
            # Generate TTS audio
            audio_data = await self.tts_callback(text)
            
            # Send audio in chunks
            websocket = self._get_websocket(session_id)
            if websocket:
                await websocket.send(json.dumps({
                    "type": "tts_start",
                    "text": text
                }))
                
                # Send audio in 1KB chunks
                chunk_size = 1024
                for i in range(0, len(audio_data), chunk_size):
                    if not session.is_streaming_tts:  # Check for interruption
                        break
                    chunk = audio_data[i:i + chunk_size]
                    await websocket.send(chunk)
                    await asyncio.sleep(0.02)  # 20ms delay between chunks
                
                await websocket.send(json.dumps({"type": "tts_end"}))
            
        except Exception as e:
            logger.error(f"Error streaming TTS: {e}")
        finally:
            if session.state == "speaking":
                session.set_state("idle")
    
    async def _handle_interruption(self, session_id: str) -> None:
        """Handle user interruption during TTS output."""
        session = self.sessions[session_id]
        detector = self.interruption_detectors[session_id]
        
        # Stop current TTS streaming
        session.is_streaming_tts = False
        session.interruption_count += 1
        
        # Preserve context at interruption point
        interruption_context = detector.get_interruption_context()
        session.context += f"[INTERRUPTED: {interruption_context}]\n"
        
        # Switch to listening mode
        session.set_state("listening")
        
        # Notify client
        websocket = self._get_websocket(session_id)
        if websocket:
            await websocket.send(json.dumps({
                "type": "interrupted",
                "context": interruption_context
            }))
    
    def _get_websocket(self, session_id: str) -> Optional[WebSocketServerProtocol]:
        """Get WebSocket connection for session (placeholder)."""
        # In a real implementation, you'd store WebSocket connections
        return None
    
    async def _cleanup_session(self, session_id: str) -> None:
        """Clean up session resources."""
        # Cancel any active streams
        if session_id in self.active_streams:
            self.active_streams[session_id].cancel()
            del self.active_streams[session_id]
        
        # Remove session data
        self.sessions.pop(session_id, None)
        self.audio_buffers.pop(session_id, None)
        self.interruption_detectors.pop(session_id, None)
        
        logger.info(f"Cleaned up session: {session_id}")
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get session statistics."""
        session = self.sessions.get(session_id)
        if not session:
            return {}
        
        return {
            "session_id": session_id,
            "state": session.state,
            "duration": time.time() - session.created_at,
            "interruptions": session.interruption_count,
            "last_activity": session.last_activity,
            "context_lines": len(session.context.split('\n'))
        }