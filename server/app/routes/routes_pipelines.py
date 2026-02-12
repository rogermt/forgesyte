"""
Phase 14: Pipeline REST Endpoints

Exposes pipeline functionality via HTTP API.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request

from app.pipeline_models.pipeline_graph_models import Pipeline
from app.services.dag_pipeline_service import DagPipelineService
from app.services.pipeline_registry_service import PipelineRegistryService

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


def get_pipeline_registry(request: Request) -> PipelineRegistryService:
    """Get pipeline registry from app state."""
    return request.app.state.pipeline_registry


def get_plugin_manager(request: Request):
    """Get plugin manager from app state."""
    return request.app.state.plugin_manager_for_pipelines


@router.get("/list")
async def list_pipelines(
    registry: PipelineRegistryService = Depends(get_pipeline_registry),
) -> Dict[str, Any]:
    """
    List all registered pipelines.

    Returns:
        Dictionary with list of pipeline metadata
    """
    if registry is None:
        raise HTTPException(status_code=503, detail="Pipeline registry not available")

    pipelines = registry.list()
    return {"pipelines": pipelines}


@router.get("/{pipeline_id}/info")
async def get_pipeline_info(
    pipeline_id: str, registry: PipelineRegistryService = Depends(get_pipeline_registry)
) -> Dict[str, Any]:
    """
    Get metadata about a specific pipeline.

    Args:
        pipeline_id: Unique pipeline identifier

    Returns:
        Dictionary with pipeline metadata

    Raises:
        HTTPException: If pipeline not found
    """
    if registry is None:
        raise HTTPException(status_code=503, detail="Pipeline registry not available")

    info = registry.get_info(pipeline_id)
    if info is None:
        raise HTTPException(
            status_code=404, detail=f"Pipeline not found: {pipeline_id}"
        )

    return info


@router.post("/validate")
async def validate_pipeline(
    pipeline: Pipeline,
    registry: PipelineRegistryService = Depends(get_pipeline_registry),
    plugin_manager=Depends(get_plugin_manager),
) -> Dict[str, Any]:
    """
    Validate a pipeline structure.

    Args:
        pipeline: Pipeline definition to validate

    Returns:
        Dictionary with validation result
    """
    if registry is None:
        raise HTTPException(status_code=503, detail="Pipeline registry not available")
    if plugin_manager is None:
        raise HTTPException(status_code=503, detail="Plugin manager not available")

    dag_service = DagPipelineService(registry, plugin_manager)
    result = dag_service.validate(pipeline)
    return {
        "valid": result.valid,
        "errors": result.errors,
    }


@router.post("/{pipeline_id}/run")
async def run_pipeline(
    pipeline_id: str,
    payload: Dict[str, Any],
    registry: PipelineRegistryService = Depends(get_pipeline_registry),
    plugin_manager=Depends(get_plugin_manager),
) -> Dict[str, Any]:
    """
    Execute a pipeline by ID.

    Args:
        pipeline_id: Unique pipeline identifier
        payload: Input data for the pipeline

    Returns:
        Dictionary with execution result

    Raises:
        HTTPException: If pipeline not found or execution fails
    """
    if registry is None:
        raise HTTPException(status_code=503, detail="Pipeline registry not available")
    if plugin_manager is None:
        raise HTTPException(status_code=503, detail="Plugin manager not available")

    dag_service = DagPipelineService(registry, plugin_manager)

    try:
        output = dag_service.run_pipeline(pipeline_id, payload)
        return {
            "status": "success",
            "output": output,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Pipeline execution failed: {str(e)}"
        ) from None
