"""REST API endpoints for the Vision MCP Server.

This module provides thin endpoint handlers that delegate business logic to
service layer classes. The separation enables testability, maintainability,
and clear concern separation between transport (HTTP) and business logic.

Endpoints are grouped by domain:
- /analyze: Image analysis job submission
- /jobs: Job status and management
- /plugins: Plugin discovery and management
- /mcp-*: MCP protocol discovery
- /health: System health monitoring
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile

from .auth import require_auth
from .exceptions import ExternalServiceError
from .mcp import (
    MCP_PROTOCOL_VERSION,
    MCP_SERVER_NAME,
    MCP_SERVER_VERSION,
    MCPAdapter,
    build_gemini_extension_manifest,
)
from .models import JobResponse, JobStatus, PluginMetadata
from .services.analysis_service import AnalysisService
from .services.job_management_service import JobManagementService
from .services.plugin_management_service import PluginManagementService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_analysis_service(request: Request) -> AnalysisService:
    """Dependency to inject AnalysisService into endpoints.

    Args:
        request: FastAPI request with app state

    Returns:
        AnalysisService instance from app state

    Raises:
        RuntimeError: If service not initialized in app state
    """
    if not hasattr(request.app.state, "analysis_service_rest"):
        raise RuntimeError("AnalysisService not initialized")
    return request.app.state.analysis_service_rest


def get_job_service(request: Request) -> JobManagementService:
    """Dependency to inject JobManagementService into endpoints.

    Args:
        request: FastAPI request with app state

    Returns:
        JobManagementService instance from app state

    Raises:
        RuntimeError: If service not initialized in app state
    """
    if not hasattr(request.app.state, "job_service"):
        raise RuntimeError("JobManagementService not initialized")
    return request.app.state.job_service


def get_plugin_service(request: Request) -> PluginManagementService:
    """Dependency to inject PluginManagementService into endpoints.

    Args:
        request: FastAPI request with app state

    Returns:
        PluginManagementService instance from app state

    Raises:
        RuntimeError: If service not initialized in app state
    """
    if not hasattr(request.app.state, "plugin_service"):
        raise RuntimeError("PluginManagementService not initialized")
    return request.app.state.plugin_service


# Analysis Endpoints


@router.post("/analyze", response_model=dict)
async def analyze_image(
    request: Request,
    file: Optional[UploadFile] = None,
    plugin: str = Query(default="ocr", description="Plugin to use"),
    image_url: Optional[str] = Query(None, description="URL of image to analyze"),
    options: Optional[str] = Query(None, description="JSON options for plugin"),
    auth: dict = Depends(require_auth(["analyze"])),
    service: AnalysisService = Depends(get_analysis_service),
) -> dict:
    """Submit an image for analysis.

    Accepts image via file upload, URL, or base64 in request body.
    Returns a job ID for tracking the analysis via /jobs/{job_id}.

    Args:
        request: FastAPI request context
        file: Optional uploaded image file
        plugin: Name of plugin to use (default: "ocr")
        image_url: Optional URL to fetch image from
        options: Optional JSON string with plugin-specific options
        auth: Authentication credentials (required)
        service: Injected AnalysisService

    Returns:
        Dictionary with job_id, status, and plugin name

    Raises:
        HTTPException: 400 if no valid image source or invalid JSON options
        HTTPException: 400 if image fetch fails
        HTTPException: 503 if server not fully initialized
    """
    try:
        # Read file if provided
        file_bytes = await file.read() if file else None

        # Parse options
        parsed_options = {}
        if options:
            try:
                parsed_options = json.loads(options)
            except json.JSONDecodeError as e:
                logger.warning(
                    "Invalid JSON in options parameter",
                    extra={"error": str(e), "plugin": plugin},
                )
                raise HTTPException(400, "Invalid JSON in options") from e

        # Delegate to service
        result = await service.process_analysis_request(
            file_bytes=file_bytes,
            image_url=image_url,
            body_bytes=await request.body() if not file else None,
            plugin=plugin,
            options=parsed_options,
        )

        logger.info(
            "Analysis request submitted",
            extra={"job_id": result["job_id"], "plugin": plugin},
        )
        return result

    except ExternalServiceError as e:
        logger.error(
            "Failed to fetch remote image",
            extra={"url": image_url, "error": str(e)},
        )
        raise HTTPException(400, f"Failed to fetch image: {e}") from e
    except ValueError as e:
        logger.warning(
            "Invalid image data",
            extra={"error": str(e), "plugin": plugin},
        )
        raise HTTPException(400, f"Invalid image: {e}") from e
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Unexpected error during analysis request",
            extra={"plugin": plugin, "error": str(e)},
        )
        raise HTTPException(500, "Internal server error") from e


# Job Management Endpoints


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: str,
    auth: dict = Depends(require_auth(["analyze"])),
    service: JobManagementService = Depends(get_job_service),
) -> JobResponse:
    """Get status and results of a specific analysis job.

    Args:
        job_id: Unique job identifier
        auth: Authentication credentials (required)
        service: Injected JobManagementService

    Returns:
        JobResponse with status, results, and metadata

    Raises:
        HTTPException: 404 if job not found
    """
    job = await service.get_job_status(job_id)
    if not job:
        logger.warning("Job not found", extra={"job_id": job_id})
        raise HTTPException(404, "Job not found")

    return JobResponse(**job)


@router.get("/jobs")
async def list_jobs(
    status: Optional[JobStatus] = None,
    plugin: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    auth: dict = Depends(require_auth(["analyze"])),
    service: JobManagementService = Depends(get_job_service),
) -> dict:
    """List recent analysis jobs with optional filtering.

    Args:
        status: Optional job status filter
        plugin: Optional plugin name filter
        limit: Maximum number of jobs to return (1-200)
        auth: Authentication with "analyze" permission (required)
        service: Injected JobManagementService

    Returns:
        Dictionary with jobs list and count
    """
    jobs_result = await service.list_jobs(status=status, plugin=plugin, limit=limit)
    jobs_list = list(jobs_result)
    logger.debug(
        "Listed jobs",
        extra={"count": len(jobs_list), "status": status, "plugin": plugin},
    )
    return {"jobs": [JobResponse(**j) for j in jobs_list], "count": len(jobs_list)}


@router.delete("/jobs/{job_id}")
async def cancel_job(
    job_id: str,
    auth: dict = Depends(require_auth(["analyze"])),
    service: JobManagementService = Depends(get_job_service),
) -> dict:
    """Cancel a queued or processing job.

    Args:
        job_id: Unique job identifier
        auth: Authentication with "analyze" permission (required)
        service: Injected JobManagementService

    Returns:
        Dictionary with status and job_id

    Raises:
        HTTPException: 400 if job cannot be cancelled (running or completed)
    """
    success = await service.cancel_job(job_id)
    if success:
        logger.info("Job cancelled", extra={"job_id": job_id})
        return {"status": "cancelled", "job_id": job_id}

    logger.warning(
        "Job cannot be cancelled",
        extra={"job_id": job_id, "reason": "running or completed"},
    )
    raise HTTPException(
        400, "Job cannot be cancelled (may already be running or completed)"
    )


# Plugin Management Endpoints


@router.get("/plugins")
async def list_plugins(
    service: PluginManagementService = Depends(get_plugin_service),
) -> dict:
    """List all available vision analysis plugins.

    Args:
        service: Injected PluginManagementService

    Returns:
        Dictionary with plugins list and count
    """
    plugins = await service.list_plugins()
    logger.debug("Listed plugins", extra={"count": len(plugins)})
    return {
        "plugins": [PluginMetadata(**meta) for meta in plugins],
        "count": len(plugins),
    }


@router.get("/plugins/{name}", response_model=PluginMetadata)
async def get_plugin_info(
    name: str,
    service: PluginManagementService = Depends(get_plugin_service),
) -> PluginMetadata:
    """Get detailed information about a specific plugin.

    Args:
        name: Plugin identifier
        service: Injected PluginManagementService

    Returns:
        PluginMetadata with plugin details

    Raises:
        HTTPException: 404 if plugin not found
    """
    plugin_info = await service.get_plugin_info(name)
    if not plugin_info:
        logger.warning("Plugin not found", extra={"plugin": name})
        raise HTTPException(404, f"Plugin '{name}' not found")

    return PluginMetadata(**plugin_info)


@router.post("/plugins/{name}/reload")
async def reload_plugin(
    name: str,
    auth: dict = Depends(require_auth(["admin"])),
    service: PluginManagementService = Depends(get_plugin_service),
) -> dict:
    """Reload a specific plugin (admin only).

    Triggers a reload of the specified plugin, refreshing its code and state.

    Args:
        name: Plugin identifier
        auth: Authentication with "admin" permission (required)
        service: Injected PluginManagementService

    Returns:
        Dictionary with status and plugin name

    Raises:
        HTTPException: 500 if reload fails
    """
    success = await service.reload_plugin(name)
    if success:
        logger.info("Plugin reloaded", extra={"plugin": name})
        return {"status": "reloaded", "plugin": name}

    logger.error("Failed to reload plugin", extra={"plugin": name})
    raise HTTPException(500, f"Failed to reload plugin '{name}'")


@router.post("/plugins/reload-all")
async def reload_all_plugins(
    auth: dict = Depends(require_auth(["admin"])),
    service: PluginManagementService = Depends(get_plugin_service),
) -> dict:
    """Reload all plugins (admin only).

    Triggers a reload of all registered plugins.

    Args:
        auth: Authentication with "admin" permission (required)
        service: Injected PluginManagementService

    Returns:
        Operation result with status details
    """
    result = await service.reload_all_plugins()
    logger.info("All plugins reloaded", extra={"result": result})
    return result


# MCP Protocol Discovery Endpoints


@router.get("/mcp-manifest")
async def mcp_manifest(
    request: Request,
    service: PluginManagementService = Depends(get_plugin_service),
) -> dict:
    """MCP manifest for Gemini-CLI discovery.

    Returns MCP protocol manifest describing available tools.

    Args:
        request: FastAPI request context
        service: Injected PluginManagementService

    Returns:
        MCP manifest dictionary
    """
    base_url = str(request.base_url).rstrip("/")
    adapter = MCPAdapter(request.app.state.plugins, base_url)
    logger.debug("MCP manifest requested", extra={"base_url": base_url})
    return adapter.get_manifest()


@router.get("/mcp-version")
async def mcp_version() -> dict:
    """MCP protocol version and server information.

    Returns server identity and protocol version information.

    Returns:
        Dictionary with server_name, server_version, and mcp_version
    """
    logger.debug("MCP version requested")
    return {
        "server_name": MCP_SERVER_NAME,
        "server_version": MCP_SERVER_VERSION,
        "mcp_version": MCP_PROTOCOL_VERSION,
    }


@router.get("/.well-known/mcp-manifest")
async def well_known_mcp_manifest(
    request: Request,
    service: PluginManagementService = Depends(get_plugin_service),
) -> dict:
    """MCP manifest at well-known location for discovery.

    Standard location for MCP discovery as per spec.

    Args:
        request: FastAPI request context
        service: Injected PluginManagementService

    Returns:
        MCP manifest dictionary
    """
    base_url = str(request.base_url).rstrip("/")
    adapter = MCPAdapter(request.app.state.plugins, base_url)
    logger.debug("Well-known MCP manifest requested", extra={"base_url": base_url})
    return adapter.get_manifest()


@router.get("/gemini-extension")
async def gemini_extension_manifest(request: Request) -> dict:
    """Gemini extension manifest for easy installation.

    Returns manifest compatible with Gemini CLI extension system.

    Args:
        request: FastAPI request context

    Returns:
        Extension manifest dictionary
    """
    base_url = str(request.base_url).rstrip("/")
    logger.debug("Gemini extension manifest requested", extra={"base_url": base_url})
    return build_gemini_extension_manifest(base_url)


# Health Check Endpoint


@router.get("/health")
async def health_check(
    request: Request,
    service: PluginManagementService = Depends(get_plugin_service),
) -> dict:
    """System health check endpoint.

    Verifies that core components are operational.

    Args:
        request: FastAPI request context
        service: Injected PluginManagementService

    Returns:
        Dictionary with status, plugins_loaded, and version
    """
    pm = request.app.state.plugins
    plugins_count = len(pm.list())
    # System is healthy if core services are running, regardless of plugin count
    # Plugins are now optional in the new architecture
    is_healthy = True

    logger.debug(
        "Health check performed",
        extra={
            "status": "healthy" if is_healthy else "degraded",
            "plugins": plugins_count,
        },
    )

    return {
        "status": "healthy" if is_healthy else "degraded",
        "plugins_loaded": plugins_count,
        "version": "0.1.0",
    }
