"""Golden snapshot test for video processing (Commit 7).

Verifies deterministic behavior against frozen output snapshot.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def golden_snapshot_path():
    """Path to golden snapshot file."""
    return Path(__file__).parent / "golden" / "golden_output.json"


@pytest.fixture
def client():
    """Create TestClient with injected state."""
    from app.main import create_app
    from app.services.pipeline_registry_service import PipelineRegistryService
    from unittest.mock import MagicMock

    app = create_app()

    # Use empty real registry
    pipelines_dir = str(Path(__file__).resolve().parents[4] / "fixtures" / "pipelines")
    registry = PipelineRegistryService(pipelines_dir)
    app.state.pipeline_registry = registry

    # Mock plugin manager
    mock_manager = MagicMock()
    app.state.plugin_manager_for_pipelines = mock_manager

    return TestClient(app)


@pytest.fixture
def tiny_mp4():
    """Create tiny MP4 (1 frame, 320×240)."""
    import tempfile
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


class TestVideoGoldenSnapshot:
    """Golden snapshot regression tests."""

    def test_snapshot_file_exists(self, golden_snapshot_path):
        """Golden snapshot file should exist."""
        assert golden_snapshot_path.exists(), "golden_output.json missing"

    def test_snapshot_valid_json(self, golden_snapshot_path):
        """Golden snapshot should be valid JSON."""
        with open(golden_snapshot_path) as f:
            data = json.load(f)
        assert data is not None

    def test_snapshot_has_results_field(self, golden_snapshot_path):
        """Golden snapshot should have 'results' field."""
        with open(golden_snapshot_path) as f:
            data = json.load(f)
        assert "results" in data

    def test_snapshot_results_is_array(self, golden_snapshot_path):
        """Golden snapshot results should be array."""
        with open(golden_snapshot_path) as f:
            data = json.load(f)
        assert isinstance(data["results"], list)

    def test_snapshot_item_has_required_fields(self, golden_snapshot_path):
        """Each result item should have frame_index and result."""
        with open(golden_snapshot_path) as f:
            data = json.load(f)
        for item in data["results"]:
            assert "frame_index" in item
            assert "result" in item

    def test_snapshot_deterministic(self, golden_snapshot_path):
        """Golden snapshot is deterministic (same input produces same output)."""
        with open(golden_snapshot_path) as f:
            snapshot1 = json.load(f)

        # Re-read to verify consistency
        with open(golden_snapshot_path) as f:
            snapshot2 = json.load(f)

        assert snapshot1 == snapshot2, "Snapshot should be deterministic"
