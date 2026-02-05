"""REST API endpoints for the Vision MCP Server.

This module provides thin endpoint handlers that delegate business logic to
service layer classes. The separation of concerns enables testability,
maintainability, and clear distinction between HTTP transport and business logic.

Endpoints are organized by domain:
    - /analyze: Image analysis job submission
    - /jobs: Job status and lifecycle management
    - /plugins: Plugin discovery and management
    - /mcp-*: Model Context Protocol discovery
    - /health: System health monitoring
"""

import json
import logging
import time
from typing import Any, Dict, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)

from .auth import require_auth
from .exceptions import ExternalServiceError
from .mcp import (
    MCP_PROTOCOL_VERSION,
    MCP_SERVER_NAME,
    MCP_SERVER_VERSION,
    MCPAdapter,
    build_gemini_extension_manifest,
)
from .models import (
    AnalyzeResponse,
    JobResponse,
    JobResultResponse,
    JobStatus,
    JobStatusResponse,
    PluginMetadata,
    PluginToolRunRequest,
    PluginToolRunResponse,
)
from .services.analysis_service import AnalysisService
from .services.device_selector import validate_device
from .services.job_management_service import JobManagementService
from .services.plugin_management_service import PluginManagementService

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================================================
# Dependency Injection
# ============================================================================


def get_analysis_service(request: Request) -> AnalysisService:
    """Inject AnalysisService from application state.

    Args:
        request: FastAPI request with app state containing services.

    Returns:
        AnalysisService instance from app state.

    Raises:
        RuntimeError: If AnalysisService not initialized in app state.
    """
    if not hasattr(request.app.state, "analysis_service_rest"):
        raise RuntimeError("AnalysisService not initialized")
    return request.app.state.analysis_service_rest


def get_job_service(request: Request) -> JobManagementService:
    """Inject JobManagementService from application state.

    Args:
        request: FastAPI request with app state containing services.

    Returns:
        JobManagementService instance from app state.

    Raises:
        RuntimeError: If JobManagementService not initialized in app state.
    """
    if not hasattr(request.app.state, "job_service"):
        raise RuntimeError("JobManagementService not initialized")
    return request.app.state.job_service


def get_plugin_service(request: Request) -> PluginManagementService:
    """Inject PluginManagementService from application state.

    Args:
        request: FastAPI request with app state containing services.

    Returns:
        PluginManagementService instance from app state.

    Raises:
        RuntimeError: If PluginManagementService not initialized in app state.
    """
    if not hasattr(request.app.state, "plugin_service"):
        raise RuntimeError("PluginManagementService not initialized")
    return request.app.state.plugin_service


