"""WebSocket API endpoint for real-time voice communication."""
import asyncio
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from pydantic import BaseModel, ValidationError

from src.voice.pipeline import VoiceAgentPipeline
from src.voice.schemas import AudioChunk, AudioFormat, VoiceEvent, VoiceCommand
from src.api.middleware.auth import verify_jwt_token
from src.memory.manager import MemoryManager
from src.agents.orchestrator import MasterOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["Voice WebSocket"])


# Global pipeline instance (would be dependency injected in production)
voice_pipeline: Optional[VoiceAgentPipeline] = None


async def get_voice_pipeline() -> VoiceAgentPipeline:
    """Get or create voice pipeline."""
    global voice_pipeline
    
    if voice_pipeline is None:
        # Initialize dependencies (these would be injected properly)
        memory_manager = MemoryManager()
        
        # Mock orchestrator for now
        class MockOrchestrator:
            def __init__(self, memory_manager):
                self.memory = memory_manager
            
            async def process_message(self, context):
                # Mock response for testing
                return type('Response', (), {
                    'text': f"I understand you're asking about {context.message[:50]}... This is a test response from the voice pipeline."
                })()
        
        orchestrator = MockOrchestrator(memory_manager)
        
        # Create pipeline
        voice_pipeline = VoiceAgentPipeline(
            memory_manager=memory_manager,
            orchestrator=orchestrator,
            target_response_time_ms=500  # 500ms target for i5-6500
        )
        
        await voice_pipeline.initialize()
    
    return voice_pipeline


