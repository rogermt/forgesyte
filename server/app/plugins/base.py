from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

logger = logging.getLogger(__name__)


class BasePlugin(ABC):
    """
    Canonical plugin contract for all ForgeSyte plugins.

    Every plugin MUST:
    - Subclass BasePlugin
    - Define `name` (unique plugin identifier)
    - Define `tools` (mapping of tool_name → metadata dict)
      where each tool has:
        - handler: callable
        - description: str
        - input_schema: dict
        - output_schema: dict
    - Implement `run_tool(tool_name, args)`
    - Optionally implement `validate()` for startup checks
    """

    # Required plugin identifier
    name: str

    # Mapping of tool_name → metadata dict
    tools: Dict[str, Dict[str, Any]]

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

        has_name = hasattr(self, "name")
        name_value = getattr(self, "name", None) if has_name else None
        is_str = isinstance(name_value, str) if has_name else False

        if not has_name or not is_str:
            logger.error(
                "Plugin name validation failed",
                extra={
                    "plugin_class": self.__class__.__name__,
                    "plugin_module": self.__class__.__module__,
                    "has_name_attribute": has_name,
                    "name_value": name_value,
                    "name_type": str(type(name_value)),
                },
            )
            raise ValueError(
                f"{self.__class__.__name__} must define a string attribute `name`. "
                f"Got: has_name={has_name}, type={type(name_value).__name__}"
            )

        has_tools = hasattr(self, "tools")
        tools_value = getattr(self, "tools", None) if has_tools else None
        is_dict = isinstance(tools_value, dict) if has_tools else False

        if not has_tools or not is_dict:
            logger.error(
                "Plugin tools validation failed",
                extra={
                    "plugin_class": self.__class__.__name__,
                    "plugin_module": self.__class__.__module__,
                    "plugin_file": getattr(self.__class__, "__file__", "unknown"),
                    "has_tools_attribute": has_tools,
                    "tools_value": tools_value,
                    "tools_type": str(type(tools_value)),
                    "tools_is_dict": is_dict,
                    "plugin_instance_dict_keys": list(self.__dict__.keys()),
                    "plugin_class_dict_keys": [
                        k for k in dir(self.__class__) if not k.startswith("_")
                    ],
                    "all_instance_attributes": [
                        k for k in dir(self) if not k.startswith("_")
                    ],
                },
            )
            raise ValueError(
                f"{self.__class__.__name__} must define a dict attribute `tools`. "
                f"Got: has_tools={has_tools}, type={type(tools_value).__name__}"
            )

        for tool_name, meta in self.tools.items():
            if not isinstance(meta, dict):
                raise ValueError(
                    f"Tool '{tool_name}' in plugin '{self.name}' "
                    "must be a dict of metadata"
                )

            handler = meta.get("handler")

            # Resolve string handler to bound method
            if isinstance(handler, str):
                resolved_handler = getattr(self, handler, None)
                if resolved_handler is None:
                    logger.error(
                        "Plugin handler method not found",
                        extra={
                            "plugin_name": self.name,
                            "plugin_class": self.__class__.__name__,
                            "tool_name": tool_name,
                            "handler_name": handler,
                            "available_methods": [
                                m for m in dir(self) if not m.startswith("_")
                            ],
                        },
                    )
                    raise ValueError(
                        f"Tool '{tool_name}' in plugin '{self.name}' "
                        f"references non-existent method '{handler}'"
                    )
                handler = resolved_handler

            # Final callable check
            if not callable(handler):
                logger.error(
                    "Plugin handler validation failed",
                    extra={
                        "plugin_name": self.name,
                        "plugin_class": self.__class__.__name__,
                        "plugin_module": self.__class__.__module__,
                        "tool_name": tool_name,
                        "handler_value": handler,
                        "handler_type": str(type(handler)),
                        "handler_is_string": isinstance(handler, str),
                        "handler_is_method": (
                            hasattr(handler, "__self__") if handler else False
                        ),
                        "tool_metadata_keys": list(meta.keys()),
                        "plugin_methods": [
                            m for m in dir(self) if not m.startswith("_")
                        ],
                    },
                )
                raise ValueError(
                    f"Tool '{tool_name}' in plugin '{self.name}' "
                    "must define a callable 'handler'"
                )

            if "description" not in meta or not isinstance(meta["description"], str):
                raise ValueError(
                    f"Tool '{tool_name}' in plugin '{self.name}' "
                    "must define a string 'description'"
                )

            if "input_schema" not in meta or not isinstance(meta["input_schema"], dict):
                raise ValueError(
                    f"Tool '{tool_name}' in plugin '{self.name}' "
                    "must define a dict 'input_schema'"
                )

            if "output_schema" not in meta or not isinstance(
                meta["output_schema"], dict
            ):
                raise ValueError(
                    f"Tool '{tool_name}' in plugin '{self.name}' "
                    "must define a dict 'output_schema'"
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
