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

    def test_function_returns_none_explicitly(self) -> None:
        """Function that explicitly returns None is handled correctly."""

        def none_fn() -> None:
            pass

        result = run_with_timeout(none_fn, timeout_seconds=5.0)

        assert result.ok is True
        assert result.result is None

    def test_zero_timeout_immediate_timeout(self) -> None:
        """Zero timeout should trigger immediate timeout for slow functions."""

        def slow_fn() -> str:
            time.sleep(0.5)
            return "done"

        result = run_with_timeout(slow_fn, timeout_seconds=0.0)

        # With zero timeout, slow function should timeout
        assert result.ok is False
        assert result.timed_out is True
        assert result.error_type == "TimeoutError"

    def test_negative_timeout_triggers_timeout(self) -> None:
        """Negative timeout value should trigger timeout for slow functions."""

        def slow_fn() -> str:
            time.sleep(0.5)
            return "done"

        # Negative timeout should cause timeout behavior
        result = run_with_timeout(slow_fn, timeout_seconds=-1.0)

        assert result.ok is False
        assert result.timed_out is True
        assert result.error_type == "TimeoutError"

    def test_concurrent_timeouts_no_interference(self) -> None:
        """Concurrent timeout executions don't interfere with each other."""
        import concurrent.futures

        results = []

        def run_quick_task(task_id: int) -> tuple[int, bool, str | None]:
            def fn() -> int:
                return task_id * 2

            result = run_with_timeout(fn, timeout_seconds=5.0)
            return (task_id, result.ok, result.result)

        def run_slow_task(task_id: int) -> tuple[int, bool, str | None]:
            def fn() -> str:
                time.sleep(2)
                return "done"

            result = run_with_timeout(fn, timeout_seconds=0.1)
            return (task_id, result.ok, result.result)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Mix quick and slow tasks
            futures = []
            for i in range(5):
                futures.append(executor.submit(run_quick_task, i))
            for i in range(5, 10):
                futures.append(executor.submit(run_slow_task, i))

            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

        # Verify quick tasks completed successfully
        quick_results = [r for r in results if r[0] < 5]
        for task_id, ok, result in quick_results:
            assert ok is True
            assert result == task_id * 2

        # Verify slow tasks timed out
        slow_results = [r for r in results if r[0] >= 5]
        for _task_id, ok, _result in slow_results:
            assert ok is False

        # Total should be 10 results
        assert len(results) == 10

    def test_concurrent_mixed_success_and_timeout(self) -> None:
        """Concurrent execution with mix of success and timeout cases."""
        import concurrent.futures

        def run_task(succeed: bool, delay: float, timeout: float) -> bool:
            def fn() -> str:
                time.sleep(delay)
                return "done"

            result = run_with_timeout(fn, timeout_seconds=timeout)
            return result.ok

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(run_task, True, 0.0, 1.0),  # Should succeed
                executor.submit(run_task, True, 0.0, 1.0),  # Should succeed
                executor.submit(run_task, False, 1.0, 0.1),  # Should timeout
                executor.submit(run_task, False, 1.0, 0.1),  # Should timeout
            ]

            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # Should have 2 successes and 2 timeouts
        assert sum(results) == 2
        assert len(results) == 4
