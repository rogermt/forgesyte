"""Motion Detector Plugin - Detect motion between frames."""

import io
import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import numpy as np
    from PIL import Image

    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False


class Plugin:
    """Motion detection plugin for live camera feeds."""

    name = "motion_detector"
    version = "1.0.0"
    description = "Detect motion between consecutive frames"

    def __init__(self) -> None:
        self._previous_frame: Optional[np.ndarray] = None
        self._frame_count = 0
        self._last_motion_time = 0
        self._motion_history: List[Dict[str, Any]] = []

    def metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "inputs": ["image"],
            "outputs": ["motion_detected", "motion_score", "regions"],
            "permissions": [],
            "config_schema": {
                "threshold": {
                    "type": "float",
                    "default": 25.0,
                    "min": 1.0,
                    "max": 100.0,
                    "description": "Motion detection threshold",
                },
                "min_area": {
                    "type": "float",
                    "default": 0.01,
                    "min": 0.001,
                    "max": 0.5,
                    "description": "Minimum motion area (fraction of frame)",
                },
                "blur_size": {
                    "type": "integer",
                    "default": 5,
                    "description": "Gaussian blur kernel size",
                },
                "reset_baseline": {
                    "type": "boolean",
                    "default": False,
                    "description": "Reset baseline frame",
                },
            },
        }

    def analyze(
        self, image_bytes: bytes, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Detect motion in the current frame."""
        options = options or {}

        if not HAS_DEPS:
            return {
                "motion_detected": False,
                "error": "PIL and numpy required",
                "motion_score": 0,
            }

        try:
            # Load image
            img = Image.open(io.BytesIO(image_bytes)).convert("L")  # Grayscale
            current_frame = np.array(img, dtype=np.float32)

            # Get options
            threshold = options.get("threshold", 25.0)
            min_area = options.get("min_area", 0.01)
            blur_size = options.get("blur_size", 5)
            reset_baseline = options.get("reset_baseline", False)

            # Reset baseline if requested
            if reset_baseline:
                self._previous_frame = None

            self._frame_count += 1

            # Apply Gaussian blur
            if blur_size > 1:
                current_frame = self._gaussian_blur(current_frame, blur_size)

            # First frame - no comparison possible
            if self._previous_frame is None:
                self._previous_frame = current_frame
                return {
                    "motion_detected": False,
                    "motion_score": 0.0,
                    "regions": [],
                    "frame_number": self._frame_count,
                    "message": "Baseline frame captured",
                }

            # Ensure same size
            if current_frame.shape != self._previous_frame.shape:
                self._previous_frame = current_frame
                return {
                    "motion_detected": False,
                    "motion_score": 0.0,
                    "regions": [],
                    "message": "Frame size changed, baseline reset",
                }

            # Calculate absolute difference
            diff = np.abs(current_frame - self._previous_frame)

            # Threshold the difference
            motion_mask = diff > threshold

            # Calculate motion score
            motion_pixels = np.sum(motion_mask)
            total_pixels = motion_mask.size
            motion_score = motion_pixels / total_pixels

            # Detect if motion exceeds minimum area
            motion_detected = motion_score >= min_area

            # Find motion regions (simplified connected components)
            regions = self._find_motion_regions(motion_mask) if motion_detected else []

            # Update baseline (adaptive)
            alpha = 0.1  # Learning rate
            self._previous_frame = (
                alpha * current_frame + (1 - alpha) * self._previous_frame
            )

            # Record motion event
            if motion_detected:
                self._last_motion_time = time.time()
                self._motion_history.append(
                    {
                        "time": self._last_motion_time,
                        "score": motion_score,
                        "frame": self._frame_count,
                    }
                )
                # Keep only recent history
                self._motion_history = self._motion_history[-100:]

            return {
                "motion_detected": motion_detected,
                "motion_score": round(motion_score * 100, 2),  # Percentage
                "regions": regions,
                "frame_number": self._frame_count,
                "threshold": threshold,
                "image_size": {"width": img.width, "height": img.height},
                "time_since_last_motion": (
                    round(time.time() - self._last_motion_time, 1)
                    if self._last_motion_time > 0
                    else None
                ),
                "recent_motion_events": len(
                    [e for e in self._motion_history if time.time() - e["time"] < 60]
                ),
            }

        except Exception as e:
            logger.error(f"Motion detection failed: {e}")
            return {"motion_detected": False, "error": str(e), "motion_score": 0}

    def _gaussian_blur(self, img: np.ndarray, size: int) -> np.ndarray:
        """Simple Gaussian blur implementation."""
        # Create Gaussian kernel
        x = np.arange(size) - size // 2
        kernel = np.exp(-(x**2) / (2 * (size / 4) ** 2))
        kernel = kernel / kernel.sum()

        # Apply separable filter
        result = np.apply_along_axis(
            lambda m: np.convolve(m, kernel, mode="same"), 0, img
        )
        result = np.apply_along_axis(
            lambda m: np.convolve(m, kernel, mode="same"), 1, result
        )

        return result

    def _find_motion_regions(
        self, motion_mask: np.ndarray, min_size: int = 100
    ) -> List[Dict[str, Any]]:
        """Find bounding boxes of motion regions."""
        regions: List[Dict[str, Any]] = []

        # Find rows and columns with motion
        rows = np.any(motion_mask, axis=1)
        cols = np.any(motion_mask, axis=0)

        if not np.any(rows) or not np.any(cols):
            return regions

        # Get bounding box of all motion
        row_indices = np.where(rows)[0]
        col_indices = np.where(cols)[0]

        y_min, y_max = row_indices[0], row_indices[-1]
        x_min, x_max = col_indices[0], col_indices[-1]

        # Calculate area
        area = (x_max - x_min) * (y_max - y_min)

        if area >= min_size:
            regions.append(
                {
                    "bbox": {
                        "x": int(x_min),
                        "y": int(y_min),
                        "width": int(x_max - x_min),
                        "height": int(y_max - y_min),
                    },
                    "area": int(area),
                    "center": {
                        "x": int((x_min + x_max) / 2),
                        "y": int((y_min + y_max) / 2),
                    },
                }
            )

        return regions

    def reset(self) -> None:
        """Reset detector state."""
        self._previous_frame = None
        self._frame_count = 0
        self._last_motion_time = 0
        self._motion_history = []

    def on_load(self) -> None:
        logger.info("Motion detector plugin loaded")

    def on_unload(self) -> None:
        self.reset()
        logger.info("Motion detector plugin unloaded")
