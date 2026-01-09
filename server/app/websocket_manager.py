"""WebSocket connection management for streaming."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Set, Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # topic -> connection_ids
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_id: str) -> bool:
        """Accept a new WebSocket connection."""
        try:
            await websocket.accept()
            async with self._lock:
                self.active_connections[client_id] = websocket
            logger.info(f"Client {client_id} connected")
            return True
        except Exception as e:
            logger.error(f"Failed to accept connection: {e}")
            return False

    async def disconnect(self, client_id: str):
        """Handle client disconnection."""
        async with self._lock:
            if client_id in self.active_connections:
                del self.active_connections[client_id]

            # Remove from all subscriptions
            for topic in self.subscriptions:
                self.subscriptions[topic].discard(client_id)

        logger.info(f"Client {client_id} disconnected")

    async def subscribe(self, client_id: str, topic: str):
        """Subscribe a client to a topic."""
        async with self._lock:
            if topic not in self.subscriptions:
                self.subscriptions[topic] = set()
            self.subscriptions[topic].add(client_id)

    async def unsubscribe(self, client_id: str, topic: str):
        """Unsubscribe a client from a topic."""
        async with self._lock:
            if topic in self.subscriptions:
                self.subscriptions[topic].discard(client_id)

    async def send_personal(self, client_id: str, message: dict):
        """Send a message to a specific client."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to {client_id}: {e}")
                await self.disconnect(client_id)

    async def broadcast(self, message: dict, topic: Optional[str] = None):
        """Broadcast a message to all clients or topic subscribers."""
        targets = set()

        if topic and topic in self.subscriptions:
            targets = self.subscriptions[topic].copy()
        else:
            targets = set(self.active_connections.keys())

        disconnected = []
        for client_id in targets:
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_json(message)
                except Exception as e:
                    logger.error(f"Failed to broadcast to {client_id}: {e}")
                    disconnected.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected:
            await self.disconnect(client_id)

    async def send_frame_result(
        self,
        client_id: str,
        frame_id: str,
        plugin: str,
        result: dict,
        processing_time_ms: float,
    ):
        """Send a frame analysis result to a client."""
        message = {
            "type": "result",
            "payload": {
                "frame_id": frame_id,
                "plugin": plugin,
                "result": result,
                "processing_time_ms": processing_time_ms,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.send_personal(client_id, message)

    async def send_error(
        self, client_id: str, error: str, frame_id: Optional[str] = None
    ):
        """Send an error message to a client."""
        message = {
            "type": "error",
            "payload": {"error": error, "frame_id": frame_id},
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.send_personal(client_id, message)

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)

    def get_stats(self) -> dict:
        """Get connection statistics."""
        return {
            "active_connections": len(self.active_connections),
            "topics": {
                topic: len(clients) for topic, clients in self.subscriptions.items()
            },
        }


# Global instance
ws_manager = ConnectionManager()
