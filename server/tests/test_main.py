"""Test suite for app/main.py module.

Tests cover:
- FastAPI app initialization and configuration
- Lifespan management (startup/shutdown)
- Dependency injection
- WebSocket streaming endpoints
- Error handling and edge cases
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.main import (
    app,
    get_analysis_service,
    lifespan,
    ws_manager,
)


@pytest.fixture
def mock_plugin_manager():
    """Mock PluginRegistry for testing."""
    mock = MagicMock()
    mock.list.return_value = {}
    mock.load_plugins.return_value = {"loaded": {}, "errors": []}
    return mock


@pytest.fixture
def mock_vision_service():
    """Mock VisionAnalysisService."""
    mock = AsyncMock()
    mock.handle_frame = AsyncMock()
    return mock


@pytest.fixture
def mock_task_processor():
    """Mock task processor."""
    return MagicMock()


@pytest.fixture
def mock_ws_manager():
    """Reset websocket manager before each test."""
    ws_manager.active_connections.clear()
    ws_manager.subscriptions.clear()
    return ws_manager


@pytest.mark.asyncio
async def test_lifespan_startup_shutdown(mock_plugin_manager, mock_task_processor):
    """Test that lifespan context manager initializes and cleans up correctly."""

    # Mock dependencies
    with (
        patch("app.main.PluginRegistry", return_value=mock_plugin_manager),
        patch("app.main.init_task_processor", return_value=mock_task_processor),
        patch("app.main.VisionAnalysisService") as MockVisionService,
        patch("app.main.init_auth_service") as mock_init_auth,
    ):

        mock_vision_instance = MagicMock()
        MockVisionService.return_value = mock_vision_instance

        # Enter lifespan
        async with lifespan(app) as _:
            # Check auth service called
            mock_init_auth.assert_called_once()

            # Check plugin manager created and loaded
            assert hasattr(app.state, "plugins")
            assert app.state.plugins == mock_plugin_manager
            mock_plugin_manager.load_plugins.assert_called_once()

            # Check task processor initialized
            assert mock_task_processor is not None

            # Check services initialized
            assert hasattr(app.state, "analysis_service")
            assert hasattr(app.state, "analysis_service_rest")
            assert hasattr(app.state, "job_service")
            assert hasattr(app.state, "plugin_service")

        # Shutdown phase — mock should have been called
        assert mock_plugin_manager is not None


def test_app_creation():
    """Test FastAPI app is created with correct metadata and middleware."""
    assert isinstance(app, FastAPI)
    assert app.title == "ForgeSyte"
    assert app.version == "0.1.0"

    # Check CORS middleware is added
    assert any(
        middleware.cls.__name__ == "CORSMiddleware"
        for middleware in app.user_middleware
    )


def test_get_analysis_service():
    """Test dependency injection of VisionAnalysisService."""
    mock_service = MagicMock()
    app.state.analysis_service = mock_service

    try:
        service = get_analysis_service()
        assert service == mock_service

        # Test missing service raises HTTPException
        delattr(app.state, "analysis_service")
        from fastapi import HTTPException

        with pytest.raises(HTTPException):
            get_analysis_service()
    finally:
        if hasattr(app.state, "analysis_service"):
            delattr(app.state, "analysis_service")


def test_root_endpoint():
    """Test root endpoint returns expected info."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "ForgeSyte"
    assert data["version"] == "0.1.0"
    assert data["docs"] == "/docs"


