"""Structured error envelope for Phase 12.

All exceptions during plugin execution are wrapped in this envelope.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import traceback


ErrorType = str  # Type alias for error classification


def classify_error(exc: Exception) -> ErrorType:
    """Classify an exception into a Phase 12 error type.

    Args:
        exc: The exception to classify

    Returns:
        Error type string
    """
    name = exc.__class__.__name__
    if "Validation" in name:
        return "ValidationError"
    if "Plugin" in name:
        return "PluginError"
    return "ExecutionError"


def build_error_envelope(
    exc: Exception,
    plugin_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a structured error envelope from an exception.

    Args:
        exc: The exception that occurred
        plugin_name: Optional name of the plugin that caused the error

    Returns:
        Structured error envelope dict
    """
    error_type = classify_error(exc)
    message = str(exc) or error_type
    tb = traceback.format_exc()

    return {
        "error": {
            "type": error_type,
            "message": message,
            "details": {},
            "plugin": plugin_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "_internal": {
            "traceback": tb,
        },
    }
