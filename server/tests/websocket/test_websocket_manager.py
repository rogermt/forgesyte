"""Tests for WebSocket connection management.

Following TDD: Write tests first, then implement code to make them pass.
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock

import pytest

# Add the server directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.websocket_manager import ConnectionManager  # noqa: E402


@pytest.fixture
def manager() -> ConnectionManager:
    """Create a fresh ConnectionManager for each test."""
    return ConnectionManager()


@pytest.fixture
def mock_websocket() -> AsyncMock:
    """Create a mock WebSocket."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.close = AsyncMock()
    return ws


class TestConnectionManagerInitialization:
    """Test ConnectionManager initialization."""

    def test_manager_initializes_with_empty_connections(self) -> None:
        """Test that manager starts with no active connections."""
        mgr = ConnectionManager()
        assert mgr.get_connection_count() == 0
        assert mgr.active_connections == {}

    def test_manager_initializes_with_empty_subscriptions(self) -> None:
        """Test that manager starts with no subscriptions."""
        mgr = ConnectionManager()
        assert mgr.subscriptions == {}

    def test_manager_has_asyncio_lock(self, manager: ConnectionManager) -> None:
        """Test that manager has an asyncio lock."""
        assert hasattr(manager, "_lock")
        assert isinstance(manager._lock, asyncio.Lock)

    def test_get_stats_empty_manager(self, manager: ConnectionManager) -> None:
        """Test stats for empty manager."""
        stats = manager.get_stats()
        assert stats["active_connections"] == 0
        assert stats["topics"] == {}


