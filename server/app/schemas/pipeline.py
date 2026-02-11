"""Pipeline schemas for Phase 13 - Multi-Tool Linear Pipelines."""

from pydantic import BaseModel
from typing import Any, Dict, List


class PipelineRequest(BaseModel):
    """Request model for video pipeline execution."""

    plugin_id: str
    tools: List[str]
    payload: Dict[str, Any]

