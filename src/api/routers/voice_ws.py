"""
WebSocket router for real-time voice communication.
Provides /ws/voice/{session_id} endpoint with JWT authentication.
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query

from src.voice.realtime import RealtimeVoiceHandler

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Global voice handler (lazy-initialised)
# ---------------------------------------------------------------------------

_voice_handler: Optional[RealtimeVoiceHandler] = None


async def get_voice_handler() -> RealtimeVoiceHandler:
    """Get or create the global RealtimeVoiceHandler."""
    global _voice_handler

    if _voice_handler is not None:
        return _voice_handler

    # ----- LLM callback (streaming) -----
    async def llm_callback(text: str):
        """Simple LLM callback – delegates to whatever LLM is configured."""
        try:
            from src.llm.router import get_llm_response_stream

            async for chunk in get_llm_response_stream(text):
                yield chunk
        except ImportError:
            # Fallback: echo the question back as a mock response
            logger.warning("LLM service not available, using echo fallback")
            yield f"I heard you say: {text}. (LLM not configured)"

    # ----- TTS callback -----
    async def tts_callback(text: str) -> bytes:
        """Generate TTS audio bytes."""
        try:
            from src.voice.tts_engine import PiperTTSEngine

            engine = PiperTTSEngine()
            await engine.initialize()
            response = await engine.synthesize_speech(text)
            return response.audio_data or b""
        except Exception as e:
            logger.warning(f"TTS synthesis failed, returning silence: {e}")
            # Return 0.5s of silence (16kHz 16-bit mono)
            import struct
            return b"\x00\x00" * 8000

    # ----- STT callback -----
    async def stt_callback(audio_bytes: bytes) -> str:
        """Transcribe audio bytes to text."""
        try:
            from src.voice.stt_engine import LocalWhisperSTTEngine
            from src.voice.schemas import AudioChunk

            engine = LocalWhisperSTTEngine(model_name="tiny", device="cpu")
            await engine.initialize()

            chunk = AudioChunk(
                audio_data=audio_bytes,
                duration_ms=len(audio_bytes) // 32,  # rough: 16kHz×2bytes
                sequence_number=0,
                is_final=True,
            )
            result = await engine.transcribe_audio(chunk)
            return result.text
        except Exception as e:
            logger.warning(f"STT transcription failed: {e}")
            return ""

    _voice_handler = RealtimeVoiceHandler(
        llm_callback=llm_callback,
        tts_callback=tts_callback,
        stt_callback=stt_callback,
    )
    return _voice_handler


# ---------------------------------------------------------------------------
# JWT helpers (lightweight – no external config dependency)
# ---------------------------------------------------------------------------

_JWT_SECRET = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY", "dev-secret-key"))
_JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


def _verify_jwt(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token. Returns payload dict."""
    try:
        import jwt as pyjwt

        payload = pyjwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


async def _authenticate_ws(
    websocket: WebSocket, token: Optional[str]
) -> Dict[str, Any]:
    """Authenticate a WebSocket connection. Returns user info or closes."""
    if not token:
        # Allow unauthenticated connections in dev mode
        if os.getenv("EDUAGI_ENV", "development") == "development":
            return {"user_id": "dev-user", "username": "developer"}
        await websocket.close(code=4001, reason="Missing authentication token")
        raise WebSocketDisconnect(code=4001)

    try:
        payload = _verify_jwt(token)
        return {
            "user_id": payload.get("user_id", payload.get("sub", "unknown")),
            "username": payload.get("username", ""),
        }
    except HTTPException as exc:
        await websocket.close(code=4001, reason=exc.detail)
        raise WebSocketDisconnect(code=4001)


# ---------------------------------------------------------------------------
# Session manager
# ---------------------------------------------------------------------------


class _SessionManager:
    """Lightweight tracker for active voice WS sessions."""

    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def add(self, session_id: str, ws: WebSocket, user_info: Dict[str, Any]):
        self.sessions[session_id] = {
            "websocket": ws,
            "user_info": user_info,
            "connected_at": asyncio.get_event_loop().time(),
        }

    def remove(self, session_id: str):
        self.sessions.pop(session_id, None)

    def get_ws(self, session_id: str) -> Optional[WebSocket]:
        entry = self.sessions.get(session_id)
        return entry["websocket"] if entry else None

    def get_all(self) -> Dict[str, Any]:
        return {
            sid: {
                "user_id": info["user_info"]["user_id"],
                "connected_at": info["connected_at"],
            }
            for sid, info in self.sessions.items()
        }


_sessions = _SessionManager()


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------


@router.websocket("/ws/voice/{session_id}")
async def voice_websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: Optional[str] = Query(None),
):
    """
    Real-time voice WebSocket endpoint.

    Protocol
    --------
    * Binary frames: raw 16 kHz mono 16-bit PCM audio
    * JSON text frames (client → server):
      - ``{"type": "start_listening"}``
      - ``{"type": "stop_listening"}``
      - ``{"type": "text_input", "text": "..."}``
      - ``{"type": "set_interruption_sensitivity", "sensitivity": "low|medium|high"}``
      - ``{"type": "ping"}``
    * JSON text frames (server → client):
      - ``{"type": "connected", ...}``
      - ``{"type": "listening_started"}``
      - ``{"type": "transcription", "text": "..."}``
      - ``{"type": "tts_start", "text": "..."}``
      - Binary TTS audio chunks
      - ``{"type": "tts_end"}``
      - ``{"type": "interrupted", "context": "..."}``
      - ``{"type": "error", "error": "..."}``
    """
    await websocket.accept()

    try:
        user_info = await _authenticate_ws(websocket, token)
    except WebSocketDisconnect:
        return

    _sessions.add(session_id, websocket, user_info)

    try:
        # Send connection confirmation
        await websocket.send_json(
            {
                "type": "connected",
                "session_id": session_id,
                "user_id": user_info["user_id"],
            }
        )

        handler = await get_voice_handler()
        await handler.handle_connection(websocket, session_id)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Voice WS error [{session_id}]: {e}", exc_info=True)
        try:
            await websocket.send_json({"type": "error", "error": str(e)})
        except Exception:
            pass
    finally:
        _sessions.remove(session_id)


# ---------------------------------------------------------------------------
# REST helpers
# ---------------------------------------------------------------------------


@router.get("/voice/ws/health")
async def voice_ws_health():
    """Health check for the realtime voice WebSocket layer."""
    handler = await get_voice_handler()
    return {
        "status": "healthy",
        "active_sessions": len(_sessions.sessions),
        "handler_ready": handler is not None,
    }


@router.get("/voice/ws/sessions")
async def list_voice_ws_sessions():
    """List active realtime voice sessions (admin/debug)."""
    handler = await get_voice_handler()
    sessions_info = {}
    for sid in _sessions.sessions:
        sessions_info[sid] = handler.get_session_stats(sid)
    return {"sessions": sessions_info}
