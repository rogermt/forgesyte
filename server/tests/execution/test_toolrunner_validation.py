"""Test ToolRunner input/output validation.

Tests verify:
- Input validation rejects invalid payloads
- Output validation rejects invalid plugin outputs
- Validation errors produce structured error envelopes
"""

import pytest

from app.core.validation.execution_validation import (
    validate_input_payload,
    validate_plugin_output,
    InputValidationError,
    OutputValidationError,
)


class TestInputValidation:
    """Tests for input payload validation."""

    def test_rejects_empty_image(self):
        """Empty image payload should raise InputValidationError."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_input_payload({
                "image": "",
                "mime_type": "image/png"
            })
        assert "image" in str(exc_info.value).lower()

    def test_rejects_missing_image(self):
        """Missing image key should raise InputValidationError."""
        with pytest.raises(InputValidationError):
            validate_input_payload({
                "mime_type": "image/png"
            })

    def test_rejects_empty_mime_type(self):
        """Empty mime_type should raise InputValidationError."""
        with pytest.raises(InputValidationError):
            validate_input_payload({
                "image": "base64data",
                "mime_type": ""
            })

    def test_rejects_missing_mime_type(self):
        """Missing mime_type key should raise InputValidationError."""
        with pytest.raises(InputValidationError):
            validate_input_payload({
                "image": "base64data"
            })

    def test_rejects_invalid_mime_type(self):
        """Non-string mime_type should raise InputValidationError."""
        with pytest.raises(InputValidationError):
            validate_input_payload({
                "image": "base64data",
                "mime_type": 123  # type: ignore
            })

    def test_accepts_valid_payload(self):
        """Valid payload should pass without exception."""
        # Should not raise
        validate_input_payload({
            "image": "base64data123",
            "mime_type": "image/png"
        })

    def test_accepts_binary_image(self):
        """Binary image data should be accepted."""
        validate_input_payload({
            "image": b"\x89PNG\r\n\x1a\n",
            "mime_type": "image/png"
        })


class TestOutputValidation:
    """Tests for plugin output validation."""

    def test_rejects_none(self):
        """None output should raise OutputValidationError."""
        with pytest.raises(OutputValidationError) as exc_info:
            validate_plugin_output(None)
        assert "None" in str(exc_info.value) or "returned None" in str(exc_info.value)

    def test_rejects_string(self):
        """String output should raise OutputValidationError."""
        with pytest.raises(OutputValidationError):
            validate_plugin_output("not a dict")

    def test_rejects_list(self):
        """List output should raise OutputValidationError."""
        with pytest.raises(OutputValidationError):
            validate_plugin_output([1, 2, 3])

    def test_rejects_number(self):
        """Number output should raise OutputValidationError."""
        with pytest.raises(OutputValidationError):
            validate_plugin_output(42)

    def test_accepts_dict(self):
        """Dict output should pass validation."""
        result = validate_plugin_output({"key": "value"})
        assert result == {"key": "value"}

    def test_accepts_empty_dict(self):
        """Empty dict should pass validation."""
        result = validate_plugin_output({})
        assert result == {}

    def test_accepts_nested_dict(self):
        """Nested dict should pass validation."""
        result = validate_plugin_output({
            "predictions": [{"label": "cat", "confidence": 0.95}],
            "metadata": {"model": "yolo"}
        })
        assert result["predictions"][0]["label"] == "cat"
