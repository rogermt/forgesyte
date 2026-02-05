"""Memory guard for Phase 11 plugin execution.

Provides memory usage monitoring and limits for plugin tool execution.
"""

import gc
import logging
import sys
from dataclasses import dataclass
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# Default memory limit: 1 GB (in bytes)
DEFAULT_MEMORY_LIMIT_BYTES = 1024 * 1024 * 1024


@dataclass
class MemoryGuardResult:
    """Result of memory-guarded plugin execution."""

    ok: bool
    result: Any = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    memory_exceeded: bool = False
    memory_limit_bytes: int = DEFAULT_MEMORY_LIMIT_BYTES
    peak_memory_bytes: int = 0


def get_memory_usage_bytes() -> int:
    """Get current process memory usage in bytes.

    Returns:
        Current memory usage in bytes, or 0 if unavailable.
    """
    try:
        import psutil

        process = psutil.Process()
        return process.memory_info().rss
    except ImportError:
        # Fallback: use gc.get_objects() approximate size
        return sum(sys.getsizeof(obj) for obj in gc.get_objects())
    except Exception:
        return 0


def run_with_memory_guard(
    tool_fn: Callable,
    memory_limit_bytes: int = DEFAULT_MEMORY_LIMIT_BYTES,
    **kwargs: Any,
) -> MemoryGuardResult:
    """
    Execute a plugin tool function with memory usage monitoring.

    Args:
        tool_fn: The plugin tool function to execute
        memory_limit_bytes: Maximum memory allowed (default: 1 GB)
        **kwargs: Additional arguments to pass to tool_fn

    Returns:
        MemoryGuardResult with ok, result, error, error_type, and memory info
    """
    # Force garbage collection before execution
    gc.collect()

    # Record starting memory
    start_memory = get_memory_usage_bytes()
    logger.debug(
        f"Starting memory: {start_memory / (1024*1024):.2f} MB",
        extra={"start_memory_mb": start_memory / (1024 * 1024)},
    )

    try:
        # Execute the tool function
        result = tool_fn(**kwargs)

        # Record peak memory after execution
        peak_memory = get_memory_usage_bytes()

        # Check if memory limit was exceeded during execution
        memory_exceeded = peak_memory > memory_limit_bytes

        if memory_exceeded:
            error_msg = (
                f"Memory limit exceeded: {peak_memory / (1024*1024):.2f} MB "
                f"(limit: {memory_limit_bytes / (1024*1024):.2f} MB)"
            )
            logger.warning(f"Memory limit exceeded: {error_msg}")
            return MemoryGuardResult(
                ok=False,
                error=error_msg,
                error_type="MemoryLimitExceeded",
                memory_exceeded=True,
                memory_limit_bytes=memory_limit_bytes,
                peak_memory_bytes=peak_memory,
            )

        logger.debug(
            f"Peak memory: {peak_memory / (1024*1024):.2f} MB",
            extra={"peak_memory_mb": peak_memory / (1024 * 1024)},
        )

        return MemoryGuardResult(
            ok=True,
            result=result,
            memory_exceeded=False,
            memory_limit_bytes=memory_limit_bytes,
            peak_memory_bytes=peak_memory,
        )

    except MemoryError as e:
        peak_memory = get_memory_usage_bytes()
        error_msg = (
            f"Plugin exhausted memory: {str(e)} "
            f"(peak: {peak_memory / (1024*1024):.2f} MB, "
            f"limit: {memory_limit_bytes / (1024*1024):.2f} MB)"
        )
        logger.error(f"MemoryError: {error_msg}")
        return MemoryGuardResult(
            ok=False,
            error=error_msg,
            error_type="MemoryError",
            memory_exceeded=True,
            memory_limit_bytes=memory_limit_bytes,
            peak_memory_bytes=peak_memory,
        )

    except Exception as e:
        logger.exception(f"Memory guard error: {str(e)}")
        return MemoryGuardResult(
            ok=False,
            error=str(e),
            error_type=type(e).__name__,
            memory_limit_bytes=memory_limit_bytes,
            peak_memory_bytes=get_memory_usage_bytes(),
        )


def check_memory_limit(
    memory_limit_bytes: int = DEFAULT_MEMORY_LIMIT_BYTES,
) -> tuple[bool, int]:
    """
    Check if current memory usage is within limits.

    Args:
        memory_limit_bytes: Maximum memory allowed

    Returns:
        Tuple of (is_within_limit, current_memory_bytes)
    """
    current_memory = get_memory_usage_bytes()
    return current_memory <= memory_limit_bytes, current_memory


def format_memory_bytes(bytes_value: int) -> str:
    """Format memory value in human-readable format.

    Args:
        bytes_value: Memory in bytes

    Returns:
        Formatted string (e.g., "1.50 GB")
    """
    if bytes_value >= 1024 * 1024 * 1024:
        return f"{bytes_value / (1024*1024*1024):.2f} GB"
    elif bytes_value >= 1024 * 1024:
        return f"{bytes_value / (1024*1024):.2f} MB"
    elif bytes_value >= 1024:
        return f"{bytes_value / 1024:.2f} KB"
    return f"{bytes_value} B"
