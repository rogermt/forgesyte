"""Tests for video_submit endpoint.

Tests verify:
1. Plugin validation works with properly loaded registry (Issue #209)
2. Tool validation uses Plugin.tools (canonical source, not manifest)
3. Error handling for invalid plugin/tool
4. v0.9.8: Multi-tool support with video_multi job type
5. v0.9.8: Mutual exclusivity check (tool vs logical_tool_id)
6. v0.9.8: Canonical JSON response
"""

import json
from io import BytesIO
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api_routes.routes.video_submit import get_plugin_manager, get_plugin_service
from app.main import app
from app.models.job import Job


@pytest.fixture
def mock_plugin():
    """Create a mock plugin with tools attribute.

    NOTE: plugin.tools uses ToolSchema which forbids input_types (extra="forbid").
    So we don't include input_types here - it comes from the manifest.
    """
    plugin = MagicMock()
    plugin.name = "yolo-tracker"
    plugin.tools = {
        "video_player_tracking": {
            "handler": "player_tracking_handler",
            "description": "Track players in video",
            "input_schema": {"properties": {"video_path": {"type": "string"}}},
            "output_schema": {"properties": {"detections": {"type": "array"}}},
        },
        "video_ball_detection": {
            "handler": "ball_detection_handler",
            "description": "Detect ball in video",
            "input_schema": {"properties": {"video_path": {"type": "string"}}},
            "output_schema": {"properties": {"detections": {"type": "array"}}},
        },
    }
    return plugin


