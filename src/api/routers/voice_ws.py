"""
WebSocket router for real-time voice communication.
Provides /ws/voice/{session_id} endpoint with JWT authentication.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.security.utils import get_authorization_scheme_param

from ...voice.realtime import RealtimeVoiceHandler
from ...core.config import get_settings
from ...core.database import get_db_session
from ...services.llm_service import LLMService
from ...services.tts_service import TTSService

logger = logging.getLogger(__name__)
settings = get_settings()

# Router setup
router = APIRouter()

# Global voice handler instance
voice_handler: Optional[RealtimeVoiceHandler] = None


async def get_voice_handler() -> RealtimeVoiceHandler:
    """Get or create the global voice handler instance."""
    global voice_handler
    
    if voice_handler is None:
        # Initialize LLM and TTS services
        llm_service = LLMService()
        tts_service = TTSService()
        
        # Create voice handler with service callbacks
        async def llm_callback(text: str):
            """Stream LLM response."""
            async for chunk in llm_service.stream_response(text):
                yield chunk
        
        async def tts_callback(text: str) -> bytes:
            """Generate TTS audio."""
            return await tts_service.synthesize(text)
        
        voice_handler = RealtimeVoiceHandler(llm_callback, tts_callback)
    
    return voice_handler


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verify JWT token and extract user information.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        # Decode and verify JWT token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Check for required fields
        if "user_id" not in payload:
            raise HTTPException(status_code=401, detail="Invalid token: missing user_id")
        
        if "exp" not in payload:
            raise HTTPException(status_code=401, detail="Invalid token: missing expiration")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


async def authenticate_websocket(websocket: WebSocket, token: Optional[str]) -> Dict[str, Any]:
    """
    Authenticate WebSocket connection using JWT token.
    
    Args:
        websocket: WebSocket connection
        token: JWT token from query parameter
        
    Returns:
        User information from token
        
    Raises:
        WebSocketException: If authentication fails
    """
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        raise WebSocketDisconnect(code=4001, reason="Missing authentication token")
    
    try:
        # Verify token
        payload = verify_jwt_token(token)
        
        # Extract user information
        user_info = {
            "user_id": payload["user_id"],
            "username": payload.get("username"),
            "email": payload.get("email"),
            "permissions": payload.get("permissions", [])
        }
        
        logger.info(f"Authenticated WebSocket connection for user: {user_info['user_id']}")
        return user_info
        
    except HTTPException as e:
        await websocket.close(code=4001, reason=e.detail)
        raise WebSocketDisconnect(code=4001, reason=e.detail)


class VoiceSessionManager:
    """Manages active voice WebSocket sessions."""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.websocket_sessions: Dict[str, WebSocket] = {}
    
    def add_session(self, session_id: str, websocket: WebSocket, user_info: Dict[str, Any]) -> None:
        """Add a new voice session."""
        self.active_sessions[session_id] = {
            "websocket": websocket,
            "user_info": user_info,
            "connected_at": asyncio.get_event_loop().time(),
            "message_count": 0
        }
        self.websocket_sessions[session_id] = websocket
        logger.info(f"Added voice session: {session_id} for user {user_info['user_id']}")
    
    def remove_session(self, session_id: str) -> None:
        """Remove a voice session."""
        self.active_sessions.pop(session_id, None)
        self.websocket_sessions.pop(session_id, None)
        logger.info(f"Removed voice session: {session_id}")
    
    def get_websocket(self, session_id: str) -> Optional[WebSocket]:
        """Get WebSocket connection for session."""
        return self.websocket_sessions.get(session_id)
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information."""
        return self.active_sessions.get(session_id)
    
    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all active sessions."""
        return self.active_sessions.copy()


# Global session manager
session_manager = VoiceSessionManager()


@router.websocket("/ws/voice/{session_id}")
async def voice_websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: Optional[str] = Query(None, description="JWT authentication token")
):
    """
    WebSocket endpoint for real-time voice communication.
    
    Args:
        websocket: WebSocket connection
        session_id: Unique session identifier
        token: JWT authentication token (required)
    
    Authentication:
        JWT token must be provided as query parameter: ?token=<jwt_token>
    
    Message Types:
        - Binary: Audio data (16kHz mono PCM)
        - JSON Control Messages:
          - {"type": "start_listening"}
          - {"type": "stop_listening"}
          - {"type": "text_input", "text": "..."}
          - {"type": "set_interruption_sensitivity", "sensitivity": "low|medium|high"}
    
    Response Types:
        - Binary: TTS audio data
        - JSON Status Messages:
          - {"type": "listening_started"}
          - {"type": "listening_stopped"}
          - {"type": "interrupted", "context": "..."}
          - {"type": "tts_start", "text": "..."}
          - {"type": "tts_end"}
          - {"type": "error", "error": "..."}
    """
    # Accept the WebSocket connection
    await websocket.accept()
    
    try:
        # Authenticate the connection
        user_info = await authenticate_websocket(websocket, token)
        
        # Add session to manager
        session_manager.add_session(session_id, websocket, user_info)
        
        # Get voice handler
        handler = await get_voice_handler()
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "user_id": user_info["user_id"],
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Handle the voice session
        await handler.handle_connection(websocket, session_id)
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Voice WebSocket error for session {session_id}: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "error": f"Internal server error: {str(e)}"
            })
        except:
            pass  # Connection might already be closed
    finally:
        # Clean up session
        session_manager.remove_session(session_id)


@router.get("/voice/sessions")
async def get_voice_sessions(
    token: str = Query(..., description="JWT authentication token")
):
    """
    Get information about active voice sessions.
    Requires admin permissions.
    """
    try:
        # Verify token and check permissions
        payload = verify_jwt_token(token)
        permissions = payload.get("permissions", [])
        
        if "admin" not in permissions and "voice_admin" not in permissions:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Get session information
        active_sessions = session_manager.get_active_sessions()
        
        # Get voice handler statistics
        handler = await get_voice_handler()
        session_stats = {}
        
        for session_id in active_sessions.keys():
            session_stats[session_id] = handler.get_session_stats(session_id)
        
        return {
            "active_sessions": len(active_sessions),
            "sessions": {
                session_id: {
                    "user_id": info["user_info"]["user_id"],
                    "connected_at": info["connected_at"],
                    "message_count": info["message_count"],
                    "stats": session_stats.get(session_id, {})
                }
                for session_id, info in active_sessions.items()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")


@router.post("/voice/sessions/{session_id}/control")
async def control_voice_session(
    session_id: str,
    action: Dict[str, Any],
    token: str = Query(..., description="JWT authentication token")
):
    """
    Send control message to a voice session.
    Requires admin permissions or session ownership.
    """
    try:
        # Verify token
        payload = verify_jwt_token(token)
        user_id = payload["user_id"]
        permissions = payload.get("permissions", [])
        
        # Check session exists
        session_info = session_manager.get_session_info(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check permissions
        session_user_id = session_info["user_info"]["user_id"]
        is_admin = "admin" in permissions or "voice_admin" in permissions
        is_owner = user_id == session_user_id
        
        if not (is_admin or is_owner):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Send control message to WebSocket
        websocket = session_manager.get_websocket(session_id)
        if not websocket:
            raise HTTPException(status_code=400, detail="Session WebSocket not available")
        
        await websocket.send_json(action)
        
        return {"status": "sent", "action": action}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to control session: {str(e)}")


@router.delete("/voice/sessions/{session_id}")
async def terminate_voice_session(
    session_id: str,
    token: str = Query(..., description="JWT authentication token")
):
    """
    Terminate a voice session.
    Requires admin permissions or session ownership.
    """
    try:
        # Verify token
        payload = verify_jwt_token(token)
        user_id = payload["user_id"]
        permissions = payload.get("permissions", [])
        
        # Check session exists
        session_info = session_manager.get_session_info(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check permissions
        session_user_id = session_info["user_info"]["user_id"]
        is_admin = "admin" in permissions or "voice_admin" in permissions
        is_owner = user_id == session_user_id
        
        if not (is_admin or is_owner):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Close WebSocket connection
        websocket = session_manager.get_websocket(session_id)
        if websocket:
            await websocket.close(code=4000, reason="Session terminated by request")
        
        # Remove from session manager
        session_manager.remove_session(session_id)
        
        return {"status": "terminated", "session_id": session_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to terminate session: {str(e)}")


# Monkey patch the voice handler to use our session manager
def _patch_voice_handler():
    """Patch the voice handler to integrate with session manager."""
    global voice_handler
    
    if voice_handler:
        # Override the _get_websocket method
        original_get_websocket = voice_handler._get_websocket
        
        def patched_get_websocket(session_id: str):
            return session_manager.get_websocket(session_id)
        
        voice_handler._get_websocket = patched_get_websocket


# Initialize handler patching on module load
asyncio.create_task(_patch_voice_handler())


# Health check endpoint
@router.get("/voice/health")
async def voice_health_check():
    """Health check for voice services."""
    try:
        handler = await get_voice_handler()
        active_count = len(session_manager.get_active_sessions())
        
        return {
            "status": "healthy",
            "active_sessions": active_count,
            "voice_handler_ready": handler is not None,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time()
        }