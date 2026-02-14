"""Unit tests for VideoFilePipelineService (Phase 15).

Tests cover:
- Happy path (frame extraction, DAG calls, result aggregation)
- Stride and max_frames options
- Error handling (missing files, corrupted MP4, pipeline errors)
- Robustness (frame ordering, JPEG encoding, resource cleanup)

All tests use MockDagPipelineService (no real plugins).
"""

import sys
from pathlib import Path

import pytest

# Add parent dirs to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.video_file_pipeline_service import VideoFilePipelineService
from app.tests.video.fakes.corrupt_mp4_generator import (
    create_corrupt_mp4_header_only,
    create_corrupt_mp4_random_bytes,
    create_corrupt_mp4_truncated,
)
from app.tests.video.fakes.mock_dag_service import MockDagPipelineService


@pytest.fixture
def tiny_mp4() -> Path:
    """Path to tiny.mp4 fixture (3 frames, 320×240)."""
    # Path from test file: test_video_service_unit.py
    # → app/tests/video/test_video_service_unit.py
    # → parent[0] = app/tests/video
    # → parent[1] = app/tests
    # → fixtures is in app/tests/fixtures
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "tiny.mp4"
    assert fixture_path.exists(), f"tiny.mp4 not found at {fixture_path}"
    return fixture_path


@pytest.fixture
def mock_dag() -> MockDagPipelineService:
    """Default mock DAG service (no failures)."""
    return MockDagPipelineService(fail_mode=None)


@pytest.fixture
def service(mock_dag: MockDagPipelineService) -> VideoFilePipelineService:
    """VideoFilePipelineService with mock DAG."""
    return VideoFilePipelineService(mock_dag)


class TestVideoServiceHappyPath:
    """Happy path tests: valid MP4, successful pipeline execution."""

    def test_processes_tiny_mp4_single_frame(
        self, service: VideoFilePipelineService, tiny_mp4: Path
    ) -> None:
        """Process single frame from tiny.mp4."""
        results = service.run_on_file(str(tiny_mp4), "yolo_ocr", max_frames=1)

        assert len(results) == 1
        assert results[0]["frame_index"] == 0
        assert "result" in results[0]
        assert "detections" in results[0]["result"]

    def test_processes_all_three_frames(
        self, service: VideoFilePipelineService, tiny_mp4: Path
    ) -> None:
        """Process all 3 frames from tiny.mp4."""
        results = service.run_on_file(str(tiny_mp4), "yolo_ocr")

        assert len(results) == 3
        assert results[0]["frame_index"] == 0
        assert results[1]["frame_index"] == 1
        assert results[2]["frame_index"] == 2

    def test_returns_correct_frame_indices(
        self, service: VideoFilePipelineService, tiny_mp4: Path
    ) -> None:
        """Verify frame_index in result matches extraction order."""
        results = service.run_on_file(str(tiny_mp4), "yolo_ocr")

        for i, result in enumerate(results):
            assert result["frame_index"] == i

    def test_result_contains_pipeline_output(
        self, service: VideoFilePipelineService, tiny_mp4: Path
    ) -> None:
        """Verify result structure contains pipeline output."""
        results = service.run_on_file(str(tiny_mp4), "yolo_ocr", max_frames=1)

        assert "result" in results[0]
        assert isinstance(results[0]["result"], dict)
        assert "detections" in results[0]["result"]
        assert "text" in results[0]["result"]


