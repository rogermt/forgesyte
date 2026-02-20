"""Tests for video submission endpoint with plugin_id and tool params."""

from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.unit
def test_submit_with_plugin_id_and_tool_returns_200(session):
    """Test POST /v1/video/submit with plugin_id and tool returns 200."""
    client = TestClient(app)

    mp4_data = b"ftypmp42" + b"\x00" * 100

    response = client.post(
        "/v1/video/submit",
        files={"file": ("test.mp4", BytesIO(mp4_data))},
        params={"plugin_id": "ocr", "tool": "extract_text"},
    )

    assert response.status_code == 200
    assert "job_id" in response.json()


@pytest.mark.unit
def test_submit_stores_plugin_id_in_job(session):
    """Test plugin_id is stored in Job record."""
    from app.models.job import Job

    client = TestClient(app)

    mp4_data = b"ftypmp42" + b"\x00" * 100

    response = client.post(
        "/v1/video/submit",
        files={"file": ("test.mp4", BytesIO(mp4_data))},
        params={"plugin_id": "yolo-tracker", "tool": "video_track"},
    )

    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # Verify plugin_id was stored
    job = session.query(Job).filter(Job.job_id == job_id).first()
    assert job is not None
    assert job.plugin_id == "yolo-tracker"


@pytest.mark.unit
def test_submit_stores_tool_in_job(session):
    """Test tool is stored in Job record."""
    from app.models.job import Job

    client = TestClient(app)

    mp4_data = b"ftypmp42" + b"\x00" * 100

    response = client.post(
        "/v1/video/submit",
        files={"file": ("test.mp4", BytesIO(mp4_data))},
        params={"plugin_id": "ocr", "tool": "extract_text"},
    )

    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # Verify tool was stored
    job = session.query(Job).filter(Job.job_id == job_id).first()
    assert job is not None
    assert job.tool == "extract_text"


@pytest.mark.unit
def test_submit_missing_plugin_id_returns_422():
    """Test POST without plugin_id returns 422."""
    client = TestClient(app)

    mp4_data = b"ftypmp42" + b"\x00" * 100

    response = client.post(
        "/v1/video/submit",
        files={"file": ("test.mp4", BytesIO(mp4_data))},
        params={"tool": "extract_text"},  # Missing plugin_id
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
