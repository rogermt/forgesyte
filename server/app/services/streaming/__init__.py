"""Streaming services for Phase 17.

This package provides:
- SessionManager: Per-connection state management
- FrameValidator: JPEG frame validation
- Backpressure: Backpressure decision logic

Author: Roger
Phase: 17
"""

from app.services.streaming.backpressure import Backpressure
from app.services.streaming.frame_validator import FrameValidationError, validate_jpeg
from app.services.streaming.session_manager import SessionManager

__all__ = ["Backpressure", "FrameValidationError", "SessionManager", "validate_jpeg"]