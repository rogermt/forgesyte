"""WebSocket connection management for streaming analysis results.

This module provides resilient WebSocket connection management with retry logic,
structured logging, and Pydantic message validation. It follows the service layer
pattern with Protocol-based abstractions for testability.

Key features:
- Async-safe connection tracking with asyncio.Lock
- Topic-based subscription and broadcasting
- Retry logic with exponential backoff for transient failures
- Pydantic message validation for type safety
- Structured logging for observability
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Protocol, Set

from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class MessagePayload(BaseModel):
    """Schema for WebSocket message payloads.

    Ensures type safety and consistency across all WebSocket communication.

    Attributes:
        frame_id: Optional identifier for the analyzed frame
        plugin: Optional plugin name that generated the result
        result: Optional analysis result from plugin
        error: Optional error message
        processing_time_ms: Optional processing duration in milliseconds
    """

    frame_id: Optional[str] = None
    plugin: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    processing_time_ms: Optional[float] = None


class WebSocketMessage(BaseModel):
    """Envelope for all WebSocket communication.

    Combines message type, payload, and timestamp into a validated structure.

    Attributes:
        type: Message type (e.g., "result", "error", "status")
        payload: Message payload with optional content
        timestamp: ISO format timestamp of message creation
    """

    type: str
    payload: MessagePayload
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WebSocketSession(Protocol):
    """Structural contract for WebSocket communication.

    Allows ConnectionManager to work with any object that satisfies this
    interface, enabling testing with mocks and future extensions.
    """

    async def accept(self) -> None:
        """Accept the WebSocket connection.

        Raises:
            RuntimeError: If connection cannot be accepted
        """
        ...

    async def send_json(self, data: Dict[str, Any]) -> None:
        """Send JSON data to the client.

        Args:
            data: Dictionary to serialize and send as JSON

        Raises:
            RuntimeError: If send fails
            ConnectionError: If connection is closed
        """
        ...

    async def close(self, code: int = 1000) -> None:
        """Close the WebSocket connection.

        Args:
            code: WebSocket close code (default 1000 = normal closure)

        Raises:
            RuntimeError: If close fails
        """
        ...


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    reraise=True,
)
async def _safe_send(websocket: WebSocketSession, message: Dict[str, Any]) -> None:
    """Send message with retry logic and exponential backoff.

    Internal helper that wraps send operations with resilience handling.
    Automatically retries on transient failures up to 3 times with exponential
    backoff between attempts.

    Args:
        websocket: WebSocket session to send to
        message: Validated message dict to send

    Raises:
        RuntimeError: If send fails after all retry attempts
        ConnectionError: If connection is closed
    """
    await websocket.send_json(message)


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting.

    Provides async-safe connection tracking, topic-based subscriptions,
    and broadcast capabilities with retry logic. All operations are protected
    by an asyncio.Lock to ensure thread-safe state mutations.

    Attributes:
        active_connections: Dict mapping client_id to WebSocket sessions
        subscriptions: Dict mapping topic names to sets of subscribed client IDs
    """

    def __init__(self) -> None:
        """Initialize the connection manager."""
        self.active_connections: Dict[str, WebSocketSession] = {}
        self.subscriptions: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocketSession, client_id: str) -> bool:
        """Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket session to accept
            client_id: Unique identifier for the client

        Returns:
            True if connection accepted successfully, False otherwise

        Raises:
            None - Errors are logged and False returned
        """
        try:
            await websocket.accept()
            async with self._lock:
                self.active_connections[client_id] = websocket
            logger.info(
                "websocket_connect",
                extra={
                    "client_id": client_id,
                    "total_connections": len(self.active_connections),
                },
            )
            return True
        except Exception as e:
            logger.error(
                "websocket_connect_failed",
                extra={"client_id": client_id, "error": str(e)},
            )
            return False

    async def disconnect(self, client_id: str) -> None:
        """Gracefully disconnect a client and remove subscriptions.

        Args:
            client_id: Unique identifier for the client to disconnect

        Raises:
            None - Errors are logged
        """
        async with self._lock:
            if client_id in self.active_connections:
                del self.active_connections[client_id]

            # Remove client from all topic subscriptions
            for topic in self.subscriptions:
                self.subscriptions[topic].discard(client_id)

        logger.info(
            "websocket_disconnect",
            extra={
                "client_id": client_id,
                "remaining_connections": len(self.active_connections),
            },
        )

    async def subscribe(self, client_id: str, topic: str) -> None:
        """Subscribe a client to a topic.

        Args:
            client_id: Client to subscribe
            topic: Topic name to subscribe to

        Raises:
            None - Errors are logged
        """
        async with self._lock:
            if topic not in self.subscriptions:
                self.subscriptions[topic] = set()
            self.subscriptions[topic].add(client_id)

        logger.info(
            "websocket_subscribe",
            extra={
                "client_id": client_id,
                "topic": topic,
                "topic_subscribers": len(self.subscriptions[topic]),
            },
        )

    async def unsubscribe(self, client_id: str, topic: str) -> None:
        """Unsubscribe a client from a topic.

        Args:
            client_id: Client to unsubscribe
            topic: Topic name to unsubscribe from

        Raises:
            None - Errors are logged
        """
        async with self._lock:
            if topic in self.subscriptions:
                self.subscriptions[topic].discard(client_id)

        logger.info(
            "websocket_unsubscribe",
            extra={"client_id": client_id, "topic": topic},
        )

    async def send_personal(
        self, client_id: str, message: WebSocketMessage | Dict[str, Any]
    ) -> None:
        """Send a message to a specific client with retry logic.

        Accepts either Pydantic WebSocketMessage or raw dict for backward
        compatibility. Sends with resilience handling via retry logic.
        Automatically disconnects client if send fails after retries.

        Args:
            client_id: Target client ID
            message: WebSocketMessage or dict to send

        Raises:
            None - Errors are logged and client is disconnected on failure
        """
        if client_id not in self.active_connections:
            logger.debug(
                "websocket_send_personal_not_found",
                extra={"client_id": client_id},
            )
            return

        try:
            ws = self.active_connections[client_id]
            # Support both WebSocketMessage and raw dicts
            if isinstance(message, WebSocketMessage):
                data = message.model_dump(mode="json")
                msg_type = message.type
            else:
                data = message
                msg_type = message.get("type", "unknown")
            await _safe_send(ws, data)
            logger.debug(
                "websocket_send_personal_success",
                extra={"client_id": client_id, "message_type": msg_type},
            )
        except Exception as e:
            logger.error(
                "websocket_send_personal_failed",
                extra={
                    "client_id": client_id,
                    "error": str(e),
                },
            )
            await self.disconnect(client_id)

    async def broadcast(
        self, message: WebSocketMessage | Dict[str, Any], topic: Optional[str] = None
    ) -> None:
        """Broadcast a message to clients, optionally filtered by topic.

        Accepts either Pydantic WebSocketMessage or raw dict for backward
        compatibility. Sends message to all subscribers of a specific topic,
        or to all connected clients if topic is not specified. Uses
        asyncio.gather for parallel delivery.

        Args:
            message: WebSocketMessage or dict to broadcast
            topic: Optional topic to limit broadcast scope

        Raises:
            None - Errors are logged per client
        """
        targets: Set[str] = set()

        async with self._lock:
            if topic is not None:
                # Topic-specific broadcast: only send to subscribers of this topic
                if topic in self.subscriptions:
                    targets = self.subscriptions[topic].copy()
                # else: no subscribers for this topic, targets remains empty
            else:
                # No topic specified: broadcast to all connections
                targets = set(self.active_connections.keys())

        # Get message type for logging
        msg_type = (
            message.type
            if isinstance(message, WebSocketMessage)
            else message.get("type", "unknown")
        )

        if not targets:
            logger.debug(
                "websocket_broadcast_no_targets",
                extra={"topic": topic, "message_type": msg_type},
            )
            return

        logger.info(
            "websocket_broadcast_start",
            extra={
                "target_count": len(targets),
                "topic": topic,
                "message_type": msg_type,
            },
        )

        # Send to all targets in parallel
        tasks = [self.send_personal(cid, message) for cid in targets]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def send_frame_result(
        self,
        client_id: str,
        frame_id: str,
        plugin: str,
        result: Dict[str, Any],
        processing_time_ms: float,
    ) -> None:
        """Send a frame analysis result to a client.

        Args:
            client_id: Target client ID
            frame_id: Identifier for the analyzed frame
            plugin: Name of the plugin that performed analysis
            result: Analysis result dictionary
            processing_time_ms: Time taken to process frame in milliseconds

        Raises:
            None - Errors are logged
        """
        message = WebSocketMessage(
            type="result",
            payload=MessagePayload(
                frame_id=frame_id,
                plugin=plugin,
                result=result,
                processing_time_ms=processing_time_ms,
            ),
        )
        await self.send_personal(client_id, message)

    async def send_error(
        self, client_id: str, error: str, frame_id: Optional[str] = None
    ) -> None:
        """Send an error message to a client.

        Args:
            client_id: Target client ID
            error: Error message text
            frame_id: Optional frame ID associated with the error

        Raises:
            None - Errors are logged
        """
        message = WebSocketMessage(
            type="error", payload=MessagePayload(error=error, frame_id=frame_id)
        )
        await self.send_personal(client_id, message)

    def get_connection_count(self) -> int:
        """Get the number of active connections.

        Returns:
            Number of currently connected clients
        """
        return len(self.active_connections)

    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics.

        Returns:
            Dictionary with active_connections count and per-topic subscriber counts
        """
        return {
            "active_connections": len(self.active_connections),
            "topics": {
                topic: len(clients) for topic, clients in self.subscriptions.items()
            },
        }


# Global instance for dependency injection
ws_manager = ConnectionManager()
