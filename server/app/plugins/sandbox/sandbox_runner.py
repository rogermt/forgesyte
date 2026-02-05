"""Sandbox runner for Phase 11 plugin crash protection.

Isolates plugin execution to prevent server crashes.
"""

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional


@dataclass
class PluginSandboxResult:
    """Result of sandboxed plugin execution."""

    ok: bool
    result: Any = None
    error: Optional[str] = None
    error_type: Optional[str] = None


logger = logging.getLogger(__name__)


def run_plugin_sandboxed(
    tool_fn: Callable,
    *,
    frame_base64: Optional[str] = None,
    device: str = "cpu",
    annotated: bool = False,
    **kwargs: Any,
) -> PluginSandboxResult:
    """
    Execute a plugin tool function in a crash-proof sandbox.

    Catches ALL exceptions and returns structured result.
    Never propagates exceptions to the caller.

    Args:
        tool_fn: The plugin tool function to execute
        frame_base64: Base64-encoded image frame (optional)
        device: Device to use (cpu/cuda)
        annotated: Whether to return annotated results
        **kwargs: Additional arguments to pass to tool_fn

    Returns:
        PluginSandboxResult with ok, result, error, error_type
    """
    try:
        # Prepare arguments
        call_args: Dict[str, Any] = {}
        if frame_base64 is not None:
            call_args["frame"] = frame_base64
        if device:
            call_args["device"] = device
        if annotated:
            call_args["annotated"] = annotated
        call_args.update(kwargs)

        # Execute the tool function
        logger.debug(f"Executing sandboxed plugin: {tool_fn.__name__}")
        result = tool_fn(**call_args)

        return PluginSandboxResult(
            ok=True,
            result=result,
            error=None,
            error_type=None,
        )

    except ImportError as e:
        error_msg = f"Plugin dependency missing: {str(e)}"
        logger.error(f"Sandbox ImportError: {error_msg}")
        return PluginSandboxResult(
            ok=False,
            error=error_msg,
            error_type="ImportError",
        )

    except RuntimeError as e:
        error_msg = f"Plugin runtime error: {str(e)}"
        logger.error(f"Sandbox RuntimeError: {error_msg}")
        return PluginSandboxResult(
            ok=False,
            error=error_msg,
            error_type="RuntimeError",
        )

    except ValueError as e:
        error_msg = f"Plugin value error: {str(e)}"
        logger.error(f"Sandbox ValueError: {error_msg}")
        return PluginSandboxResult(
            ok=False,
            error=error_msg,
            error_type="ValueError",
        )

    except MemoryError as e:
        error_msg = f"Plugin memory exhausted: {str(e)}"
        logger.error(f"Sandbox MemoryError: {error_msg}")
        return PluginSandboxResult(
            ok=False,
            error=error_msg,
            error_type="MemoryError",
        )

    except Exception as e:
        # Catch-all for any other exception
        error_msg = f"Plugin execution failed: {str(e)}"
        logger.exception(f"Sandbox unexpected error: {error_msg}")
        return PluginSandboxResult(
            ok=False,
            error=error_msg,
            error_type=type(e).__name__,
        )


def run_with_timeout(
    tool_fn: Callable,
    timeout_seconds: float = 60.0,
    **kwargs: Any,
) -> PluginSandboxResult:
    """
    Execute plugin with timeout protection.

    Args:
        tool_fn: Function to execute
        timeout_seconds: Maximum execution time (default: 60s)
        **kwargs: Arguments to pass to tool_fn

    Returns:
        PluginSandboxResult
    """
    import concurrent.futures

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_plugin_sandboxed, tool_fn, **kwargs)
            result = future.result(timeout=timeout_seconds)
            return result

    except concurrent.futures.TimeoutError:
        error_msg = f"Plugin execution timed out after {timeout_seconds}s"
        logger.error(f"Sandbox timeout: {error_msg}")
        return PluginSandboxResult(
            ok=False,
            error=error_msg,
            error_type="TimeoutError",
        )

    except Exception as e:
        error_msg = f"Timeout wrapper failed: {str(e)}"
        logger.exception(f"Sandbox timeout error: {error_msg}")
        return PluginSandboxResult(
            ok=False,
            error=error_msg,
            error_type=type(e).__name__,
        )
