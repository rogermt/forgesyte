"""Vision analysis service for WebSocket streaming.

v0.13.0 — Upgraded to use Ray Actors for real-time streaming.
This service is used ONLY for the /v1/stream WebSocket endpoint.
It performs real-time per-frame analysis using long-lived Ray Actors
that hold plugin models in GPU memory across frames.

Architecture:
    WebSocket Frame → VisionAnalysisService → StreamingToolActor (GPU)
                                                          ↓
                                                  process_frame.remote()
                                                          ↓
                                                  Plugin executed with
                                                  cached model in VRAM

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
from typing import Any, Dict, List

import ray

from ..protocols import WebSocketProvider
from .plugin_management_service import PluginManagementService

logger = logging.getLogger(__name__)


class VisionAnalysisService:
    """Orchestrates real-time image analysis using registered plugins.

    Handles the core loop: receiving frames, decoding, timing execution,
    dispatching to plugins, and sending results back to clients.

    v0.13.0: Now uses Ray Actors to cache plugin models in GPU memory
    across frames, enabling near-zero latency for real-time streaming.

    Depends on Protocols for flexibility and testability:
    - PluginManagementService: Abstracts plugin execution
    - WebSocketProvider: Abstracts message delivery mechanism

    Attributes:
        plugin_service: Plugin management service for executing tools
        ws_manager: WebSocket manager for client communication
        active_actors: Dict mapping client_id -> {tool_name: actor_handle}
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
        # Track active Ray actors: client_id -> {tool_name: actor_handle}
        self.active_actors: Dict[str, Dict[str, Any]] = {}

        logger.debug("VisionAnalysisService initialized")

    def _get_or_create_actor(
        self, client_id: str, plugin_name: str, tool_name: str
    ) -> Any:
        """Get or create a Ray Actor for a specific client/tool combination.

        This method implements lazy initialization with caching:
        - First call creates a new actor
        - Subsequent calls return the cached actor

        Args:
            client_id: Unique client identifier
            plugin_name: Plugin identifier
            tool_name: Tool name within the plugin

        Returns:
            Ray Actor handle for the StreamingToolActor
        """
        from ..workers.ray_actors import StreamingToolActor

        if client_id not in self.active_actors:
            self.active_actors[client_id] = {}

        if tool_name not in self.active_actors[client_id]:
            logger.info(f"Spawning Ray Actor for client {client_id}, tool {tool_name}")
            # StreamingToolActor.remote is dynamically created by @ray.remote
            actor = StreamingToolActor.remote(plugin_name, tool_name)  # type: ignore[attr-defined]
            self.active_actors[client_id][tool_name] = actor

        return self.active_actors[client_id][tool_name]

    async def cleanup_client(self, client_id: str) -> None:
        """Kill all Ray actors associated with a disconnected client.

        This method MUST be called when a WebSocket disconnects to
        free GPU VRAM. Otherwise, actors will leak and exhaust GPU memory.

        Args:
            client_id: Unique client identifier
        """
        if client_id in self.active_actors:
            if ray.is_initialized():
                for tool_name, actor in self.active_actors[client_id].items():
                    logger.info(
                        f"Killing Ray Actor for client {client_id}, tool {tool_name}"
                    )
                    ray.kill(actor)
            del self.active_actors[client_id]

    async def handle_frame(
        self, client_id: str, plugin_name: str, data: Dict[str, Any]
    ) -> None:
        """Process a single frame through a vision plugin.

        Orchestrates the complete analysis pipeline:
        1. Decode base64 image data
        2. Time the analysis execution
        3. Execute plugin analysis (via Ray Actor if available)
        4. Send results back to client
        5. Handle errors gracefully

        v0.13.0: Uses Ray Actors for GPU-accelerated streaming when
        Ray is initialized. Falls back to local execution otherwise.

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

            # Check if Ray is available for GPU-accelerated streaming
            use_ray = ray.is_initialized()

            # Execute each tool and collect results
            # v0.10.1: True multi-tool streaming – one frame, many tools, merged result
            # v0.13.0: Use Ray Actors when available for GPU caching
            merged_results: Dict[str, Any] = {}
            for tool_name in tools:
                args = {
                    "image_bytes": image_bytes,
                    "options": data.get("options", {}),
                }

                if use_ray:
                    # Use cached Ray Actor for GPU-accelerated processing
                    actor = self._get_or_create_actor(client_id, plugin_name, tool_name)
                    future = actor.process_frame.remote(args)
                    tool_result = ray.get(future)
                else:
                    # Fallback to local synchronous execution
                    tool_result = self.plugin_service.run_plugin_tool(
                        plugin_id=plugin_name,
                        tool_name=tool_name,
                        args=args,
                    )
                merged_results[tool_name] = tool_result

            # Build a canonical multi-tool payload
            # Frontend can read per-tool results from output["tools"][tool_name]
            final_output: Dict[str, Any] = {
                "tools": merged_results,
                "tool_order": tools,
            }

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

    async def list_available_plugins(self) -> List[Any]:
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
            return []
