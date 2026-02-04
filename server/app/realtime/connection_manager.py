"""Phase 10: Connection Manager for WebSocket connections.

Manages active WebSocket connections for real-time communication.

TODO: Implement the following:
- connect(session_id, websocket): Accept and register a new WebSocket connection
- disconnect(session_id): Remove a WebSocket connection
- broadcast(message): Send a message to all connected clients
- is_connected(session_id): Check if a session is connected
- get_active_connections(): Get all active connection session IDs

Author: Roger
Phase: 10
"""

from typing import Dict

from fastapi import WebSocket


class ConnectionManager:
    """Manage WebSocket connections for real-time communication."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[session_id] = websocket

    async def disconnect(self, session_id: str) -> None:
        """Remove a WebSocket connection."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def broadcast(self, message: dict) -> None:
        """Send a message to all connected clients."""
        for websocket in self.active_connections.values():
            try:
                await websocket.send_json(message)
            except Exception:
                # Remove broken connections
                pass

    def is_connected(self, session_id: str) -> bool:
        """Check if a session is currently connected."""
        return session_id in self.active_connections

    def get_active_connections(self) -> list[str]:
        """Get all active connection session IDs."""
        return list(self.active_connections.keys())

    async def send_to(self, session_id: str, message: dict) -> bool:
        """Send a message to a specific session."""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(message)
                return True
            except Exception:
                await self.disconnect(session_id)
        return False