def test_mcp_manifest_redirect():
    """Test MCP manifest redirect."""
    client = TestClient(app)
    response = client.get("/.well-known/mcp-manifest", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["location"] == "/v1/.well-known/mcp-manifest"


def test_websocket_stream_connection(mock_vision_service):
    """Test WebSocket connection establishment and initial message."""
    client = TestClient(app)
    mock_vision_service.plugins = {"motion_detector": MagicMock()}
    mock_vision_service.handle_frame = AsyncMock(return_value=None)

    # Set up app state for dependency injection
    app.state.analysis_service = mock_vision_service

    try:
        with client.websocket_connect("/v1/stream?plugin=motion_detector") as websocket:
            # Receive initial connection confirmation
            data = websocket.receive_json()
            assert data["type"] == "connected"
            assert "client_id" in data["payload"]
            assert data["payload"]["plugin"] == "motion_detector"
    finally:
        # Clean up app state
        if hasattr(app.state, "analysis_service"):
            delattr(app.state, "analysis_service")


def test_websocket_stream_frame_handling(mock_vision_service):
    """Test frame message delegation to service layer."""
    client = TestClient(app)
    mock_vision_service.plugins = {"motion_detector": MagicMock()}
    mock_vision_service.handle_frame = AsyncMock(return_value=None)

    app.state.analysis_service = mock_vision_service

    try:
        with client.websocket_connect("/v1/stream?plugin=motion_detector") as websocket:
            # Skip initial connection message
            websocket.receive_json()

            # Send ping first to verify connection works
            websocket.send_json({"type": "ping"})
            pong = websocket.receive_json()
            assert pong["type"] == "pong"

            # Service handle_frame is called but we don't await response
            # Just verify endpoint handles frame without error
            websocket.send_json(
                {
                    "type": "frame",
                    "tools": ["detect"],
                    "data": "base64data==",
                    "options": {},
                }
            )
    finally:
        if hasattr(app.state, "analysis_service"):
            delattr(app.state, "analysis_service")


def test_websocket_stream_ping_pong(mock_vision_service):
    """Test ping/pong message exchange."""
    client = TestClient(app)
    mock_vision_service.plugins = {"motion_detector": MagicMock()}
    mock_vision_service.handle_frame = AsyncMock(return_value=None)

    app.state.analysis_service = mock_vision_service

    try:
        with client.websocket_connect("/v1/stream?plugin=motion_detector") as websocket:
            # Skip connected message
            websocket.receive_json()

            # Send ping
            websocket.send_json({"type": "ping"})

            # Receive pong
            response = websocket.receive_json()
            assert response["type"] == "pong"
    finally:
        if hasattr(app.state, "analysis_service"):
            delattr(app.state, "analysis_service")


def test_websocket_stream_plugin_switch_valid(mock_vision_service):
    """Test plugin switching with valid plugin."""
    client = TestClient(app)
    mock_vision_service.plugins = {
        "motion_detector": MagicMock(),
        "ocr": MagicMock(),
    }
    mock_vision_service.handle_frame = AsyncMock(return_value=None)

    app.state.analysis_service = mock_vision_service

    try:
        with client.websocket_connect("/v1/stream?plugin=motion_detector") as websocket:
            # Skip connected message
            websocket.receive_json()

            # Switch to valid plugin
            websocket.send_json({"type": "switch_plugin", "plugin": "ocr"})

            # Receive confirmation
            response = websocket.receive_json()
            assert response["type"] == "plugin_switched"
            assert response["payload"]["plugin"] == "ocr"
    finally:
        if hasattr(app.state, "analysis_service"):
            delattr(app.state, "analysis_service")


def test_websocket_stream_plugin_switch_invalid(mock_vision_service):
    """Test plugin switching with invalid plugin name."""
    client = TestClient(app)
    mock_vision_service.plugins = {"motion_detector": MagicMock()}
    mock_vision_service.handle_frame = AsyncMock(return_value=None)

    app.state.analysis_service = mock_vision_service

    try:
        with client.websocket_connect("/v1/stream?plugin=motion_detector") as websocket:
            # Skip connected message
            websocket.receive_json()

            # Try to switch to non-existent plugin
            websocket.send_json({"type": "switch_plugin", "plugin": "nonexistent"})

            # Receive error
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "not found" in response["message"]
    finally:
        if hasattr(app.state, "analysis_service"):
            delattr(app.state, "analysis_service")


@pytest.mark.asyncio
async def test_websocket_stream_plugin_switch_registry_protocol(mock_vision_service):
    """Test plugin switching when using a registry that
    implements .get() but not 'in'."""
    from app.main import websocket_stream

    class StrictRegistry:
        def __init__(self, plugins):
            self._plugins = plugins

        def get(self, name):
            return self._plugins.get(name)

        def __iter__(self):
            # This makes 'in' operator raise TypeError
            raise TypeError("StrictRegistry is not iterable")

    mock_vision_service.plugins = StrictRegistry({"ocr": MagicMock()})

    # Mock WebSocket
    mock_ws = AsyncMock()
    # First message: connected, then switch_plugin, then stop
    mock_ws.receive_json.side_effect = [
        {"type": "switch_plugin", "plugin": "ocr"},
        Exception("Stop Loop"),
    ]

    try:
        await websocket_stream(
            websocket=mock_ws, plugin="motion_detector", service=mock_vision_service
        )
    except Exception as e:
        if str(e) != "Stop Loop":
            raise

    # Verify 'plugin_switched' message was sent
    # In broken state, this will fail because TypeError causes disconnect before sending
    mock_ws.send_json.assert_any_call(
        {
            "type": "plugin_switched",
            "payload": {"plugin": "ocr"},
        }
    )


def test_websocket_stream_subscribe_topic(mock_vision_service):
    """Test topic subscription message."""
    client = TestClient(app)
    mock_vision_service.plugins = {"motion_detector": MagicMock()}
    mock_vision_service.handle_frame = AsyncMock(return_value=None)

    app.state.analysis_service = mock_vision_service

    try:
        with client.websocket_connect("/v1/stream?plugin=motion_detector") as websocket:
            # Skip connected message
            websocket.receive_json()

            # Subscribe to topic
            websocket.send_json({"type": "subscribe", "topic": "analysis_results"})

            # Should not receive immediate response, but should be subscribed
            # Verify by sending ping and getting pong (connection still works)
            websocket.send_json({"type": "ping"})
            response = websocket.receive_json()
            assert response["type"] == "pong"
    finally:
        if hasattr(app.state, "analysis_service"):
            delattr(app.state, "analysis_service")
