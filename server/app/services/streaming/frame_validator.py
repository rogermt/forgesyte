"""Frame Validator for Phase 17 streaming.

Validates incoming JPEG frames before processing.

This module provides:
- JPEG SOI/EOI marker validation
- Frame size limit checking
- Structured error reporting

Author: Roger
Phase: 17
"""

import os


class FrameValidationError(Exception):
    """Exception raised when frame validation fails."""

    def __init__(self, code: str, detail: str) -> None:
        """Initialize frame validation error.

        Args:
            code: Error code ("invalid_frame" or "frame_too_large")
            detail: Human-readable error message
        """
        self.code = code
        self.detail = detail
        super().__init__(detail)


def validate_jpeg(frame_bytes: bytes) -> None:
    """Validate a JPEG frame.

    Checks:
    - JPEG SOI marker (0xFF 0xD8)
    - JPEG EOI marker (0xFF 0xD9)
    - Size limit (configurable via STREAM_MAX_FRAME_SIZE_MB, default 5MB)

    Args:
        frame_bytes: Raw frame bytes to validate

    Raises:
        FrameValidationError: If validation fails
    """
    # Check for empty bytes
    if not frame_bytes:
        raise FrameValidationError("invalid_frame", "Frame is empty (no data provided)")

    # Check size limit
    max_size_mb = float(os.getenv("STREAM_MAX_FRAME_SIZE_MB", "5"))
    max_size_bytes = int(max_size_mb * 1024 * 1024)

    if len(frame_bytes) > max_size_bytes:
        raise FrameValidationError(
            "frame_too_large",
            f"Frame size ({len(frame_bytes)} bytes) exceeds limit ({max_size_bytes} bytes)",
        )

    # Check for JPEG SOI marker (0xFF 0xD8)
    if len(frame_bytes) < 2 or frame_bytes[0:2] != b"\xFF\xD8":
        raise FrameValidationError(
            "invalid_frame", "Frame is not a valid JPEG (missing SOI marker)"
        )

    # Check for JPEG EOI marker (0xFF 0xD9)
    if len(frame_bytes) < 2 or frame_bytes[-2:] != b"\xFF\xD9":
        raise FrameValidationError(
            "invalid_frame", "Frame is not a valid JPEG (missing EOI marker)"
        )
