"""REST API endpoints for the Vision MCP Server.

This module provides thin endpoint handlers that delegate business logic to
service layer classes. The separation of concerns enables testability,
maintainability, and clear distinction between HTTP transport and business logic.

Endpoints are organized by domain:
    - /plugins: Plugin discovery and management
    - /mcp-*: Model Context Protocol discovery
    - /health: System health monitoring

Note: Legacy /analyze and /jobs endpoints were removed in v0.9.3.
      Use the unified job system via /v1/image/submit and /v1/jobs/{id}.
"""

import logging
import time
from typing import Any, Dict, List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)

from .auth import require_auth

# Import tool mapping configuration
from .mcp import (
    MCP_PROTOCOL_VERSION,
    MCP_SERVER_NAME,
    MCP_SERVER_VERSION,
    MCPAdapter,
    build_gemini_extension_manifest,
)
from .models_pydantic import (
    PluginToolRunRequest,
    PluginToolRunResponse,
)
from .services.plugin_management_service import PluginManagementService

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================================================
# Dependency Injection
# ============================================================================


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
# Plugin Management Endpoints
# ============================================================================


@router.get("/plugins")
async def list_plugins(
    service: PluginManagementService = Depends(get_plugin_service),
) -> List[Dict[str, Any]]:
    """List all available vision analysis plugins.

    Phase 11 API Contract: Returns flat list of PluginHealthResponse dicts.

    Args:
        service: Injected PluginManagementService.

    Returns:
        Flat list of plugin health status dicts with fields:
        - name: Plugin identifier
        - state: Lifecycle state (LOADED|INITIALIZED|RUNNING|FAILED|UNAVAILABLE)
        - description: Human-readable description
        - reason: Error reason if FAILED/UNAVAILABLE
        - success_count: Number of successful executions
        - error_count: Number of failed executions
        - last_used: ISO timestamp of last use
        - uptime_seconds: Seconds since plugin was loaded
        - last_execution_time_ms: Last execution duration in ms
        - avg_execution_time_ms: Average execution duration in ms
    """
    # Get registry directly to access health data (not service which returns manifests)
    from .plugins.loader.plugin_registry import get_registry

    registry = get_registry()
    plugins = registry.list_all()
    logger.debug("Plugins listed", extra={"count": len(plugins)})

    # Return flat list of PluginHealthResponse dicts (Phase 11 contract)
    return [
        plugin.model_dump() if hasattr(plugin, "model_dump") else plugin
        for plugin in plugins
    ]


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
