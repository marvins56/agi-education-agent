"""WebSocket gateway for real-time voice communication."""
import asyncio
import logging
import json
from typing import Dict, Set, Optional
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from src.voice.schemas import (
    VoiceCommand, VoiceEvent, AudioChunk, ConversationState,
    VoicePersona, AudioFormat
)
from src.voice.conversation.manager import VoiceConversationManager

logger = logging.getLogger(__name__)


class VoiceWebSocketGateway:
    """WebSocket gateway for voice conversations."""
    
    def __init__(self, conversation_manager: VoiceConversationManager):
        self.conversation_manager = conversation_manager
        
        # Active WebSocket connections
        self.connections: Dict[str, WebSocket] = {}
        self.session_connections: Dict[str, str] = {}  # session_id -> connection_id
        
        # Connection metadata
        self.connection_metadata: Dict[str, Dict] = {}
    
    async def handle_connection(
        self,
        websocket: WebSocket,
        connection_id: str,
        student_id: str
    ):
        """Handle new WebSocket connection."""
        
        await websocket.accept()
        
        # Store connection
        self.connections[connection_id] = websocket
        self.connection_metadata[connection_id] = {
            "student_id": student_id,
            "connected_at": datetime.now(),
            "session_id": None
        }
        
        logger.info(f"Voice WebSocket connected: {connection_id} (student: {student_id})")
        
        try:
            # Send welcome message
            await self._send_event(connection_id, VoiceEvent(
                event="connected",
                session_id="",
                data={
                    "connection_id": connection_id,
                    "message": "Voice gateway connected",
                    "supported_formats": ["wav", "mp3", "webm"],
                    "max_duration_ms": 300000  # 5 minutes
                }
            ))
            
            # Message handling loop
            while True:
                try:
                    # Receive message
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Create command object
                    try:
                        command = VoiceCommand(**message)
                    except ValidationError as e:
                        await self._send_error(connection_id, "", f"Invalid command format: {e}")
                        continue
                    
                    # Process command
                    await self._handle_command(connection_id, command)
                    
                except json.JSONDecodeError:
                    await self._send_error(connection_id, "", "Invalid JSON format")
                    continue
                    
        except WebSocketDisconnect:
            logger.info(f"Voice WebSocket disconnected: {connection_id}")
        except Exception as e:
            logger.error(f"Voice WebSocket error for {connection_id}: {e}")
        finally:
            await self._cleanup_connection(connection_id)
    
    async def _handle_command(self, connection_id: str, command: VoiceCommand):
        """Handle incoming voice command."""
        
        try:
            if command.command == "create_session":
                await self._handle_create_session(connection_id, command)
            
            elif command.command == "start_listening":
                await self._handle_start_listening(connection_id, command)
            
            elif command.command == "send_audio":
                await self._handle_send_audio(connection_id, command)
            
            elif command.command == "stop_listening":
                await self._handle_stop_listening(connection_id, command)
            
            elif command.command == "end_session":
                await self._handle_end_session(connection_id, command)
            
            elif command.command == "interrupt":
                await self._handle_interrupt(connection_id, command)
            
            elif command.command == "get_status":
                await self._handle_get_status(connection_id, command)
            
            else:
                await self._send_error(
                    connection_id, 
                    command.session_id,
                    f"Unknown command: {command.command}"
                )
                
        except Exception as e:
            logger.error(f"Error handling command {command.command}: {e}")
            await self._send_error(connection_id, command.session_id, str(e))
    
    async def _handle_create_session(self, connection_id: str, command: VoiceCommand):
        """Handle session creation."""
        
        metadata = self.connection_metadata[connection_id]
        student_id = metadata["student_id"]
        
        # Extract configuration
        config = command.data or {}
        
        # Create conversation session
        session = await self.conversation_manager.create_session(
            session_id=command.session_id,
            student_id=student_id,
            config=config
        )
        
        # Link session to connection
        metadata["session_id"] = command.session_id
        self.session_connections[command.session_id] = connection_id
        
        # Send confirmation
        await self._send_event(connection_id, VoiceEvent(
            event="session_created",
            session_id=command.session_id,
            data={
                "session_id": command.session_id,
                "student_id": student_id,
                "voice_persona": session.preferred_voice.value,
                "language": session.language,
                "state": session.state.value
            }
        ))
    
    async def _handle_start_listening(self, connection_id: str, command: VoiceCommand):
        """Handle start listening command."""
        
        # Check session exists
        session = await self.conversation_manager.get_session(command.session_id)
        if not session:
            await self._send_error(connection_id, command.session_id, "Session not found")
            return
        
        # Update session state would be handled by conversation manager
        await self._send_event(connection_id, VoiceEvent(
            event="listening_started",
            session_id=command.session_id,
            data={
                "message": "Ready to receive audio",
                "max_chunk_size": 8192,  # 8KB chunks
                "expected_format": "wav"
            }
        ))
    
    async def _handle_send_audio(self, connection_id: str, command: VoiceCommand):
        """Handle incoming audio chunk."""
        
        if not command.audio_chunk:
            await self._send_error(connection_id, command.session_id, "No audio data provided")
            return
        
        try:
            # Parse audio data
            audio_data = command.data or {}
            
            # Create audio chunk
            audio_chunk = AudioChunk.from_base64(
                command.audio_chunk,
                format=AudioFormat(audio_data.get("format", "wav")),
                sample_rate=audio_data.get("sample_rate", 16000),
                channels=audio_data.get("channels", 1),
                duration_ms=audio_data.get("duration_ms", 0),
                sequence_number=audio_data.get("sequence_number", 0),
                is_final=audio_data.get("is_final", False)
            )
            
            # Process audio through conversation manager
            event = await self.conversation_manager.process_audio(
                command.session_id, 
                audio_chunk
            )
            
            # Send any resulting events
            if event:
                await self._send_event(connection_id, event)
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            await self._send_error(connection_id, command.session_id, f"Audio processing error: {e}")
    
    async def _handle_stop_listening(self, connection_id: str, command: VoiceCommand):
        """Handle stop listening command."""
        
        # Send final audio chunk to trigger processing
        try:
            final_chunk = AudioChunk(
                audio_data=b"",
                duration_ms=0,
                sequence_number=9999,
                is_final=True
            )
            
            event = await self.conversation_manager.process_audio(
                command.session_id,
                final_chunk
            )
            
            if event:
                await self._send_event(connection_id, event)
            
        except Exception as e:
            logger.error(f"Error stopping listening: {e}")
            await self._send_error(connection_id, command.session_id, str(e))
    
    async def _handle_end_session(self, connection_id: str, command: VoiceCommand):
        """Handle session end."""
        
        # End conversation session
        success = await self.conversation_manager.end_session(command.session_id)
        
        if success:
            # Get final analytics
            analytics = await self.conversation_manager.get_session_analytics(command.session_id)
            
            # Remove from tracking
            if command.session_id in self.session_connections:
                del self.session_connections[command.session_id]
            
            metadata = self.connection_metadata.get(connection_id, {})
            metadata["session_id"] = None
            
            await self._send_event(connection_id, VoiceEvent(
                event="session_ended",
                session_id=command.session_id,
                data=analytics or {"message": "Session ended"}
            ))
        else:
            await self._send_error(connection_id, command.session_id, "Failed to end session")
    
    async def _handle_interrupt(self, connection_id: str, command: VoiceCommand):
        """Handle conversation interruption."""
        
        interruption_type = command.data.get("type", "user_speech") if command.data else "user_speech"
        
        event = await self.conversation_manager.handle_interruption(
            command.session_id,
            interruption_type
        )
        
        await self._send_event(connection_id, event)
    
    async def _handle_get_status(self, connection_id: str, command: VoiceCommand):
        """Handle status request."""
        
        if command.session_id:
            # Get specific session status
            analytics = await self.conversation_manager.get_session_analytics(command.session_id)
            await self._send_event(connection_id, VoiceEvent(
                event="status",
                session_id=command.session_id,
                data=analytics or {"error": "Session not found"}
            ))
        else:
            # Get gateway status
            active_sessions = self.conversation_manager.get_active_sessions()
            await self._send_event(connection_id, VoiceEvent(
                event="gateway_status",
                session_id="",
                data={
                    "active_connections": len(self.connections),
                    "active_sessions": len(active_sessions),
                    "sessions": active_sessions
                }
            ))
    
    async def _send_event(self, connection_id: str, event: VoiceEvent):
        """Send event to WebSocket client."""
        
        if connection_id not in self.connections:
            return
        
        try:
            websocket = self.connections[connection_id]
            message = event.dict()
            await websocket.send_text(json.dumps(message, default=str))
            
        except Exception as e:
            logger.error(f"Error sending event to {connection_id}: {e}")
            await self._cleanup_connection(connection_id)
    
    async def _send_error(self, connection_id: str, session_id: str, error_message: str):
        """Send error event to client."""
        
        error_event = VoiceEvent(
            event="error",
            session_id=session_id,
            data={"error": error_message}
        )
        
        await self._send_event(connection_id, error_event)
    
    async def _cleanup_connection(self, connection_id: str):
        """Clean up connection resources."""
        
        # End any active session
        metadata = self.connection_metadata.get(connection_id, {})
        session_id = metadata.get("session_id")
        
        if session_id:
            await self.conversation_manager.end_session(session_id)
            if session_id in self.session_connections:
                del self.session_connections[session_id]
        
        # Remove connection
        if connection_id in self.connections:
            del self.connections[connection_id]
        
        if connection_id in self.connection_metadata:
            del self.connection_metadata[connection_id]
        
        logger.info(f"Cleaned up voice connection: {connection_id}")
    
    async def broadcast_to_session(self, session_id: str, event: VoiceEvent):
        """Broadcast event to all connections in a session."""
        
        connection_id = self.session_connections.get(session_id)
        if connection_id:
            await self._send_event(connection_id, event)
    
    def get_connection_stats(self) -> Dict[str, int]:
        """Get connection statistics."""
        return {
            "total_connections": len(self.connections),
            "active_sessions": len(self.session_connections),
            "connections_with_sessions": len([
                m for m in self.connection_metadata.values()
                if m.get("session_id")
            ])
        }