"""Tests for v0.10.1 split video endpoints.

v0.10.1: Deterministic tool-locking flow requires:
1. POST /v1/video/upload - Upload-only, returns {video_path}
2. POST /v1/video/submit - Accepts JSON body {plugin_id, video_path, lockedTools}

This enables:
- Upload video → Tools lock → User chooses Start Streaming or Run Job
- Both paths use LOCKED_TOOLS

TDD: These tests are written FIRST and should FAIL until implementation.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.api_routes.routes.video_submit import get_plugin_manager, get_plugin_service


@pytest.fixture
def mock_plugin():
    """Create a mock plugin with video tools."""
    plugin = MagicMock()
    plugin.name = "yolo-tracker"
    plugin.tools = {
        "video_player_tracking": {
            "handler": "player_tracking_handler",
            "description": "Track players in video",
            "input_schema": {"properties": {"video_path": {"type": "string"}}},
            "output_schema": {"properties": {"detections": {"type": "array"}}},
        },
    }
    return plugin


@pytest.fixture
def mock_manifest():
    """Create a mock manifest with input_types."""
    return {
        "id": "yolo-tracker",
        "name": "YOLO Tracker",
        "version": "1.0.0",
        "capabilities": ["player_detection"],
        "tools": [
            {
                "id": "video_player_tracking",
                "title": "Player Tracking (Video)",
                "description": "Track players",
                "input_types": ["video"],
                "output_types": ["detections"],
                "capabilities": ["player_detection"],
            },
        ],
    }


@pytest.fixture
def mock_plugin_service(mock_plugin, mock_manifest):
    """Create a mock plugin management service."""
    mock = MagicMock()
    mock.get_available_tools.return_value = list(mock_plugin.tools.keys())
    mock.get_plugin_manifest.return_value = mock_manifest
    return mock


@pytest.fixture
def mock_plugin_registry(mock_plugin):
    """Create a mock plugin registry with a loaded plugin."""
    mock = MagicMock()
    mock.get.return_value = mock_plugin
    return mock


# =============================================================================
# TDD: POST /v1/video/upload - Upload-only endpoint
# =============================================================================


class TestVideoUploadEndpoint:
    """Tests for the new upload-only endpoint (v0.10.1)."""

    @pytest.mark.unit
    def test_video_upload_returns_video_path(self, mock_plugin_registry, mock_plugin_service):
        """POST /v1/video/upload should return {video_path}, NOT {job_id}."""
        def override_get_plugin_manager():
            return mock_plugin_registry

        def override_get_plugin_service():
            return mock_plugin_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        # Create fake MP4 data with ftyp marker
        mp4_data = b"ftypmp42" + b"\x00" * 100

        response = client.post(
            "/v1/video/upload",
            files={"file": ("test.mp4", mp4_data)},
            params={"plugin_id": "yolo-tracker"},
        )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        # KEY: Should return video_path, NOT job_id
        assert "video_path" in data
        assert "job_id" not in data

    @pytest.mark.unit
    def test_video_upload_validates_mp4(self, mock_plugin_registry, mock_plugin_service):
        """POST /v1/video/upload should reject non-MP4 files."""
        def override_get_plugin_manager():
            return mock_plugin_registry

        def override_get_plugin_service():
            return mock_plugin_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        # Invalid file (no ftyp marker)
        invalid_data = b"INVALID VIDEO DATA"

        response = client.post(
            "/v1/video/upload",
            files={"file": ("test.txt", invalid_data)},
            params={"plugin_id": "yolo-tracker"},
        )

        app.dependency_overrides.clear()

        assert response.status_code == 400

    @pytest.mark.unit
    def test_video_upload_validates_plugin(self, mock_plugin_service):
        """POST /v1/video/upload should reject invalid plugin_id."""
        mock_registry = MagicMock()
        mock_registry.get.return_value = None  # Plugin not found

        def override_get_plugin_manager():
            return mock_registry

        def override_get_plugin_service():
            return mock_plugin_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        mp4_data = b"ftypmp42" + b"\x00" * 100

        response = client.post(
            "/v1/video/upload",
            files={"file": ("test.mp4", mp4_data)},
            params={"plugin_id": "nonexistent"},
        )

        app.dependency_overrides.clear()

        assert response.status_code == 400


# =============================================================================
# TDD: POST /v1/video/job - JSON body with video_path and lockedTools
# =============================================================================


class TestVideoJobEndpoint:
    """Tests for /video/job endpoint accepting JSON body (v0.10.1)."""

    @pytest.mark.unit
    def test_video_job_accepts_json_body(self, mock_plugin_registry, mock_plugin_service):
        """POST /v1/video/job should accept JSON body with video_path and lockedTools."""
        from unittest.mock import patch

        def override_get_plugin_manager():
            return mock_plugin_registry

        def override_get_plugin_service():
            return mock_plugin_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        # Mock storage.file_exists to return True
        with patch("app.api_routes.routes.video_submit.storage.file_exists", return_value=True):
            response = client.post(
                "/v1/video/job",
                json={
                    "plugin_id": "yolo-tracker",
                    "video_path": "video/input/test-video.mp4",
                    "lockedTools": ["video_player_tracking"],
                },
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

    @pytest.mark.unit
    def test_video_job_validates_tools(self, mock_plugin_registry, mock_manifest):
        """POST /v1/video/job should validate tools exist in plugin."""
        mock_service = MagicMock()
        mock_service.get_available_tools.return_value = ["different_tool"]
        mock_service.get_plugin_manifest.return_value = mock_manifest

        def override_get_plugin_manager():
            return mock_plugin_registry

        def override_get_plugin_service():
            return mock_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        response = client.post(
            "/v1/video/job",
            json={
                "plugin_id": "yolo-tracker",
                "video_path": "video/input/test-video.mp4",
                "lockedTools": ["invalid_tool"],
            },
        )

        app.dependency_overrides.clear()

        assert response.status_code == 400

    @pytest.mark.unit
    def test_video_job_requires_video_path(self, mock_plugin_registry, mock_plugin_service):
        """POST /v1/video/job should require video_path in JSON body."""
        def override_get_plugin_manager():
            return mock_plugin_registry

        def override_get_plugin_service():
            return mock_plugin_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        response = client.post(
            "/v1/video/job",
            json={
                "plugin_id": "yolo-tracker",
                "lockedTools": ["video_player_tracking"],
            },
        )

        app.dependency_overrides.clear()

        assert response.status_code == 422  # Validation error

    @pytest.mark.unit
    def test_video_job_requires_locked_tools(self, mock_plugin_registry, mock_plugin_service):
        """POST /v1/video/job should require lockedTools in JSON body."""
        def override_get_plugin_manager():
            return mock_plugin_registry

        def override_get_plugin_service():
            return mock_plugin_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        response = client.post(
            "/v1/video/job",
            json={
                "plugin_id": "yolo-tracker",
                "video_path": "video/input/test-video.mp4",
            },
        )

        app.dependency_overrides.clear()

        assert response.status_code == 422  # Validation error
