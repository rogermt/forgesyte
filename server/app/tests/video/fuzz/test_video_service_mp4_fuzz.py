"""Fuzz tests: malformed MP4 inputs (Commit 8).

Tests that the service gracefully rejects garbage input without crashing or hanging.
All fuzz cases must either:
- Return 0 results (empty list), OR
- Raise ValueError (invalid input)

Never crash. Never hang. Never raise an unhandled exception type.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import tempfile

import pytest

from app.services.video_file_pipeline_service import VideoFilePipelineService
from app.tests.video.fakes.mock_dag_service import MockDagPipelineService


class TestVideoServiceMP4Fuzz:
    """Fuzz tests with malformed/corrupted MP4 inputs."""

    def test_fuzz_random_128_bytes(self):
        """Fuzz case: 128 random bytes (not MP4)."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        # Fixed seed for determinism
        fake_data = b"\x00\x01\x02" * 43 + b"\x00"  # Exactly 128 bytes, deterministic
        with open(tmp_path, "wb") as f:
            f.write(fake_data)

        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        # Should either return 0 results OR raise ValueError
        try:
            results = service.run_on_file(str(tmp_path), "yolo_ocr")
            # If no exception, must return 0 results
            assert isinstance(results, list)
            assert len(results) == 0, "Invalid MP4 should yield 0 results"
        except ValueError:
            # ValueError is acceptable (invalid format)
            pass

    def test_fuzz_random_1kb(self):
        """Fuzz case: 1KB random bytes (not MP4)."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        # Fixed seed for determinism
        fake_data = (b"\xaa\xbb\xcc" * 341) + b"\xdd"  # Exactly 1024 bytes
        with open(tmp_path, "wb") as f:
            f.write(fake_data)

        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        try:
            results = service.run_on_file(str(tmp_path), "yolo_ocr")
            assert isinstance(results, list)
            assert len(results) == 0
        except ValueError:
            pass

    def test_fuzz_header_only_mp4(self):
        """Fuzz case: MP4 with only header, no mdat/moov atoms."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        # Minimal MP4-like header (ftyp atom only)
        # ftyp box: 20 bytes
        header = b"\x00\x00\x00\x20ftypisom"  # ftyp header
        header += b"\x00\x00\x00\x00"  # minor version, brand flags
        header += b"isomiso2mp41"  # compatible brands

        with open(tmp_path, "wb") as f:
            f.write(header)

        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        try:
            results = service.run_on_file(str(tmp_path), "yolo_ocr")
            assert isinstance(results, list)
            assert len(results) == 0
        except ValueError:
            pass

    def test_fuzz_truncated_mp4(self):
        """Fuzz case: MP4 file truncated mid-stream."""
        import cv2
        import numpy as np

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        # Write valid MP4
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(tmp_path), fourcc, 1.0, (320, 240))
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        out.write(frame)
        out.release()

        # Truncate file to 50% size
        file_size = tmp_path.stat().st_size
        with open(tmp_path, "r+b") as f:
            f.truncate(file_size // 2)

        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        try:
            results = service.run_on_file(str(tmp_path), "yolo_ocr")
            assert isinstance(results, list)
            assert len(results) == 0
        except ValueError:
            pass

    def test_fuzz_empty_file(self):
        """Fuzz case: Empty file (0 bytes)."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        # Leave file empty
        tmp_path.touch()

        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        try:
            results = service.run_on_file(str(tmp_path), "yolo_ocr")
            assert isinstance(results, list)
            assert len(results) == 0
        except ValueError:
            pass

    def test_fuzz_all_zeros(self):
        """Fuzz case: File filled with zeros (not valid MP4)."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        # 512 bytes of zeros
        with open(tmp_path, "wb") as f:
            f.write(b"\x00" * 512)

        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        try:
            results = service.run_on_file(str(tmp_path), "yolo_ocr")
            assert isinstance(results, list)
            assert len(results) == 0
        except ValueError:
            pass

    def test_fuzz_never_raises_unexpected_exception(self):
        """All fuzz cases should only raise ValueError or succeed (return [])."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        # Write garbage
        with open(tmp_path, "wb") as f:
            f.write(b"\xff" * 256)

        mock_dag = MockDagPipelineService(fail_mode=None)
        service = VideoFilePipelineService(mock_dag)

        try:
            results = service.run_on_file(str(tmp_path), "yolo_ocr")
            # If we get here, it's a success case
            assert isinstance(results, list)
        except ValueError:
            # Expected error type
            pass
        except Exception as e:
            # Any other exception is a failure
            pytest.fail(f"Unexpected exception type: {type(e).__name__}: {e}")
