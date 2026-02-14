"""Router for video file processing (Phase 15).

Handles synchronous MP4 processing through YOLO+OCR pipeline.
Single request/response per MP4 file.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel, Field

from app.services.dag_pipeline_service import DagPipelineService
from app.services.pipeline_registry_service import PipelineRegistryService
from app.services.video_file_pipeline_service import VideoFilePipelineService

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class VideoProcessingRequest(BaseModel):
    """Request to process video file through pipeline."""

    pipeline_id: str = Field(
        ...,
        description="Pipeline ID to execute (e.g., 'yolo_ocr')",
    )
    frame_stride: int = Field(
        default=1,
        ge=1,
        description="Process every Nth frame (e.g., 2 = every 2nd frame)",
    )
    max_frames: int | None = Field(
        default=None,
        ge=1,
        description="Maximum number of frames to process (None = all)",
    )


class FrameResult(BaseModel):
    """Result for a single frame."""

    frame_index: int = Field(..., description="Zero-indexed frame number")
    result: Dict[str, Any] = Field(
        ...,
        description="Pipeline output for this frame",
    )


class VideoProcessingResponse(BaseModel):
    """Response from video processing."""

    results: list[FrameResult] = Field(
        ...,
        description="Results aggregated from all processed frames",
    )


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/video", tags=["video"])


def get_pipeline_registry(request: Request) -> PipelineRegistryService:
    """Get pipeline registry from app state."""
    return request.app.state.pipeline_registry


def get_plugin_manager(request: Request):
    """Get plugin manager from app state."""
    return request.app.state.plugin_manager_for_pipelines


@router.post(
    "/process",
    response_model=VideoProcessingResponse,
    summary="Process video file through pipeline",
    description="Synchronously process MP4 file frame-by-frame through YOLO+OCR pipeline.",
)
async def process_video_file(
    file: UploadFile = File(..., description="MP4 video file to process"),
    pipeline_id: str = Query("yolo_ocr", description="Pipeline ID to execute"),
    frame_stride: int = Query(1, ge=1, description="Process every Nth frame"),
    max_frames: int | None = Query(None, ge=1, description="Maximum frames to process"),
    registry: PipelineRegistryService = Depends(get_pipeline_registry),
    plugin_manager=Depends(get_plugin_manager),
) -> VideoProcessingResponse:
    """Process video file through pipeline.

    Args:
        file: MP4 video file to process
        pipeline_id: Pipeline ID (e.g., 'yolo_ocr')
        frame_stride: Process every Nth frame (default=1)
        max_frames: Max frames to process (None=all)
        registry: Pipeline registry (injected)
        plugin_manager: Plugin manager (injected)

    Returns:
        VideoProcessingResponse with aggregated frame results

    Raises:
        HTTPException 400: Invalid file format or parameters
        HTTPException 404: Pipeline not found
        HTTPException 500: Pipeline execution failed
    """
    # Validate dependencies
    if registry is None:
        raise HTTPException(status_code=503, detail="Pipeline registry not available")
    if plugin_manager is None:
        raise HTTPException(status_code=503, detail="Plugin manager not available")

    # Validate file extension
    if not file.filename or not file.filename.lower().endswith(
        (".mp4", ".mov", ".avi")
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Must be MP4, MOV, or AVI.",
        )

    tmp_path = None
    try:
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Create DAG service and process video
        dag_service = DagPipelineService(registry, plugin_manager)
        video_service = VideoFilePipelineService(dag_service)
        results = video_service.run_on_file(
            mp4_path=tmp_path,
            pipeline_id=pipeline_id,
            frame_stride=frame_stride,
            max_frames=max_frames,
        )

        # Validate that at least one frame was processed
        # Empty results means corrupted/invalid MP4
        if not results:
            raise ValueError("Unable to read video file: no frames extracted")

        # Convert to response format
        frame_results = [
            FrameResult(
                frame_index=r["frame_index"],
                result=r["result"],
            )
            for r in results
        ]

        return VideoProcessingResponse(results=frame_results)

    except ValueError as e:
        if "Unable to read video file" in str(e):
            raise HTTPException(status_code=400, detail=str(e)) from e
        elif "pipeline not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e)) from e
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution failed: {str(e)}",
        ) from e
    finally:
        # Clean up temp file
        if tmp_path and Path(tmp_path).exists():
            Path(tmp_path).unlink()
