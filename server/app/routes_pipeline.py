"""Pipeline routes for Phase 13 - Multi-Tool Linear Pipelines.

This module provides REST endpoints for video pipeline execution.
"""

from fastapi import APIRouter, Depends, Request
from typing import Any, Dict

from ..protocols import PluginRegistry
from ..services.video_pipeline_service import VideoPipelineService
from ..schemas.pipeline import PipelineRequest


def get_plugin_registry(request: Request) -> PluginRegistry:
    """Dependency to get the plugin registry from app state."""
    return request.state.plugins


def get_pipeline_service(plugins: PluginRegistry = Depends(get_plugin_registry)) -> VideoPipelineService:
    """Dependency to get the VideoPipelineService."""
    return VideoPipelineService(plugins)


def init_pipeline_routes() -> APIRouter:
    """Initialize pipeline routes with dependency injection."""
    router = APIRouter()

    @router.post("/video/pipeline")
    async def run_video_pipeline(
        req: PipelineRequest,
        pipeline_service: VideoPipelineService = Depends(get_pipeline_service),
    ) -> Dict[str, Any]:
        """Execute a linear pipeline of tools for a single plugin."""
        result = pipeline_service.run_pipeline(
            plugin_id=req.plugin_id,
            tools=req.tools,
            payload=req.payload,
        )
        return {"result": result}

    return router

