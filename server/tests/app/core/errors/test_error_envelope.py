"""Tests for error_envelope.py - Phase 12 structured error handling."""

from app.core.errors.error_envelope import (
    ErrorType,
    build_error_envelope,
    classify_error,
)


class TestClassifyError:
    """Tests for classify_error function."""

    def test_classify_validation_error(self) -> None:
        """ValidationError classes are classified correctly."""

        class CustomValidationError(Exception):
            pass

        result = classify_error(CustomValidationError("test"))
        assert result == "ValidationError"

    def test_classify_plugin_error(self) -> None:
        """Plugin-related exceptions are classified as PluginError."""

        class PluginLoadError(Exception):
            pass

        result = classify_error(PluginLoadError("failed to load"))
        assert result == "PluginError"

    def test_classify_generic_error(self) -> None:
        """Generic exceptions are classified as ExecutionError."""
        result = classify_error(ValueError("bad value"))
        assert result == "ExecutionError"

        result = classify_error(RuntimeError("oops"))
        assert result == "ExecutionError"

        result = classify_error(Exception("unknown"))
        assert result == "ExecutionError"


class TestBuildErrorEnvelope:
    """Tests for build_error_envelope function."""

    def test_basic_error_envelope(self) -> None:
        """Builds envelope with required fields."""
        exc = ValueError("test error message")
        envelope = build_error_envelope(exc)

        assert "error" in envelope
        assert envelope["error"]["type"] == "ExecutionError"
        assert envelope["error"]["message"] == "test error message"
        assert envelope["error"]["plugin"] is None
        assert "timestamp" in envelope["error"]
        assert "_internal" in envelope
        assert "traceback" in envelope["_internal"]

    def test_error_envelope_with_plugin_name(self) -> None:
        """Includes plugin name when provided."""
        exc = RuntimeError("plugin crashed")
        envelope = build_error_envelope(exc, plugin_name="test-plugin")

        assert envelope["error"]["plugin"] == "test-plugin"

    def test_error_envelope_empty_message(self) -> None:
        """Uses error type as message when exception has no message."""
        exc = Exception()  # Empty exception
        envelope = build_error_envelope(exc)

        # Should use error type as fallback message
        assert envelope["error"]["message"] == "ExecutionError"

    def test_error_envelope_validation_error(self) -> None:
        """Correctly classifies and formats validation errors."""

        class DataValidationError(Exception):
            pass

        exc = DataValidationError("invalid data format")
        envelope = build_error_envelope(exc, plugin_name="validator")

        assert envelope["error"]["type"] == "ValidationError"
        assert envelope["error"]["message"] == "invalid data format"
        assert envelope["error"]["plugin"] == "validator"

    def test_error_envelope_plugin_error(self) -> None:
        """Correctly classifies and formats plugin errors."""

        class PluginExecutionError(Exception):
            pass

        exc = PluginExecutionError("execution failed")
        envelope = build_error_envelope(exc)

        assert envelope["error"]["type"] == "PluginError"
        assert envelope["error"]["message"] == "execution failed"

    def test_error_envelope_details_field(self) -> None:
        """Details field is present and empty by default."""
        exc = ValueError("test")
        envelope = build_error_envelope(exc)

        assert envelope["error"]["details"] == {}

    def test_error_envelope_timestamp_format(self) -> None:
        """Timestamp is in ISO format with timezone."""
        exc = ValueError("test")
        envelope = build_error_envelope(exc)

        timestamp = envelope["error"]["timestamp"]
        # ISO format should contain 'T' separator
        assert "T" in timestamp
        # Should end with timezone (e.g., +00:00 or Z)
        assert "+" in timestamp or timestamp.endswith("Z")

    def test_error_envelope_traceback_present(self) -> None:
        """Traceback field is present in internal section."""
        exc = ValueError("traceback test")
        envelope = build_error_envelope(exc)

        # Traceback field exists (format_exc() may return "None" outside except block)
        assert "traceback" in envelope["_internal"]
        assert isinstance(envelope["_internal"]["traceback"], str)


class TestErrorType:
    """Tests for ErrorType alias usage."""

    def test_error_type_is_string(self) -> None:
        """ErrorType is a string type."""
        error_type: ErrorType = "ValidationError"
        assert isinstance(error_type, str)

        error_type = "PluginError"
        assert isinstance(error_type, str)

        error_type = "ExecutionError"
        assert isinstance(error_type, str)
