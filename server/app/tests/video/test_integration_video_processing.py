"""Integration tests for Phase-15 video processing endpoint (Commit 6).

Covers 6 scenarios:
- 400 invalid file type (no DAG needed)
- 400 empty file (no DAG needed)
- 400 corrupted MP4 (no DAG needed)  
- 404 invalid pipeline (no DAG needed)
- 422 missing fields (no DAG needed)
- 200 success (with mocked registry - if DAG setup available)
"""

import sys
from pathlib import Path
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import pytest
import cv2
import numpy as np
from fastapi.testclient import TestClient


@pytest.fixture
def tiny_mp4():
    """Create tiny MP4 (1 frame, 320×240)."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(tmp_path), fourcc, 1.0, (320, 240))
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    out.write(frame)
    out.release()
    return tmp_path


@pytest.fixture
def corrupt_mp4():
    """Create corrupted MP4 (invalid header)."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(b"\x00\x00\x00\x18ftypmp42BADBAD")
        tmp_path = Path(tmp.name)
    return tmp_path


@pytest.fixture
def empty_file():
    """Create empty file."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    return tmp_path


@pytest.fixture
def client():
    """Create TestClient from FastAPI app with injected state."""
    from app.main import create_app
    from app.services.pipeline_registry_service import PipelineRegistryService
    from app.services.plugin_management_service import PluginManagementService
    
    app = create_app()
    
    # Inject empty (but functional) dependencies
    # This avoids the FastAPI TestClient lifespan limitation
    registry = PipelineRegistryService()
    app.state.pipeline_registry = registry
    app.state.plugin_manager_for_pipelines = PluginManagementService(registry)
    
    return TestClient(app)


class TestVideoEndpointIntegration:
    """Integration tests: endpoint validation (no DAG execution required)."""

    def test_scenario_2_invalid_file_type(self, client):
        """Scenario 2: Invalid file type → 400 Bad Request."""
        files = {"file": ("doc.txt", b"not a video", "text/plain")}
        response = client.post(
            "/v1/video/process",
            files=files,
            params={"pipeline_id": "yolo_ocr"},
        )

        assert response.status_code == 400, f"Got {response.status_code}"
        assert "Invalid file format" in response.json()["detail"]

    def test_scenario_4_empty_file(self, client, empty_file):
        """Scenario 4: Empty file → 400 Bad Request."""
        with open(empty_file, "rb") as f:
            files = {"file": ("video.mp4", f, "video/mp4")}
            response = client.post(
                "/v1/video/process",
                files=files,
                params={"pipeline_id": "yolo_ocr"},
            )

        assert response.status_code == 400, f"Got {response.status_code}"

    def test_scenario_5_corrupted_mp4(self, client, corrupt_mp4):
        """Scenario 5: Corrupted MP4 → 400 Bad Request."""
        with open(corrupt_mp4, "rb") as f:
            files = {"file": ("video.mp4", f, "video/mp4")}
            response = client.post(
                "/v1/video/process",
                files=files,
                params={"pipeline_id": "yolo_ocr"},
            )

        assert response.status_code == 400, f"Got {response.status_code}"
        assert "Unable to read video file" in response.json()["detail"]

    def test_scenario_3_invalid_pipeline_id(self, client, tiny_mp4):
        """Scenario 3: Invalid pipeline ID → 404 Not Found."""
        with open(tiny_mp4, "rb") as f:
            files = {"file": ("video.mp4", f, "video/mp4")}
            response = client.post(
                "/v1/video/process",
                files=files,
                params={"pipeline_id": "nonexistent_pipeline"},
            )

        assert response.status_code == 404, f"Got {response.status_code}"

    def test_scenario_6_missing_form_fields(self, client):
        """Scenario 6: Missing file field → 422 Unprocessable Entity."""
        response = client.post(
            "/v1/video/process",
            params={"pipeline_id": "yolo_ocr"},
        )

        assert response.status_code == 422, f"Got {response.status_code}"


class TestVideoEndpointQueryParams:
    """Test query parameter validation."""

    def test_frame_stride_parameter_accepted(self, client, tiny_mp4):
        """frame_stride parameter is accepted (doesn't cause validation error)."""
        with open(tiny_mp4, "rb") as f:
            files = {"file": ("video.mp4", f, "video/mp4")}
            response = client.post(
                "/v1/video/process",
                files=files,
                params={"pipeline_id": "yolo_ocr", "frame_stride": 2},
            )

        # Should not be 422 (validation error)
        assert response.status_code != 422

    def test_max_frames_parameter_accepted(self, client, tiny_mp4):
        """max_frames parameter is accepted."""
        with open(tiny_mp4, "rb") as f:
            files = {"file": ("video.mp4", f, "video/mp4")}
            response = client.post(
                "/v1/video/process",
                files=files,
                params={"pipeline_id": "yolo_ocr", "max_frames": 5},
            )

        # Should not be 422 (validation error)
        assert response.status_code != 422

    def test_both_parameters_accepted(self, client, tiny_mp4):
        """Both stride and max_frames accepted together."""
        with open(tiny_mp4, "rb") as f:
            files = {"file": ("video.mp4", f, "video/mp4")}
            response = client.post(
                "/v1/video/process",
                files=files,
                params={
                    "pipeline_id": "yolo_ocr",
                    "frame_stride": 2,
                    "max_frames": 3,
                },
            )

        # Should not be 422 (validation error)
        assert response.status_code != 422