class TestVideoServiceStride:
    """Test frame_stride option (skip frames)."""

    def test_applies_stride_2(
        self, service: VideoFilePipelineService, tiny_mp4: Path
    ) -> None:
        """Process every 2nd frame (0, 2)."""
        results = service.run_on_file(str(tiny_mp4), "yolo_ocr", frame_stride=2)

        assert len(results) == 2
        assert results[0]["frame_index"] == 0
        assert results[1]["frame_index"] == 2

    def test_applies_stride_3(
        self, service: VideoFilePipelineService, tiny_mp4: Path
    ) -> None:
        """Process every 3rd frame (0)."""
        results = service.run_on_file(str(tiny_mp4), "yolo_ocr", frame_stride=3)

        assert len(results) == 1
        assert results[0]["frame_index"] == 0

    def test_stride_larger_than_video(
        self, service: VideoFilePipelineService, tiny_mp4: Path
    ) -> None:
        """Stride larger than frame count returns only frame 0."""
        results = service.run_on_file(str(tiny_mp4), "yolo_ocr", frame_stride=10)

        assert len(results) == 1
        assert results[0]["frame_index"] == 0


class TestVideoServiceMaxFrames:
    """Test max_frames option (frame limit)."""

    def test_respects_max_frames_1(
        self, service: VideoFilePipelineService, tiny_mp4: Path
    ) -> None:
        """max_frames=1 returns only 1 result."""
        results = service.run_on_file(str(tiny_mp4), "yolo_ocr", max_frames=1)

        assert len(results) == 1
        assert results[0]["frame_index"] == 0

    def test_respects_max_frames_2(
        self, service: VideoFilePipelineService, tiny_mp4: Path
    ) -> None:
        """max_frames=2 returns only 2 results."""
        results = service.run_on_file(str(tiny_mp4), "yolo_ocr", max_frames=2)

        assert len(results) == 2
        assert results[0]["frame_index"] == 0
        assert results[1]["frame_index"] == 1

    def test_max_frames_larger_than_video(
        self, service: VideoFilePipelineService, tiny_mp4: Path
    ) -> None:
        """max_frames larger than frame count returns all frames."""
        results = service.run_on_file(str(tiny_mp4), "yolo_ocr", max_frames=10)

        assert len(results) == 3  # tiny.mp4 has 3 frames


class TestVideoServiceCombined:
    """Test stride + max_frames together."""

    def test_stride_2_max_frames_1(
        self, service: VideoFilePipelineService, tiny_mp4: Path
    ) -> None:
        """stride=2 max_frames=1 returns frame 0."""
        results = service.run_on_file(
            str(tiny_mp4), "yolo_ocr", frame_stride=2, max_frames=1
        )

        assert len(results) == 1
        assert results[0]["frame_index"] == 0

    def test_stride_and_max_frames_interaction(
        self, service: VideoFilePipelineService, tiny_mp4: Path
    ) -> None:
        """stride=2 max_frames=2 returns frames 0 and 2."""
        results = service.run_on_file(
            str(tiny_mp4), "yolo_ocr", frame_stride=2, max_frames=2
        )

        assert len(results) == 2
        assert results[0]["frame_index"] == 0
        assert results[1]["frame_index"] == 2


