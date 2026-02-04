"""
Phase 10 Real-Time Infrastructure

This module provides WebSocket-based real-time communication infrastructure.

TODO: Implement the following:
- ConnectionManager: Manages WebSocket connections
- WebSocket router for /v1/realtime endpoint
- RealtimeMessage schema with typed message types

Author: Roger
Phase: 10
"""

from .connection_manager import ConnectionManager
from .message_types import RealtimeMessage
from .websocket_router import router as websocket_router

__all__ = [
    "ConnectionManager",
    "RealtimeMessage",
    "websocket_router",
]

