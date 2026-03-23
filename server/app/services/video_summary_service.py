"""Video summary extraction service.

Discussion #354: Pre-compute summary for /v1/jobs hot path.
Discussion #357: Handle YOLO tracked_objects format in all frame structures.
"""

from typing import List, Optional


def _extract_class_name(det: dict) -> Optional[str]:
    """Extract class name from detection, handling multiple formats.

    Handles:
    - "class": "player" (string format)
    - "label": "player" (alternative key)
    - "class_id": 0 (integer format, returns "class_0")

    Args:
        det: Detection dict (or any value, returns None if not dict)

    Returns:
        Class name string, or None if not found
    """
    # Defensive: det must be a dict
    if not isinstance(det, dict):
        return None

    # Priority 1: "class" key (string)
    if "class" in det and isinstance(det["class"], str):
        return det["class"]

    # Priority 2: "label" key (alternative)
    if "label" in det and isinstance(det["label"], str):
        return det["label"]

    # Priority 3: "class_id" key (integer, convert to "class_N")
    if "class_id" in det:
        return f"class_{det['class_id']}"

    return None


def extract_detections(frame: dict) -> List[dict]:
    """Extract detections list from frame, handling multiple formats.

    Handles:
    - detections: [...] (standard list format)
    - detections: {"tracked_objects": [...]} (YOLO tracker format)

    Args:
        frame: Frame dict containing detections

    Returns:
        List of detection dicts, or empty list if not found/invalid
    """
    detections = frame.get("detections", [])
    if isinstance(detections, list):
        return detections
    if isinstance(detections, dict):
        # YOLO tracker format: {"tracked_objects": [...]}
        return detections.get("tracked_objects", [])
    return []


def derive_video_summary(results: dict) -> dict:
    """Derive summary metadata from video job results.

    Handles multiple result structures:
    1. Single-tool video: {"frames": [{"detections": [...]}]}
    2. Multi-tool raw: {"tools": {"tool_name": {"frames": [...]}}}
    3. Multi-tool merged: {"frames": [{"frame_idx": 0, "tool_name": {...}}]}

    Discussion #354: Extract lightweight metadata from video results
    for pre-computed storage to avoid loading full artifacts on hot path.

    Discussion #357: Support YOLO tracked_objects format in all structures.

    Args:
        results: Full video results dict

    Returns:
        Summary dict with frame_count, detection_count, classes
    """
    frame_count = 0
    detection_count = 0
    classes: List[str] = []

    # Known frame keys that are NOT tool payloads (from _merge_video_frames)
    KNOWN_FRAME_KEYS = {"frame_idx", "frame_index", "timestamp", "detections"}

    # Handle frames array (most common structure)
    frames = results.get("frames", [])
    if isinstance(frames, list):
        frame_count = len(frames)

        classes_set: set = set()
        for frame in frames:
            # Discussion #353: Defensive check - frame must be a dict
            if not isinstance(frame, dict):
                continue

            # Check for top-level detections (single-tool format)
            detections = extract_detections(frame)
            detection_count += len(detections)
            for det in detections:
                class_name = _extract_class_name(det)
                if class_name:
                    classes_set.add(class_name)

            # Discussion #357: Handle video_multi merged frames structure
            # Each frame may have tool-specific keys (e.g., "player_tracker")
            for key in frame:
                if key not in KNOWN_FRAME_KEYS:
                    # This is a tool payload
                    tool_payload = frame[key]
                    if isinstance(tool_payload, dict):
                        # Use extract_detections to handle tracked_objects format
                        tool_dets = extract_detections(tool_payload)
                        detection_count += len(tool_dets)
                        for det in tool_dets:
                            class_name = _extract_class_name(det)
                            if class_name:
                                classes_set.add(class_name)

        classes = sorted(classes_set)

    # Handle tools structure (legacy multi-tool video jobs)
    tools = results.get("tools", {})
    if isinstance(tools, dict):
        tool_detections = 0
        tool_classes: set = set()

        for _tool_name, tool_results in tools.items():
            # Defensive: skip if tool_results is not a dict (malformed data)
            if not isinstance(tool_results, dict):
                continue
            tool_frames = tool_results.get("frames", [])
            # Defensive: skip if tool_frames is not a list
            if not isinstance(tool_frames, list):
                continue
            for frame in tool_frames:
                # Discussion #353: Defensive check - frame must be a dict
                if not isinstance(frame, dict):
                    continue
                detections = extract_detections(frame)
                tool_detections += len(detections)
                for det in detections:
                    class_name = _extract_class_name(det)
                    if class_name:
                        tool_classes.add(class_name)

        # Add to existing counts
        detection_count += tool_detections
        classes = sorted(set(classes) | tool_classes)

    return {
        "frame_count": frame_count,
        "detection_count": detection_count,
        "classes": classes,
    }