class TestVideoServiceErrors:
    """Error handling tests."""

    def test_raises_on_nonexistent_file(
        self, service: VideoFilePipelineService
    ) -> None:
        """Nonexistent file raises ValueError."""
        with pytest.raises(ValueError, match="Unable to read video file"):
            service.run_on_file("/nonexistent/video.mp4", "yolo_ocr")

    def test_raises_on_corrupted_mp4_header_only(
        self, service: VideoFilePipelineService, tmp_path: Path
    ) -> None:
        """Corrupted MP4 (header only) raises ValueError."""
        corrupt_file = tmp_path / "corrupt_header.mp4"
        create_corrupt_mp4_header_only(corrupt_file)

        with pytest.raises(ValueError, match="Unable to read video file"):
            service.run_on_file(str(corrupt_file), "yolo_ocr")

    def test_raises_on_corrupted_mp4_random_bytes(
        self, service: VideoFilePipelineService, tmp_path: Path
    ) -> None:
        """Corrupted MP4 (random bytes) raises ValueError."""
        corrupt_file = tmp_path / "corrupt_random.mp4"
        create_corrupt_mp4_random_bytes(corrupt_file, size=256)

        with pytest.raises(ValueError, match="Unable to read video file"):
            service.run_on_file(str(corrupt_file), "yolo_ocr")

    def test_raises_on_corrupted_mp4_truncated(
        self, service: VideoFilePipelineService, tmp_path: Path
    ) -> None:
        """Corrupted MP4 (truncated) raises ValueError."""
        corrupt_file = tmp_path / "corrupt_truncated.mp4"
        create_corrupt_mp4_truncated(corrupt_file)

        with pytest.raises(ValueError, match="Unable to read video file"):
            service.run_on_file(str(corrupt_file), "yolo_ocr")

    def test_pipeline_not_found_error_propagates(
        self, tiny_mp4: Path, tmp_path: Path
    ) -> None:
        """Pipeline not found error from DAG propagates."""
        mock_dag = MockDagPipelineService(fail_mode="pipeline_not_found")
        service = VideoFilePipelineService(mock_dag)

        with pytest.raises(ValueError, match="not found"):
            service.run_on_file(str(tiny_mp4), "invalid_pipeline")

    def test_plugin_error_propagates(self, tiny_mp4: Path, tmp_path: Path) -> None:
        """Plugin execution error from DAG propagates."""
        mock_dag = MockDagPipelineService(fail_mode="plugin_error")
        service = VideoFilePipelineService(mock_dag)

        with pytest.raises(RuntimeError, match="Plugin execution failed"):
            service.run_on_file(str(tiny_mp4), "yolo_ocr")


class TestVideoServiceRobustness:
    """Robustness and data integrity tests."""

    def test_frames_sequential_no_gaps(
        self, service: VideoFilePipelineService, tiny_mp4: Path
    ) -> None:
        """All frames present, sequential, no gaps."""
        results = service.run_on_file(str(tiny_mp4), "yolo_ocr")

        frame_indices = [r["frame_index"] for r in results]
        assert frame_indices == [0, 1, 2]

    def test_no_duplicate_frames(
        self, service: VideoFilePipelineService, tiny_mp4: Path
    ) -> None:
        """No frame appears twice in results."""
        results = service.run_on_file(str(tiny_mp4), "yolo_ocr")

        frame_indices = [r["frame_index"] for r in results]
        assert len(frame_indices) == len(set(frame_indices))

    def test_jpeg_encoding_produces_bytes(
        self,
        service: VideoFilePipelineService,
        tiny_mp4: Path,
        mock_dag: MockDagPipelineService,
    ) -> None:
        """Verify image_bytes in payload is binary, not string."""
        service.run_on_file(str(tiny_mp4), "yolo_ocr", max_frames=1)

        payload = mock_dag.last_payload
        assert payload is not None
        assert isinstance(payload["image_bytes"], bytes)
        assert len(payload["image_bytes"]) > 0

    def test_frame_index_in_payload_matches_result(
        self,
        service: VideoFilePipelineService,
        tiny_mp4: Path,
        mock_dag: MockDagPipelineService,
    ) -> None:
        """frame_index in payload matches result frame_index."""
        results = service.run_on_file(str(tiny_mp4), "yolo_ocr", max_frames=1)

        payload = mock_dag.last_payload
        assert payload is not None
        assert payload["frame_index"] == results[0]["frame_index"]

    def test_dag_called_once_per_frame(
        self,
        service: VideoFilePipelineService,
        tiny_mp4: Path,
        mock_dag: MockDagPipelineService,
    ) -> None:
        """DAG called exactly once per processed frame."""
        service.run_on_file(str(tiny_mp4), "yolo_ocr")

        assert mock_dag.call_count == 3  # 3 frames in tiny.mp4

    def test_dag_called_respecting_stride(
        self,
        service: VideoFilePipelineService,
        tiny_mp4: Path,
        mock_dag: MockDagPipelineService,
    ) -> None:
        """DAG called only for stride frames."""
        service.run_on_file(str(tiny_mp4), "yolo_ocr", frame_stride=2)

        assert mock_dag.call_count == 2  # frames 0 and 2
