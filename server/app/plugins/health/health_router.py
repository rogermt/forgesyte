"""Health router for Phase 11 plugin health API.

FastAPI router for /v1/plugins and /v1/plugins/{name}/health endpoints.
"""

from fastapi import APIRouter, HTTPException

from ..loader.plugin_registry import get_registry
from .health_model import PluginHealthResponse, PluginListResponse

router = APIRouter(prefix="/v1/plugins", tags=["plugins"])


@router.get(
    "/",
    response_model=PluginListResponse,
    summary="List all plugins",
    description="Returns list of all plugins with their health status, including failed ones.",
)
def list_plugins():
    """
    List all plugins and their health status.

    Returns:
        - total: total number of plugins
        - available: number of LOADED/INITIALIZED/RUNNING plugins
        - failed: number of FAILED plugins
        - unavailable: number of UNAVAILABLE plugins (missing deps, etc.)
        - plugins: list of PluginHealthResponse objects
    """
    registry = get_registry()
    plugins = registry.list_all()

    available = sum(
        1
        for p in plugins
        if p.state.value in {"LOADED", "INITIALIZED", "RUNNING"}
    )
    failed = sum(1 for p in plugins if p.state.value == "FAILED")
    unavailable = sum(1 for p in plugins if p.state.value == "UNAVAILABLE")

    return PluginListResponse(
        plugins=plugins,
        total=len(plugins),
        available=available,
        failed=failed,
        unavailable=unavailable,
    )


@router.get(
    "/{name}/health",
    response_model=PluginHealthResponse,
    summary="Get plugin health status",
    description="Returns detailed health status for a specific plugin, including FAILED/UNAVAILABLE plugins.",
)
def get_plugin_health(name: str):
    """
    Get health status for a specific plugin.

    Returns plugin state, error reason (if failed), and execution metrics.

    Raises:
        HTTPException 404: if plugin not found
    """
    registry = get_registry()
    status = registry.get_status(name)

    if status is None:
        raise HTTPException(
            status_code=404,
            detail=f"Plugin '{name}' not found",
        )

    return status
