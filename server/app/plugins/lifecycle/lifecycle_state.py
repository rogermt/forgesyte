"""Lifecycle state definitions for Phase 11.

Defines the 5 lifecycle states: LOADED, INITIALIZED, RUNNING, FAILED, UNAVAILABLE.
"""

from enum import Enum


class PluginLifecycleState(str, Enum):
    """Plugin lifecycle states.

    States are unidirectional and final once FAILED/UNAVAILABLE.
    """

    LOADED = "LOADED"
    INITIALIZED = "INITIALIZED"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"