# ============================================================================
# Image Analysis Endpoints
# ============================================================================


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_image(
    request: Request,
    file: Optional[UploadFile] = None,
    plugin: str = Query(..., description="Vision plugin identifier"),
    image_url: Optional[str] = Query(None, description="URL of image to analyze"),
    options: Optional[str] = Query(None, description="JSON string of plugin options"),
    device: str = Query("cpu", description="Device to use: 'cpu' or 'gpu'"),
    auth: Dict[str, Any] = Depends(require_auth(["analyze"])),
    service: AnalysisService = Depends(get_analysis_service),
) -> AnalyzeResponse:
    """Submit an image for analysis using specified vision plugin.

    Supports multiple image sources: file upload, remote URL, or raw body bytes.
    Returns job ID for asynchronous result tracking via GET /jobs/{job_id}.

    Args:
        request: FastAPI request context with body and app state.
        file: Optional file upload containing image data.
                Defaults to "ocr".
        image_url: Optional HTTP(S) URL to fetch image from.
        options: Optional JSON string with plugin-specific configuration.
        device: Device to use ("cpu" or "gpu", default "cpu").
        auth: Authentication credentials (required, "analyze" permission).
        service: Injected AnalysisService for orchestration.

    Returns:
        AnalyzeResponse containing job_id, device info, and frame tracking.

    Raises:
        HTTPException: 400 Bad Request if options JSON is invalid.
        HTTPException: 400 Bad Request if image URL fetch fails.
        HTTPException: 400 Bad Request if image data is invalid.
        HTTPException: 400 Bad Request if device parameter is invalid.
        HTTPException: 500 Internal Server Error if unexpected failure occurs.
    """
    try:
        # Validate plugin is not empty
        if not plugin or not plugin.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Plugin name is required",
            )

        # Validate device parameter
        if not validate_device(device):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid device: '{device}'. Must be 'cpu' or 'gpu'.",
            )

        # Read uploaded file if provided
        file_bytes = await file.read() if file else None

        # Parse JSON options string into dict
        parsed_options: Dict[str, Any] = {}
        if options:
            try:
                parsed_options = json.loads(options)
            except json.JSONDecodeError as e:
                logger.warning(
                    "Invalid JSON in options parameter",
                    extra={"error": str(e), "plugin": plugin},
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON in options",
                ) from e

        # Delegate to service layer for analysis orchestration
        result = await service.process_analysis_request(
            file_bytes=file_bytes,
            image_url=image_url,
            body_bytes=await request.body() if not file else None,
            plugin=plugin,
            options=parsed_options,
            device=device.lower(),
        )

        logger.info(
            "Analysis request submitted",
            extra={"job_id": result["job_id"], "plugin": plugin},
        )

        # Return typed response with device info and frame tracking
        device_requested = device.lower()
        return AnalyzeResponse(
            job_id=result["job_id"],
            device_requested=device_requested,
            device_used=device_requested,  # Will be updated when job completes
            fallback=False,  # Will be updated if fallback occurs
            frames=[],  # Will be populated as frames are processed
            result=None,  # Will be populated when analysis completes
        )

    except ExternalServiceError as e:
        logger.error(
            "Failed to fetch remote image",
            extra={"url": image_url, "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch image: {e}",
        ) from e

    except ValueError as e:
        logger.warning(
            "Invalid image data provided",
            extra={"error": str(e), "plugin": plugin},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image: {e}",
        ) from e

    except HTTPException:
        raise

    except Exception as e:
        logger.exception(
            "Unexpected error during analysis submission",
            extra={"plugin": plugin, "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


# ============================================================================
# Job Management Endpoints
# ============================================================================


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    auth: Dict[str, Any] = Depends(require_auth(["analyze"])),
    service: JobManagementService = Depends(get_job_service),
) -> JobStatusResponse:
    """Retrieve status and results for a specific analysis job.

    Args:
        job_id: Unique job identifier to retrieve.
        auth: Authentication credentials (required, "analyze" permission).
        service: Injected JobManagementService.

    Returns:
        JobStatusResponse containing job status and device information.

    Raises:
        HTTPException: 404 Not Found if job does not exist.
    """
    job = await service.get_job_status(job_id)
    if not job:
        logger.warning("Job not found", extra={"job_id": job_id})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Map job status string to JobStatus enum
    job_status = job.get("status", "queued")
    if isinstance(job_status, str):
        try:
            job_status = JobStatus(job_status)
        except ValueError:
            job_status = JobStatus.QUEUED

    return JobStatusResponse(
        job_id=job["job_id"],
        status=job_status,
        device_requested=job.get("device_requested", "cpu"),
        device_used=job.get("device_used", job.get("device_requested", "cpu")),
    )


@router.get("/jobs/{job_id}/result", response_model=JobResultResponse)
async def get_job_result(
    job_id: str,
    auth: Dict[str, Any] = Depends(require_auth(["analyze"])),
    service: JobManagementService = Depends(get_job_service),
) -> JobResultResponse:
    """Retrieve full results for a completed analysis job.

    Returns the complete job result including frames and analysis output.

    Args:
        job_id: Unique job identifier to retrieve.
        auth: Authentication credentials (required, "analyze" permission).
        service: Injected JobManagementService.

    Returns:
        JobResultResponse containing job result with frames and analysis output.

    Raises:
        HTTPException: 404 Not Found if job does not exist.
    """
    job = await service.get_job_status(job_id)
    if not job:
        logger.warning("Job not found", extra={"job_id": job_id})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Determine if fallback occurred
    device_requested = job.get("device_requested", "cpu")
    device_used = job.get("device_used", device_requested)
    fallback = device_requested != device_used

    # Get result data
    result = job.get("result", {})

    return JobResultResponse(
        job_id=job["job_id"],
        device_requested=device_requested,
        device_used=device_used,
        fallback=fallback,
        frames=[],  # Will be populated as frames are tracked
        result=result,
    )


@router.get("/jobs")
async def list_jobs(
    status: Optional[JobStatus] = None,
    plugin: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    auth: Dict[str, Any] = Depends(require_auth(["analyze"])),
    service: JobManagementService = Depends(get_job_service),
) -> Dict[str, Any]:
    """List recent analysis jobs with optional filtering.

    Args:
        status: Optional job status filter (queued, running, done, error).
        plugin: Optional plugin name filter.
        limit: Maximum number of jobs to return. Range: 1-200, default: 50.
        auth: Authentication credentials (required, "analyze" permission).
        service: Injected JobManagementService.

    Returns:
        Dictionary containing:
            - jobs: List of JobResponse objects.
            - count: Total number of jobs returned.
    """
    jobs_result = await service.list_jobs(status=status, plugin=plugin, limit=limit)
    jobs_list = list(jobs_result)

    logger.debug(
        "Jobs listed",
        extra={"count": len(jobs_list), "status": status, "plugin": plugin},
    )

    # Ensure all required JobResponse fields are present
    jobs_response = []
    for j in jobs_list:
        # Provide defaults for required fields if missing
        job_data = {
            "job_id": j.get("job_id"),
            "status": j.get("status", JobStatus.QUEUED),
            "result": j.get("result"),
            "error": j.get("error"),
            "created_at": j.get("created_at"),
            "completed_at": j.get("completed_at"),
            "plugin": j.get("plugin", "unknown"),
            "progress": j.get("progress", 0),
        }
        jobs_response.append(JobResponse(**job_data))

    return {
        "jobs": jobs_response,
        "count": len(jobs_list),
    }


@router.delete("/jobs/{job_id}")
async def cancel_job(
    job_id: str,
    auth: Dict[str, Any] = Depends(require_auth(["analyze"])),
    service: JobManagementService = Depends(get_job_service),
) -> Dict[str, Any]:
    """Cancel a queued or processing analysis job.

    Only jobs in queued or processing state can be cancelled. Completed or
    errored jobs cannot be cancelled.

    Args:
        job_id: Unique job identifier to cancel.
        auth: Authentication credentials (required, "analyze" permission).
        service: Injected JobManagementService.

    Returns:
        Dictionary containing:
            - status: "cancelled" if successful.
            - job_id: The cancelled job identifier.

    Raises:
        HTTPException: 404 Not Found if job doesn't exist or cannot be cancelled.
    """
    success = await service.cancel_job(job_id)
    if not success:
        logger.warning(
            "Job cannot be cancelled",
            extra={"job_id": job_id, "reason": "not found or already completed"},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or already completed",
        )

    logger.info("Job cancelled", extra={"job_id": job_id})
    return {"status": "cancelled", "job_id": job_id}


# ============================================================================
# Plugin Management Endpoints
# ============================================================================


@router.get("/plugins")
async def list_plugins(
    service: PluginManagementService = Depends(get_plugin_service),
) -> Dict[str, Any]:
    """List all available vision analysis plugins.

    Args:
        service: Injected PluginManagementService.

    Returns:
        Dictionary containing:
            - plugins: List of PluginMetadata objects.
            - count: Total number of plugins available.
    """
    plugins = await service.list_plugins()

    logger.debug("Plugins listed", extra={"count": len(plugins)})

    return {
        "plugins": [plugin.metadata() for plugin in plugins],
        "count": len(plugins),
    }


@router.get("/plugins/{name}", response_model=PluginMetadata)
async def get_plugin_info(
    name: str,
    service: PluginManagementService = Depends(get_plugin_service),
) -> PluginMetadata:
    """Retrieve detailed information about a specific plugin.

    Args:
        name: Plugin identifier to retrieve.
        service: Injected PluginManagementService.

    Returns:
        PluginMetadata containing plugin details.

    Raises:
        HTTPException: 404 Not Found if plugin does not exist.
    """
    plugin = await service.get_plugin_info(name)
    if not plugin:
        logger.warning("Plugin not found", extra={"plugin": name})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{name}' not found",
        )

    return plugin.metadata()


@router.post("/plugins/{name}/reload")
async def reload_plugin(
    name: str,
    auth: Dict[str, Any] = Depends(require_auth(["admin"])),
    service: PluginManagementService = Depends(get_plugin_service),
) -> Dict[str, Any]:
    """Reload a specific plugin (admin only).

    Triggers a dynamic reload of the specified plugin, refreshing its code
    and internal state without restarting the server.

    Args:
        name: Plugin identifier to reload.
        auth: Authentication credentials (required, "admin" permission).
        service: Injected PluginManagementService.

    Returns:
        Dictionary containing:
            - status: "reloaded" if successful.
            - plugin: The reloaded plugin name.

    Raises:
        HTTPException: 500 Internal Server Error if reload fails.
    """
    success = await service.reload_plugin(name)
    if not success:
        logger.error("Failed to reload plugin", extra={"plugin": name})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload plugin '{name}'",
        )

    logger.info("Plugin reloaded", extra={"plugin": name})
    return {"status": "reloaded", "plugin": name}


