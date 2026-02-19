"""
Real-time voice handler for bidirectional audio communication.
Handles WebSocket audio streams with barge-in detection and streaming LLM→TTS pipeline.
Works with both FastAPI WebSocket and standalone websockets library.
"""

import asyncio
import json
import logging
import struct
import time
from typing import Optional, Dict, Any, Callable, Union

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
        if len(self.buffer) > self.max_buffer_bytes:
            excess = len(self.buffer) - self.max_buffer_bytes
            self.buffer = self.buffer[excess:]

    def read_chunk(self) -> Optional[bytes]:
        """Read one 20ms chunk if available."""
        if len(self.buffer) >= self.chunk_size_bytes:
            chunk = bytes(self.buffer[: self.chunk_size_bytes])
            self.buffer = self.buffer[self.chunk_size_bytes :]
            return chunk
        return None

    def read_all(self) -> bytes:
        """Read and drain the entire buffer."""
        data = bytes(self.buffer)
        self.buffer.clear()
        return data

    def clear(self) -> None:
        self.buffer.clear()

    def get_duration_ms(self) -> int:
        samples = len(self.buffer) // 2
        return (samples * 1000) // self.sample_rate

    @property
    def size(self) -> int:
        return len(self.buffer)


class VoiceSession:
    """Voice session state management."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = time.time()
        self.last_activity = time.time()
        self.state = "idle"  # idle, listening, speaking, processing
        self.context = ""
        self.interruption_count = 0
        self.speaking_start_time: Optional[float] = None
        self.is_streaming_tts = False

    def update_activity(self) -> None:
        self.last_activity = time.time()

    def set_state(self, state: str) -> None:
        logger.info(f"Session {self.session_id}: {self.state} -> {state}")
        self.state = state
        self.update_activity()
        if state == "speaking":
            self.speaking_start_time = time.time()
            self.is_streaming_tts = True
        elif state != "speaking":
            self.is_streaming_tts = False

    def add_context(self, text: str, role: str = "user") -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.context += f"[{timestamp}] {role}: {text}\n"
        lines = self.context.split("\n")
        if len(lines) > 50:
            self.context = "\n".join(lines[-50:])


class RealtimeVoiceHandler:
    """
    Main handler for real-time voice communication.

    Works with FastAPI WebSocket objects.  The handler stores a reference to
    each active WebSocket so that TTS audio and control messages can be pushed
    back to the client.
    """

    # Minimum accumulated audio (in bytes) before we attempt STT.
    # 16 kHz × 2 bytes × 1.0 s = 32 000 bytes  (~1 second of speech).
    MIN_STT_BYTES = 32_000

    # Silence timeout: if no audio arrives for this many seconds while
    # listening we treat it as end-of-utterance.
    SILENCE_TIMEOUT_S = 1.5

    def __init__(
        self,
        llm_callback: Callable,
        tts_callback: Callable,
        stt_callback: Optional[Callable] = None,
    ):
        """
        Args:
            llm_callback: ``async def(text) -> AsyncGenerator[str, None]``
            tts_callback: ``async def(text) -> bytes``
            stt_callback: ``async def(audio_bytes) -> str``  (optional)
        """
        self.llm_callback = llm_callback
        self.tts_callback = tts_callback
        self.stt_callback = stt_callback

        self.sessions: Dict[str, VoiceSession] = {}
        self.audio_buffers: Dict[str, AudioBuffer] = {}
        self.interruption_detectors: Dict[str, InterruptionDetector] = {}
        self.active_streams: Dict[str, asyncio.Task] = {}

        # WebSocket references keyed by session_id
        self._websockets: Dict[str, Any] = {}

        # Accumulation buffers for STT (raw PCM bytes per session)
        self._stt_accum: Dict[str, bytearray] = {}

        # Silence-detection tasks
        self._silence_tasks: Dict[str, asyncio.Task] = {}

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def handle_connection(self, websocket: Any, session_id: str) -> None:
        """Handle a new WebSocket connection (FastAPI or plain websockets)."""
        logger.info(f"New voice connection: {session_id}")

        session = VoiceSession(session_id)
        self.sessions[session_id] = session
        self.audio_buffers[session_id] = AudioBuffer()
        self.interruption_detectors[session_id] = InterruptionDetector()
        self._websockets[session_id] = websocket
        self._stt_accum[session_id] = bytearray()

        try:
            await self._handle_session(websocket, session)
        except Exception as e:
            # Catch both FastAPI WebSocketDisconnect and websockets ConnectionClosed
            exc_name = type(e).__name__
            if exc_name in ("WebSocketDisconnect", "ConnectionClosed", "ConnectionClosedOK"):
                logger.info(f"Voice connection closed: {session_id}")
            else:
                logger.error(f"Voice session error: {e}", exc_info=True)
        finally:
            await self._cleanup_session(session_id)

    async def _handle_session(self, websocket: Any, session: VoiceSession) -> None:
        """Message loop – handles both binary audio and JSON control messages."""
        session_id = session.session_id

        while True:
            message = await self._recv(websocket)
            if message is None:
                break  # connection closed

            try:
                if isinstance(message, bytes):
                    await self._handle_audio_data(session_id, message)
                else:
                    data = json.loads(message)
                    await self._handle_control_message(session_id, data)
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                await self._send_json(session_id, {"type": "error", "error": str(e)})

    # ------------------------------------------------------------------
    # Audio handling
    # ------------------------------------------------------------------

    async def _handle_audio_data(self, session_id: str, audio_data: bytes) -> None:
        session = self.sessions[session_id]
        buffer = self.audio_buffers[session_id]
        detector = self.interruption_detectors[session_id]

        session.update_activity()
        buffer.write(audio_data)

        # Barge-in detection while TTS is playing
        if session.is_streaming_tts:
            if detector.detect_speech_onset(audio_data):
                logger.info(f"Barge-in detected for session {session_id}")
                await self._handle_interruption(session_id)
                return

        # Accumulate audio for STT while listening
        if session.state == "listening":
            self._stt_accum.setdefault(session_id, bytearray())
            self._stt_accum[session_id].extend(audio_data)

            # Reset silence timer
            self._reset_silence_timer(session_id)

    def _reset_silence_timer(self, session_id: str) -> None:
        """(Re)start a timer that fires STT after a period of silence."""
        if session_id in self._silence_tasks:
            self._silence_tasks[session_id].cancel()

        self._silence_tasks[session_id] = asyncio.create_task(
            self._silence_timeout(session_id)
        )

    async def _silence_timeout(self, session_id: str) -> None:
        """Called after SILENCE_TIMEOUT_S of no new audio while listening."""
        try:
            await asyncio.sleep(self.SILENCE_TIMEOUT_S)
        except asyncio.CancelledError:
            return

        session = self.sessions.get(session_id)
        if not session or session.state != "listening":
            return

        accum = self._stt_accum.get(session_id, bytearray())
        if len(accum) >= self.MIN_STT_BYTES:
            await self._run_stt_and_respond(session_id)

    async def _run_stt_and_respond(self, session_id: str) -> None:
        """Run STT on accumulated audio, then LLM → TTS pipeline."""
        session = self.sessions.get(session_id)
        if not session:
            return

        accum = bytes(self._stt_accum.get(session_id, b""))
        self._stt_accum[session_id] = bytearray()

        if len(accum) < self.MIN_STT_BYTES:
            return

        session.set_state("processing")

        # --- STT ---
        text = ""
        if self.stt_callback:
            try:
                text = await self.stt_callback(accum)
            except Exception as e:
                logger.error(f"STT error: {e}")
        else:
            logger.warning("No STT callback configured; skipping transcription")

        if not text or not text.strip():
            await self._send_json(session_id, {"type": "no_speech"})
            session.set_state("listening")
            return

        # Notify client of transcription
        await self._send_json(
            session_id,
            {"type": "transcription", "text": text},
        )
        session.add_context(text, "user")

        # --- LLM → TTS ---
        await self._process_text_input(session_id, text)

    # ------------------------------------------------------------------
    # Control messages
    # ------------------------------------------------------------------

    async def _handle_control_message(
        self, session_id: str, data: Dict[str, Any]
    ) -> None:
        session = self.sessions[session_id]
        msg_type = data.get("type")

        if msg_type == "start_listening":
            session.set_state("listening")
            self._stt_accum[session_id] = bytearray()
            await self._send_json(session_id, {"type": "listening_started"})

        elif msg_type == "stop_listening":
            # Trigger STT on whatever we have
            if len(self._stt_accum.get(session_id, b"")) >= self.MIN_STT_BYTES:
                await self._run_stt_and_respond(session_id)
            else:
                session.set_state("idle")
                await self._send_json(session_id, {"type": "listening_stopped"})

        elif msg_type == "text_input":
            text = data.get("text", "")
            if text.strip():
                session.add_context(text, "user")
                asyncio.create_task(self._process_text_input(session_id, text))

        elif msg_type == "set_interruption_sensitivity":
            sensitivity = data.get("sensitivity", "medium")
            self.interruption_detectors[session_id].set_sensitivity(sensitivity)
            await self._send_json(
                session_id,
                {"type": "config_updated", "sensitivity": sensitivity},
            )

        elif msg_type == "ping":
            await self._send_json(session_id, {"type": "pong"})

        else:
            logger.warning(f"Unknown message type: {msg_type}")

    # ------------------------------------------------------------------
    # LLM → TTS pipeline
    # ------------------------------------------------------------------

    async def _process_text_input(self, session_id: str, text: str) -> None:
        """Stream LLM response, accumulate sentences, TTS each sentence."""
        session = self.sessions.get(session_id)
        if not session:
            return

        try:
            session.set_state("processing")

            response_text = ""
            async for chunk in self.llm_callback(text):
                response_text += chunk

                # Stream a sentence as soon as we have one
                if len(response_text) > 60 and response_text.rstrip()[-1:] in ".!?":
                    await self._stream_tts_response(session_id, response_text.strip())
                    session.add_context(response_text.strip(), "assistant")
                    response_text = ""

                # Check for interruption
                if not session.is_streaming_tts and session.state == "listening":
                    break  # user interrupted

            # Final remainder
            if response_text.strip():
                await self._stream_tts_response(session_id, response_text.strip())
                session.add_context(response_text.strip(), "assistant")

            session.set_state("idle")

        except Exception as e:
            logger.error(f"Error processing text input: {e}")
            session.set_state("idle")

    async def _stream_tts_response(self, session_id: str, text: str) -> None:
        """Convert text to speech and stream audio chunks to client."""
        session = self.sessions.get(session_id)
        if not session:
            return

        try:
            session.set_state("speaking")

            audio_data = await self.tts_callback(text)

            await self._send_json(session_id, {"type": "tts_start", "text": text})

            chunk_size = 1024
            for i in range(0, len(audio_data), chunk_size):
                if not session.is_streaming_tts:
                    break
                chunk = audio_data[i : i + chunk_size]
                await self._send_bytes(session_id, chunk)
                await asyncio.sleep(0.02)

            await self._send_json(session_id, {"type": "tts_end"})

        except Exception as e:
            logger.error(f"Error streaming TTS: {e}")
        finally:
            if session.state == "speaking":
                session.set_state("idle")

    # ------------------------------------------------------------------
    # Interruption / barge-in
    # ------------------------------------------------------------------

    async def _handle_interruption(self, session_id: str) -> None:
        session = self.sessions[session_id]
        detector = self.interruption_detectors[session_id]

        session.is_streaming_tts = False
        session.interruption_count += 1

        interruption_context = detector.get_interruption_context()
        session.context += f"[INTERRUPTED: {interruption_context}]\n"

        session.set_state("listening")
        self._stt_accum[session_id] = bytearray()

        await self._send_json(
            session_id,
            {"type": "interrupted", "context": interruption_context},
        )

    # ------------------------------------------------------------------
    # WebSocket I/O helpers (FastAPI + plain websockets compatible)
    # ------------------------------------------------------------------

    def _get_websocket(self, session_id: str) -> Optional[Any]:
        return self._websockets.get(session_id)

    async def _recv(self, websocket: Any) -> Optional[Union[str, bytes]]:
        """Receive a message from the WebSocket (FastAPI or websockets)."""
        try:
            # FastAPI WebSocket
            if hasattr(websocket, "receive"):
                msg = await websocket.receive()
                if msg.get("type") == "websocket.disconnect":
                    return None
                if "bytes" in msg and msg["bytes"]:
                    return msg["bytes"]
                if "text" in msg and msg["text"]:
                    return msg["text"]
                return None
            else:
                # plain websockets library
                return await websocket.recv()
        except Exception:
            return None

    async def _send_json(self, session_id: str, data: Dict[str, Any]) -> None:
        ws = self._websockets.get(session_id)
        if not ws:
            return
        try:
            text = json.dumps(data)
            if hasattr(ws, "send_text"):
                await ws.send_text(text)
            else:
                await ws.send(text)
        except Exception as e:
            logger.error(f"Error sending JSON to {session_id}: {e}")

    async def _send_bytes(self, session_id: str, data: bytes) -> None:
        ws = self._websockets.get(session_id)
        if not ws:
            return
        try:
            if hasattr(ws, "send_bytes"):
                await ws.send_bytes(data)
            else:
                await ws.send(data)
        except Exception as e:
            logger.error(f"Error sending bytes to {session_id}: {e}")

    # ------------------------------------------------------------------
    # Cleanup & stats
    # ------------------------------------------------------------------

    async def _cleanup_session(self, session_id: str) -> None:
        if session_id in self._silence_tasks:
            self._silence_tasks[session_id].cancel()
            del self._silence_tasks[session_id]

        if session_id in self.active_streams:
            self.active_streams[session_id].cancel()
            del self.active_streams[session_id]

        self.sessions.pop(session_id, None)
        self.audio_buffers.pop(session_id, None)
        self.interruption_detectors.pop(session_id, None)
        self._websockets.pop(session_id, None)
        self._stt_accum.pop(session_id, None)

        logger.info(f"Cleaned up session: {session_id}")

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session:
            return {}
        return {
            "session_id": session_id,
            "state": session.state,
            "duration": time.time() - session.created_at,
            "interruptions": session.interruption_count,
            "last_activity": session.last_activity,
            "context_lines": len(session.context.split("\n")),
        }
