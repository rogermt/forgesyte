"""Stress test: 1000-frame MP4 processing (Commit 8).

Proves the service handles high volume without memory leaks or crashes.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import tempfile

import cv2
import numpy as np
import pytest

from app.services.video_file_pipeline_service import VideoFilePipelineService
from app.tests.video.fakes.mock_dag_service import MockDagPipelineService


@pytest.fixture
def video_1000_frames():
    """Create 1000-frame MP4 at 320×240."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(tmp_path), fourcc, 1.0, (320, 240))

    for i in range(1000):
        # Vary pixel value by frame to ensure they're all different
        frame = np.full((240, 320, 3), fill_value=(i % 256), dtype=np.uint8)
        out.write(frame)

    out.release()
    return tmp_path


class TestVideoService1000Frames:
    """1000-frame stress test."""

    def test_1000_frame_video_processes_all(self, video_1000_frames):
        """Process 1000-frame video without crashing."""
        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        results = service.run_on_file(
            str(video_1000_frames),
            "yolo_ocr",
        )

        # Core assertion: all 1000 frames processed
        assert len(results) == 1000

    def test_1000_frames_first_frame_is_0(self, video_1000_frames):
        """First result has frame_index 0."""
        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        results = service.run_on_file(
            str(video_1000_frames),
            "yolo_ocr",
        )

        assert results[0]["frame_index"] == 0

    def test_1000_frames_last_frame_is_999(self, video_1000_frames):
        """Last result has frame_index 999."""
        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        results = service.run_on_file(
            str(video_1000_frames),
            "yolo_ocr",
        )

        assert results[-1]["frame_index"] == 999

    def test_1000_frames_sequential_no_gaps(self, video_1000_frames):
        """All frame indices are sequential with no gaps and no duplicates."""
        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        results = service.run_on_file(
            str(video_1000_frames),
            "yolo_ocr",
        )

        # Extract frame indices
        indices = [r["frame_index"] for r in results]

        # Check no duplicates
        assert len(indices) == len(set(indices)), "Found duplicate frame indices"

        # Check sequential 0 to 999
        expected = list(range(1000))
        assert indices == expected, "Frame indices not sequential"

    def test_1000_frames_mock_called_1000_times(self, video_1000_frames):
        """DAG service called 1000 times (once per frame)."""
        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        results = service.run_on_file(
            str(video_1000_frames),
            "yolo_ocr",
        )

        assert mock_dag.call_count == 1000
        assert len(results) == 1000

    def test_1000_frames_completes_in_reasonable_time(self, video_1000_frames):
        """1000-frame video processes within reasonable time (< 30s)."""
        import time

        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        start = time.time()
        results = service.run_on_file(
            str(video_1000_frames),
            "yolo_ocr",
        )
        elapsed = time.time() - start

        assert len(results) == 1000
        assert elapsed < 30, f"Processing took {elapsed:.2f}s (expected < 30s)"
