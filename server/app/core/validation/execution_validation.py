"""Execution validation for Phase 12.

Input/output validation for plugin execution.
"""

from typing import Any, Dict


class InputValidationError(Exception):
    """Raised when incoming request payload is invalid."""
    pass


class OutputValidationError(Exception):
    """Raised when plugin output is invalid or malformed."""
    pass


def validate_input_payload(payload: Dict[str, Any]) -> None:
    """Validate incoming request payload before execution.

    Args:
        payload: Request payload dict

    Raises:
        InputValidationError: If payload is invalid
    """
    image = payload.get("image")
    if not image:
        raise InputValidationError("Empty or missing image payload")

    mime_type = payload.get("mime_type")
    if not mime_type:
        raise InputValidationError("Missing or empty mime_type")

    if not isinstance(mime_type, str):
        raise InputValidationError("mime_type must be a string")


def validate_plugin_output(raw_output: Any) -> Dict[str, Any]:
    """Validate plugin output after execution.

    Args:
        raw_output: Raw output from plugin.run()

    Returns:
        Validated output dict

    Raises:
        OutputValidationError: If output is invalid
    """
    if raw_output is None:
        raise OutputValidationError("Plugin returned None")

    if not isinstance(raw_output, dict):
        raise OutputValidationError("Plugin output must be a dict")

    return raw_output
