"""Plugin execution service that wraps ToolRunner for execution delegation.

This service:
- Wraps ToolRunner (plugin.run_tool)
- Delegates execution without calling plugin.run() directly
- Does NOT manage lifecycle or metrics
- Validates input/output as per Phase 12 requirements

Execution Chain:
    JobExecutionService → PluginExecutionService → ToolRunner
"""

import asyncio
import logging
from typing import Any, Callable, Dict

from app.core.validation.execution_validation import (
    InputValidationError,
    OutputValidationError,
    validate_input_payload,
    validate_plugin_output,
)
from app.exceptions import PluginExecutionError

logger = logging.getLogger(__name__)


class PluginExecutionService:
    """Service for executing plugin tools via ToolRunner delegation.

    Responsibilities:
    - Validate input payload before execution
    - Delegate to ToolRunner (plugin.run_tool)
    - Validate plugin output after execution
    - Return validated result or raise appropriate error

    Does NOT:
    - Call plugin.run() directly
    - Manage job lifecycle (handled by JobExecutionService)
    - Track metrics (handled by PluginRegistry)
    """

    def __init__(self, tool_runner: Callable[..., Any]):
        """Initialize plugin execution service with a ToolRunner.

        Args:
            tool_runner: A callable that executes tools (e.g., plugin.run_tool)
        """
        self._tool_runner = tool_runner
        logger.debug("PluginExecutionService initialized")

    async def execute_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        mime_type: str = "image/png",
    ) -> Dict[str, Any]:
        """Execute a tool via ToolRunner delegation.

        Validates input, delegates to ToolRunner, validates output,
        and returns the validated result.

        Args:
            tool_name: Name of the tool to execute
            args: Tool-specific arguments dictionary
            mime_type: MIME type of the input (default: "image/png")

        Returns:
            Validated output dictionary from plugin execution

        Raises:
            InputValidationError: If input payload is invalid
            OutputValidationError: If plugin output is invalid
            PluginExecutionError: If ToolRunner execution fails
        """
        # Step 1: Validate input payload
        input_payload = {
            "image": args.get("image"),
            "mime_type": mime_type,
        }
        try:
            validate_input_payload(input_payload)
        except InputValidationError as e:
            logger.warning(
                "Input validation failed",
                extra={"tool_name": tool_name, "error": str(e)},
            )
            raise

        # Step 2: Delegate to ToolRunner (plugin.run_tool)
        try:
            logger.debug(
                "Delegating to ToolRunner",
                extra={"tool_name": tool_name},
            )
            raw_result = await self._tool_runner(tool_name, args)
        except Exception as e:
            logger.error(
                "ToolRunner execution failed",
                extra={"tool_name": tool_name, "error": str(e)},
            )
            raise PluginExecutionError(
                plugin_name=tool_name,
                message=f"Tool execution failed: {str(e)}",
                original_error=e,
            ) from e

        # Step 3: Validate plugin output
        try:
            validated_result = validate_plugin_output(raw_result)
        except OutputValidationError as e:
            logger.warning(
                "Output validation failed",
                extra={"tool_name": tool_name, "error": str(e)},
            )
            raise

        logger.info(
            "Tool execution completed successfully",
            extra={"tool_name": tool_name},
        )

        return validated_result

    async def execute_tool_sync(
        self,
        tool_name: str,
        args: Dict[str, Any],
        mime_type: str = "image/png",
    ) -> Dict[str, Any]:
        """Synchronous version of execute_tool for compatibility.

        Some callers may need synchronous execution (e.g., thread pool).
        Note: This method is async to allow awaiting tool_runner if it's async.

        Args:
            tool_name: Name of the tool to execute
            args: Tool-specific arguments dictionary
            mime_type: MIME type of the input (default: "image/png")

        Returns:
            Validated output dictionary from plugin execution
        """
        # For sync execution, we assume the tool_runner is already
        # configured for sync use (e.g., running in thread pool)
        input_payload = {
            "image": args.get("image"),
            "mime_type": mime_type,
        }
        validate_input_payload(input_payload)

        try:
            # Handle both sync and async tool runners
            if asyncio.iscoroutinefunction(self._tool_runner):
                raw_result = await self._tool_runner(tool_name, args)
            else:
                raw_result = self._tool_runner(tool_name, args)
        except Exception as e:
            raise PluginExecutionError(
                plugin_name=tool_name,
                message=f"Tool execution failed: {str(e)}",
                original_error=e,
            ) from e

        return validate_plugin_output(raw_result)
