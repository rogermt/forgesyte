from typing import Dict, Optional

from app.plugins.base import BasePlugin


class PluginRegistry:
    def __init__(self):
        self._plugins: Dict[str, BasePlugin] = {}

    def register(self, plugin: BasePlugin) -> None:
        """
        Register a plugin after enforcing the BasePlugin contract.
        """

        # Must subclass BasePlugin
        if not isinstance(plugin, BasePlugin):
            raise TypeError(
                f"Plugin '{plugin.__class__.__name__}' must subclass BasePlugin"
            )

        # Validate name
        if not isinstance(plugin.name, str) or not plugin.name.strip():
            raise ValueError(
                f"Plugin '{plugin.__class__.__name__}' must define a non-empty "
                "string 'name'"
            )

        # Validate tools dict
        if not isinstance(plugin.tools, dict):
            raise ValueError(f"Plugin '{plugin.name}' must define 'tools' as a dict")

        for tool_name, handler in plugin.tools.items():
            if not callable(handler):
                raise ValueError(
                    f"Tool '{tool_name}' in plugin '{plugin.name}' must be callable"
                )

        # Validate run_tool exists
        if not hasattr(plugin, "run_tool") or not callable(plugin.run_tool):
            raise ValueError(
                f"Plugin '{plugin.name}' must implement run_tool(tool_name, args)"
            )

        # All good → register
        self._plugins[plugin.name] = plugin

    def get(self, name: str) -> Optional[BasePlugin]:
        return self._plugins.get(name)

    def list(self) -> Dict[str, BasePlugin]:
        return dict(self._plugins)
