"""
WebSocket endpoint for real-time pipeline status updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Dict, Set
import asyncio
import logging
import json
from uuid import UUID
from services.queue_service import queue_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Track active connections per pipeline
active_connections: Dict[str, Set[WebSocket]] = {}

class ConnectionManager:
    """Manage WebSocket connections for pipeline updates"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, pipeline_id: str):
        """Accept a WebSocket connection for a pipeline"""
        await websocket.accept()

        if pipeline_id not in self.active_connections:
            self.active_connections[pipeline_id] = set()

        self.active_connections[pipeline_id].add(websocket)

        logger.info(f"WebSocket connected for pipeline {pipeline_id}")

    def disconnect(self, websocket: WebSocket, pipeline_id: str):
        """Remove a WebSocket connection"""

        if pipeline_id in self.active_connections:
            self.active_connections[pipeline_id].discard(websocket)

            # Clean up empty pipeline connection sets
            if not self.active_connections[pipeline_id]:
                del self.active_connections[pipeline_id]

        logger.info(f"WebSocket disconnected for pipeline {pipeline_id}")

    async def broadcast_to_pipeline(self, pipeline_id: str, message: dict):
        """Broadcast a message to all connections for a pipeline"""

        if pipeline_id not in self.active_connections:
            return

        # Create a copy to avoid modification during iteration
        connections = list(self.active_connections[pipeline_id])

        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                # Remove dead connection
                self.active_connections[pipeline_id].discard(connection)

manager = ConnectionManager()

@router.websocket("/pipelines/{pipeline_id}")
async def pipeline_status_websocket(
    websocket: WebSocket,
    pipeline_id: UUID
):
    """
    WebSocket endpoint for real-time pipeline status updates

    Clients connect to receive updates about:
    - Document processing progress
    - Claim extraction status
    - Job completion
    - Errors
    """

    pipeline_id_str = str(pipeline_id)

    await manager.connect(websocket, pipeline_id_str)

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            'type': 'connected',
            'pipeline_id': pipeline_id_str,
            'message': 'Connected to pipeline status updates'
        })

        # Keep connection alive and poll for status updates
        while True:
            try:
                # Wait for client messages (ping/pong for keep-alive)
                # Use a timeout so we can send periodic updates
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=5.0
                )

                # Handle client messages (e.g., ping)
                if data == 'ping':
                    await websocket.send_json({'type': 'pong'})

            except asyncio.TimeoutError:
                # No message received, send a heartbeat
                await websocket.send_json({
                    'type': 'heartbeat',
                    'timestamp': asyncio.get_event_loop().time()
                })

            except WebSocketDisconnect:
                break

    except Exception as e:
        logger.error(f"WebSocket error for pipeline {pipeline_id}: {e}")

    finally:
        manager.disconnect(websocket, pipeline_id_str)

async def notify_pipeline_update(pipeline_id: str, update_type: str, data: dict):
    """
    Helper function to send updates to all connected clients for a pipeline

    Usage from other parts of the app:
        from routes.websocket.router import notify_pipeline_update

        await notify_pipeline_update(
            pipeline_id='xxx',
            update_type='claim_extracted',
            data={'claims_count': 10}
        )
    """

    message = {
        'type': update_type,
        'pipeline_id': pipeline_id,
        'data': data,
        'timestamp': asyncio.get_event_loop().time()
    }

    await manager.broadcast_to_pipeline(pipeline_id, message)

@router.get("/stats")
async def websocket_stats():
    """Get WebSocket connection statistics"""

    stats = {
        'total_connections': sum(len(conns) for conns in manager.active_connections.values()),
        'pipelines_with_connections': len(manager.active_connections),
        'connections_per_pipeline': {
            pipeline_id: len(conns)
            for pipeline_id, conns in manager.active_connections.items()
        }
    }

    return stats
