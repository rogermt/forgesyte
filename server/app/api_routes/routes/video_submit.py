"""Video submission endpoint for Phase 16 job processing.
<<<<<<< HEAD
=======

v0.9.7: Added logical_tool_id parameter for capability-based tool resolution.
The UI can now send a logical tool ID (capability string) instead of the exact
plugin tool ID, and the backend resolves it dynamically using the plugin manifest.
"""
>>>>>>> 7931b05 (feat(video): add logical_tool_id parameter for capability-based resolution)

v0.9.7: Added multi-tool support via repeated tool query parameters.
Example: ?tool=player_detection_video&tool=ball_detection_video
"""

import json
from io import BytesIO
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile

from app.core.database import SessionLocal
from app.models.job import Job, JobStatus
from app.plugin_loader import PluginRegistry
from app.services.plugin_management_service import PluginManagementService
from app.services.storage.local_storage import LocalStorageService
from app.services.tool_router import resolve_tool

router = APIRouter()
storage = LocalStorageService()


def get_plugin_manager():
    """Get plugin manager from app state with loaded plugins."""
    from app.main import app

    plugin_manager = getattr(app.state, "plugins", None)
    if not plugin_manager:
        plugin_manager = PluginRegistry()
        plugin_manager.load_plugins()
    return plugin_manager


def get_plugin_service(plugin_manager=Depends(get_plugin_manager)):
    """Get plugin service with dependency injection."""
    return PluginManagementService(plugin_manager)


def validate_mp4_magic_bytes(data: bytes) -> None:
    """Validate that data contains MP4 magic bytes.

    Args:
        data: File bytes to validate

    Raises:
        HTTPException: If file is not a valid MP4
    """
    if b"ftyp" not in data[:64]:
        raise HTTPException(status_code=400, detail="Invalid MP4 file")


@router.post("/v1/video/submit")
async def submit_video(
    file: UploadFile,
    plugin_id: str = Query(..., description="Plugin ID from /v1/plugins"),
<<<<<<< HEAD
    tool: List[str] = Query(
        ...,
        description="Tool ID(s) from plugin manifest. Can be repeated for multi-tool.",
=======
    tool: str | None = Query(
        None,
        description="Tool ID from plugin manifest (optional if logical_tool_id provided)",
    ),
    logical_tool_id: str | None = Query(
        None, description="Logical tool ID (capability string) for dynamic resolution"
>>>>>>> 7931b05 (feat(video): add logical_tool_id parameter for capability-based resolution)
    ),
    plugin_manager=Depends(get_plugin_manager),
    plugin_service=Depends(get_plugin_service),
):
    """Submit a video file for processing.

    This endpoint creates a new job with job_type="video" and supports
    both single-tool and multi-tool video processing.

    v0.9.7: Supports multiple tools via repeated query parameters.
    Example: ?tool=player_detection_video&tool=ball_detection_video

    Args:
        file: MP4 video file to process
        plugin_id: ID of the plugin to use (from /v1/plugins)
<<<<<<< HEAD
        tool: Tool ID(s) to run (from plugin manifest). Can be repeated for multi-tool.
=======
        tool: ID of the tool to run (from plugin manifest) - optional if logical_tool_id provided
        logical_tool_id: Logical tool ID (capability string) for dynamic resolution
            e.g., "player_detection", "ball_detection", "pitch_detection", "radar"