class VoiceWebSocketManager:
    """Manages WebSocket connections for voice communication."""
    
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.connection_sessions: Dict[str, str] = {}  # connection_id -> session_id
        self.session_connections: Dict[str, str] = {}  # session_id -> connection_id
        
        # Connection metadata
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Performance tracking
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "total_sessions": 0,
            "active_sessions": 0,
            "total_messages": 0,
            "websocket_errors": 0
        }
    
    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        student_id: str,
        session_id: Optional[str] = None
    ) -> bool:
        """Handle new WebSocket connection."""
        
        try:
            await websocket.accept()
            
            # Store connection
            self.connections[connection_id] = websocket
            self.connection_metadata[connection_id] = {
                "student_id": student_id,
                "session_id": session_id,
                "connected_at": datetime.now(),
                "last_activity": datetime.now(),
                "messages_sent": 0,
                "messages_received": 0
            }
            
            # Link to session if provided
            if session_id:
                self.connection_sessions[connection_id] = session_id
                self.session_connections[session_id] = connection_id
            
            # Update stats
            self.stats["total_connections"] += 1
            self.stats["active_connections"] += 1
            
            logger.info(f"Voice WebSocket connected: {connection_id} (student: {student_id})")
            
            # Send welcome message
            await self.send_event(connection_id, VoiceEvent(
                event="connected",
                session_id=session_id or "",
                data={
                    "connection_id": connection_id,
                    "message": "Voice WebSocket connected",
                    "server_time": datetime.now().isoformat(),
                    "capabilities": {
                        "real_time_processing": True,
                        "streaming_tts": True,
                        "barge_in_detection": True,
                        "target_response_time_ms": 500
                    }
                }
            ))
            
            return True
            
        except Exception as e:
            logger.error(f"Error connecting WebSocket {connection_id}: {e}")
            return False
    
    async def disconnect(self, connection_id: str):
        """Handle WebSocket disconnection."""
        
        try:
            # Get session if exists
            session_id = self.connection_sessions.get(connection_id)
            
            # End voice session
            if session_id:
                pipeline = await get_voice_pipeline()
                await pipeline.end_session(session_id)
                
                # Clean up session mapping
                if session_id in self.session_connections:
                    del self.session_connections[session_id]
                if connection_id in self.connection_sessions:
                    del self.connection_sessions[connection_id]
                
                self.stats["active_sessions"] = max(0, self.stats["active_sessions"] - 1)
            
            # Remove connection
            if connection_id in self.connections:
                del self.connections[connection_id]
            
            if connection_id in self.connection_metadata:
                del self.connection_metadata[connection_id]
            
            # Update stats
            self.stats["active_connections"] = max(0, self.stats["active_connections"] - 1)
            
            logger.info(f"Voice WebSocket disconnected: {connection_id}")
            
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket {connection_id}: {e}")
    
    async def send_event(self, connection_id: str, event: VoiceEvent) -> bool:
        """Send event to WebSocket client."""
        
        if connection_id not in self.connections:
            return False
        
        try:
            websocket = self.connections[connection_id]
            message = event.dict()
            await websocket.send_text(json.dumps(message, default=str))
            
            # Update metadata
            if connection_id in self.connection_metadata:
                self.connection_metadata[connection_id]["messages_sent"] += 1
                self.connection_metadata[connection_id]["last_activity"] = datetime.now()
            
            self.stats["total_messages"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error sending event to {connection_id}: {e}")
            await self.disconnect(connection_id)
            return False
    
    async def handle_message(
        self,
        connection_id: str,
        message: str
    ) -> bool:
        """Handle incoming WebSocket message."""
        
        try:
            # Parse message
            try:
                data = json.loads(message)
                command = VoiceCommand(**data)
            except (json.JSONDecodeError, ValidationError) as e:
                await self.send_event(connection_id, VoiceEvent(
                    event="error",
                    session_id="",
                    data={"error": f"Invalid message format: {e}"}
                ))
                return False
            
            # Update metadata
            if connection_id in self.connection_metadata:
                self.connection_metadata[connection_id]["messages_received"] += 1
                self.connection_metadata[connection_id]["last_activity"] = datetime.now()
            
            # Handle command
            await self._handle_command(connection_id, command)
            return True
            
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")
            self.stats["websocket_errors"] += 1
            return False
    
    async def _handle_command(self, connection_id: str, command: VoiceCommand):
        """Handle voice command."""
        
        pipeline = await get_voice_pipeline()
        
        try:
            if command.command == "create_session":
                await self._handle_create_session(connection_id, command, pipeline)
            
            elif command.command == "send_audio":
                await self._handle_send_audio(connection_id, command, pipeline)
            
            elif command.command == "interrupt":
                await self._handle_interrupt(connection_id, command, pipeline)
            
            elif command.command == "end_session":
                await self._handle_end_session(connection_id, command, pipeline)
            
            elif command.command == "get_status":
                await self._handle_get_status(connection_id, command, pipeline)
            
            else:
                await self.send_event(connection_id, VoiceEvent(
                    event="error",
                    session_id=command.session_id,
                    data={"error": f"Unknown command: {command.command}"}
                ))
                
        except Exception as e:
            logger.error(f"Error handling command {command.command}: {e}")
            await self.send_event(connection_id, VoiceEvent(
                event="error",
                session_id=command.session_id,
                data={"error": str(e)}
            ))
    
    async def _handle_create_session(
        self,
        connection_id: str,
        command: VoiceCommand,
        pipeline: VoiceAgentPipeline
    ):
        """Handle session creation."""
        
        metadata = self.connection_metadata[connection_id]
        student_id = metadata["student_id"]
        
        try:
            # Create session
            session_info = await pipeline.create_session(
                session_id=command.session_id,
                student_id=student_id,
                config=command.data or {}
            )
            
            # Link session to connection
            self.connection_sessions[connection_id] = command.session_id
            self.session_connections[command.session_id] = connection_id
            metadata["session_id"] = command.session_id
            
            # Update stats
            self.stats["total_sessions"] += 1
            self.stats["active_sessions"] += 1
            
            # Send confirmation
            await self.send_event(connection_id, VoiceEvent(
                event="session_created",
                session_id=command.session_id,
                data={
                    **session_info,
                    "websocket_connection": connection_id
                }
            ))
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            await self.send_event(connection_id, VoiceEvent(
                event="error",
                session_id=command.session_id,
                data={"error": f"Failed to create session: {e}"}
            ))
    
    async def _handle_send_audio(
        self,
        connection_id: str,
        command: VoiceCommand,
        pipeline: VoiceAgentPipeline
    ):
        """Handle audio data."""
        
        if not command.audio_chunk:
            await self.send_event(connection_id, VoiceEvent(
                event="error",
                session_id=command.session_id,
                data={"error": "No audio data provided"}
            ))
            return
        
        try:
            # Parse audio metadata
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
            
            # Process through pipeline
            result = await pipeline.process_single_audio(
                command.session_id,
                audio_chunk
            )
            
            # Send result
            await self.send_event(connection_id, result)
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            await self.send_event(connection_id, VoiceEvent(
                event="error",
                session_id=command.session_id,
                data={"error": f"Audio processing failed: {e}"}
            ))
    
    async def _handle_interrupt(
        self,
        connection_id: str,
        command: VoiceCommand,
        pipeline: VoiceAgentPipeline
    ):
        """Handle interruption command."""
        
        try:
            success = await pipeline.interrupt_generation(command.session_id)
            
            await self.send_event(connection_id, VoiceEvent(
                event="interrupted" if success else "interrupt_failed",
                session_id=command.session_id,
                data={"success": success}
            ))
            
        except Exception as e:
            logger.error(f"Error handling interrupt: {e}")
            await self.send_event(connection_id, VoiceEvent(
                event="error",
                session_id=command.session_id,
                data={"error": str(e)}
            ))
    
    async def _handle_end_session(
        self,
        connection_id: str,
        command: VoiceCommand,
        pipeline: VoiceAgentPipeline
    ):
        """Handle session end."""
        
        try:
            success = await pipeline.end_session(command.session_id)
            
            # Clean up mappings
            if connection_id in self.connection_sessions:
                del self.connection_sessions[connection_id]
            if command.session_id in self.session_connections:
                del self.session_connections[command.session_id]
            
            # Update metadata
            metadata = self.connection_metadata.get(connection_id, {})
            metadata["session_id"] = None
            
            # Update stats
            self.stats["active_sessions"] = max(0, self.stats["active_sessions"] - 1)
            
            await self.send_event(connection_id, VoiceEvent(
                event="session_ended",
                session_id=command.session_id,
                data={"success": success}
            ))
            
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            await self.send_event(connection_id, VoiceEvent(
                event="error",
                session_id=command.session_id,
                data={"error": str(e)}
            ))
    
    async def _handle_get_status(
        self,
        connection_id: str,
        command: VoiceCommand,
        pipeline: VoiceAgentPipeline
    ):
        """Handle status request."""
        
        try:
            if command.session_id:
                # Get session status
                session_analytics = pipeline.get_pipeline_stats()
                await self.send_event(connection_id, VoiceEvent(
                    event="session_status",
                    session_id=command.session_id,
                    data=session_analytics
                ))
            else:
                # Get overall status
                status_data = {
                    "websocket_stats": self.stats,
                    "pipeline_stats": pipeline.get_pipeline_stats(),
                    "active_connections": len(self.connections),
                    "active_sessions": len(self.session_connections)
                }
                
                await self.send_event(connection_id, VoiceEvent(
                    event="server_status",
                    session_id="",
                    data=status_data
                ))
                
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            await self.send_event(connection_id, VoiceEvent(
                event="error",
                session_id=command.session_id,
                data={"error": str(e)}
            ))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics."""
        return {
            **self.stats,
            "current_connections": len(self.connections),
            "current_sessions": len(self.session_connections)
        }


# Global WebSocket manager
ws_manager = VoiceWebSocketManager()


@router.websocket("/ws/{session_id}")
async def voice_websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(..., description="JWT authentication token"),
    student_id: Optional[str] = Query(None, description="Student ID (extracted from token if not provided)")
):
    """WebSocket endpoint for real-time voice communication.
    
    Args:
        websocket: WebSocket connection
        session_id: Voice session identifier
        token: JWT authentication token
        student_id: Student identifier (optional, extracted from token)
    """
    
    connection_id = f"{session_id}_{uuid.uuid4().hex[:8]}"
    
    try:
        # Authenticate user
        try:
            payload = verify_jwt_token(token)
            if not student_id:
                student_id = payload.get("student_id") or payload.get("user_id")
            
            if not student_id:
                await websocket.close(code=4001, reason="Authentication failed: no student ID")
                return
                
        except Exception as e:
            logger.error(f"WebSocket authentication failed: {e}")
            await websocket.close(code=4001, reason="Authentication failed")
            return
        
        # Connect
        connected = await ws_manager.connect(
            websocket=websocket,
            connection_id=connection_id,
            student_id=student_id,
            session_id=session_id
        )
        
        if not connected:
            await websocket.close(code=4003, reason="Connection failed")
            return
        
        # Message loop
        try:
            while True:
                try:
                    # Wait for message
                    message = await websocket.receive_text()
                    
                    # Handle message
                    await ws_manager.handle_message(connection_id, message)
                    
                except WebSocketDisconnect:
                    logger.info(f"WebSocket {connection_id} disconnected normally")
                    break
                except Exception as e:
                    logger.error(f"WebSocket {connection_id} message error: {e}")
                    await ws_manager.send_event(connection_id, VoiceEvent(
                        event="error",
                        session_id=session_id,
                        data={"error": str(e)}
                    ))
                    
        except Exception as e:
            logger.error(f"WebSocket {connection_id} loop error: {e}")
        
    except Exception as e:
        logger.error(f"WebSocket {connection_id} setup error: {e}")
    
    finally:
        # Cleanup
        await ws_manager.disconnect(connection_id)


@router.get("/ws/status")
async def get_websocket_status():
    """Get WebSocket server status."""
    
    try:
        pipeline = await get_voice_pipeline()
        
        return {
            "websocket_manager": ws_manager.get_stats(),
            "voice_pipeline": pipeline.get_pipeline_stats(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting WebSocket status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get status")


@router.post("/ws/broadcast/{session_id}")
async def broadcast_to_session(
    session_id: str,
    event_data: Dict[str, Any]
):
    """Broadcast message to a specific session.
    
    Args:
        session_id: Session to broadcast to
        event_data: Event data to broadcast
    """
    
    try:
        # Create event
        event = VoiceEvent(
            event=event_data.get("event", "broadcast"),
            session_id=session_id,
            data=event_data.get("data", {})
        )
        
        # Send to session
        connection_id = ws_manager.session_connections.get(session_id)
        if connection_id:
            success = await ws_manager.send_event(connection_id, event)
            return {"success": success, "connection_found": True}
        else:
            return {"success": False, "connection_found": False}
            
    except Exception as e:
        logger.error(f"Error broadcasting to session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Broadcast failed")


# Health check endpoint
@router.get("/ws/health")
async def websocket_health():
    """Health check for voice WebSocket service."""
    
    try:
        pipeline = await get_voice_pipeline()
        pipeline_ready = pipeline.initialized
        
        return {
            "status": "healthy" if pipeline_ready else "initializing",
            "pipeline_ready": pipeline_ready,
            "active_connections": len(ws_manager.connections),
            "active_sessions": len(ws_manager.session_connections),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"WebSocket health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }