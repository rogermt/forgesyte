"""
Device selection and validation service.

Handles device parameter validation, GPU availability detection, and fallback logic.
"""

import logging
from typing import Literal

logger = logging.getLogger(__name__)


Device = Literal["cpu", "gpu"]


def validate_device(device: str) -> bool:
    """Validate device is 'cpu' or 'gpu' (case-insensitive).

    Args:
        device: Device string to validate.

    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(device, str):
        return False
    return device.lower() in ["cpu", "gpu"]


def get_gpu_available() -> bool:
    """Check if GPU is available on this system.

    Returns:
        True if CUDA/GPU is available, False otherwise.
    """
    try:
        import torch

        available = torch.cuda.is_available()
        if available:
            logger.info(
                "GPU detected",
                extra={"device_count": torch.cuda.device_count()},
            )
        return available
    except ImportError:
        logger.debug("torch not available, GPU detection skipped")
        return False
    except Exception as e:
        logger.warning(
            "Error detecting GPU availability",
            extra={"error": str(e)},
        )
        return False


def resolve_device(
    requested: str, gpu_available: bool | None = None
) -> Device:
    """Resolve requested device to actual device with fallback.

    If GPU is requested but not available, falls back to CPU.

    Args:
        requested: Requested device ("cpu" or "gpu").
        gpu_available: Whether GPU is available. If None, will detect.

    Returns:
        Actual device to use ("cpu" or "gpu").

    Raises:
        ValueError: If requested device is invalid.
    """
    if not validate_device(requested):
        raise ValueError(f"Invalid device: {requested}. Must be 'cpu' or 'gpu'.")

    if gpu_available is None:
        gpu_available = get_gpu_available()

    requested_lower = requested.lower()

    if requested_lower == "gpu":
        if not gpu_available:
            logger.warning(
                "GPU requested but not available, falling back to CPU",
                extra={"requested": requested_lower},
            )
            return "cpu"
        return "gpu"

    return "cpu"
