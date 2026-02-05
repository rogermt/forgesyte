"""Sandbox module for Phase 11 plugin crash protection.

Provides exception isolation for plugin execution with timeout and memory guards.
"""

from .memory_guard import (
    DEFAULT_MEMORY_LIMIT_BYTES,
    check_memory_limit,
    format_memory_bytes,
    get_memory_usage_bytes,
    run_with_memory_guard,
)
from .sandbox_runner import run_plugin_sandboxed
from .timeout import run_sandboxed_with_timeout, run_with_timeout

__all__ = [
    "run_plugin_sandboxed",
    "run_with_timeout",
    "run_sandboxed_with_timeout",
    "run_with_memory_guard",
    "get_memory_usage_bytes",
    "check_memory_limit",
    "format_memory_bytes",
    "DEFAULT_MEMORY_LIMIT_BYTES",
]
