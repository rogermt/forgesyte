"""Ray remote tasks for distributed plugin execution.

This module provides Ray-decorated functions for executing plugin tools
in a distributed Ray cluster environment. GPU-heavy plugins (like YOLO)
can be executed on remote GPU workers while the head node manages job dispatch.

Architecture:
    Laptop (Ray Head) --> Lightning AI (GPU Worker)
                        --> Lightning AI (GPU Worker)
                        --> ...

The head node dispatches jobs via execute_pipeline_remote.remote() and
polls for completion via ray.wait() + ray.get().

Usage:
    # In JobWorker:
    future = execute_pipeline_remote.remote(
        plugin_id="yolo",
        tools_to_run=["player_detector"],
        input_path="s3://bucket/video.mp4",
        job_type="video"
    )
    # Later: ray.wait() + ray.get(future)
"""

import base64
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

import ray

logger = logging.getLogger(__name__)


class StorageServiceProtocol(Protocol):
    """Protocol for storage service (for type hints)."""

    def load_file(self, path: str) -> Path:
        """Load file from storage and return local path."""
        ...

    def save_file(self, src, dest_path: str) -> str:
        """Save file to storage."""
        ...


class PluginServiceProtocol(Protocol):
    """Protocol for plugin service (for type hints)."""

    def get_plugin_manifest(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get plugin manifest."""
        ...

    def run_plugin_tool(
        self,
        plugin_id: str,
        tool_name: str,
        args: Dict[str, Any],
        progress_callback=None,
    ) -> Any:
        """Run a plugin tool."""
        ...


def _get_plugin_service() -> PluginServiceProtocol:
    """Get plugin service instance (lazy import to avoid circular deps)."""
    from .plugin_loader import PluginRegistry
    from .services.plugin_management_service import PluginManagementService

    registry = PluginRegistry()
    return PluginManagementService(registry)


def _get_storage_service() -> StorageServiceProtocol:
    """Get storage service instance (lazy import)."""
    from .services.storage.factory import get_storage_service

    return get_storage_service()


@ray.remote(num_gpus=1)
def execute_pipeline_remote(
    plugin_id: str,
    tools_to_run: List[str],
    input_path: str,
    job_type: str,
) -> Dict[str, Any]:
    """Execute a plugin pipeline on a Ray worker (GPU-enabled).

    This function runs on a Ray worker node (e.g., Lightning AI GPU).
    It downloads the input file from storage, executes the plugin tools,
    and returns the results.

    Args:
        plugin_id: Plugin identifier (e.g., "yolo", "ocr")
        tools_to_run: List of tool names to execute sequentially
        input_path: Path to input file in storage (S3/MinIO or local)
        job_type: Type of job ("image", "image_multi", "video", "video_multi")

    Returns:
        Dict mapping tool_name -> result for each tool executed

    Raises:
        RuntimeError: If plugin or tool execution fails
    """
    return _execute_pipeline_impl(
        plugin_id,
        tools_to_run,
        input_path,
        job_type,
        _get_plugin_service,
        _get_storage_service,
    )


def _execute_pipeline_impl(
    plugin_id: str,
    tools_to_run: List[str],
    input_path: str,
    job_type: str,
    get_plugin_service_fn=None,
    get_storage_service_fn=None,
) -> Dict[str, Any]:
    """Implementation of pipeline execution (separated for testing).

    This function contains the actual logic without Ray decoration,
    allowing it to be unit tested without a Ray cluster.

    Args:
        plugin_id: Plugin identifier
        tools_to_run: List of tool names to execute
        input_path: Path to input file in storage
        job_type: Type of job ("image", "image_multi", "video", "video_multi")
        get_plugin_service_fn: Optional override for dependency injection
        get_storage_service_fn: Optional override for dependency injection
    """
    # Use injected dependencies or defaults
    if get_plugin_service_fn is None:
        get_plugin_service_fn = _get_plugin_service
    if get_storage_service_fn is None:
        get_storage_service_fn = _get_storage_service

    plugin_service = get_plugin_service_fn()
    storage = get_storage_service_fn()

    # Download from remote S3 directly to the GPU Worker's temp disk
    local_file_path = storage.load_file(input_path)

    try:
        args: Dict[str, Any] = {}
        manifest = plugin_service.get_plugin_manifest(plugin_id)
        if not manifest:
            raise RuntimeError(f"Plugin '{plugin_id}' not found")

        manifest_tools = manifest.get("tools", [])

        # Handle both dict and list format for tools
        if isinstance(manifest_tools, dict):
            manifest_tools = [{"id": k, **v} for k, v in manifest_tools.items()]

        # Prepare arguments based on job type
        if job_type in ("image", "image_multi"):
            with open(local_file_path, "rb") as f:
                image_bytes = f.read()

            # Get first tool's input types
            first_tool_def = next(
                (t for t in manifest_tools if t.get("id") == tools_to_run[0]), None
            )
            input_type_list = first_tool_def.get("inputs", []) if first_tool_def else []

            if "image_base64" in input_type_list:
                args = {"image_base64": base64.b64encode(image_bytes).decode("utf-8")}
            else:
                args = {"image_bytes": image_bytes}
        else:
            # Video job: pass the local file path
            args = {"video_path": str(local_file_path)}

        # Execute tools sequentially
        results: Dict[str, Any] = {}
        for tool_name in tools_to_run:
            logger.info(f"Ray Worker executing {plugin_id}.{tool_name}")

            # Note: progress_callback is disabled for Ray tasks in Phase B
            # Progress tracking happens at the JobWorker level
            result = plugin_service.run_plugin_tool(
                plugin_id, tool_name, args, progress_callback=None
            )

            # Handle Pydantic models
            if hasattr(result, "model_dump"):
                result = result.model_dump()
            elif hasattr(result, "dict"):
                result = result.dict()

            results[tool_name] = result

        return results

    finally:
        # Clean up the worker's local temp file
        if local_file_path.exists():
            local_file_path.unlink()
