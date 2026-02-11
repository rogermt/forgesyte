"""VideoPipelineService for Phase 13 - Multi-Tool Linear Pipelines.

This service executes linear, single-plugin tool pipelines for the VideoTracker.
"""

import logging
from typing import Any, Dict, List

from ..protocols import PluginRegistry

logger = logging.getLogger(__name__)


class VideoPipelineService:
    """Executes linear multi-tool pipelines for VideoTracker."""

    def __init__(self, plugins: PluginRegistry) -> None:
        """Initialize the pipeline service with a plugin registry.

        Args:
            plugins: Plugin registry implementing PluginRegistry protocol
        """
        self.plugins = plugins

    def run_pipeline(
        self, plugin_id: str, tools: List[str], payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tools sequentially, chaining outputs.

        Args:
            plugin_id: The plugin to execute tools from
            tools: List of tool names to execute in order
            payload: Initial payload dictionary

        Returns:
            Dictionary with:
                - result: Output from the last tool execution
                - steps: List of step outputs for debugging

        Raises:
            ValueError: If plugin not found, tools is empty, or tool not in plugin
        """
        # Validate plugin
        plugin = self.plugins.get(plugin_id)
        if plugin is None:
            raise ValueError(f"Plugin '{plugin_id}' not found")

        # Validate tools[]
        if not tools or not isinstance(tools, list):
            raise ValueError("Pipeline requires a non-empty tools[] array")

        steps: List[Dict[str, Any]] = []
        current_payload = payload

        for tool_name in tools:
            # Validate tool exists
            if tool_name not in plugin.tools:
                raise ValueError(
                    f"Tool '{tool_name}' not found in plugin '{plugin_id}'"
                )

            # Execute tool
            output = plugin.run_tool(tool_name, current_payload)

            # Minimal debug logging
            logger.debug(
                f"[Pipeline] Executed {plugin_id}:{tool_name}, output keys={list(output.keys())}"
            )

            # Record step
            steps.append({"tool": tool_name, "output": output})

            # Prepare payload for next tool
            # Pass original payload + previous tool output as "input"
            current_payload = {**payload, "input": output}

        # Final output is the last tool's output
        return {"result": steps[-1]["output"], "steps": steps}

    def _validate(self, plugin_id: str, tools: List[str]) -> None:
        """Validate plugin_id and tools[] exist.

        Args:
            plugin_id: Plugin identifier to validate
            tools: List of tool names to validate

        Raises:
            ValueError: If validation fails
        """
        pass
