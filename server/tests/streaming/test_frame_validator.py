"""Tests for Frame Validator (Commit 3).

Following TDD: Write tests first, then implement code to make them pass.

These tests verify:
- Valid JPEG passes validation
- Invalid JPEG (missing SOI) raises FrameValidationError("invalid_frame", ...)
- Invalid JPEG (missing EOI) raises FrameValidationError("invalid_frame", ...)
- Oversized frame raises FrameValidationError("frame_too_large", ...)
- Empty bytes raises FrameValidationError("invalid_frame", ...)
- Size limit reads from environment variable
"""

import os
import sys

import pytest

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


class TestFrameValidatorValidFrame:
    """Test valid frame validation."""

    def test_valid_jpeg_passes_validation(self) -> None:
        """Test that valid JPEG passes validation."""
        from app.services.streaming.frame_validator import validate_jpeg

        # Create a minimal valid JPEG (SOI + EOI markers)
        valid_jpeg = b"\xFF\xD8\xFF\xD9"

        # Should not raise any exception
        validate_jpeg(valid_jpeg)


class TestFrameValidatorInvalidFrame:
    """Test invalid frame validation."""

    def test_invalid_jpeg_missing_soi_raises_error(self) -> None:
        """Test that invalid JPEG (missing SOI) raises FrameValidationError."""
        from app.services.streaming.frame_validator import (
            FrameValidationError,
            validate_jpeg,
        )

        # Missing SOI marker
        invalid_jpeg = b"\x00\x00\xFF\xD9"

        with pytest.raises(FrameValidationError) as exc_info:
            validate_jpeg(invalid_jpeg)

        assert exc_info.value.code == "invalid_frame"
        assert "SOI" in exc_info.value.detail or "marker" in exc_info.value.detail

    def test_invalid_jpeg_missing_eoi_raises_error(self) -> None:
        """Test that invalid JPEG (missing EOI) raises FrameValidationError."""
        from app.services.streaming.frame_validator import (
            FrameValidationError,
            validate_jpeg,
        )

        # Missing EOI marker
        invalid_jpeg = b"\xFF\xD8\x00\x00"

        with pytest.raises(FrameValidationError) as exc_info:
            validate_jpeg(invalid_jpeg)

        assert exc_info.value.code == "invalid_frame"
        assert "EOI" in exc_info.value.detail or "marker" in exc_info.value.detail

    def test_empty_bytes_raises_error(self) -> None:
        """Test that empty bytes raises FrameValidationError."""
        from app.services.streaming.frame_validator import (
            FrameValidationError,
            validate_jpeg,
        )

        with pytest.raises(FrameValidationError) as exc_info:
            validate_jpeg(b"")

        assert exc_info.value.code == "invalid_frame"


class TestFrameValidatorOversizedFrame:
    """Test oversized frame validation."""

    def test_oversized_frame_raises_error(self) -> None:
        """Test that oversized frame raises FrameValidationError."""
        from app.services.streaming.frame_validator import (
            FrameValidationError,
            validate_jpeg,
        )

        # Create a frame larger than 5MB default limit
        # 5MB = 5 * 1024 * 1024 = 5242880 bytes
        oversized_frame = b"\xFF\xD8" + (b"\x00" * 6000000) + b"\xFF\xD9"

        with pytest.raises(FrameValidationError) as exc_info:
            validate_jpeg(oversized_frame)

        assert exc_info.value.code == "frame_too_large"
        assert "size" in exc_info.value.detail.lower() or "too large" in exc_info.value.detail.lower()


class TestFrameValidatorEnvironmentVariables:
    """Test environment variable configuration."""

    def test_size_limit_reads_from_environment_variable(self) -> None:
        """Test that size limit reads from environment variable."""
        # Set custom size limit
        os.environ["STREAM_MAX_FRAME_SIZE_MB"] = "1"

        try:
            # Import after setting env var
            from app.services.streaming.frame_validator import (
                FrameValidationError,
                validate_jpeg,
            )

            # Create a frame larger than 1MB but smaller than 5MB
            # 1MB = 1048576 bytes
            oversized_frame = b"\xFF\xD8" + (b"\x00" * 2000000) + b"\xFF\xD9"

            with pytest.raises(FrameValidationError) as exc_info:
                validate_jpeg(oversized_frame)

            assert exc_info.value.code == "frame_too_large"
        finally:
            # Clean up
            del os.environ["STREAM_MAX_FRAME_SIZE_MB"]