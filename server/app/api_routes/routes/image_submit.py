"""Image submission endpoint for v0.9.2 unified job system.

Provides POST /v1/image/submit endpoint for submitting image files
for processing using the new Job model with job_type="image".
"""

from io import BytesIO
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, UploadFile

from app.core.database import SessionLocal
from app.models.job import Job, JobStatus
from app.plugin_loader import PluginRegistry
from app.services.plugin_management_service import PluginManagementService
from app.services.storage.local_storage import LocalStorageService

router = APIRouter()
storage = LocalStorageService()
plugin_manager = PluginRegistry()
plugin_service = PluginManagementService(plugin_manager)


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
    tool: str = Query(..., description="Tool ID from plugin manifest"),
):
    """Submit an image file for processing.

    This endpoint creates a new job with job_type="image" and enqueues it
    for processing by the worker. The worker will execute the specified
    tool using plugin_service.run_plugin_tool().

    Args:
        file: Image file (PNG or JPEG) to process
        plugin_id: ID of the plugin to use (from /v1/plugins)
        tool: ID of the tool to run (from plugin manifest)

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

    # Validate tool exists and supports image input
    manifest = plugin_service.get_plugin_manifest(plugin_id)
    if not manifest:
        raise HTTPException(
            status_code=400,
            detail=f"Could not load manifest for plugin '{plugin_id}'",
        )

    # Find tool in manifest
    tools = manifest.get("tools", {})
    tool_def = None
    for tool_name, tool_info in tools.items():
        if tool_name == tool:
            tool_def = tool_info
            break

    if not tool_def:
        raise HTTPException(
            status_code=400,
            detail=f"Tool '{tool}' not found in plugin '{plugin_id}'",
        )

    # Validate tool supports image input
    tool_inputs = tool_def.get("inputs", [])
    if not any(i in tool_inputs for i in ("image_bytes", "image_base64")):
        raise HTTPException(
            status_code=400,
            detail=f"Tool '{tool}' does not support image input",
        )

    # Read and validate file
    contents = await file.read()
    validate_image_magic_bytes(contents)

    # Create job record
    job_id = str(uuid4())
    input_path = f"image/input/{job_id}_{file.filename}"

    # Save file to storage
    storage.save_file(src=BytesIO(contents), dest_path=input_path)

    # Create database record
    db = SessionLocal()
    try:
        job = Job(
            job_id=job_id,
            status=JobStatus.pending,
            plugin_id=plugin_id,
            tool=tool,
            input_path=input_path,
            job_type="image",
        )
        db.add(job)
        db.commit()
    finally:
        db.close()

    return {"job_id": job_id}
