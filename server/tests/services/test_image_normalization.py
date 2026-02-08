"""Tests for image input normalization in AnalysisExecutionService.

TEST-CHANGE: Add image normalization tests for handling various image input formats
(raw bytes, base64 strings, or file IDs) before passing to plugins.
"""

import base64
from unittest.mock import AsyncMock

import pytest

from app.services.execution.analysis_execution_service import (
    AnalysisExecutionService,
)


class TestNormalizeImageInput:
    """Tests for normalize_image_input helper function."""

    def test_normalize_raw_bytes_returns_unchanged(self) -> None:
        """Verify raw bytes are preserved as-is."""
        raw_bytes = b"\x89PNG\r\n\x1a\n"
        result = AnalysisExecutionService.normalize_image_input(image_bytes=raw_bytes)
        assert result == raw_bytes
        assert isinstance(result, bytes)

    def test_normalize_base64_image_string(self) -> None:
        """Verify base64 strings in 'image' field are decoded."""
        raw_bytes = b"test_image_data"
        base64_string = base64.b64encode(raw_bytes).decode("utf-8")

        result = AnalysisExecutionService.normalize_image_input(image=base64_string)

        assert result == raw_bytes
        assert isinstance(result, bytes)

    def test_normalize_base64_frame_string(self) -> None:
        """Verify base64 strings in 'frame' field are decoded."""
        raw_bytes = b"test_frame_data"
        base64_string = base64.b64encode(raw_bytes).decode("utf-8")

        result = AnalysisExecutionService.normalize_image_input(frame=base64_string)

        assert result == raw_bytes
        assert isinstance(result, bytes)

    def test_normalize_prefers_image_bytes_over_image(self) -> None:
        """Verify image_bytes takes precedence when both are provided."""
        raw_bytes = b"bytes_data"
        base64_string = base64.b64encode(b"image_data").decode("utf-8")

        result = AnalysisExecutionService.normalize_image_input(
            image_bytes=raw_bytes, image=base64_string
        )

        assert result == raw_bytes

    def test_normalize_raises_when_no_image_source(self) -> None:
        """Verify ValueError raised when no image source is found."""
        with pytest.raises(
            ValueError,
            match="No valid image source found",
        ):
            AnalysisExecutionService.normalize_image_input()

    def test_normalize_raises_on_invalid_base64(self) -> None:
        """Verify ValueError raised when base64 string is malformed."""
        with pytest.raises(ValueError, match="Failed to decode base64"):
            AnalysisExecutionService.normalize_image_input(image="not-valid-base64!!!")


class TestAnalysisExecutionServiceAnalyzeWithImageNormalization:
    """Tests for AnalysisExecutionService.analyze with image normalization."""

    @pytest.mark.asyncio
    async def test_analyze_normalizes_base64_image_to_image_bytes(self) -> None:
        """Verify plugin receives image_bytes key, not image."""
        # Setup
        mock_job_execution_service = AsyncMock()
        mock_job_execution_service.create_job = AsyncMock(return_value="job-123")
        mock_job_execution_service.run_job = AsyncMock(
            return_value={"result": {"detections": []}}
        )
        service = AnalysisExecutionService(mock_job_execution_service)

        raw_bytes = b"test_image_content"
        base64_string = base64.b64encode(raw_bytes).decode("utf-8")

        # Call analyze with base64 image
        result, error = await service.analyze(
            plugin_name="test_plugin",
            args={"image": base64_string, "mime_type": "image/png"},
        )

        # Verify job_execution_service was called with image_bytes, not image
        assert mock_job_execution_service.create_job.called
        call_args = mock_job_execution_service.create_job.call_args
        plugin_args = call_args[1]["args"]

        assert "image_bytes" in plugin_args
        assert plugin_args["image_bytes"] == raw_bytes
        assert "image" not in plugin_args

    @pytest.mark.asyncio
    async def test_analyze_preserves_raw_bytes(self) -> None:
        """Verify raw bytes in image_bytes are preserved."""
        # Setup
        mock_job_execution_service = AsyncMock()
        mock_job_execution_service.create_job = AsyncMock(return_value="job-123")
        mock_job_execution_service.run_job = AsyncMock(
            return_value={"result": {"detections": []}}
        )
        service = AnalysisExecutionService(mock_job_execution_service)

        raw_bytes = b"\x89PNG\r\n\x1a\n"

        # Call analyze with raw bytes (simulating direct image_bytes)
        result, error = await service.analyze(
            plugin_name="test_plugin",
            args={"image_bytes": raw_bytes, "mime_type": "image/png"},
        )

        # Verify plugin received unchanged bytes
        call_args = mock_job_execution_service.create_job.call_args
        plugin_args = call_args[1]["args"]

        assert plugin_args["image_bytes"] == raw_bytes