@pytest.fixture
def mock_manifest():
    """Create a mock manifest with input_types.

    The manifest.json file contains input_types which plugin.tools cannot have
    due to ToolSchema's extra="forbid" restriction.
    """
    return {
        "id": "yolo-tracker",
        "name": "YOLO Tracker",
        "version": "1.0.0",
        "capabilities": ["player_detection", "ball_detection"],
        "tools": [
            {
                "id": "video_player_tracking",
                "title": "Player Tracking (Video)",
                "description": "Track players",
                "input_types": ["video"],
                "output_types": ["detections"],
                "capabilities": ["player_detection"],
            },
            {
                "id": "video_ball_detection",
                "title": "Ball Detection (Video)",
                "description": "Detect ball",
                "input_types": ["video"],
                "output_types": ["detections"],
                "capabilities": ["ball_detection"],
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


@pytest.mark.unit
def test_submit_video_success(
    session: Session, mock_plugin_registry, mock_plugin_service
):
    """Test video submission with valid MP4 file."""

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
        "/v1/video/submit",
        files={"file": ("test.mp4", BytesIO(mp4_data))},
        params={"plugin_id": "yolo-tracker", "tool": "video_player_tracking"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data


@pytest.mark.unit
def test_submit_video_invalid_plugin(mock_plugin_service):
    """Test video submission with invalid plugin returns 400."""
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
        "/v1/video/submit",
        files={"file": ("test.mp4", BytesIO(mp4_data))},
        params={"plugin_id": "nonexistent", "tool": "video_player_tracking"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400


@pytest.mark.unit
def test_submit_video_invalid_tool(mock_plugin, mock_plugin_registry, mock_manifest):
    """Test video submission with invalid tool returns 400."""
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

    mp4_data = b"ftypmp42" + b"\x00" * 100

    response = client.post(
        "/v1/video/submit",
        files={"file": ("test.mp4", BytesIO(mp4_data))},
        params={"plugin_id": "yolo-tracker", "tool": "invalid_tool"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400


@pytest.mark.unit
def test_submit_video_invalid_file_format(mock_plugin_registry, mock_plugin_service):
    """Test video submission with invalid file format returns 400."""

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
        "/v1/video/submit",
        files={"file": ("test.txt", BytesIO(invalid_data))},
        params={"plugin_id": "yolo-tracker", "tool": "video_player_tracking"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400


# =============================================================================
# v0.9.8: Multi-tool support tests (TDD Red Phase)
# =============================================================================


class TestVideoSubmitMutualExclusivity:
    """Tests for tool vs logical_tool_id mutual exclusivity (v0.9.8)."""

    def test_mutual_exclusivity_tool_and_logical_tool_id(self, mock_plugin):
        """400 if both tool and logical_tool_id provided."""
        mock_registry = MagicMock()
        mock_registry.get.return_value = mock_plugin

        mock_service = MagicMock()
        mock_service.get_available_tools.return_value = list(mock_plugin.tools.keys())

        def override_get_plugin_manager():
            return mock_registry

        def override_get_plugin_service():
            return mock_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        mp4_data = b"ftypmp42" + b"\x00" * 100

        response = client.post(
            "/v1/video/submit",
            files={"file": ("test.mp4", BytesIO(mp4_data))},
            params={
                "plugin_id": "yolo-tracker",
                "tool": "video_player_tracking",
                "logical_tool_id": "player_detection",
            },
        )

        app.dependency_overrides.clear()

        assert response.status_code == 400
        assert "mutually exclusive" in response.json()["detail"].lower()


class TestVideoSubmitMultiTool:
    """Tests for multi-tool video submission (v0.9.8)."""

    def test_video_multi_job_type(self, session: Session):
        """Multiple tools creates video_multi job_type."""
        # Create plugin with two video tools
        plugin = MagicMock()
        plugin.tools = {
            "video_player_tracking": {
                "handler": "player_tracking_handler",
                "input_schema": {"properties": {"video_path": {"type": "string"}}},
            },
            "video_ball_detection": {
                "handler": "ball_detection_handler",
                "input_schema": {"properties": {"video_path": {"type": "string"}}},
            },
        }

        mock_registry = MagicMock()
        mock_registry.get.return_value = plugin

        mock_service = MagicMock()
        mock_service.get_available_tools.return_value = [
            "video_player_tracking",
            "video_ball_detection",
        ]
        mock_service.get_plugin_manifest.return_value = {
            "tools": [
                {
                    "id": "video_player_tracking",
                    "input_types": ["video"],
                    "capabilities": ["player_detection"],
                },
                {
                    "id": "video_ball_detection",
                    "input_types": ["video"],
                    "capabilities": ["ball_detection"],
                },
            ]
        }

        def override_get_plugin_manager():
            return mock_registry

        def override_get_plugin_service():
            return mock_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        mp4_data = b"ftypmp42" + b"\x00" * 100

        response = client.post(
            "/v1/video/submit",
            files={"file": ("test.mp4", BytesIO(mp4_data))},
            params={
                "plugin_id": "yolo-tracker",
                "logical_tool_id": ["player_detection", "ball_detection"],
            },
        )

        app.dependency_overrides.clear()

        assert response.status_code == 200, f"Got: {response.text}"
        data = response.json()
        assert "job_id" in data

        # Verify job was created with video_multi type
        job_id = data["job_id"]
        job = session.query(Job).filter(Job.job_id == job_id).first()
        assert job is not None
        assert job.job_type == "video_multi"

    def test_video_multi_tool_list(self, session: Session):
        """tool_list JSON field populated for multi-tool."""
        plugin = MagicMock()
        plugin.tools = {
            "video_player_tracking": {
                "handler": "player_tracking_handler",
                "input_schema": {"properties": {"video_path": {"type": "string"}}},
            },
            "video_ball_detection": {
                "handler": "ball_detection_handler",
                "input_schema": {"properties": {"video_path": {"type": "string"}}},
            },
        }

        mock_registry = MagicMock()
        mock_registry.get.return_value = plugin

        mock_service = MagicMock()
        mock_service.get_available_tools.return_value = [
            "video_player_tracking",
            "video_ball_detection",
        ]
        mock_service.get_plugin_manifest.return_value = {
            "tools": [
                {
                    "id": "video_player_tracking",
                    "input_types": ["video"],
                    "capabilities": ["player_detection"],
                },
                {
                    "id": "video_ball_detection",
                    "input_types": ["video"],
                    "capabilities": ["ball_detection"],
                },
            ]
        }

        def override_get_plugin_manager():
            return mock_registry

        def override_get_plugin_service():
            return mock_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        mp4_data = b"ftypmp42" + b"\x00" * 100

        response = client.post(
            "/v1/video/submit",
            files={"file": ("test.mp4", BytesIO(mp4_data))},
            params={
                "plugin_id": "yolo-tracker",
                "logical_tool_id": ["player_detection", "ball_detection"],
            },
        )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        job_id = data["job_id"]
        job = session.query(Job).filter(Job.job_id == job_id).first()

        # tool_list should be a JSON array
        assert job.tool_list is not None
        tool_list = json.loads(job.tool_list)
        assert "video_player_tracking" in tool_list
        assert "video_ball_detection" in tool_list


class TestVideoSubmitCanonicalJson:
    """Tests for canonical JSON response (v0.9.8)."""

    def test_canonical_json_single_tool(self, session: Session):
        """Response should include tool field for single-tool."""
        plugin = MagicMock()
        plugin.tools = {
            "video_player_tracking": {
                "handler": "player_tracking_handler",
                "input_schema": {"properties": {"video_path": {"type": "string"}}},
            }
        }

        mock_registry = MagicMock()
        mock_registry.get.return_value = plugin

        mock_service = MagicMock()
        mock_service.get_available_tools.return_value = ["video_player_tracking"]
        mock_service.get_plugin_manifest.return_value = {
            "tools": [
                {
                    "id": "video_player_tracking",
                    "input_types": ["video"],
                    "capabilities": ["player_detection"],
                },
            ]
        }

        def override_get_plugin_manager():
            return mock_registry

        def override_get_plugin_service():
            return mock_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        mp4_data = b"ftypmp42" + b"\x00" * 100

        response = client.post(
            "/v1/video/submit",
            files={"file": ("test.mp4", BytesIO(mp4_data))},
            params={
                "plugin_id": "yolo-tracker",
                "logical_tool_id": "player_detection",
            },
        )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()

        # Canonical JSON for single-tool
        assert "tool" in data
        assert data["tool"] == "video_player_tracking"
        assert "tools" not in data  # Should NOT have tools array for single
        assert "submitted_at" in data
        assert data["status"] == "queued"

    def test_canonical_json_multi_tool(self, session: Session):
        """Response should include tools array for multi-tool."""
        plugin = MagicMock()
        plugin.tools = {
            "video_player_tracking": {
                "handler": "player_tracking_handler",
                "input_schema": {"properties": {"video_path": {"type": "string"}}},
            },
            "video_ball_detection": {
                "handler": "ball_detection_handler",
                "input_schema": {"properties": {"video_path": {"type": "string"}}},
            },
        }

        mock_registry = MagicMock()
        mock_registry.get.return_value = plugin

        mock_service = MagicMock()
        mock_service.get_available_tools.return_value = [
            "video_player_tracking",
            "video_ball_detection",
        ]
        mock_service.get_plugin_manifest.return_value = {
            "tools": [
                {
                    "id": "video_player_tracking",
                    "input_types": ["video"],
                    "capabilities": ["player_detection"],
                },
                {
                    "id": "video_ball_detection",
                    "input_types": ["video"],
                    "capabilities": ["ball_detection"],
                },
            ]
        }

        def override_get_plugin_manager():
            return mock_registry

        def override_get_plugin_service():
            return mock_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        mp4_data = b"ftypmp42" + b"\x00" * 100

        response = client.post(
            "/v1/video/submit",
            files={"file": ("test.mp4", BytesIO(mp4_data))},
            params={
                "plugin_id": "yolo-tracker",
                "logical_tool_id": ["player_detection", "ball_detection"],
            },
        )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()

        # Canonical JSON for multi-tool
        assert "tools" in data
        assert len(data["tools"]) == 2
        assert data["tools"][0]["logical"] == "player_detection"
        assert data["tools"][0]["resolved"] == "video_player_tracking"
        assert data["tools"][1]["logical"] == "ball_detection"
        assert data["tools"][1]["resolved"] == "video_ball_detection"
        assert "submitted_at" in data
        assert data["status"] == "queued"
