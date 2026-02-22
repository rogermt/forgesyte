"""Pipeline routes for Phase 13 - Multi-Tool Linear Pipelines.

v0.9.3 — Updated to use PluginManagementService instead of VideoPipelineService.
This module provides REST endpoints for video pipeline execution.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request

from .protocols import PluginRegistry
from .schemas.pipeline import PipelineRequest
from .services.plugin_management_service import PluginManagementService


def get_plugin_registry(request: Request) -> PluginRegistry:
    """Dependency to get the plugin registry from app state."""
    return request.app.state.plugins


def get_plugin_service(
    plugins: PluginRegistry = Depends(get_plugin_registry),
) -> PluginManagementService:
    """Dependency to get the PluginManagementService."""
    return PluginManagementService(plugins)


def init_pipeline_routes() -> APIRouter:
    """Initialize pipeline routes with dependency injection."""
    router = APIRouter()

    @router.post("/video/pipeline")
    async def run_video_pipeline(
        req: PipelineRequest,
        plugin_service: PluginManagementService = Depends(get_plugin_service),
    ) -> Dict[str, Any]:
        """Execute a linear pipeline of tools for a single plugin.

        v0.9.3: Updated to use PluginManagementService.run_plugin_tool()
        for each tool in the pipeline instead of VideoPipelineService.
        """
        try:
            # Execute each tool sequentially
            results = []
            current_payload = req.payload

            for tool_name in req.tools:
                result = plugin_service.run_plugin_tool(
                    plugin_id=req.plugin_id,
                    tool_name=tool_name,
                    args=current_payload,
                )
                results.append(result)
                # Use the result as input for the next tool
                current_payload = result

            return {
                "result": results[-1] if results else {},
                "steps": results,
                "plugin_id": req.plugin_id,
                "tools": req.tools,
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    return router
