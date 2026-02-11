"""Pipeline schemas for Phase 13 - Multi-Tool Linear Pipelines."""

from typing import Any, Dict, List

from pydantic import BaseModel


class PipelineRequest(BaseModel):
    """Request model for video pipeline execution."""

    plugin_id: str
    tools: List[str]
    payload: Dict[str, Any]
