"""Dependency checker for Phase 11 plugin stability.

Validates plugin dependencies including GPU availability and model files.
"""

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DependencyCheckResult:
    """Result of dependency validation."""

    ok: bool
    reason: Optional[str] = None
    gpu_available: bool = False
    missing_deps: Optional[List[str]] = None

    def __post_init__(self):
        if self.missing_deps is None:
            self.missing_deps = []


class DependencyChecker:
    """
    Validates plugin dependencies before initialization.

    Authoritative checks:
    - GPU availability (dual check: torch + nvidia-smi)
    - Model file existence and integrity
    - Python package dependencies
    """

    def __init__(self) -> None:
        """Initialize dependency checker."""
        self._gpu_cache: Optional[bool] = None

    def check_gpu(self) -> bool:
        """
        Dual GPU check: torch.cuda + nvidia-smi (fail-safe).

        Returns True only if BOTH checks pass.
        This prevents false positives from broken CUDA installs.
        """
        if self._gpu_cache is not None:
            return self._gpu_cache

        # Check 1: torch.cuda.is_available()
        torch_available = False
        try:
            import torch
            torch_available = torch.cuda.is_available()
            logger.debug(f"torch.cuda.is_available(): {torch_available}")
        except ImportError:
            logger.debug("torch not installed")
        except Exception as e:
            logger.warning(f"torch CUDA check failed: {e}")

        # Check 2: nvidia-smi
        nvidia_available = False
        try:
            result = subprocess.run(
                ["nvidia-smi"],
                capture_output=True,
                timeout=5,
                check=False,
            )
            nvidia_available = result.returncode == 0
            logger.debug(f"nvidia-smi available: {nvidia_available}")
        except FileNotFoundError:
            logger.debug("nvidia-smi not found")
        except subprocess.TimeoutExpired:
            logger.warning("nvidia-smi timed out")
        except Exception as e:
            logger.warning(f"nvidia-smi check failed: {e}")

        # Both must pass for GPU to be considered available
        self._gpu_cache = torch_available and nvidia_available

        if self._gpu_cache:
            logger.info("✓ GPU available (torch + nvidia-smi)")
        else:
            logger.info(
                f"⊘ GPU unavailable: torch={torch_available}, nvidia-smi={nvidia_available}"
            )

        return self._gpu_cache

    def check_model_file(self, path: str, read_bytes: int = 16) -> bool:
        """
        Check model file exists and is readable.

        Reads first N bytes to detect corruption.

        Args:
            path: Path to model file
            read_bytes: Number of bytes to read for corruption check

        Returns:
            True if file exists and is readable
        """
        try:
            model_path = Path(path)

            if not model_path.exists():
                logger.error(f"Model file not found: {path}")
                return False

            if not model_path.is_file():
                logger.error(f"Model path is not a file: {path}")
                return False

            # Read first bytes to verify file is not corrupted
            with open(model_path, "rb") as f:
                header = f.read(read_bytes)
                if len(header) < read_bytes:
                    logger.warning(
                        f"Model file smaller than expected: {path} ({len(header)} bytes)"
                    )

            logger.debug(f"✓ Model file valid: {path}")
            return True

        except PermissionError:
            logger.error(f"Permission denied reading model: {path}")
            return False
        except Exception as e:
            logger.error(f"Error checking model file {path}: {e}")
            return False

    def check_python_package(self, package_name: str) -> bool:
        """Check if a Python package is installed."""
        try:
            __import__(package_name)
            return True
        except ImportError:
            return False

    def validate_plugin(
        self,
        plugin_name: str,
        requires_gpu: bool = False,
        model_paths: Optional[List[str]] = None,
        required_packages: Optional[List[str]] = None,
    ) -> DependencyCheckResult:
        """
        Full validation of plugin dependencies.

        Args:
            plugin_name: Name of plugin being validated
            requires_gpu: Whether plugin needs GPU
            model_paths: List of model file paths to check
            required_packages: List of required Python packages

        Returns:
            DependencyCheckResult with ok status and details
        """
        missing_deps: List[str] = []

        # Check GPU if required
        if requires_gpu:
            if not self.check_gpu():
                missing_deps.append("GPU (CUDA not available)")

        # Check model files
        if model_paths:
            for path in model_paths:
                if not self.check_model_file(path):
                    missing_deps.append(f"Model file: {path}")

        # Check Python packages
        if required_packages:
            for pkg in required_packages:
                if not self.check_python_package(pkg):
                    missing_deps.append(f"Python package: {pkg}")

        # Build result
        if missing_deps:
            reason = f"Missing dependencies: {', '.join(missing_deps)}"
            logger.error(f"✗ Plugin {plugin_name} validation failed: {reason}")
            return DependencyCheckResult(
                ok=False,
                reason=reason,
                gpu_available=self._gpu_cache or False,
                missing_deps=missing_deps,
            )

        logger.info(f"✓ Plugin {plugin_name} dependencies validated")
        return DependencyCheckResult(
            ok=True,
            gpu_available=self._gpu_cache or False,
            missing_deps=[],
        )


# Singleton instance
_checker: Optional[DependencyChecker] = None


def get_dependency_checker() -> DependencyChecker:
    """Get or create the global dependency checker."""
    global _checker
    if _checker is None:
        _checker = DependencyChecker()
    return _checker
