"""Service for processing video files through pipelines (Phase 15).

This module provides the core business logic for:
- Opening MP4 files with OpenCV
- Extracting frames sequentially
- Encoding frames as JPEG bytes
- Calling DAG pipeline per frame
- Aggregating results
"""

from typing import Any, Dict, List, Optional, Protocol

import cv2


class DagPipelineService(Protocol):
    """Protocol for DAG pipeline execution (allows mocking)."""

    def run_pipeline(self, pipeline_id: str, payload: Dict[str, Any]) -> Any:
        """Execute pipeline with given payload.

        Args:
            pipeline_id: ID of pipeline to execute
            payload: Input payload (frame_index, image_bytes)

        Returns:
            Result from pipeline execution

        Raises:
            ValueError: If pipeline not found
            RuntimeError: If execution fails
        """
        ...


class VideoFilePipelineService:
    """Process video files frame-by-frame through a DAG pipeline."""

    def __init__(self, dag_service: DagPipelineService) -> None:
        """Initialize service with DAG executor.

        Args:
            dag_service: Service to execute DAG pipelines
        """
        self.dag_service = dag_service

    @staticmethod
    def is_valid_pipeline(pipeline_id: str) -> bool:
        """
        Check if a pipeline ID is valid.

        This is a placeholder - the actual validation requires a DagPipelineService instance.
        Use the instance method via the dag_service attribute for actual validation.

        Args:
            pipeline_id: Pipeline ID to validate

        Returns:
            False by default - use instance method for actual validation
        """
        return False

    def run_on_file(
        self,
        mp4_path: str,
        pipeline_id: str,
        frame_stride: int = 1,
        max_frames: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Process video file through pipeline.

        Opens MP4, extracts frames, runs pipeline per frame, aggregates results.

        Args:
            mp4_path: Path to MP4 file
            pipeline_id: ID of pipeline to execute
            frame_stride: Process every Nth frame (e.g., 2 = every 2nd frame)
            max_frames: Maximum number of frames to process (None = all)

        Returns:
            List of results: [{"frame_index": int, "result": {...}}, ...]

        Raises:
            ValueError: If unable to read video file
            ValueError: If pipeline not found
            RuntimeError: If pipeline execution fails
        """
        cap = cv2.VideoCapture(mp4_path)
        if not cap.isOpened():
            raise ValueError("Unable to read video file")

        results: List[Dict[str, Any]] = []
        frame_index = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:  # End of video
                    break

                # Apply frame stride filter
                if frame_index % frame_stride == 0:
                    # Encode frame as JPEG bytes (raw, not base64)
                    success, jpeg_bytes = cv2.imencode(".jpg", frame)
                    if not success:
                        raise RuntimeError(f"Failed to encode frame {frame_index}")

                    # Create payload per Phase 15 spec
                    payload = {
                        "frame_index": frame_index,
                        "image_bytes": jpeg_bytes.tobytes(),
                    }

                    # Call DAG pipeline with payload
                    result = self.dag_service.run_pipeline(pipeline_id, payload)

                    # Aggregate result
                    results.append({"frame_index": frame_index, "result": result})

                    # Check max_frames limit
                    if max_frames is not None and len(results) >= max_frames:
                        break

                frame_index += 1

        finally:
            cap.release()  # Always release, prevent leaks

        return results
