"""Ray actors for real-time WebSocket streaming (Phase C).

v0.13.0: Long-lived Ray Actors for holding plugin state in GPU memory
across frames, enabling near-zero latency real-time streaming.

Architecture:
    WebSocket Frame → VisionAnalysisService → StreamingToolActor (GPU)
                                                      ↓
                                              process_frame.remote()
                                                      ↓
                                              Plugin executed with
                                              cached model in VRAM

The Actor lifecycle is managed by VisionAnalysisService:
    - Created on first frame (lazy initialization)
    - Reused for subsequent frames (caching)
    - Killed on WebSocket disconnect (cleanup)
"""

import logging
from typing import Any, Dict

import ray

logger = logging.getLogger(__name__)


# Fractional GPU allocation: 0.25 allows up to 4 concurrent actors per GPU.
# This prevents CPU-only scheduling while avoiding deadlock from full GPU
# reservation when multiple tools are requested per WebSocket.
@ray.remote(num_gpus=0.25)
class StreamingToolActor:
    """Ray Actor for holding plugin state in memory across frames.

    This actor is created when a WebSocket client connects and requests
    a specific tool. The actor loads the plugin once and holds the model
    in GPU VRAM, enabling near-zero latency for subsequent frames.

    Lifecycle:
        1. Created by VisionAnalysisService._get_or_create_actor()
        2. Calls plugin.validate() to preload models into VRAM
        3. Processes frames via process_frame()
        4. Killed by VisionAnalysisService.cleanup_client()

    Attributes:
        plugin_id: The plugin identifier (e.g., "object-tracker")
        tool_name: The tool name (e.g., "player_detection")
        registry: PluginRegistry instance for loading plugins
        plugin_service: PluginManagementService for tool execution
    """

    def __init__(self, plugin_id: str, tool_name: str):
        """Initialize the actor with a specific plugin and tool.

        Args:
            plugin_id: Plugin identifier
            tool_name: Tool name within the plugin

        Raises:
            RuntimeError: If plugin or tool cannot be loaded
        """
        from app.plugin_loader import PluginRegistry
        from app.services.plugin_management_service import PluginManagementService

        logger.info(f"Initializing StreamingToolActor for {plugin_id}.{tool_name}")
        self.plugin_id = plugin_id
        self.tool_name = tool_name

        # Ray workers run in separate processes - must load plugins locally.
        # Wrap entire setup in try to ensure all failures yield RuntimeError.
        try:
            # PluginRegistry from app.plugin_loader has load_plugins() method.
            self.registry = PluginRegistry()
            self.registry.load_plugins()
            self.plugin_service = PluginManagementService(self.registry)  # type: ignore[arg-type]

            # Instantiate plugin and validate tool exists
            plugin = self.plugin_service.get_plugin_instance(self.plugin_id)

            # Validate tool exists in plugin
            if not hasattr(plugin, "tools") or tool_name not in plugin.tools:
                available = (
                    list(plugin.tools.keys()) if hasattr(plugin, "tools") else []
                )
                raise ValueError(
                    f"Tool '{tool_name}' not found in plugin '{plugin_id}'. "
                    f"Available: {available}"
                )

            # Run validation to preload models into VRAM
            if hasattr(plugin, "validate"):
                plugin.validate()
                logger.info(f"Plugin {plugin_id} validated, models preloaded into VRAM")
        except Exception as e:
            raise RuntimeError(
                f"Actor initialization failed for {plugin_id}.{tool_name}: {e}"
            ) from e

    def process_frame(self, args: Dict[str, Any]) -> Any:
        """Process a single frame synchronously within the long-lived actor.

        This method is called for each incoming frame from the WebSocket.
        The plugin's model is already loaded in VRAM, so execution is fast.

        Args:
            args: Arguments dict with:
                - image_bytes: Raw image bytes
                - options: Optional plugin-specific options

        Returns:
            Raw result from plugin tool execution (dict, list, str, etc.)

        Raises:
            RuntimeError: If tool execution fails
        """
        try:
            result = self.plugin_service.run_plugin_tool(
                self.plugin_id, self.tool_name, args, progress_callback=None
            )
            return result
        except Exception as e:
            logger.error(
                f"StreamingToolActor.process_frame failed for "
                f"{self.plugin_id}.{self.tool_name}: {e}"
            )
            raise RuntimeError(f"Frame processing failed: {e}") from e