>>>>>>> 7931b05 (feat(video): add logical_tool_id parameter for capability-based resolution)
        plugin_manager: PluginRegistry from app state (DI)
        plugin_service: PluginManagementService instance (DI)

    Returns:
        JSON with job_id for polling

    Raises:
        HTTPException: If file is invalid or processing fails

    v0.9.7: If logical_tool_id is provided, resolves the actual tool ID using
    capability-based resolution via resolve_tool(). This enables the UI to send
    semantic tool IDs without knowing the exact plugin tool naming scheme.
    """
    # Validate plugin exists
    plugin = plugin_manager.get(plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=400,
            detail=f"Plugin '{plugin_id}' not found",
        )

<<<<<<< HEAD
    # Validate all tools exist using plugin.tools (canonical source, NOT manifest)
    # See: docs/releases/v0.9.3/TOOL_CHECK_FIX.md
    available_tools = plugin_service.get_available_tools(plugin_id)

    for t in tool:
        if t not in available_tools:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Tool '{t}' not found in plugin '{plugin_id}'. "
                    f"Available: {available_tools}"
                ),
            )
=======
    # v0.9.7: Resolve tool ID using capability-based resolution if logical_tool_id provided
    if logical_tool_id:
        try:
            resolved_tool = resolve_tool(
                logical_tool_id, file.content_type or "video/mp4", plugin_id
            )
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e),
            ) from e
    elif tool:
        resolved_tool = tool
    else:
        raise HTTPException(
            status_code=400,
            detail="Either 'tool' or 'logical_tool_id' must be provided",
        )

    # Validate tool exists using plugin.tools (canonical source, NOT manifest)
    # See: docs/releases/v0.9.3/TOOL_CHECK_FIX.md
    available_tools = plugin_service.get_available_tools(plugin_id)
    if resolved_tool not in available_tools:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Tool '{resolved_tool}' not found in plugin '{plugin_id}'. "
                f"Available: {available_tools}"
            ),
        )
>>>>>>> 7931b05 (feat(video): add logical_tool_id parameter for capability-based resolution)

    # v0.9.5: Validate tool supports video input using input_types from MANIFEST
    # NOTE: plugin.tools uses ToolSchema which forbids input_types (extra="forbid")
    # So we must read input_types from manifest.json, not from plugin.tools dict
    # v0.9.7: Using resolved_tool (may differ from original tool/logical_tool_id)
    manifest = plugin_service.get_plugin_manifest(plugin_id)
    if not manifest:
        raise HTTPException(
            status_code=400,
            detail=f"Manifest not found for plugin '{plugin_id}'",
        )

    # v0.9.7: Validate all tools support video input
    manifest_tools = manifest.get("tools", [])
<<<<<<< HEAD

    for t in tool:
        # Find tool in manifest tools array
        tool_def = None
        for mt in manifest_tools:
            if mt.get("id") == t:
                tool_def = mt
                break

        if not tool_def:
            raise HTTPException(
                status_code=400,
                detail=f"Tool '{t}' definition not found in manifest for '{plugin_id}'",
            )

        # Check input_types from manifest
        input_types = tool_def.get("input_types", [])
        if "video" not in input_types:
            raise HTTPException(
                status_code=400,
                detail=f"Tool '{t}' does not support video input (input_types: {input_types})",
            )

    # v0.9.7: Determine if multi-tool
    is_multi_tool = len(tool) > 1
=======
    tool_def = None
    for t in manifest_tools:
        if t.get("id") == resolved_tool:
            tool_def = t
            break

    if not tool_def:
        raise HTTPException(
            status_code=400,
            detail=f"Tool '{resolved_tool}' definition not found in manifest for '{plugin_id}'",
        )

    # Check input_types from manifest
    input_types = tool_def.get("input_types", [])
    if "video" not in input_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tool '{resolved_tool}' does not support video input (input_types: {input_types})",
        )
>>>>>>> 7931b05 (feat(video): add logical_tool_id parameter for capability-based resolution)

    # Read and validate file
    contents = await file.read()
    validate_mp4_magic_bytes(contents)

    # Create job record with UUID object (not string)
    job_id = uuid4()
    input_path = f"video/input/{job_id}.mp4"

    # Save file to storage
    storage.save_file(src=BytesIO(contents), dest_path=input_path)

    # Create database record
    db = SessionLocal()
    try:
        job = Job(
            job_id=job_id,  # Pass UUID object, not string
            status=JobStatus.pending,
            plugin_id=plugin_id,
<<<<<<< HEAD
            tool=(
                tool[0] if not is_multi_tool else None
            ),  # Single tool for backward compat
            tool_list=(
                json.dumps(tool) if is_multi_tool else None
            ),  # v0.9.7: Store tools as JSON
=======
            tool=resolved_tool,
>>>>>>> 7931b05 (feat(video): add logical_tool_id parameter for capability-based resolution)
            input_path=input_path,
            job_type="video",  # v0.9.7: Always "video" (not "video_multi")
        )
        db.add(job)
        db.commit()
    finally:
        db.close()

    return {"job_id": str(job_id)}  # Return string in response
