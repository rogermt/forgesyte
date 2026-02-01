"""FastAPI router for plugin management endpoints.

Provides:
- GET /v1/plugins/{plugin_id}/manifest - retrieve plugin manifest

Uses dependency injection for PluginManagementService and ManifestCacheService.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request

from .services.manifest_cache import ManifestCacheService
from .services.plugin_management_service import PluginManagementService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/plugins", tags=["plugins"])


def get_plugin_service(request: Request) -> PluginManagementService:
    """Dependency: get PluginManagementService from app state.

    Args:
        request: FastAPI Request with app.state

    Returns:
        PluginManagementService instance

    Raises:
        RuntimeError: If service not initialized in app state
    """
    if not hasattr(request.app.state, "plugin_service"):
        raise RuntimeError("PluginManagementService not initialized in app state")
    return request.app.state.plugin_service


@router.get("/{plugin_id}/manifest")
async def get_manifest(
    plugin_id: str,
    plugin_service: PluginManagementService = Depends(get_plugin_service),
    cache: ManifestCacheService = Depends(ManifestCacheService.dep),
) -> Dict[str, Any]:
    """Get plugin manifest by ID.

    Retrieves the plugin's manifest.json, which defines:
    - Plugin metadata (name, version, description)
    - Available tools and their schemas (inputs/outputs)

    Manifest is cached with 60-second TTL to reduce disk I/O.

    Args:
        plugin_id: Plugin identifier (e.g., "yolo-tracker", "ocr")
        plugin_service: PluginManagementService dependency
        cache: ManifestCacheService dependency (60s TTL)

    Returns:
        Manifest dictionary with plugin metadata and tool schemas

    Raises:
        HTTPException 404: Plugin not found
        HTTPException 503: Unable to retrieve manifest
    """
    logger.debug(f"GET /plugins/{plugin_id}/manifest")

    # Try cache first
    cached = cache.get(plugin_id)
    if cached is not None:
        logger.debug(f"Cache hit for manifest '{plugin_id}'")
        return cached

    # Load from disk via PluginManagementService
    try:
        manifest = plugin_service.get_plugin_manifest(plugin_id)

        if manifest is None:
            logger.warning(f"Plugin '{plugin_id}' not found")
            raise HTTPException(
                status_code=404,
                detail=f"Plugin '{plugin_id}' not found",
            )

        # Cache for future requests
        cache.set(plugin_id, manifest)
        logger.debug(f"Cached manifest for '{plugin_id}'")

        return manifest

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(
            f"Failed to retrieve manifest for '{plugin_id}'",
            extra={"error": str(e)},
        )
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve plugin manifest",
        ) from e
