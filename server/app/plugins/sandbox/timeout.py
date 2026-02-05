"""Timeout guard for Phase 11 plugin execution.

Provides timeout protection for plugin tool execution with configurable limits.
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from typing import Any, Callable, Optional

from .sandbox_runner import PluginSandboxResult, run_plugin_sandboxed

logger = logging.getLogger(__name__)

# Default timeout: 60 seconds
DEFAULT_TIMEOUT_SECONDS = 60.0


@dataclass
class TimeoutGuardResult:
    """Result of timeout-guarded plugin execution."""

    ok: bool
    result: Any = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    timed_out: bool = False
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS


def run_with_timeout(
    tool_fn: Callable,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    **kwargs: Any,
) -> TimeoutGuardResult:
    """
    Execute a plugin tool function with timeout protection.

    Args:
        tool_fn: The plugin tool function to execute
        timeout_seconds: Maximum execution time (default: 60 seconds)
        **kwargs: Additional arguments to pass to tool_fn

    Returns:
        TimeoutGuardResult with ok, result, error, error_type, and timed_out flag
    """
    try:
        logger.debug(
            f"Executing with timeout: {timeout_seconds}s",
            extra={"timeout": timeout_seconds},
        )

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_plugin_sandboxed, tool_fn, **kwargs)
            sandbox_result = future.result(timeout=timeout_seconds)

            return TimeoutGuardResult(
                ok=sandbox_result.ok,
                result=sandbox_result.result,
                error=sandbox_result.error,
                error_type=sandbox_result.error_type,
                timed_out=False,
                timeout_seconds=timeout_seconds,
            )

    except FuturesTimeoutError:
        error_msg = f"Plugin execution timed out after {timeout_seconds}s"
        logger.warning(f"Timeout: {error_msg}")
        return TimeoutGuardResult(
            ok=False,
            error=error_msg,
            error_type="TimeoutError",
            timed_out=True,
            timeout_seconds=timeout_seconds,
        )

    except Exception as e:
        error_msg = f"Timeout wrapper failed: {str(e)}"
        logger.exception(f"Timeout error: {error_msg}")
        return TimeoutGuardResult(
            ok=False,
            error=error_msg,
            error_type=type(e).__name__,
            timed_out=False,
            timeout_seconds=timeout_seconds,
        )


def run_sandboxed_with_timeout(
    tool_fn: Callable,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    **kwargs: Any,
) -> PluginSandboxResult:
    """
    Execute a plugin tool in sandbox with timeout protection.

    This is a convenience function that combines sandbox execution
    with timeout protection, returning the standard PluginSandboxResult.

    Args:
        tool_fn: The plugin tool function to execute
        timeout_seconds: Maximum execution time (default: 60 seconds)
        **kwargs: Additional arguments to pass to tool_fn

    Returns:
        PluginSandboxResult (timed out executions have error_type="TimeoutError")
    """
    timeout_result = run_with_timeout(tool_fn, timeout_seconds, **kwargs)

    if timeout_result.timed_out:
        return PluginSandboxResult(
            ok=False,
            error=timeout_result.error,
            error_type="TimeoutError",
        )

    return PluginSandboxResult(
        ok=timeout_result.ok,
        result=timeout_result.result,
        error=timeout_result.error,
        error_type=timeout_result.error_type,
    )