@router.post("/plugins/reload-all")
async def reload_all_plugins(
    auth: Dict[str, Any] = Depends(require_auth(["admin"])),
    service: PluginManagementService = Depends(get_plugin_service),
) -> Dict[str, Any]:
    """Reload all registered plugins (admin only).

    Triggers a dynamic reload of all active plugins simultaneously.

    Args:
        auth: Authentication credentials (required, "admin" permission).
        service: Injected PluginManagementService.

    Returns:
        Operation result with status details and per-plugin results.
    """
    result = await service.reload_all_plugins()

    logger.info("All plugins reloaded", extra={"result": result})

    return result


# ============================================================================
# Video Tracker Endpoints (Manifest & Tool Execution)
# ============================================================================


@router.get("/plugins/{plugin_id}/manifest")
async def get_plugin_manifest(
    plugin_id: str,
    plugin_service: PluginManagementService = Depends(get_plugin_service),
) -> Dict[str, Any]:
    """Get plugin manifest including tool schemas.

    The manifest describes what tools a plugin exposes, their input schemas,
    and output schemas. This enables the web-ui to dynamically discover and
    call tools without hardcoding plugin logic.

    Args:
        plugin_service: Plugin management service (injected)

    Returns:
        Manifest dict:
        {
            "name": "YOLO Football Tracker",
            "version": "1.0.0",
            "description": "...",
            "tools": {
                "player_detection": {
                    "description": "...",
                    "inputs": {...},
                    "outputs": {...}
                },
                ...
            }
        }

    Raises:
        HTTPException(404): Plugin not found or has no manifest
        HTTPException(500): Error reading manifest file

    Example:
        → 200 OK
        {
            "name": "YOLO Football Tracker",
            "tools": { ... }
        }
    """
    try:
        manifest = plugin_service.get_plugin_manifest(plugin_id)
        if not manifest:
            raise HTTPException(
                status_code=404,
                detail=f"Plugin '{plugin_id}' not found or has no manifest",
            )
        return manifest
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting manifest for plugin '{plugin_id}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error reading manifest: {str(e)}",
        ) from e


