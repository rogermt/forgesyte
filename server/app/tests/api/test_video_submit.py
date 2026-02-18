"""Tests for /v1/video/submit endpoint (v0.9.0).

TDD approach: Write failing tests first, then implement.
"""

import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


@pytest.fixture
def tiny_mp4():
    """Create tiny MP4 (1 frame, 320×240) with valid MP4 magic bytes."""
    import cv2
    import numpy as np

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(tmp_path), fourcc, 1.0, (320, 240))
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    out.write(frame)
    out.release()
    return tmp_path


@pytest.fixture
def client():
    """Create TestClient from FastAPI app."""
    from app.main import create_app

    app = create_app()
    return TestClient(app)


class TestVideoSubmitOptionalPipelineId:
    """Tests for making pipeline_id optional with default 'ocr_only'."""

    def test_submit_without_pipeline_id_uses_default(self, client, tiny_mp4):
        """Test: Submit without pipeline_id → uses default 'ocr_only'."""
        # Submit without pipeline_id
        with open(tiny_mp4, "rb") as f:
            response = client.post(
                "/v1/video/submit",
                files={"file": ("video.mp4", f, "video/mp4")},
            )

        # Should succeed
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert isinstance(data["job_id"], str)
        assert len(data["job_id"]) > 0

    def test_submit_with_explicit_pipeline_id(self, client, tiny_mp4):
        """Test: Submit with explicit pipeline_id='yolo_ocr' → uses specified."""
        # Submit with explicit pipeline_id
        with open(tiny_mp4, "rb") as f:
            response = client.post(
                "/v1/video/submit",
                files={"file": ("video.mp4", f, "video/mp4")},
                params={"pipeline_id": "yolo_ocr"},
            )

        # Should succeed
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

    def test_submit_with_invalid_pipeline_id(self, client, tiny_mp4):
        """Test: Submit with invalid pipeline_id → still creates job (validation happens later)."""
        # Submit with invalid pipeline_id
        with open(tiny_mp4, "rb") as f:
            response = client.post(
                "/v1/video/submit",
                files={"file": ("video.mp4", f, "video/mp4")},
                params={"pipeline_id": "invalid_pipeline"},
            )

        # Should still succeed (validation happens in worker)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
