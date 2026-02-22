"""Image submission endpoint for v0.9.2 unified job system.

Provides POST /v1/image/submit endpoint for submitting image files
for processing using the new Job model with job_type="image".

v0.9.4: Added multi-tool support via repeated tool query parameters.
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

router = APIRouter()
storage = LocalStorageService()


def get_plugin_manager():
    """Get plugin manager from app state with loaded plugins.

    This replaces the module-level PluginRegistry() which was empty
    because it never called load_plugins(). (Issue #209)

    Returns:
        PluginRegistry with loaded plugins from app state
    """
    from app.main import app

    plugin_manager = getattr(app.state, "plugins", None)
    if not plugin_manager:
        # Fallback: create and load plugins (for tests without app state)
        plugin_manager = PluginRegistry()
        plugin_manager.load_plugins()
    return plugin_manager


def get_plugin_service(plugin_manager=Depends(get_plugin_manager)):
    """Get plugin service with dependency injection.

    Args:
        plugin_manager: PluginRegistry from app state

    Returns:
        PluginManagementService instance
    """
    return PluginManagementService(plugin_manager)


def validate_image_magic_bytes(data: bytes) -> None:
    """Validate that data contains PNG or JPEG magic bytes.

    Args:
        data: File bytes to validate

    Raises:
        HTTPException: If file is not a valid PNG or JPEG
    """
    # PNG magic bytes: 89 50 4E 47 0D 0A 1A 0A
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return

    # JPEG magic bytes: FF D8 FF
    if data.startswith(b"\xFF\xD8\xFF"):
        return

    raise HTTPException(
        status_code=400,
        detail="Invalid image file (expected PNG or JPEG)",
    )


@router.post("/v1/image/submit")
async def submit_image(
    file: UploadFile,
    plugin_id: str = Query(..., description="Plugin ID from /v1/plugins"),
    tool: List[str] = Query(..., description="Tool ID(s) from plugin manifest"),
    plugin_manager=Depends(get_plugin_manager),
    plugin_service=Depends(get_plugin_service),
):
    """Submit an image file for processing.

    This endpoint creates a new job with job_type="image" (single tool) or
    job_type="image_multi" (multiple tools) and enqueues it for processing
    by the worker.

    v0.9.4: Supports multiple tools via repeated query parameters.
    Example: ?tool=player_detection&tool=ball_detection

    Args:
        file: Image file (PNG or JPEG) to process
        plugin_id: ID of the plugin to use (from /v1/plugins)
        tool: Tool ID(s) to run (from plugin manifest). Can be repeated for multi-tool.
        plugin_manager: PluginRegistry from app state (DI)
        plugin_service: PluginManagementService instance (DI)

    Returns:
        JSON with job_id for polling via /v1/jobs/{job_id}

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

    # Validate all tools support image input
    for t in tool:
        tool_def = plugin.tools.get(t)
        if not tool_def:
            raise HTTPException(
                status_code=400,
                detail=f"Tool '{t}' definition not found in plugin '{plugin_id}'",
            )

        # Validate tool supports image input (supports both Pydantic + flat dict schemas)
        # See: docs/releases/v0.9.3/IMAGE_SUBMIT_400_ROOT_CAUSE.md
        input_schema = tool_def.get("input_schema") or {}

        # Pydantic-style: {"properties": {...}}
        if "properties" in input_schema and isinstance(
            input_schema["properties"], dict
        ):
            tool_keys = set(input_schema["properties"].keys())
        else:
            # Flat dict style: {"image_bytes": {...}, ...}
            tool_keys = set(input_schema.keys())

        if not any(k in tool_keys for k in ("image_bytes", "image_base64")):
            raise HTTPException(
                status_code=400,
                detail=f"Tool '{t}' does not support image input",
            )

    # Read and validate file
    contents = await file.read()
    validate_image_magic_bytes(contents)

    # Determine job type based on number of tools
    is_multi_tool = len(tool) > 1
    job_type = "image_multi" if is_multi_tool else "image"

    # Create job record with UUID object (not string)
    job_id = uuid4()
    input_path = f"image/input/{job_id}_{file.filename}"

    # Save file to storage
    storage.save_file(src=BytesIO(contents), dest_path=input_path)

    # Create database record
    db = SessionLocal()
    try:
        job = Job(
            job_id=job_id,  # Pass UUID object, not string
            status=JobStatus.pending,
            plugin_id=plugin_id,
            tool=tool[0] if not is_multi_tool else None,
            tool_list=json.dumps(tool) if is_multi_tool else None,
            input_path=input_path,
            job_type=job_type,
        )
        db.add(job)
        db.commit()
    finally:
        db.close()

    return {"job_id": str(job_id)}  # Return string in response