class TestConnectionConnect:
    """Test connect functionality."""

    @pytest.mark.asyncio
    async def test_connect_accepts_websocket(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test that connect accepts the WebSocket."""
        result = await manager.connect(mock_websocket, "client1")
        assert result is True
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_stores_connection(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test that connect stores the connection."""
        await manager.connect(mock_websocket, "client1")
        assert "client1" in manager.active_connections
        assert manager.active_connections["client1"] is mock_websocket

    @pytest.mark.asyncio
    async def test_connect_increments_connection_count(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test that connection count increases."""
        await manager.connect(mock_websocket, "client1")
        assert manager.get_connection_count() == 1

    @pytest.mark.asyncio
    async def test_connect_multiple_clients(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test connecting multiple clients."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()

        await manager.connect(ws1, "client1")
        await manager.connect(ws2, "client2")

        assert manager.get_connection_count() == 2
        assert "client1" in manager.active_connections
        assert "client2" in manager.active_connections

    @pytest.mark.asyncio
    async def test_connect_handles_accept_failure(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test that connect returns False if accept fails."""
        mock_websocket.accept.side_effect = Exception("Connection failed")
        result = await manager.connect(mock_websocket, "client1")
        assert result is False
        assert manager.get_connection_count() == 0


class TestConnectionDisconnect:
    """Test disconnect functionality."""

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test that disconnect removes the connection."""
        await manager.connect(mock_websocket, "client1")
        await manager.disconnect("client1")
        assert "client1" not in manager.active_connections

    @pytest.mark.asyncio
    async def test_disconnect_decrements_connection_count(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test that connection count decreases."""
        await manager.connect(mock_websocket, "client1")
        assert manager.get_connection_count() == 1
        await manager.disconnect("client1")
        assert manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_disconnect_removes_from_subscriptions(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test that disconnect removes client from all subscriptions."""
        await manager.connect(mock_websocket, "client1")
        await manager.subscribe("client1", "topic1")
        await manager.subscribe("client1", "topic2")

        await manager.disconnect("client1")

        assert "client1" not in manager.subscriptions["topic1"]
        assert "client1" not in manager.subscriptions["topic2"]

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_client(
        self, manager: ConnectionManager
    ) -> None:
        """Test disconnect on non-existent client doesn't error."""
        # Should not raise an exception
        await manager.disconnect("nonexistent")
        assert manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_disconnect_multiple_clients(
        self, manager: ConnectionManager
    ) -> None:
        """Test disconnecting multiple clients."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()

        await manager.connect(ws1, "client1")
        await manager.connect(ws2, "client2")
        await manager.disconnect("client1")

        assert manager.get_connection_count() == 1
        assert "client1" not in manager.active_connections
        assert "client2" in manager.active_connections


class TestSubscriptions:
    """Test subscription functionality."""

    @pytest.mark.asyncio
    async def test_subscribe_creates_topic(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test that subscribe creates topic if it doesn't exist."""
        await manager.connect(mock_websocket, "client1")
        await manager.subscribe("client1", "topic1")
        assert "topic1" in manager.subscriptions

    @pytest.mark.asyncio
    async def test_subscribe_adds_client_to_topic(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test that subscribe adds client to topic."""
        await manager.connect(mock_websocket, "client1")
        await manager.subscribe("client1", "topic1")
        assert "client1" in manager.subscriptions["topic1"]

    @pytest.mark.asyncio
    async def test_subscribe_multiple_clients_same_topic(
        self, manager: ConnectionManager
    ) -> None:
        """Test multiple clients subscribing to same topic."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()

        await manager.connect(ws1, "client1")
        await manager.connect(ws2, "client2")
        await manager.subscribe("client1", "topic1")
        await manager.subscribe("client2", "topic1")

        assert len(manager.subscriptions["topic1"]) == 2
        assert "client1" in manager.subscriptions["topic1"]
        assert "client2" in manager.subscriptions["topic1"]

    @pytest.mark.asyncio
    async def test_subscribe_same_client_multiple_topics(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test one client subscribing to multiple topics."""
        await manager.connect(mock_websocket, "client1")
        await manager.subscribe("client1", "topic1")
        await manager.subscribe("client1", "topic2")
        await manager.subscribe("client1", "topic3")

        assert "client1" in manager.subscriptions["topic1"]
        assert "client1" in manager.subscriptions["topic2"]
        assert "client1" in manager.subscriptions["topic3"]

    @pytest.mark.asyncio
    async def test_unsubscribe_removes_client_from_topic(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test that unsubscribe removes client from topic."""
        await manager.connect(mock_websocket, "client1")
        await manager.subscribe("client1", "topic1")
        await manager.unsubscribe("client1", "topic1")
        assert "client1" not in manager.subscriptions["topic1"]

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent_topic(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test unsubscribe from non-existent topic doesn't error."""
        await manager.connect(mock_websocket, "client1")
        # Should not raise an exception
        await manager.unsubscribe("client1", "nonexistent")

    @pytest.mark.asyncio
    async def test_subscribe_idempotent(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test that subscribing twice doesn't duplicate."""
        await manager.connect(mock_websocket, "client1")
        await manager.subscribe("client1", "topic1")
        await manager.subscribe("client1", "topic1")
        assert len(manager.subscriptions["topic1"]) == 1


class TestSendPersonal:
    """Test sending personal (unicast) messages."""

    @pytest.mark.asyncio
    async def test_send_personal_sends_to_client(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test that send_personal sends message to correct client."""
        await manager.connect(mock_websocket, "client1")
        message = {"type": "test", "data": "hello"}
        await manager.send_personal("client1", message)
        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_personal_to_nonexistent_client(
        self, manager: ConnectionManager
    ) -> None:
        """Test send_personal to non-existent client doesn't error."""
        message = {"type": "test", "data": "hello"}
        # Should not raise an exception
        await manager.send_personal("nonexistent", message)

    @pytest.mark.asyncio
    async def test_send_personal_handles_send_error(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test that send_personal handles send errors gracefully."""
        await manager.connect(mock_websocket, "client1")
        mock_websocket.send_json.side_effect = Exception("Send failed")

        message = {"type": "test"}
        await manager.send_personal("client1", message)

        # Client should be disconnected after error
        assert "client1" not in manager.active_connections

    @pytest.mark.asyncio
    async def test_send_personal_multiple_messages(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test sending multiple messages to same client."""
        await manager.connect(mock_websocket, "client1")

        msg1 = {"type": "message1"}
        msg2 = {"type": "message2"}
        msg3 = {"type": "message3"}

        await manager.send_personal("client1", msg1)
        await manager.send_personal("client1", msg2)
        await manager.send_personal("client1", msg3)

        assert mock_websocket.send_json.call_count == 3


class TestBroadcast:
    """Test broadcast functionality."""

    @pytest.mark.asyncio
    async def test_broadcast_to_all_clients(self, manager: ConnectionManager) -> None:
        """Test broadcasting to all connected clients."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()

        await manager.connect(ws1, "client1")
        await manager.connect(ws2, "client2")

        message = {"type": "broadcast", "data": "all"}
        await manager.broadcast(message)

        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_to_topic(self, manager: ConnectionManager) -> None:
        """Test broadcasting to clients subscribed to a topic."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws3 = AsyncMock()
        ws3.accept = AsyncMock()

        await manager.connect(ws1, "client1")
        await manager.connect(ws2, "client2")
        await manager.connect(ws3, "client3")

        await manager.subscribe("client1", "updates")
        await manager.subscribe("client2", "updates")
        # client3 not subscribed to updates

        message = {"type": "update"}
        await manager.broadcast(message, topic="updates")

        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)
        ws3.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_broadcast_empty_topic(self, manager: ConnectionManager) -> None:
        """Test broadcast to topic with no subscribers."""
        message = {"type": "update"}
        # Should not raise an exception
        await manager.broadcast(message, topic="empty_topic")

    @pytest.mark.asyncio
    async def test_broadcast_handles_send_error(
        self, manager: ConnectionManager
    ) -> None:
        """Test that broadcast removes clients that fail to receive."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws1.send_json.side_effect = Exception("Send failed")
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()

        await manager.connect(ws1, "client1")
        await manager.connect(ws2, "client2")

        message = {"type": "broadcast"}
        await manager.broadcast(message)

        # client1 should be disconnected due to error
        assert "client1" not in manager.active_connections
        assert "client2" in manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_partial_failure(self, manager: ConnectionManager) -> None:
        """Test broadcast when some clients fail."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws1.send_json.side_effect = Exception("Failed")
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws3 = AsyncMock()
        ws3.accept = AsyncMock()

        await manager.connect(ws1, "client1")
        await manager.connect(ws2, "client2")
        await manager.connect(ws3, "client3")

        message = {"type": "broadcast"}
        await manager.broadcast(message)

        # Only failed client should be removed
        assert "client1" not in manager.active_connections
        assert "client2" in manager.active_connections
        assert "client3" in manager.active_connections


class TestFrameResultMessages:
    """Test send_frame_result functionality."""

    @pytest.mark.asyncio
    async def test_send_frame_result_structure(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test that frame result message has correct structure."""
        await manager.connect(mock_websocket, "client1")

        result_data = {"detected_objects": ["person", "car"]}
        await manager.send_frame_result(
            "client1", "frame123", "motion_detector", result_data, 45.2
        )

        # Verify message structure
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "result"
        assert call_args["payload"]["frame_id"] == "frame123"
        assert call_args["payload"]["plugin"] == "motion_detector"
        assert call_args["payload"]["result"] == result_data
        assert call_args["payload"]["processing_time_ms"] == 45.2
        assert "timestamp" in call_args

    @pytest.mark.asyncio
    async def test_send_frame_result_to_nonexistent_client(
        self, manager: ConnectionManager
    ) -> None:
        """Test sending frame result to non-existent client."""
        result_data = {"data": "test"}
        # Should not raise an exception
        await manager.send_frame_result(
            "nonexistent", "frame1", "plugin1", result_data, 10.0
        )

    @pytest.mark.asyncio
    async def test_send_frame_result_with_complex_result(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test frame result with complex nested data."""
        await manager.connect(mock_websocket, "client1")

        complex_result = {
            "regions": [
                {"x": 0, "y": 0, "width": 100, "height": 100, "confidence": 0.95},
                {"x": 150, "y": 150, "width": 80, "height": 80, "confidence": 0.87},
            ],
            "metadata": {"model": "v2", "input_size": 640},
        }

        await manager.send_frame_result(
            "client1", "frame456", "detector", complex_result, 123.45
        )

        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["payload"]["result"] == complex_result


class TestErrorMessages:
    """Test send_error functionality."""

    @pytest.mark.asyncio
    async def test_send_error_structure(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test that error message has correct structure."""
        await manager.connect(mock_websocket, "client1")
        await manager.send_error("client1", "Invalid input")

        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["payload"]["error"] == "Invalid input"
        assert call_args["payload"]["frame_id"] is None
        assert "timestamp" in call_args

    @pytest.mark.asyncio
    async def test_send_error_with_frame_id(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test error message with associated frame."""
        await manager.connect(mock_websocket, "client1")
        await manager.send_error("client1", "Processing failed", frame_id="frame789")

        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["payload"]["error"] == "Processing failed"
        assert call_args["payload"]["frame_id"] == "frame789"

    @pytest.mark.asyncio
    async def test_send_error_to_nonexistent_client(
        self, manager: ConnectionManager
    ) -> None:
        """Test sending error to non-existent client."""
        # Should not raise an exception
        await manager.send_error("nonexistent", "Some error")


class TestConcurrency:
    """Test concurrent operations."""

    @pytest.mark.asyncio
    async def test_concurrent_connects(self, manager: ConnectionManager) -> None:
        """Test concurrent connect operations."""
        mock_sockets = [AsyncMock() for _ in range(10)]
        for ws in mock_sockets:
            ws.accept = AsyncMock()

        tasks = [manager.connect(ws, f"client{i}") for i, ws in enumerate(mock_sockets)]
        results = await asyncio.gather(*tasks)

        assert all(results)
        assert manager.get_connection_count() == 10

    @pytest.mark.asyncio
    async def test_concurrent_operations_mixed(
        self, manager: ConnectionManager
    ) -> None:
        """Test concurrent mixed operations (connect, subscribe, send)."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()

        await manager.connect(ws1, "client1")
        await manager.connect(ws2, "client2")

        tasks = [
            manager.subscribe("client1", "topic1"),
            manager.subscribe("client2", "topic1"),
            manager.send_personal("client1", {"msg": "hello"}),
            manager.broadcast({"msg": "broadcast"}, topic="topic1"),
        ]

        await asyncio.gather(*tasks)

        assert manager.get_connection_count() == 2
        assert len(manager.subscriptions["topic1"]) == 2

    @pytest.mark.asyncio
    async def test_concurrent_disconnect_and_send(
        self, manager: ConnectionManager
    ) -> None:
        """Test sending while disconnecting."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()

        await manager.connect(ws1, "client1")

        # Run send and disconnect concurrently
        tasks = [
            manager.send_personal("client1", {"msg": "test"}),
            manager.disconnect("client1"),
        ]

        await asyncio.gather(*tasks)

        # Should not error, one operation wins
        assert manager.get_connection_count() == 0


class TestConnectionStats:
    """Test statistics retrieval."""

    @pytest.mark.asyncio
    async def test_get_stats_with_connections_and_subscriptions(
        self, manager: ConnectionManager
    ) -> None:
        """Test stats with multiple connections and subscriptions."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws3 = AsyncMock()
        ws3.accept = AsyncMock()

        await manager.connect(ws1, "client1")
        await manager.connect(ws2, "client2")
        await manager.connect(ws3, "client3")

        await manager.subscribe("client1", "updates")
        await manager.subscribe("client2", "updates")
        await manager.subscribe("client1", "notifications")

        stats = manager.get_stats()

        assert stats["active_connections"] == 3
        assert "updates" in stats["topics"]
        assert "notifications" in stats["topics"]
        assert stats["topics"]["updates"] == 2
        assert stats["topics"]["notifications"] == 1

    @pytest.mark.asyncio
    async def test_get_connection_count_accuracy(
        self, manager: ConnectionManager
    ) -> None:
        """Test connection count remains accurate through operations."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()

        await manager.connect(ws1, "client1")
        assert manager.get_connection_count() == 1

        await manager.connect(ws2, "client2")
        assert manager.get_connection_count() == 2

        await manager.disconnect("client1")
        assert manager.get_connection_count() == 1

        await manager.disconnect("client2")
        assert manager.get_connection_count() == 0


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_empty_message_send(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test sending empty message."""
        await manager.connect(mock_websocket, "client1")
        await manager.send_personal("client1", {})
        mock_websocket.send_json.assert_called_once_with({})

    @pytest.mark.asyncio
    async def test_very_large_message(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test sending large message payload."""
        await manager.connect(mock_websocket, "client1")

        large_data = {"data": "x" * 100000}
        await manager.send_personal("client1", large_data)

        mock_websocket.send_json.assert_called_once_with(large_data)

    @pytest.mark.asyncio
    async def test_special_characters_in_client_id(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test client IDs with special characters."""
        client_id = "client-123_456.789"
        await manager.connect(mock_websocket, client_id)
        assert client_id in manager.active_connections

    @pytest.mark.asyncio
    async def test_many_subscriptions_per_client(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test client subscribing to many topics."""
        await manager.connect(mock_websocket, "client1")

        for i in range(100):
            await manager.subscribe("client1", f"topic{i}")

        assert len(manager.subscriptions) == 100
        assert all("client1" in manager.subscriptions[f"topic{i}"] for i in range(100))
