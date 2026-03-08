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

# Note: We omit num_gpus=1 here because a single WebSocket might request
# multiple tools. Ray scheduling would deadlock if they all demanded a full GPU.
# Instead, we let Ray's resource scheduler handle GPU allocation based on
# the actual plugin requirements.


@ray.remote
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

        # Initialize plugin registry and service
        self.registry = PluginRegistry()
        self.registry.load_plugins()
        self.plugin_service = PluginManagementService(self.registry)

        # Instantiate plugin and run optional validation to preload models
        plugin = self.plugin_service.get_plugin_instance(self.plugin_id)
        if plugin and hasattr(plugin, "validate"):
            try:
                plugin.validate()
                logger.info(f"Plugin {plugin_id} validated, models preloaded into VRAM")
            except Exception as e:
                logger.warning(f"Plugin {plugin_id} validation failed: {e}")

    def process_frame(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single frame synchronously within the long-lived actor.

        This method is called for each incoming frame from the WebSocket.
        The plugin's model is already loaded in VRAM, so execution is fast.

        Args:
            args: Arguments dict with:
                - image_bytes: Raw image bytes
                - options: Optional plugin-specific options

        Returns:
            Dict containing the tool execution result

        Raises:
            RuntimeError: If tool execution fails
        """
        try:
            result = self.plugin_service.run_plugin_tool(
                self.plugin_id, self.tool_name, args, progress_callback=None
            )

            # Handle Pydantic models
            if hasattr(result, "model_dump"):
                return result.model_dump()
            elif hasattr(result, "dict"):
                return result.dict()

            return dict(result) if result else {}

        except Exception as e:
            logger.error(
                f"StreamingToolActor.process_frame failed for "
                f"{self.plugin_id}.{self.tool_name}: {e}"
            )
            raise RuntimeError(f"Frame processing failed: {e}") from e
