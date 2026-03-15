"""Image submission endpoint for v0.9.2 unified job system.

Provides POST /v1/image/submit endpoint for submitting image files
for processing using the new Job model with job_type="image".

v0.9.4: Added multi-tool support via repeated tool query parameters.
v0.9.7: Added logical_tool_id parameter for capability-based resolution.
v0.9.8: Added mutual exclusivity check (tool vs logical_tool_id),
        repeatable logical_tool_id, and canonical JSON response.
"""

import json
import logging
import traceback
from datetime import timezone
from io import BytesIO
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile

from app.core.database import SessionLocal
from app.models.job import Job, JobStatus
from app.plugin_loader import PluginRegistry
from app.services.plugin_management_service import PluginManagementService
from app.services.storage.factory import get_storage_service
from app.services.tool_router import resolve_tools
from app.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()


def debug_file(msg: str) -> None:
    """Write debug message to file since logging may not work."""
    with open("debug_output.txt", "a") as f:
        f.write(msg + "\n")


def get_storage():
    """Get storage service via lazy initialization.

    This avoids import-time S3 connection attempts and allows
    dependency injection for testing. See issue #243.
    """
    return get_storage_service(settings)


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
    tool: List[str] | None = Query(
        None,
        description="Tool ID(s) from plugin manifest (optional if logical_tool_id provided)",
    ),
    logical_tool_id: List[str] | None = Query(
        None,
        description="Logical tool ID(s) (capability strings). Repeatable for multi-tool.",
    ),
    plugin_manager=Depends(get_plugin_manager),
    plugin_service=Depends(get_plugin_service),
    storage=Depends(get_storage),
):
    """Submit an image file for processing.

    This endpoint creates a new job with job_type="image" (single tool) or
    job_type="image_multi" (multiple tools) and enqueues it for processing
    by the worker.

    v0.9.4: Supports multiple tools via repeated query parameters.
    Example: ?tool=player_detection&tool=ball_detection

    v0.9.7: Supports logical_tool_id parameter for capability-based resolution.
    The logical tool ID (capability string) is matched against tool capabilities
    in the manifest to find the actual plugin tool ID.

    v0.9.8: Mutual exclusivity - cannot provide both tool and logical_tool_id.
    Canonical JSON response with submitted_at, tools array for multi-tool.

    Args:
        file: Image file (PNG or JPEG) to process
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
    # DEBUG: Log incoming request parameters
    debug_file(
        f"[DEBUG] submit_image called: plugin_id={plugin_id}, tool={tool}, logical_tool_id={logical_tool_id}"
    )
    logger.info(
        f"[DEBUG] submit_image called: plugin_id={plugin_id}, tool={tool}, logical_tool_id={logical_tool_id}"
    )

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
        # DEBUG: Log manifest structure before resolving
        debug_file(f"[DEBUG] logical_tool_id provided: {logical_tool_id}")
        try:
            manifest = plugin_service.get_plugin_manifest(plugin_id)
            debug_file(
                f"[DEBUG] Manifest tools: {json.dumps(manifest.get('tools', [])[:3], default=str)[:500]}"
            )
            logger.info(
                f"[DEBUG] Manifest for '{plugin_id}': {json.dumps(manifest, indent=2, default=str)[:2000]}"
            )
        except Exception as e:
            debug_file(f"[DEBUG] Failed to get manifest: {e}")
            logger.error(f"[DEBUG] Failed to get manifest: {e}")

        try:
            logicals_used = logical_tool_id
            debug_file(
                f"[DEBUG] Calling resolve_tools with logical_tool_id={logical_tool_id}, mime={file.content_type}"
            )
            logger.info(
                f"[DEBUG] Calling resolve_tools with logical_tool_id={logical_tool_id}, mime={file.content_type}"
            )
            resolved_tools = resolve_tools(
                logical_tool_id,
                file.content_type or "image/png",
                plugin_id,
                plugin_service,
            )
            debug_file(f"[DEBUG] resolve_tools returned: {resolved_tools}")
            logger.info(f"[DEBUG] resolve_tools returned: {resolved_tools}")
        except ValueError as e:
            debug_file(f"[DEBUG] resolve_tools ValueError: {e}")
            logger.error(f"[DEBUG] resolve_tools ValueError: {e}")
            raise HTTPException(
                status_code=400,
                detail=str(e),
            ) from e
        except Exception as e:
            debug_file(f"[DEBUG] resolve_tools unexpected error: {e}")
            logger.error(
                f"[DEBUG] resolve_tools unexpected error: {e}\n{traceback.format_exc()}"
            )
            raise
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

    for t in resolved_tools:
        if t not in available_tools:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Tool '{t}' not found in plugin '{plugin_id}'. "
                    f"Available: {available_tools}"
                ),
            )

    # Validate all tools support image input
    for t in resolved_tools:
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
    is_multi_tool = len(resolved_tools) > 1
    job_type = "image_multi" if is_multi_tool else "image"

    debug_file(
        f"[DEBUG] is_multi_tool={is_multi_tool}, job_type={job_type}, resolved_tools={resolved_tools}"
    )
    logger.info(
        f"[DEBUG] is_multi_tool={is_multi_tool}, job_type={job_type}, resolved_tools={resolved_tools}"
    )

    # Create job record with UUID object (not string)
    job_id = uuid4()
    input_path = f"image/input/{job_id}_{file.filename}"

    # Save file to storage
    try:
        storage.save_file(src=BytesIO(contents), dest_path=input_path)
        debug_file(f"[DEBUG] File saved to {input_path}")
        logger.info(f"[DEBUG] File saved to {input_path}")
    except Exception as e:
        debug_file(f"[DEBUG] Storage save failed: {e}")
        logger.error(f"[DEBUG] Storage save failed: {e}\n{traceback.format_exc()}")
        raise

    # Create database record
    db = SessionLocal()
    try:
        from app.services.job_tools_service import JobToolsService

        job = Job(
            job_id=job_id,  # Pass UUID object, not string
            status=JobStatus.pending,
            plugin_id=plugin_id,
            input_path=input_path,
            job_type=job_type,
        )
        db.add(job)
        db.flush()  # Flush to ensure job exists before adding tools

        # Add tools to job_tools table via service
        JobToolsService.add_tools_to_job(db, job_id, resolved_tools)

        db.commit()
        db.refresh(job)
        debug_file(f"[DEBUG] Job created: job_id={job_id}")
        logger.info(f"[DEBUG] Job created: job_id={job_id}")
    except Exception as e:
        debug_file(f"[DEBUG] Database error: {e}")
        logger.error(f"[DEBUG] Database error: {e}\n{traceback.format_exc()}")
        raise
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
        debug_file(
            f"[DEBUG] Returning multi-tool response: job_id={job_id}, tools={resolved_tools}"
        )
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
        debug_file(
            f"[DEBUG] Returning single-tool response: job_id={job_id}, tool={resolved_tools[0]}"
        )
        return {
            "job_id": str(job_id),
            "plugin": plugin_id,
            "tool": resolved_tools[0],
            "status": "queued",
            "submitted_at": submitted_at,
        }

    # Legacy (tool=...) callers get basic response
    debug_file(f"[DEBUG] Returning legacy response: job_id={job_id}")
    return {"job_id": str(job_id)}
