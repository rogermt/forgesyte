"""Vision analysis service for WebSocket streaming.

v0.9.3 — Rewritten to use the unified plugin system.
This service is used ONLY for the /v1/stream WebSocket endpoint.
It performs real-time per-frame analysis by calling plugin.run_tool()
directly on each incoming frame.

The service depends on Protocols (PluginRegistry, WebSocketProvider) rather than
concrete implementations, making it easily testable and extensible.

Example:
    from .vision_analysis import VisionAnalysisService
    from .plugin_management_service import PluginManagementService

    plugin_service = PluginManagementService(plugin_registry)
    service = VisionAnalysisService(plugin_service, ws_manager)
"""

import base64
import logging
import time
import uuid
from typing import Any, Dict

from ..protocols import WebSocketProvider
from .plugin_management_service import PluginManagementService

logger = logging.getLogger(__name__)


class VisionAnalysisService:
    """Orchestrates real-time image analysis using registered plugins.

    Handles the core loop: receiving frames, decoding, timing execution,
    dispatching to plugins, and sending results back to clients.

    Depends on Protocols for flexibility and testability:
    - PluginManagementService: Abstracts plugin execution
    - WebSocketProvider: Abstracts message delivery mechanism
    """

    def __init__(
        self, plugin_service: PluginManagementService, ws_manager: WebSocketProvider
    ) -> None:
        """Initialize vision analysis service with dependencies.

        Args:
            plugin_service: Plugin management service for executing tools
            ws_manager: WebSocket manager (implements WebSocketProvider protocol)

        Raises:
            TypeError: If plugin_service or ws_manager don't have required methods
        """
        self.plugin_service = plugin_service
        self.ws_manager = ws_manager

        logger.debug("VisionAnalysisService initialized")

    async def handle_frame(
        self, client_id: str, plugin_name: str, data: Dict[str, Any]
    ) -> None:
        """Process a single frame through a vision plugin.

        Orchestrates the complete analysis pipeline:
        1. Decode base64 image data
        2. Time the analysis execution
        3. Execute plugin analysis
        4. Send results back to client
        5. Handle errors gracefully

        Args:
            client_id: Unique client identifier
            plugin_name: Name of plugin to use
            data: Frame data dict with 'data' (base64) and optional 'options'
                  {"data": "<base64>", "options": {...}, "frame_id": "...", "tools": [...]}

        Raises:
            PluginNotFoundError: If plugin doesn't exist (sent to client)
            PluginExecutionError: If plugin.run_tool() fails (sent to client)
        """
        # Generate frame ID if not provided
        frame_id = data.get("frame_id", str(uuid.uuid4()))

        try:
            # Decode base64 image data
            # Accept both 'image_data' (client) and 'data' (legacy) field names
            image_data = data.get("image_data") or data.get("data")
            if not image_data:
                raise ValueError(
                    "Frame data missing required field: 'image_data' or 'data'"
                )

            image_bytes = base64.b64decode(image_data)
            logger.debug(
                "Frame decoded",
                extra={"client_id": client_id, "size_bytes": len(image_bytes)},
            )

            # Time the analysis execution
            start_time = time.time()

            # Get tools from request
            tools = data.get("tools")
            if not tools:
                raise ValueError("WebSocket frame missing 'tools' field")

            # Execute each tool sequentially and collect results
            # For streaming, we typically run one tool per frame
            results = []
            for tool_name in tools:
                tool_result = self.plugin_service.run_plugin_tool(
                    plugin_id=plugin_name,
                    tool_name=tool_name,
                    args={
                        "image_bytes": image_bytes,
                        "options": data.get("options", {}),
                    },
                )
                results.append(tool_result)

            # Use the last result as the final output
            final_output = results[-1] if results else {}

            processing_time = (time.time() - start_time) * 1000

            # Send results back to client
            await self.ws_manager.send_frame_result(
                client_id, frame_id, plugin_name, final_output, processing_time
            )

            logger.info(
                "Frame analysis completed",
                extra={
                    "client_id": client_id,
                    "plugin": plugin_name,
                    "frame_id": frame_id,
                    "processing_time_ms": processing_time,
                },
            )

        except ValueError as e:
            # Validation error (missing fields, bad base64, etc)
            error_msg = f"Invalid frame data: {str(e)}"
            logger.error(
                "Frame validation failed",
                extra={"client_id": client_id, "error": str(e)},
            )
            await self.ws_manager.send_personal(
                client_id,
                {"type": "error", "message": error_msg, "frame_id": frame_id},
            )

        except Exception as e:
            # Plugin execution error
            error_msg = f"Analysis failed: {str(e)}"
            logger.exception(
                "Frame analysis failed",
                extra={
                    "client_id": client_id,
                    "plugin": plugin_name,
                    "frame_id": frame_id,
                    "error": str(e),
                },
            )
            await self.ws_manager.send_personal(
                client_id,
                {"type": "error", "message": error_msg, "frame_id": frame_id},
            )

    async def list_available_plugins(self) -> Dict[str, Any]:
        """Get list of available plugins with their metadata.

        Returns:
            Dictionary mapping plugin names to their metadata

        Raises:
            RuntimeError: If plugin list cannot be retrieved
        """
        try:
            result = await self.plugin_service.list_plugins()
            logger.debug("Listed plugins", extra={"count": len(result)})
            return result
        except Exception as e:
            logger.error(
                "Failed to list plugins",
                extra={"error": str(e)},
            )
            return {}