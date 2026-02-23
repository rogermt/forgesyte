"""Tests for video submission endpoint with plugin_id and tool params."""

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
    plugin.name = "ocr"
    plugin.tools = {
        "analyze": {
            "handler": "analyze_handler",
            "description": "Extract text",
            "input_schema": {"properties": {"video_path": {"type": "string"}}},
            "output_schema": {},
        },
        "video_track": {
            "handler": "video_track_handler",
            "description": "Track video",
            "input_schema": {"properties": {"video_path": {"type": "string"}}},
            "output_schema": {},
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
        "id": "ocr",
        "name": "OCR",
        "version": "1.0.0",
        "tools": [
            {
                "id": "analyze",
                "title": "Analyze",
                "description": "Extract text",
                "input_types": ["video"],  # v0.9.5: Video input support
                "output_types": ["text"],
            },
            {
                "id": "video_track",
                "title": "Video Track",
                "description": "Track video",
                "input_types": ["video"],  # v0.9.5: Video input support
                "output_types": ["tracks"],
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
def test_submit_with_plugin_id_and_tool_returns_200(
    session, mock_plugin_registry, mock_plugin_service
):
    """Test POST /v1/video/submit with plugin_id and tool returns 200."""

    def override_get_plugin_manager():
        return mock_plugin_registry

    def override_get_plugin_service():
        return mock_plugin_service

    app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
    app.dependency_overrides[get_plugin_service] = override_get_plugin_service

    client = TestClient(app)

    mp4_data = b"ftypmp42" + b"\x00" * 100

    response = client.post(
        "/v1/video/submit",
        files={"file": ("test.mp4", BytesIO(mp4_data))},
        params={"plugin_id": "ocr", "tool": "analyze"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "job_id" in response.json()


@pytest.mark.unit
def test_submit_stores_plugin_id_in_job(
    session: Session, mock_plugin, mock_plugin_registry, mock_manifest
):
    """Test plugin_id is stored in Job record."""
    mock_service = MagicMock()
    mock_service.get_available_tools.return_value = list(mock_plugin.tools.keys())
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
        params={"plugin_id": "yolo-tracker", "tool": "video_track"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # Verify plugin_id was stored
    job = session.query(Job).filter(Job.job_id == job_id).first()
    assert job is not None
    assert job.plugin_id == "yolo-tracker"


@pytest.mark.unit
def test_submit_stores_tool_in_job(
    session: Session, mock_plugin_registry, mock_plugin_service
):
    """Test tool is stored in Job record."""

    def override_get_plugin_manager():
        return mock_plugin_registry

    def override_get_plugin_service():
        return mock_plugin_service

    app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
    app.dependency_overrides[get_plugin_service] = override_get_plugin_service

    client = TestClient(app)

    mp4_data = b"ftypmp42" + b"\x00" * 100

    response = client.post(
        "/v1/video/submit",
        files={"file": ("test.mp4", BytesIO(mp4_data))},
        params={"plugin_id": "ocr", "tool": "analyze"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # Verify tool was stored
    job = session.query(Job).filter(Job.job_id == job_id).first()
    assert job is not None
    assert job.tool == "analyze"


@pytest.mark.unit
def test_submit_missing_plugin_id_returns_422():
    """Test POST without plugin_id returns 422."""
    client = TestClient(app)

    mp4_data = b"ftypmp42" + b"\x00" * 100

    response = client.post(
        "/v1/video/submit",
        files={"file": ("test.mp4", BytesIO(mp4_data))},
        params={"tool": "analyze"},  # Missing plugin_id
    )

    assert response.status_code == 422


@pytest.mark.unit
def test_submit_missing_tool_returns_422():
    """Test POST without tool returns 422."""
    client = TestClient(app)

    mp4_data = b"ftypmp42" + b"\x00" * 100

    response = client.post(
        "/v1/video/submit",
        files={"file": ("test.mp4", BytesIO(mp4_data))},
        params={"plugin_id": "ocr"},  # Missing tool
    )

    assert response.status_code == 422
