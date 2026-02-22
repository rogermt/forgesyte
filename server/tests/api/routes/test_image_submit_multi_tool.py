"""Tests for v0.9.4 multi-tool image submission.

Tests verify:
1. API accepts multiple tool parameters
2. Multi-tool submission creates job_type="image_multi"
3. tool_list is stored as JSON-encoded list
4. All tools are validated against plugin.tools
5. All tools are validated for image input support
6. Single-tool backward compatibility is maintained
"""

import json
from io import BytesIO
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api_routes.routes.image_submit import get_plugin_manager, get_plugin_service
from app.main import app
from app.models.job import Job


@pytest.fixture
def mock_multi_tool_plugin():
    """Create a mock plugin with multiple tools."""
    plugin = MagicMock()
    plugin.name = "yolo-tracker"
    plugin.description = "YOLO Tracker Plugin"
    plugin.version = "1.0.0"
    plugin.tools = {
        "player_detection": {
            "handler": "detect_players",
            "description": "Detect players",
            "input_schema": {"image_bytes": {"type": "bytes"}},
            "output_schema": {"detections": {"type": "array"}},
        },
        "ball_detection": {
            "handler": "detect_ball",
            "description": "Detect ball",
            "input_schema": {"image_bytes": {"type": "bytes"}},
            "output_schema": {"detections": {"type": "array"}},
        },
        "player_tracking": {
            "handler": "track_players",
            "description": "Track players",
            "input_schema": {"image_bytes": {"type": "bytes"}},
            "output_schema": {"tracks": {"type": "array"}},
        },
    }
    return plugin


@pytest.fixture
def mock_multi_tool_plugin_service(mock_multi_tool_plugin):
    """Create a mock plugin management service for multi-tool."""
    mock = MagicMock()
    mock.get_available_tools.return_value = list(mock_multi_tool_plugin.tools.keys())
    return mock


@pytest.fixture
def mock_multi_tool_registry(mock_multi_tool_plugin):
    """Create a mock plugin registry with multi-tool plugin."""
    mock = MagicMock()
    mock.get.return_value = mock_multi_tool_plugin
    return mock


@pytest.fixture
def client_multi_tool(mock_multi_tool_registry, mock_multi_tool_plugin_service):
    """Create a test client with mocked multi-tool dependencies."""

    def override_get_plugin_manager():
        return mock_multi_tool_registry

    def override_get_plugin_service():
        return mock_multi_tool_plugin_service

    app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
    app.dependency_overrides[get_plugin_service] = override_get_plugin_service

    yield TestClient(app)

    app.dependency_overrides.clear()


class TestMultiToolSubmission:
    """Tests for multi-tool image submission."""

    def test_submit_image_multi_tool_creates_image_multi_job(
        self, session, client_multi_tool
    ):
        """Test that multi-tool submission creates job_type='image_multi'."""
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        response = client_multi_tool.post(
            "/v1/image/submit?plugin_id=yolo-tracker&tool=player_detection&tool=ball_detection",
            files={"file": ("test.png", BytesIO(png_data), "image/png")},
        )

        assert response.status_code == 200
        job_id = response.json()["job_id"]

        job = session.query(Job).filter(Job.job_id == job_id).first()
        assert job is not None
        assert job.job_type == "image_multi"

    def test_submit_image_multi_tool_stores_tool_list(self, session, client_multi_tool):
        """Test that multi-tool submission stores tool_list as JSON."""
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        response = client_multi_tool.post(
            "/v1/image/submit?plugin_id=yolo-tracker&tool=player_detection&tool=ball_detection&tool=player_tracking",
            files={"file": ("test.png", BytesIO(png_data), "image/png")},
        )

        assert response.status_code == 200
        job_id = response.json()["job_id"]

        job = session.query(Job).filter(Job.job_id == job_id).first()
        assert job is not None
        assert job.tool is None  # tool is null for multi-tool jobs

        # Parse tool_list
        tool_list = json.loads(job.tool_list)
        assert tool_list == ["player_detection", "ball_detection", "player_tracking"]

    def test_submit_image_single_tool_backward_compatible(
        self, session, client_multi_tool
    ):
        """Test that single-tool submission still works unchanged."""
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        response = client_multi_tool.post(
            "/v1/image/submit?plugin_id=yolo-tracker&tool=player_detection",
            files={"file": ("test.png", BytesIO(png_data), "image/png")},
        )

        assert response.status_code == 200
        job_id = response.json()["job_id"]

        job = session.query(Job).filter(Job.job_id == job_id).first()
        assert job is not None
        assert job.job_type == "image"  # NOT image_multi
        assert job.tool == "player_detection"
        assert job.tool_list is None

    def test_submit_image_multi_tool_validates_all_tools(self, mock_multi_tool_plugin):
        """Test that all tools are validated against plugin.tools."""
        mock_registry = MagicMock()
        mock_registry.get.return_value = mock_multi_tool_plugin

        # Service returns only valid tools
        mock_service = MagicMock()
        mock_service.get_available_tools.return_value = [
            "player_detection",
            "ball_detection",
        ]

        def override_get_plugin_manager():
            return mock_registry

        def override_get_plugin_service():
            return mock_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        # Request with one invalid tool
        response = client.post(
            "/v1/image/submit?plugin_id=yolo-tracker&tool=player_detection&tool=invalid_tool",
            files={"file": ("test.png", BytesIO(png_data), "image/png")},
        )

        app.dependency_overrides.clear()

        assert response.status_code == 400
        assert "invalid_tool" in response.json()["detail"]

    def test_submit_image_multi_tool_validates_image_input(self):
        """Test that all tools are validated for image input support."""
        # Create plugin with one tool that doesn't support images
        plugin = MagicMock()
        plugin.tools = {
            "image_tool": {
                "input_schema": {"image_bytes": {"type": "bytes"}},
            },
            "video_only_tool": {
                "input_schema": {"video_path": {"type": "string"}},  # No image support
            },
        }

        mock_registry = MagicMock()
        mock_registry.get.return_value = plugin

        mock_service = MagicMock()
        mock_service.get_available_tools.return_value = list(plugin.tools.keys())

        def override_get_plugin_manager():
            return mock_registry

        def override_get_plugin_service():
            return mock_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        # Request with tool that doesn't support images
        response = client.post(
            "/v1/image/submit?plugin_id=test&tool=image_tool&tool=video_only_tool",
            files={"file": ("test.png", BytesIO(png_data), "image/png")},
        )

        app.dependency_overrides.clear()

        assert response.status_code == 400
        assert "does not support image input" in response.json()["detail"].lower()

    def test_submit_image_multi_tool_preserves_order(self, session, client_multi_tool):
        """Test that tool order is preserved in tool_list."""
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        # Submit with specific order
        response = client_multi_tool.post(
            "/v1/image/submit?plugin_id=yolo-tracker&tool=player_tracking&tool=ball_detection&tool=player_detection",
            files={"file": ("test.png", BytesIO(png_data), "image/png")},
        )

        assert response.status_code == 200
        job_id = response.json()["job_id"]

        job = session.query(Job).filter(Job.job_id == job_id).first()
        tool_list = json.loads(job.tool_list)

        # Order should match query parameter order
        assert tool_list == ["player_tracking", "ball_detection", "player_detection"]
