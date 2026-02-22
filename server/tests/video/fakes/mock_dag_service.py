"""Mock DAG service for unit testing (Phase 15).

Provides a test double for DagPipelineService that:
- Returns deterministic mock results
- Supports failure injection (pipeline_not_found, plugin_error)
- Never calls real plugins
"""

from typing import Any, Dict, Optional


class MockDagPipelineService:
    """Mock implementation of DagPipelineService for testing.

    Allows tests to run without real plugins installed.
    Supports failure injection for error scenario testing.
    """

    def __init__(self, fail_mode: Optional[str] = None) -> None:
        """Initialize mock service.

        Args:
            fail_mode: None (success), "pipeline_not_found", "plugin_error"
        """
        self.fail_mode = fail_mode
        self.call_count = 0
        self.last_payload: Optional[Dict[str, Any]] = None

    def run_pipeline(self, pipeline_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute mock pipeline (returns deterministic result).

        Args:
            pipeline_id: ID of pipeline to execute
            payload: Input payload {frame_index, image_bytes}

        Returns:
            Mock YOLO + OCR result

        Raises:
            ValueError: If pipeline not found (when fail_mode set)
            RuntimeError: If plugin error (when fail_mode set)
        """
        self.call_count += 1
        self.last_payload = payload

        # Inject failures
        if self.fail_mode == "pipeline_not_found":
            raise ValueError(f"Pipeline '{pipeline_id}' not found")

        if self.fail_mode == "plugin_error":
            raise RuntimeError("Plugin execution failed")

        # Success: return mock YOLO + OCR result
        # Deterministic output based on frame_index
        frame_index = payload.get("frame_index", 0)
        return {
            "detections": [
                {
                    "class": "player",
                    "confidence": 0.95,
                    "bbox": [10 + frame_index * 5, 20, 100, 200],
                }
            ],
            "text": f"Frame {frame_index}: SCORE 2-1",
        }
