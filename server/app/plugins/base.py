from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict


class BasePlugin(ABC):
    """
    Canonical plugin contract for all ForgeSyte plugins.

    Every plugin MUST:
    - Subclass BasePlugin
    - Define `name` (unique plugin identifier)
    - Define `tools` (mapping of tool_name → callable)
    - Implement `run_tool(tool_name, args)`
    - Optionally implement `validate()` for startup checks
    """

    # Required plugin identifier
    name: str

    # Mapping of tool_name → callable
    tools: Dict[str, Callable[..., Any]]

    def __init__(self) -> None:
        # Validate plugin structure immediately on instantiation
        self._validate_plugin_contract()

    # ----------------------------------------------------------------------
    # Contract enforcement
    # ----------------------------------------------------------------------

    def _validate_plugin_contract(self) -> None:
        """
        Validate plugin structure at load time.
        Raises explicit errors if plugin is malformed.
        """

        if not hasattr(self, "name") or not isinstance(self.name, str):
            raise ValueError(
                f"{self.__class__.__name__} must define a string attribute `name`"
            )

        if not hasattr(self, "tools") or not isinstance(self.tools, dict):
            raise ValueError(
                f"{self.__class__.__name__} must define a dict attribute `tools`"
            )

        for tool_name, handler in self.tools.items():
            if not callable(handler):
                raise ValueError(
                    f"Tool '{tool_name}' in plugin '{self.name}' must be callable"
                )

    # ----------------------------------------------------------------------
    # Required API
    # ----------------------------------------------------------------------

    @abstractmethod
    def run_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """
        Execute a tool by name.

        Must:
        - Validate tool exists
        - Validate args
        - Execute tool handler
        - Return JSON-serializable result
        - Raise PluginExecutionError on failure
        """
        raise NotImplementedError

    # ----------------------------------------------------------------------
    # Optional lifecycle hook
    # ----------------------------------------------------------------------

    def validate(self) -> None:  # noqa: B027
        """
        Optional plugin-level validation hook.

        Plugins may override this to:
        - Load models
        - Check file paths
        - Check GPU availability
        - Preload resources
        - Validate configuration

        Called once at plugin registration time.
        """
        pass
