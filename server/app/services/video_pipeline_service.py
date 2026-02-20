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

        for idx, tool_name in enumerate(tools):
            # Validate tool exists
            if tool_name not in plugin.tools:
                raise ValueError(
                    f"Tool '{tool_name}' not found in plugin '{plugin_id}'"
                )

            # Execute tool
            output = plugin.run_tool(tool_name, current_payload)

            # -----------------------------------------
            # PHASE‑13 COMMIT 8: Logging for observability
            # -----------------------------------------
            logger.info(
                "Video pipeline step",
                extra={
                    "plugin_id": plugin_id,
                    "tool_name": tool_name,
                    "step": idx,
                },
            )

            # Record step
            steps.append({"tool": tool_name, "output": output})

            # Prepare payload for next tool
            # Pass original payload + previous tool output as "input"
            current_payload = {**payload, "input": output}

        # Final output is the last tool's output
        return {"result": steps[-1]["output"], "steps": steps}

    def run_on_file(
        self, file_path: str, plugin_id: str, tools: List[str]
    ) -> Dict[str, Any]:
        """Phase-16 compatibility: run a pipeline using a file path.

        Args:
            file_path: Path to the video file to process
            plugin_id: The plugin to execute tools from
            tools: List of tool names to execute in order

        Returns:
            Dictionary with result and steps from pipeline execution
        """
        payload = {"file_path": file_path}
        return self.run_pipeline(plugin_id, tools, payload)

    def run(self, file_path: str, plugin_id: str, tools: List[str]) -> Dict[str, Any]:
        """Alias used by some worker implementations.

        Args:
            file_path: Path to the video file to process
            plugin_id: The plugin to execute tools from
            tools: List of tool names to execute in order

        Returns:
            Dictionary with result and steps from pipeline execution
        """
        return self.run_on_file(file_path, plugin_id, tools)

    def run_on_payload(
        self, payload: Dict[str, Any], plugin_id: str, tools: List[str]
    ) -> Dict[str, Any]:
        """Optional compatibility wrapper for payload-based execution.

        Args:
            payload: Initial payload dictionary
            plugin_id: The plugin to execute tools from
            tools: List of tool names to execute in order

        Returns:
            Dictionary with result and steps from pipeline execution
        """
        return self.run_pipeline(plugin_id, tools, payload)

    def _validate(self, plugin_id: str, tools: List[str]) -> None:
        """Validate plugin_id and tools[] exist.

        Args:
            plugin_id: Plugin identifier to validate
            tools: List of tool names to validate

        Raises:
            ValueError: If validation fails
        """
        pass
