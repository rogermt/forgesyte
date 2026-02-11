"""Test helpers for Phase 13 - FakeRegistry and FakePlugin.

These fakes are used for testing the VideoPipelineService and related components.
"""

from typing import Any, Dict, Optional


class FakePlugin:
    """Fake plugin for testing."""

    def __init__(self):
        self.id = "test-plugin"
        self.name = "Test Plugin"
        self.tools = {
            "detect_players": "detect_players",
            "track_players": "track_players",
            "annotate_frame": "annotate_frame",
        }

    def run_tool(self, tool_name: str, args: Dict) -> Dict:
        """Execute a tool and return result."""
        return {"tool": tool_name, "step_completed": tool_name, **args}


class FakeRegistry:
    """Fake plugin registry for testing."""

    def __init__(self, plugin: Optional[FakePlugin] = None):
        self._plugin = plugin

    def get(self, plugin_id: str) -> Optional[FakePlugin]:
        """Get a plugin by name."""
        return self._plugin

    def list(self) -> Dict[str, Dict[str, Any]]:
        """List all plugins."""
        if self._plugin:
            return {
                self._plugin.id: {
                    "name": self._plugin.name,
                    "tools": self._plugin.tools,
                }
            }
        return {}
