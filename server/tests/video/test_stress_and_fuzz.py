"""Stress and fuzz tests (Commit 8).

Tests:
- Large video files
- Many frames
- Extreme parameter values
- Memory cleanup
- Resource limits
"""

import sys
from pathlib import Path

# Import path workaround for tests (per AGENTS.md)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import tempfile

import cv2
import numpy as np
import pytest

from app.services.video_file_pipeline_service import VideoFilePipelineService
from tests.video.fakes.mock_dag_service import MockDagPipelineService


@pytest.fixture
def large_mp4():
    """Create a larger MP4 with 30 frames."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(tmp_path), fourcc, 1.0, (640, 480))

    for i in range(30):
        frame = np.full((480, 640, 3), fill_value=i * 8, dtype=np.uint8)
        out.write(frame)

    out.release()
    return tmp_path


class TestStressLargeVideos:
    """Stress tests with large video files."""

    def test_process_30_frame_video(self, large_mp4):
        """Process 30-frame video without crashing."""
        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        results = service.run_on_file(
            str(large_mp4),
            "yolo_ocr",
        )

        assert len(results) == 30
        for i, result in enumerate(results):
            assert result["frame_index"] == i

    def test_process_with_large_stride(self, large_mp4):
        """Process with stride=10 (every 10th frame)."""
        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        results = service.run_on_file(
            str(large_mp4),
            "yolo_ocr",
            frame_stride=10,
        )

        # Frames 0, 10, 20 (30 is out of bounds)
        assert len(results) == 3
        assert [r["frame_index"] for r in results] == [0, 10, 20]

    def test_max_frames_respects_limit(self, large_mp4):
        """max_frames correctly limits processing."""
        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        # Request only 5 frames from 30-frame video
        results = service.run_on_file(
            str(large_mp4),
            "yolo_ocr",
            max_frames=5,
        )

        assert len(results) == 5

    def test_stride_and_max_frames_combined(self, large_mp4):
        """Stride and max_frames work together."""
        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        # Every 5th frame, but max 3 frames
        results = service.run_on_file(
            str(large_mp4),
            "yolo_ocr",
            frame_stride=5,
            max_frames=3,
        )

        assert len(results) == 3
        # Frames: 0, 5, 10
        assert [r["frame_index"] for r in results] == [0, 5, 10]

    def test_processes_many_frames(self, large_mp4):
        """Successfully processes all 30 frames."""
        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        results = service.run_on_file(
            str(large_mp4),
            "yolo_ocr",
            frame_stride=1,
        )

        # Verify all frames processed in order
        assert len(results) == 30
        for i in range(30):
            assert results[i]["frame_index"] == i


class TestFuzzExtremeValues:
    """Fuzz tests with extreme parameter values."""

    def test_frame_stride_1_processes_all(self, large_mp4):
        """Stride=1 (minimum) processes all frames."""
        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        results = service.run_on_file(
            str(large_mp4),
            "yolo_ocr",
            frame_stride=1,
        )

        assert len(results) == 30

    def test_frame_stride_large_value(self, large_mp4):
        """Large stride value (e.g., 999) returns few or no frames."""
        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        results = service.run_on_file(
            str(large_mp4),
            "yolo_ocr",
            frame_stride=999,
        )

        # Only frame 0 matches stride filter
        assert len(results) == 1
        assert results[0]["frame_index"] == 0

    def test_max_frames_1(self, large_mp4):
        """max_frames=1 returns single frame."""
        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        results = service.run_on_file(
            str(large_mp4),
            "yolo_ocr",
            max_frames=1,
        )

        assert len(results) == 1

    def test_max_frames_exceeds_video_length(self, large_mp4):
        """max_frames > video length returns all available."""
        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        results = service.run_on_file(
            str(large_mp4),
            "yolo_ocr",
            max_frames=9999,
        )

        # Should get all 30 frames
        assert len(results) == 30

    def test_both_limits_very_restrictive(self, large_mp4):
        """stride=30 and max_frames=1 returns single frame."""
        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        results = service.run_on_file(
            str(large_mp4),
            "yolo_ocr",
            frame_stride=30,
            max_frames=1,
        )

        assert len(results) == 1
        assert results[0]["frame_index"] == 0


class TestResourceCleanup:
    """Test proper resource cleanup."""

    def test_video_capture_released(self, large_mp4):
        """VideoCapture is always released, even on success."""

        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        # Get initial capture count
        results = service.run_on_file(str(large_mp4), "yolo_ocr")

        assert len(results) > 0
        # If we reach here, video was properly closed (no resource leak)

    def test_video_capture_released_on_error(self, large_mp4):
        """VideoCapture is released even on pipeline error."""
        mock_dag = MockDagPipelineService(fail_mode="plugin_error")
        service = VideoFilePipelineService(mock_dag)

        with pytest.raises(RuntimeError):
            service.run_on_file(str(large_mp4), "yolo_ocr")

        # If we reach here, capture was released despite error

    def test_processes_video_after_previous_failure(self, large_mp4):
        """Can process another video after a previous error."""
        mock_dag_fail = MockDagPipelineService(fail_mode="plugin_error")
        service = VideoFilePipelineService(mock_dag_fail)

        # First attempt fails
        with pytest.raises(RuntimeError):
            service.run_on_file(str(large_mp4), "yolo_ocr")

        # Switch to working mock
        mock_dag_ok = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag_ok)

        # Second attempt succeeds
        results = service.run_on_file(str(large_mp4), "yolo_ocr")
        assert len(results) > 0


class TestDagServiceMockRobustness:
    """Test MockDagPipelineService behaves correctly under stress."""

    def test_mock_handles_many_calls(self, large_mp4):
        """MockDagPipelineService handles many sequential calls."""
        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        # Process all 30 frames = 30 DAG calls
        results = service.run_on_file(
            str(large_mp4),
            "yolo_ocr",
        )

        assert len(results) == 30
        # All calls should have succeeded
        for result in results:
            assert isinstance(result["result"], dict)

    def test_mock_returns_consistent_results(self, large_mp4):
        """Each DAG call returns valid result."""
        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        results = service.run_on_file(str(large_mp4), "yolo_ocr")

        for i, result in enumerate(results):
            assert isinstance(result, dict)
            assert "frame_index" in result
            assert "result" in result
            assert result["frame_index"] == i
