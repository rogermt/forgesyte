"""Test Phase 10: Connection Manager.

This test verifies that the ConnectionManager class properly manages WebSocket connections.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.realtime.connection_manager import ConnectionManager


@pytest.mark.asyncio
async def test_connection_manager_init():
    """Verify ConnectionManager initializes with empty connections."""
    manager = ConnectionManager()
    assert manager.active_connections == {}
    assert manager.get_active_connections() == []


@pytest.mark.asyncio
async def test_connection_manager_connect():
    """Verify ConnectionManager can add a connection."""
    manager = ConnectionManager()
    
    # Create a mock websocket
    mock_websocket = AsyncMock()
    mock_websocket.accept = AsyncMock()
    
    await manager.connect("session-1", mock_websocket)
    
    assert manager.is_connected("session-1")
    mock_websocket.accept.assert_called_once()


@pytest.mark.asyncio
async def test_connection_manager_disconnect():
    """Verify ConnectionManager can remove a connection."""
    manager = ConnectionManager()
    
    # Create a mock websocket
    mock_websocket = AsyncMock()
    mock_websocket.accept = AsyncMock()
    
    await manager.connect("session-1", mock_websocket)
    assert manager.is_connected("session-1")
    
    await manager.disconnect("session-1")
    assert not manager.is_connected("session-1")


@pytest.mark.asyncio
async def test_connection_manager_broadcast():
    """Verify ConnectionManager broadcasts messages to all connections."""
    manager = ConnectionManager()
    
    # Create mock websockets
    mock_ws1 = AsyncMock()
    mock_ws1.accept = AsyncMock()
    mock_ws1.send_json = AsyncMock()
    
    mock_ws2 = AsyncMock()
    mock_ws2.accept = AsyncMock()
    mock_ws2.send_json = AsyncMock()
    
    await manager.connect("session-1", mock_ws1)
    await manager.connect("session-2", mock_ws2)
    
    message = {"type": "test", "payload": "hello"}
    await manager.broadcast(message)
    
    mock_ws1.send_json.assert_called_once_with(message)
    mock_ws2.send_json.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_connection_manager_get_active_connections():
    """Verify ConnectionManager returns all active session IDs."""
    manager = ConnectionManager()
    
    mock_ws = AsyncMock()
    mock_ws.accept = AsyncMock()
    
    await manager.connect("session-1", mock_ws)
    await manager.connect("session-2", mock_ws)
    
    connections = manager.get_active_connections()
    assert "session-1" in connections
    assert "session-2" in connections
    assert len(connections) == 2


@pytest.mark.asyncio
async def test_connection_manager_send_to():
    """Verify ConnectionManager can send to a specific session."""
    manager = ConnectionManager()
    
    mock_ws = AsyncMock()
    mock_ws.accept = AsyncMock()
    mock_ws.send_json = AsyncMock()
    
    await manager.connect("session-1", mock_ws)
    
    message = {"type": "test"}
    result = await manager.send_to("session-1", message)
    
    assert result is True
    mock_ws.send_json.assert_called_once_with(message)

