"""Tests for video submission endpoint."""

from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.unit
def test_submit_video_success(session):
    """Test successful video submission."""
    client = TestClient(app)

    # Create a fake MP4 file (magic bytes: ftyp)
    mp4_data = b"ftypmp42" + b"\x00" * 100

    response = client.post(
        "/v1/video/submit",
        files={"file": ("test.mp4", BytesIO(mp4_data))},
        params={"plugin_id": "yolo-tracker", "tool": "video_track"},
    )

    assert response.status_code == 200
    assert "job_id" in response.json()


@pytest.mark.unit
def test_submit_video_invalid_mp4():
    """Test submission with invalid MP4 file."""
    client = TestClient(app)

    # Invalid file (no ftyp magic bytes)
    invalid_data = b"invalid video data"

    response = client.post(
        "/v1/video/submit",
        files={"file": ("test.mp4", BytesIO(invalid_data))},
        params={"plugin_id": "yolo-tracker", "tool": "video_track"},
    )

    assert response.status_code == 400


@pytest.mark.unit
def test_submit_video_missing_plugin_id():
    """Test submission without plugin_id returns 422."""
    client = TestClient(app)

    mp4_data = b"ftypmp42" + b"\x00" * 100

    response = client.post(
        "/v1/video/submit",
        files={"file": ("test.mp4", BytesIO(mp4_data))},
    )

    # Should fail because plugin_id is required
    assert response.status_code == 422
