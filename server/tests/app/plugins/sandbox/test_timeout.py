"""Tests for timeout.py - Phase 11 timeout protection."""

import time

import pytest

from app.plugins.sandbox.timeout import (
    DEFAULT_TIMEOUT_SECONDS,
    TimeoutGuardResult,
    run_sandboxed_with_timeout,
    run_with_timeout,
)


@pytest.mark.unit
class TestRunWithTimeout:
    """Tests for run_with_timeout function."""

    def test_success_within_timeout(self) -> None:
        """Successful execution within timeout returns ok=True."""

        def quick_fn() -> str:
            return "done"

        result = run_with_timeout(quick_fn, timeout_seconds=5.0)

        assert result.ok is True
        assert result.result == "done"
        assert result.timed_out is False
        assert result.error is None

    def test_passes_kwargs_to_function(self) -> None:
        """Keyword arguments are passed to the function."""

        def compute_fn(x: int, y: int) -> int:
            return x + y

        result = run_with_timeout(compute_fn, timeout_seconds=5.0, x=2, y=3)

        assert result.ok is True
        assert result.result == 5

    def test_timeout_exceeded(self) -> None:
        """Timeout exceeded returns timed_out=True."""

        def slow_fn() -> str:
            time.sleep(2)  # Sleep longer than timeout
            return "done"

        result = run_with_timeout(slow_fn, timeout_seconds=0.1)  # Very short timeout

        assert result.ok is False
        assert result.timed_out is True
        assert result.error_type == "TimeoutError"
        assert "timed out" in (result.error or "").lower()

    def test_exception_handling(self) -> None:
        """Exceptions are caught and returned in result."""

        def failing_fn() -> None:
            raise ValueError("intentional failure")

        result = run_with_timeout(failing_fn, timeout_seconds=5.0)

        assert result.ok is False
        assert "intentional failure" in (result.error or "")
        assert result.error_type == "ValueError"
        assert result.timed_out is False

    def test_custom_timeout_value(self) -> None:
        """Custom timeout value is stored in result."""

        def fn() -> str:
            return "ok"

        result = run_with_timeout(fn, timeout_seconds=30.0)

        assert result.timeout_seconds == 30.0

    def test_default_timeout(self) -> None:
        """Default timeout is 60 seconds."""
        assert DEFAULT_TIMEOUT_SECONDS == 60.0


@pytest.mark.unit
class TestRunSandboxedWithTimeout:
    """Tests for run_sandboxed_with_timeout function."""

    def test_success_returns_sandbox_result(self) -> None:
        """Successful execution returns PluginSandboxResult."""

        def fn() -> str:
            return "success"

        result = run_sandboxed_with_timeout(fn, timeout_seconds=5.0)

        assert result.ok is True
        assert result.result == "success"
        assert result.error is None

    def test_timeout_returns_timeout_error(self) -> None:
        """Timeout returns error_type='TimeoutError'."""

        def slow_fn() -> str:
            time.sleep(2)
            return "done"

        result = run_sandboxed_with_timeout(slow_fn, timeout_seconds=0.1)

        assert result.ok is False
        assert result.error_type == "TimeoutError"
        assert "timed out" in (result.error or "").lower()

    def test_exception_returns_error(self) -> None:
        """Exceptions are returned in PluginSandboxResult."""

        def failing_fn() -> None:
            raise RuntimeError("sandbox error")

        result = run_sandboxed_with_timeout(failing_fn, timeout_seconds=5.0)

        assert result.ok is False
        assert "sandbox error" in (result.error or "")
        assert result.error_type == "RuntimeError"


@pytest.mark.unit
class TestTimeoutGuardResult:
    """Tests for TimeoutGuardResult dataclass."""

    def test_default_values(self) -> None:
        """Default values are set correctly."""
        result = TimeoutGuardResult(ok=True)

        assert result.ok is True
        assert result.result is None
        assert result.error is None
        assert result.error_type is None
        assert result.timed_out is False
        assert result.timeout_seconds == DEFAULT_TIMEOUT_SECONDS

    def test_custom_values(self) -> None:
        """Custom values are stored correctly."""
        result = TimeoutGuardResult(
            ok=False,
            error="timeout exceeded",
            error_type="TimeoutError",
            timed_out=True,
            timeout_seconds=30.0,
        )

        assert result.ok is False
        assert result.error == "timeout exceeded"
        assert result.error_type == "TimeoutError"
        assert result.timed_out is True
        assert result.timeout_seconds == 30.0


@pytest.mark.integration
class TestTimeoutIntegration:
    """Integration tests for timeout behavior."""

    def test_quick_function_completes(self) -> None:
        """Quick function completes before timeout."""

        def instant_fn() -> int:
            return 42

        result = run_with_timeout(instant_fn, timeout_seconds=1.0)

        assert result.ok is True
        assert result.result == 42

    def test_function_with_return_value(self) -> None:
        """Function with complex return value works."""

        def dict_fn() -> dict:
            return {"key": "value", "number": 123}

        result = run_with_timeout(dict_fn, timeout_seconds=5.0)

        assert result.ok is True
        assert result.result == {"key": "value", "number": 123}
