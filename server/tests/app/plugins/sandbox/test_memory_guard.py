"""Tests for memory_guard.py - Phase 11 memory protection."""

from unittest.mock import MagicMock, patch

import pytest

from app.plugins.sandbox.memory_guard import (
    DEFAULT_MEMORY_LIMIT_BYTES,
    MemoryGuardResult,
    check_memory_limit,
    format_memory_bytes,
    get_memory_usage_bytes,
    run_with_memory_guard,
)


@pytest.mark.integration
class TestGetMemoryUsageBytes:
    """Tests for get_memory_usage_bytes function."""

    def test_returns_int(self) -> None:
        """Returns an integer value."""
        result = get_memory_usage_bytes()
        assert isinstance(result, int)
        assert result >= 0

    def test_uses_psutil_when_available(self) -> None:
        """Uses psutil when available (integration test)."""
        # psutil is available in this environment
        result = get_memory_usage_bytes()
        # Should return a reasonable memory value (at least 1 MB for a running process)
        assert result > 1024 * 1024  # More than 1 MB

    def test_returns_positive_value(self) -> None:
        """Returns a positive memory value."""
        result = get_memory_usage_bytes()
        assert result > 0  # Process should use some memory


@pytest.mark.unit
class TestRunWithMemoryGuard:
    """Tests for run_with_memory_guard function."""

    def test_success_path(self) -> None:
        """Successful execution returns ok=True."""

        def successful_fn() -> str:
            return "success"

        result = run_with_memory_guard(successful_fn)

        assert result.ok is True
        assert result.result == "success"
        assert result.error is None
        assert result.memory_exceeded is False

    def test_passes_kwargs_to_function(self) -> None:
        """Keyword arguments are passed to the function."""

        def add_fn(a: int, b: int) -> int:
            return a + b

        result = run_with_memory_guard(add_fn, a=2, b=3)

        assert result.ok is True
        assert result.result == 5

    def test_exception_handling(self) -> None:
        """Exceptions are caught and returned in result."""

        def failing_fn() -> None:
            raise ValueError("intentional failure")

        result = run_with_memory_guard(failing_fn)

        assert result.ok is False
        assert result.error == "intentional failure"
        assert result.error_type == "ValueError"
        assert result.memory_exceeded is False

    @patch("app.plugins.sandbox.memory_guard.get_memory_usage_bytes")
    def test_memory_exceeded(self, mock_get_memory: MagicMock) -> None:
        """Memory limit exceeded returns memory_exceeded=True."""
        # Simulate memory going from 100MB to 2GB (exceeding 1GB limit)
        mock_get_memory.side_effect = [
            100 * 1024 * 1024,  # start memory
            2 * 1024 * 1024 * 1024,  # peak memory (2GB > 1GB limit)
        ]

        def allocate_fn() -> str:
            return "allocated"

        result = run_with_memory_guard(allocate_fn)

        assert result.ok is False
        assert result.memory_exceeded is True
        assert "Memory limit exceeded" in (result.error or "")
        assert result.error_type == "MemoryLimitExceeded"

    @patch("app.plugins.sandbox.memory_guard.get_memory_usage_bytes")
    def test_memory_error_exception(self, mock_get_memory: MagicMock) -> None:
        """MemoryError is caught and handled specially."""
        mock_get_memory.return_value = 500 * 1024 * 1024  # 500 MB

        def memory_error_fn() -> None:
            raise MemoryError("out of memory")

        result = run_with_memory_guard(memory_error_fn)

        assert result.ok is False
        assert result.memory_exceeded is True
        assert result.error_type == "MemoryError"
        # The error message includes "exhausted memory"
        assert "exhausted memory" in (result.error or "")

    def test_custom_memory_limit(self) -> None:
        """Custom memory limit is respected."""

        def small_fn() -> str:
            return "ok"

        # Use a very high limit that won't be exceeded
        result = run_with_memory_guard(
            small_fn, memory_limit_bytes=10 * 1024 * 1024 * 1024
        )  # 10GB

        assert result.ok is True
        assert result.memory_limit_bytes == 10 * 1024 * 1024 * 1024

    def test_result_includes_peak_memory(self) -> None:
        """Result includes peak memory usage."""

        def fn() -> str:
            return "done"

        result = run_with_memory_guard(fn)

        assert result.peak_memory_bytes >= 0


@pytest.mark.unit
class TestCheckMemoryLimit:
    """Tests for check_memory_limit function."""

    @patch("app.plugins.sandbox.memory_guard.get_memory_usage_bytes")
    def test_within_limit(self, mock_get_memory: MagicMock) -> None:
        """Returns True when within limit."""
        mock_get_memory.return_value = 500 * 1024 * 1024  # 500 MB

        is_within, current = check_memory_limit(1024 * 1024 * 1024)  # 1 GB limit

        assert is_within is True
        assert current == 500 * 1024 * 1024

    @patch("app.plugins.sandbox.memory_guard.get_memory_usage_bytes")
    def test_exceeds_limit(self, mock_get_memory: MagicMock) -> None:
        """Returns False when exceeding limit."""
        mock_get_memory.return_value = 2 * 1024 * 1024 * 1024  # 2 GB

        is_within, current = check_memory_limit(1024 * 1024 * 1024)  # 1 GB limit

        assert is_within is False
        assert current == 2 * 1024 * 1024 * 1024

    def test_default_limit(self) -> None:
        """Default limit is 1 GB."""
        assert DEFAULT_MEMORY_LIMIT_BYTES == 1024 * 1024 * 1024


@pytest.mark.unit
class TestFormatMemoryBytes:
    """Tests for format_memory_bytes function."""

    def test_format_bytes(self) -> None:
        """Formats bytes correctly."""
        assert format_memory_bytes(512) == "512 B"

    def test_format_kilobytes(self) -> None:
        """Formats kilobytes correctly."""
        assert format_memory_bytes(2048) == "2.00 KB"
        assert format_memory_bytes(1536) == "1.50 KB"

    def test_format_megabytes(self) -> None:
        """Formats megabytes correctly."""
        assert format_memory_bytes(1024 * 1024) == "1.00 MB"
        assert format_memory_bytes(512 * 1024 * 1024) == "512.00 MB"

    def test_format_gigabytes(self) -> None:
        """Formats gigabytes correctly."""
        assert format_memory_bytes(1024 * 1024 * 1024) == "1.00 GB"
        assert format_memory_bytes(2 * 1024 * 1024 * 1024) == "2.00 GB"


@pytest.mark.unit
class TestMemoryGuardResult:
    """Tests for MemoryGuardResult dataclass."""

    def test_default_values(self) -> None:
        """Default values are set correctly."""
        result = MemoryGuardResult(ok=True)

        assert result.ok is True
        assert result.result is None
        assert result.error is None
        assert result.error_type is None
        assert result.memory_exceeded is False
        assert result.memory_limit_bytes == DEFAULT_MEMORY_LIMIT_BYTES
        assert result.peak_memory_bytes == 0

    def test_custom_values(self) -> None:
        """Custom values are stored correctly."""
        result = MemoryGuardResult(
            ok=False,
            error="test error",
            error_type="TestError",
            memory_exceeded=True,
            memory_limit_bytes=100,
            peak_memory_bytes=200,
        )

        assert result.ok is False
        assert result.error == "test error"
        assert result.error_type == "TestError"
        assert result.memory_exceeded is True
        assert result.memory_limit_bytes == 100
        assert result.peak_memory_bytes == 200
