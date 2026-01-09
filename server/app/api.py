"""REST API endpoints for the Vision MCP Server."""

import base64
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile

from .auth import get_api_key, require_auth
from .mcp_adapter import MCPAdapter, build_gemini_extension_manifest
from .models import JobResponse, JobStatus, PluginMetadata
from .tasks import job_store, task_processor

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze", response_model=dict)
async def analyze_image(
    request: Request,
    file: Optional[UploadFile] = None,
    plugin: str = Query(default="ocr", description="Plugin to use"),
    image_url: Optional[str] = Query(None, description="URL of image to analyze"),
    options: Optional[str] = Query(None, description="JSON options for plugin"),
    auth: dict = Depends(get_api_key),
):
    """
    Analyze an image using the specified plugin.

    Either upload a file or provide an image URL.
    Returns a job ID for tracking the analysis.
    """
    image_bytes = None

    if file:
        image_bytes = await file.read()
    elif image_url:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url, timeout=10.0)
                response.raise_for_status()
                image_bytes = response.content
        except Exception as e:
            raise HTTPException(400, f"Failed to fetch image: {e}") from e
    else:
        # Check for base64 in body
        body = await request.body()
        if body:
            try:
                image_bytes = base64.b64decode(body)
            except Exception:
                raise HTTPException(400, "No valid image provided") from None

    if not image_bytes:
        raise HTTPException(400, "No image provided")

    # Parse options
    parsed_options = {}
    if options:
        import json

        try:
            parsed_options = json.loads(options)
        except json.JSONDecodeError:
            raise HTTPException(400, "Invalid JSON in options") from None

    # Submit job
    if not task_processor:
        raise HTTPException(503, "Server not fully initialized")

    job_id = await task_processor.submit_job(
        image_bytes=image_bytes, plugin_name=plugin, options=parsed_options
    )

    return {"job_id": job_id, "status": "queued", "plugin": plugin}


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str, auth: dict = Depends(get_api_key)):
    """Get the status and results of an analysis job."""
    job = await job_store.get(job_id)

    if not job:
        raise HTTPException(404, "Job not found")

    return JobResponse(**job)


@router.get("/jobs")
async def list_jobs(
    status: Optional[JobStatus] = None,
    plugin: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    auth: dict = Depends(require_auth(["analyze"])),
):
    """List recent analysis jobs."""
    jobs = await job_store.list_jobs(status=status, plugin=plugin, limit=limit)
    return {"jobs": [JobResponse(**j) for j in jobs], "count": len(jobs)}


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str, auth: dict = Depends(require_auth(["analyze"]))):
    """Cancel a queued job."""
    if not task_processor:
        raise HTTPException(503, "Server not initialized")

    success = await task_processor.cancel_job(job_id)
    if success:
        return {"status": "cancelled", "job_id": job_id}
    else:
        raise HTTPException(
            400, "Job cannot be cancelled (may already be running " "or completed)"
        )


@router.get("/plugins")
async def list_plugins(request: Request):
    """List all available vision plugins."""
    pm = request.app.state.plugins
    plugins = pm.list()

    return {
        "plugins": [PluginMetadata(**meta) for meta in plugins.values()],
        "count": len(plugins),
    }


@router.get("/plugins/{name}")
async def get_plugin_info(name: str, request: Request):
    """Get detailed information about a plugin."""
    pm = request.app.state.plugins
    plugin = pm.get(name)

    if not plugin:
        raise HTTPException(404, f"Plugin '{name}' not found")

    return PluginMetadata(**plugin.metadata())


@router.post("/plugins/{name}/reload")
async def reload_plugin(
    name: str, request: Request, auth: dict = Depends(require_auth(["admin"]))
):
    """Reload a specific plugin (admin only)."""
    pm = request.app.state.plugins
    success = pm.reload_plugin(name)

    if success:
        return {"status": "reloaded", "plugin": name}
    else:
        raise HTTPException(500, f"Failed to reload plugin '{name}'")


@router.post("/plugins/reload-all")
async def reload_all_plugins(
    request: Request, auth: dict = Depends(require_auth(["admin"]))
):
    """Reload all plugins (admin only)."""
    pm = request.app.state.plugins
    result = pm.reload_all()
    return result


# MCP Discovery Endpoints


@router.get("/.well-known/mcp-manifest")
async def mcp_manifest(request: Request):
    """MCP manifest for Gemini-CLI discovery."""
    pm = request.app.state.plugins
    base_url = str(request.base_url).rstrip("/")
    adapter = MCPAdapter(pm, base_url)
    return adapter.get_manifest()


@router.get("/gemini-extension")
async def gemini_extension_manifest(request: Request):
    """Gemini extension manifest for easy installation."""
    base_url = str(request.base_url).rstrip("/")
    return build_gemini_extension_manifest(base_url)


# Health Check


@router.get("/health")
async def health_check(request: Request):
    """Health check endpoint."""
    pm = request.app.state.plugins
    return {"status": "healthy", "plugins_loaded": len(pm.plugins), "version": "0.1.0"}
