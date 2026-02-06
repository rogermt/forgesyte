"""Execution API routes - Phase 12 governed plugin execution."""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.services.execution.analysis_execution_service import AnalysisExecutionService

router = APIRouter()
_service = AnalysisExecutionService()


@router.post("/v1/analyze-execution")
async def analyze_execution(payload: Dict[str, Any]):
    """Execute analysis with full Phase 12 governance.

    Phase 12 endpoint for governed plugin execution with:
    - Input validation (empty image, invalid MIME)
    - Structured error envelopes
    - Registry metrics update
    - Execution timing measurement
    - Output validation

    Returns structured success or structured error envelope.
    """
    plugin_name = payload.get("plugin", "default")
    result, error = _service.analyze(plugin_name=plugin_name, payload=payload)

    if error:
        # Phase 12: return structured error envelope
        raise HTTPException(status_code=400, detail=error["error"])

    return {"plugin": plugin_name, "result": result}