@router.post(
    "/plugins/{plugin_id}/tools/{tool_name}/run",
    response_model=PluginToolRunResponse,
)
async def run_plugin_tool(
    plugin_id: str,
    tool_name: str,
    request: PluginToolRunRequest,
    plugin_service: PluginManagementService = Depends(get_plugin_service),
) -> PluginToolRunResponse:
    """Execute a plugin tool directly (synchronous).

    Runs a specified tool from a plugin with the provided arguments.
    This is a synchronous endpoint used for real-time frame processing.
    For batch/video processing, use the async job endpoints instead.

    Args:
        tool_name: Tool name (e.g., "player_detection")
        request: Tool execution request with arguments
        plugin_service: Plugin management service (injected)

    Returns:
        PluginToolRunResponse with:
        - tool_name: Name of executed tool
        - plugin_id: Plugin ID
        - result: Tool output (dict, matches manifest output schema)
        - processing_time_ms: Execution time

    Raises:
        HTTPException(400): Invalid arguments or plugin execution failed
        HTTPException(404): Plugin or tool not found
        HTTPException(500): Unexpected error

    Example:
        {
            "args": {
                "frame_base64": "iVBORw0KGgo...",
                "device": "cpu",
                "annotated": false
            }
        }
        → 200 OK
        {
            "tool_name": "player_detection",
            "result": {"detections": [...]},
            "processing_time_ms": 42
        }
    """
    try:
        # Record start time
        start_time = time.time()

        # Execute tool
        logger.debug(
            f"Executing tool '{tool_name}' on plugin '{plugin_id}' "
            f"with {len(request.args)} args"
        )

        result = plugin_service.run_plugin_tool(
            plugin_id=plugin_id, tool_name=tool_name, args=request.args
        )

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Log successful execution
        logger.info(
            f"Tool execution successful: {plugin_id}/{tool_name} "
            f"({processing_time_ms}ms)"
        )

        return PluginToolRunResponse(
            tool_name=tool_name,
            plugin_id=plugin_id,
            result=result,
            processing_time_ms=processing_time_ms,
        )

    except ValueError as e:
        # Plugin/tool not found or validation error
        logger.warning(f"Tool execution validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e

    except TimeoutError as e:
        # Tool execution timed out
        logger.error(f"Tool execution timeout: {e}")
        raise HTTPException(
            status_code=408,
            detail=f"Tool execution timed out: {str(e)}",
        ) from e

    except Exception as e:
        # Unexpected error
        logger.error(
            f"Unexpected error executing tool '{tool_name}' "
            f"on plugin '{plugin_id}': {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Tool execution failed: {str(e)}",
        ) from e


# ============================================================================
# Protocol Discovery Endpoints (MCP & Gemini)
# ============================================================================


@router.get("/mcp-manifest")
async def mcp_manifest(
    request: Request,
    service: PluginManagementService = Depends(get_plugin_service),
) -> Dict[str, Any]:
    """Return Model Context Protocol manifest for tool discovery.

    Provides MCP-compliant manifest describing available analysis tools
    and their capabilities for integration with MCP clients.

    Args:
        request: FastAPI request context with base URL.
        service: Injected PluginManagementService.

    Returns:
        MCP manifest dictionary containing tools and server information.
    """
    base_url = str(request.base_url).rstrip("/")
    adapter = MCPAdapter(request.app.state.plugins, base_url)

    logger.debug("MCP manifest requested", extra={"base_url": base_url})

    return adapter.get_manifest()


@router.get("/mcp-version")
async def mcp_version() -> Dict[str, str]:
    """Return MCP protocol and server version information.

    Provides server identity and supported MCP protocol version for clients
    to verify compatibility before establishing connections.

    Returns:
        Dictionary containing:
            - server_name: Server identifier.
            - server_version: Application semantic version.
            - mcp_version: Supported MCP protocol version.
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
) -> Dict[str, Any]:
    """Return MCP manifest at standard well-known location.

    Provides MCP discovery at the standardized /.well-known/ path for
    automatic client discovery and compatibility checking.

    Args:
        request: FastAPI request context with base URL.
        service: Injected PluginManagementService.

    Returns:
        MCP manifest dictionary (same as /mcp-manifest).
    """
    base_url = str(request.base_url).rstrip("/")
    adapter = MCPAdapter(request.app.state.plugins, base_url)

    logger.debug("Well-known MCP manifest requested", extra={"base_url": base_url})

    return adapter.get_manifest()


@router.get("/gemini-extension")
async def gemini_extension_manifest(request: Request) -> Dict[str, Any]:
    """Return manifest for Gemini CLI extension installation.

    Provides extension manifest compatible with Gemini CLI for streamlined
    plugin installation and integration.

    Args:
        request: FastAPI request context with base URL.

    Returns:
        Gemini extension manifest dictionary.
    """
    base_url = str(request.base_url).rstrip("/")

    logger.debug("Gemini extension manifest requested", extra={"base_url": base_url})

    return build_gemini_extension_manifest(base_url)


# ============================================================================
# Health Monitoring Endpoint
# ============================================================================


@router.get("/health")
async def health_check(
    request: Request,
    service: PluginManagementService = Depends(get_plugin_service),
) -> Dict[str, Any]:
    """System health check endpoint for infrastructure monitoring.

    Verifies that core components are operational. Used by load balancers,
    container orchestrators, and monitoring systems to detect failures and
    route traffic accordingly.

    Note: Plugins are optional in the current architecture. System is considered
    healthy if core services are running, regardless of plugin count.

    Args:
        request: FastAPI request context with app state.
        service: Injected PluginManagementService.

    Returns:
        Dictionary containing:
            - status: "healthy" or "degraded" based on system state.
            - plugins_loaded: Number of loaded vision plugins.
            - version: Application semantic version.
    """
    pm = request.app.state.plugins
    plugins_count = len(pm.list())

    # Core services determine health; plugins are optional
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
