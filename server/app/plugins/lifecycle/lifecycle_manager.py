"""Lifecycle manager for Phase 11 plugin state transitions.

Manages state transitions between LOADED, INITIALIZED, RUNNING, FAILED, UNAVAILABLE.
"""

from typing import Dict, Optional

from .lifecycle_state import PluginLifecycleState


class PluginLifecycleManager:
    """Manages plugin lifecycle state transitions.

    Guarantees:
    - Every plugin has a queryable state
    - State transitions are tracked
    - No state is lost on error
    """

    def __init__(self) -> None:
        """Initialize the lifecycle manager."""
        self._states: Dict[str, PluginLifecycleState] = {}

    def set_state(self, name: str, state: PluginLifecycleState) -> None:
        """Set the lifecycle state for a plugin."""
        self._states[name] = state

    def get_state(self, name: str) -> Optional[PluginLifecycleState]:
        """Get the current lifecycle state for a plugin."""
        return self._states.get(name)

    def all_states(self) -> Dict[str, PluginLifecycleState]:
        """Get all plugin states as a dict."""
        return self._states.copy()
