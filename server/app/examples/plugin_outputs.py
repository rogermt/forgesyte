"""Example Plugin Outputs.

This module provides example outputs for plugins:
- OCR_EXAMPLE: Example output from OCR/an text recognition plugin
- TRACKING_EXAMPLE: Example output from object tracking plugin

These examples are used for:
- API response documentation
- Frontend development/testing
- Plugin output standardization

Phase 9: API Typed Responses & UI Controls
"""

from typing import Any, Dict, List, Optional


# =============================================================================
# OCR Plugin Example Output
# =============================================================================

OCR_EXAMPLE: Dict[str, Any] = {
    "job_id": "ocr-job-001",
    "device_requested": "gpu",
    "device_used": "gpu",
    "fallback": False,
    "frames": [
        {
            "frame_number": 0,
            "timestamp": 0.0,
            "text_blocks": [
                {
                    "text": "Hello World",
                    "confidence": 0.98,
                    "bounds": {
                        "x1": 100,
                        "y1": 50,
                        "x2": 300,
                        "y2": 100,
                    },
                    "language": "eng",
                },
                {
                    "text": "ForgeSyte",
                    "confidence": 0.95,
                    "bounds": {
                        "x1": 150,
                        "y1": 120,
                        "x2": 400,
                        "y2": 180,
                    },
                    "language": "eng",
                },
            ],
            "full_text": "Hello World\nForgeSyte",
            "processing_time_ms": 45,
        },
        {
            "frame_number": 1,
            "timestamp": 0.033,
            "text_blocks": [
                {
                    "text": "Hello World",
                    "confidence": 0.97,
                    "bounds": {
                        "x1": 100,
                        "y1": 50,
                        "x2": 300,
                        "y2": 100,
                    },
                    "language": "eng",
                },
            ],
            "full_text": "Hello World",
            "processing_time_ms": 42,
        },
    ],
    "result": {
        "total_text_blocks": 3,
        "languages_detected": ["eng"],
        "processing_time_ms": 87,
    },
}


# =============================================================================
# Tracking Plugin Example Output
# =============================================================================

TRACKING_EXAMPLE: Dict[str, Any] = {
    "job_id": "tracking-job-001",
    "device_requested": "nvidia",
    "device_used": "nvidia",
    "fallback": False,
    "frames": [
        {
            "frame_number": 0,
            "timestamp": 0.0,
            "detections": [
                {
                    "track_id": 1,
                    "class": "person",
                    "confidence": 0.92,
                    "bbox": {
                        "x1": 120,
                        "y1": 200,
                        "x2": 180,
                        "y2": 450,
                    },
                    "history": [],
                },
                {
                    "track_id": 2,
                    "class": "person",
                    "confidence": 0.88,
                    "bbox": {
                        "x1": 400,
                        "y1": 180,
                        "x2": 480,
                        "y2": 460,
                    },
                    "history": [],
                },
            ],
            "tracking_enabled": True,
            "processing_time_ms": 32,
        },
        {
            "frame_number": 1,
            "timestamp": 0.033,
            "detections": [
                {
                    "track_id": 1,
                    "class": "person",
                    "confidence": 0.94,
                    "bbox": {
                        "x1": 125,
                        "y1": 195,
                        "x2": 185,
                        "y2": 448,
                    },
                    "velocity": {
                        "dx": 5.0,
                        "dy": -5.0,
                    },
                    "history": [{"x1": 120, "y1": 200, "x2": 180, "y2": 450}],
                },
                {
                    "track_id": 2,
                    "class": "person",
                    "confidence": 0.91,
                    "bbox": {
                        "x1": 405,
                        "y1": 175,
                        "x2": 485,
                        "y2": 465,
                    },
                    "velocity": {
                        "dx": 5.0,
                        "dy": -5.0,
                    },
                    "history": [{"x1": 400, "y1": 180, "x2": 480, "y2": 460}],
                },
            ],
            "tracking_enabled": True,
            "processing_time_ms": 35,
        },
    ],
    "result": {
        "total_tracks": 2,
        "total_frames": 2,
        "processing_time_ms": 67,
        "tracks": {
            "1": {
                "class": "person",
                "total_detections": 2,
                "avg_confidence": 0.93,
            },
            "2": {
                "class": "person",
                "total_detections": 2,
                "avg_confidence": 0.895,
            },
        },
    },
}


# =============================================================================
# Utility Functions
# =============================================================================

def get_example_output(plugin_type: str) -> Dict[str, Any]:
    """Get example output by plugin type.
    
    Args:
        plugin_type: Type of plugin ('ocr' or 'tracking')
    
    Returns:
        Example output dictionary
    
    Raises:
        ValueError: If plugin_type is not recognized
    """
    if plugin_type.lower() == "ocr":
        return OCR_EXAMPLE.copy()
    elif plugin_type.lower() == "tracking":
        return TRACKING_EXAMPLE.copy()
    else:
        raise ValueError(f"Unknown plugin type: {plugin_type}. Supported types: 'ocr', 'tracking'")


def get_example_output_for_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Get example output by job_id.
    
    Args:
        job_id: Job identifier
    
    Returns:
        Example output dictionary or None if not found
    """
    if job_id == OCR_EXAMPLE["job_id"]:
        return OCR_EXAMPLE.copy()
    elif job_id == TRACKING_EXAMPLE["job_id"]:
        return TRACKING_EXAMPLE.copy()
    return None

