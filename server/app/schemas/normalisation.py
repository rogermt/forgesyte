"""Canonical normalisation layer for all plugin outputs.

Transforms plugin-specific outputs into a unified schema.
"""

from typing import Any, TypedDict


class Box(TypedDict):
    """Bounding box in canonical form."""

    x1: float
    y1: float
    x2: float
    y2: float


class Frame(TypedDict):
    """Single frame in canonical normalised form."""

    frame_index: int
    boxes: list[Box]
    scores: list[float]
    labels: list[str]


class NormalisedOutput(TypedDict):
    """Canonical normalised output."""

    frames: list[Frame]


def normalise_output(raw: dict[str, Any]) -> NormalisedOutput:
    """
    Transform plugin-specific output to canonical schema.

    Input format (plugin output):
        {
            "boxes": [[x1, y1, x2, y2], ...],
            "scores": [float, ...],
            "labels": [str, ...]
        }

    Output format (canonical):
        {
            "frames": [
                {
                    "frame_index": int,
                    "boxes": [
                        {"x1": float, "y1": float, "x2": float, "y2": float}, ...
                    ],
                    "scores": [float, ...],
                    "labels": [str, ...]
                }
            ]
        }

    Args:
        raw: Plugin-specific output dict

    Returns:
        Normalised output in canonical schema

    Raises:
        ValueError: If validation fails
    """
    # Validate required fields present
    if "boxes" not in raw:
        raise ValueError("Missing required field: 'boxes'")
    if "scores" not in raw:
        raise ValueError("Missing required field: 'scores'")
    if "labels" not in raw:
        raise ValueError("Missing required field: 'labels'")

    boxes_raw = raw["boxes"]
    scores = raw["scores"]
    labels = raw["labels"]

    # Validate not empty
    if not boxes_raw or not scores or not labels:
        raise ValueError("boxes, scores, and labels must not be empty")

    # Validate lengths match
    if not (len(boxes_raw) == len(scores) == len(labels)):
        raise ValueError(
            f"Length mismatch: boxes={len(boxes_raw)}, "
            f"scores={len(scores)}, labels={len(labels)}"
        )

    # Transform boxes from [x1, y1, x2, y2] to {x1, y1, x2, y2}
    boxes: list[Box] = []
    for box in boxes_raw:
        if len(box) != 4:
            raise ValueError(
                f"Each box must have 4 coordinates [x1, y1, x2, y2], got {len(box)}"
            )
        boxes.append(
            Box(x1=float(box[0]), y1=float(box[1]), x2=float(box[2]), y2=float(box[3]))
        )

    # Ensure scores are floats and in [0, 1]
    scores_norm = []
    for score in scores:
        s = float(score)
        if not (0 <= s <= 1):
            raise ValueError(f"Score must be in [0, 1], got {s}")
        scores_norm.append(s)

    # Ensure labels are strings
    labels_norm = [str(label) for label in labels]

    # Create single frame (multi-frame support in later step)
    frame: Frame = Frame(
        frame_index=0, boxes=boxes, scores=scores_norm, labels=labels_norm
    )

    return NormalisedOutput(frames=[frame])
