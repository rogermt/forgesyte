"""Video submission endpoint for Phase 16 job processing.

v0.9.7: Added logical_tool_id parameter for capability-based tool resolution.
The UI can now send a logical tool ID (capability string) instead of the exact
plugin tool ID, and the backend resolves it dynamically using the plugin manifest.

v0.9.8: Added multi-tool support with video_multi job type, mutual exclusivity
check (tool vs logical_tool_id), and canonical JSON response.
"""

import json
from datetime import timezone
from io import BytesIO
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile

from app.core.database import SessionLocal
from app.models.job import Job, JobStatus
from app.plugin_loader import PluginRegistry
from app.services.plugin_management_service import PluginManagementService
from app.services.storage.local_storage import LocalStorageService
from app.services.tool_router import resolve_tools

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
    tool: List[str] | None = Query(
        None,
        description="Tool ID(s) from plugin manifest. Repeatable for multi (optional if logical_tool_id provided)",
    ),
    logical_tool_id: List[str] | None = Query(
        None,
        description="Logical tool ID(s) (capability strings). Repeatable for multi-tool.",
    ),
    plugin_manager=Depends(get_plugin_manager),
    plugin_service=Depends(get_plugin_service),
):
    """Submit a video file for processing.

    This endpoint creates a new job with job_type="video" (single tool) or
    job_type="video_multi" (multiple tools) and enqueues it for processing
    by the worker.

    v0.9.7: Supports logical_tool_id parameter for capability-based resolution.
    The logical tool ID (capability string) is matched against tool capabilities
    in the manifest to find the actual plugin tool ID.

    v0.9.8: Mutual exclusivity - cannot provide both tool and logical_tool_id.
    Canonical JSON response with submitted_at, tools array for multi-tool.

    Args:
        file: MP4 video file to process
        plugin_id: ID of the plugin to use (from /v1/plugins)
        tool: Tool ID(s) to run (from plugin manifest). Can be repeated for multi-tool.
            Optional if logical_tool_id is provided.
        logical_tool_id: Logical tool ID(s) (capability strings) for dynamic resolution.
            Repeatable for multi-tool. e.g., "player_detection", "ball_detection"
        plugin_manager: PluginRegistry from app state (DI)
        plugin_service: PluginManagementService instance (DI)

    Returns:
        Canonical JSON:
        - Single tool: {"job_id": "...", "plugin": "...", "tool": "...", "status": "queued", "submitted_at": "..."}
        - Multi tool: {"job_id": "...", "plugin": "...", "tools": [...], "status": "queued", "submitted_at": "..."}

    Raises:
        HTTPException: If file is invalid or processing fails
    """
    # Validate plugin exists
    plugin = plugin_manager.get(plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=400,
            detail=f"Plugin '{plugin_id}' not found",
        )

    # v0.9.8: STRICT ARCHITECTURE RULE - mutual exclusivity check
    if tool and logical_tool_id:
        raise HTTPException(
            status_code=400,
            detail="Mutually exclusive parameters: You cannot provide both 'tool' and 'logical_tool_id' in the same request.",
        )

    # v0.9.8: Resolve tool IDs using capability-based resolution if logical_tool_id provided
    resolved_tools: List[str] = []
    logicals_used: List[str] = []

    if logical_tool_id and len(logical_tool_id) > 0:
        try:
            logicals_used = logical_tool_id
            resolved_tools = resolve_tools(
                logical_tool_id,
                file.content_type or "video/mp4",
                plugin_id,
                plugin_service,
            )
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e),
            ) from e
    elif tool and len(tool) > 0:
        resolved_tools = tool
    else:
        raise HTTPException(
            status_code=400,
            detail="Either 'tool' or 'logical_tool_id' must be provided",
        )

    # Validate all tools exist using plugin.tools (canonical source, NOT manifest)
    # See: docs/releases/v0.9.3/TOOL_CHECK_FIX.md
    available_tools = plugin_service.get_available_tools(plugin_id)

    for resolved_tool in resolved_tools:
        if resolved_tool not in available_tools:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Tool '{resolved_tool}' not found in plugin '{plugin_id}'. "
                    f"Available: {available_tools}"
                ),
            )

    # v0.9.5: Validate tool supports video input using input_types from MANIFEST
    # NOTE: plugin.tools uses ToolSchema which forbids input_types (extra="forbid")
    # So we must read input_types from manifest.json, not from plugin.tools dict
    manifest = plugin_service.get_plugin_manifest(plugin_id)
    if not manifest:
        raise HTTPException(
            status_code=400,
            detail=f"Manifest not found for plugin '{plugin_id}'",
        )

    # Build tool map from manifest
    manifest_tools = manifest.get("tools", [])
    if isinstance(manifest_tools, list):
        tool_map = {t.get("id"): t for t in manifest_tools if isinstance(t, dict)}
    elif isinstance(manifest_tools, dict):
        tool_map = {k: {"id": k, **v} for k, v in manifest_tools.items()}
    else:
        tool_map = {}

    # Validate each tool supports video input
    for resolved_tool in resolved_tools:
        tool_def = tool_map.get(resolved_tool)
        if not tool_def:
            raise HTTPException(
                status_code=400,
                detail=f"Tool '{resolved_tool}' definition not found in manifest for '{plugin_id}'",
            )

        input_types = tool_def.get("input_types", [])
        if "video" not in input_types:
            raise HTTPException(
                status_code=400,
                detail=f"Tool '{resolved_tool}' does not support video input (input_types: {input_types})",
            )

    # Read and validate file
    contents = await file.read()
    validate_mp4_magic_bytes(contents)

    # Determine job type based on number of tools
    is_multi_tool = len(resolved_tools) > 1
    job_type = "video_multi" if is_multi_tool else "video"

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
            tool=resolved_tools[0] if not is_multi_tool else None,
            tool_list=json.dumps(resolved_tools) if is_multi_tool else None,
            input_path=input_path,
            job_type=job_type,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
    finally:
        db.close()

    # v0.9.8: Canonical JSON response
    # Handle case where created_at might be None (e.g., in mocked tests)
    if job.created_at:
        submitted_at = (
            job.created_at.replace(tzinfo=timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )
    else:
        from datetime import datetime

        submitted_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    if logicals_used and len(resolved_tools) > 1:
        # Multi-tool with logical IDs
        return {
            "job_id": str(job_id),
            "plugin": plugin_id,
            "tools": [
                {"logical": logical_id, "resolved": resolved_id}
                for logical_id, resolved_id in zip(
                    logicals_used, resolved_tools, strict=False
                )
            ],
            "status": "queued",
            "submitted_at": submitted_at,
        }

    if logicals_used and len(resolved_tools) == 1:
        # Single tool with logical ID
        return {
            "job_id": str(job_id),
            "plugin": plugin_id,
            "tool": resolved_tools[0],
            "status": "queued",
            "submitted_at": submitted_at,
        }

    # Legacy (tool=...) callers get basic response
    return {"job_id": str(job_id)}
