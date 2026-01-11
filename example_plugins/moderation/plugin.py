"""Moderation Plugin - Content safety detection.

This plugin detects potentially unsafe or inappropriate content in images
using configurable sensitivity levels and category detection. Provides detailed
analysis with confidence scores and recommendations for content review.
"""

from typing import Dict, Any, List, Optional, cast
import io
import logging
import hashlib

logger = logging.getLogger(__name__)

try:
    from PIL import Image  # type: ignore[import-not-found]
    import numpy as np  # type: ignore[import-not-found]

    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False


class Plugin:
    """Content moderation plugin for safety detection.

    Analyzes images for unsafe or inappropriate content across multiple
    categories (NSFW, violence, hate speech) with configurable sensitivity.
    """

    name: str = "moderation"
    version: str = "1.0.0"
    description: str = "Detect potentially unsafe or inappropriate content"

    def __init__(self) -> None:
        """Initialize the moderation plugin.

        Sets default sensitivity and initializes ML model reference.
        """
        self.sensitivity: str = "medium"
        # In production, load a real model here
        self._model: Optional[Any] = None

    def metadata(self) -> Dict[str, Any]:
        """Return plugin metadata.

        Returns:
            Dictionary with plugin info, inputs/outputs, permissions, and
            configuration schema for sensitivity and category selection.
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "inputs": ["image"],
            "outputs": ["safe", "categories", "confidence"],
            "permissions": ["moderation"],
            "config_schema": {
                "sensitivity": {
                    "type": "string",
                    "default": "medium",
                    "enum": ["low", "medium", "high"],
                    "description": "Detection sensitivity level",
                },
                "categories": {
                    "type": "array",
                    "default": ["nsfw", "violence", "hate"],
                    "description": "Categories to check",
                },
            },
        }

    def analyze(
        self, image_bytes: bytes, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze image for content safety.

        Detects unsafe or inappropriate content across multiple categories
        with configurable sensitivity levels and category selection.

        Args:
            image_bytes: Raw image data (PNG, JPEG, etc).
            options: Configuration with sensitivity level and categories to check.

        Returns:
            Dictionary with safety verdict, confidence, category scores, and
            image metadata for review.

        Raises:
            None - catches and logs all exceptions, returning error dict.
        """
        options = options or {}

        if not HAS_DEPS:
            return self._basic_analysis(image_bytes, options)

        try:
            img = Image.open(io.BytesIO(image_bytes))

            # Get configuration
            sensitivity = options.get("sensitivity", "medium")
            categories = options.get("categories", ["nsfw", "violence", "hate"])

            # Perform analysis
            # NOTE: This is a placeholder - in production, use a real model
            # like transformers pipeline, CLIP, or a dedicated moderation API
            results = self._analyze_content(img, categories, sensitivity)

            # Calculate overall safety
            is_safe = all(
                cat["score"] < self._get_threshold(sensitivity)
                for cat in results["categories"]
            )

            # Generate content hash for caching/tracking
            content_hash = hashlib.md5(image_bytes).hexdigest()

            return {
                "safe": is_safe,
                "confidence": results["overall_confidence"],
                "categories": results["categories"],
                "sensitivity": sensitivity,
                "content_hash": content_hash,
                "image_info": {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                },
                "recommendation": self._get_recommendation(is_safe, results),
            }

        except Exception as e:
            logger.error(
                "Moderation analysis failed",
                extra={"error": str(e)},
            )
            return {"safe": None, "error": str(e), "categories": [], "confidence": 0}

    def _analyze_content(
        self, img: Image.Image, categories: List[str], sensitivity: str
    ) -> Dict[str, Any]:
        """Analyze content for specified categories.

        Runs analysis on each category and computes overall confidence score.

        Args:
            img: PIL Image object to analyze.
            categories: List of categories to check (nsfw, violence, hate).
            sensitivity: Sensitivity level (low, medium, high).

        Returns:
            Dictionary with list of category results and overall confidence.
        """
        # Placeholder analysis - replace with real model inference
        # This uses basic heuristics as a demonstration

        arr = np.array(img.convert("RGB"))

        results = []
        for category in categories:
            # Placeholder scores based on image statistics
            # In production, use actual ML models
            score = self._calculate_placeholder_score(arr, category)

            results.append(
                {
                    "category": category,
                    "score": score,
                    "flagged": score > self._get_threshold(sensitivity),
                    "confidence": 0.5
                    + (0.5 - abs(score - 0.5)),  # Higher near extremes
                }
            )

        confidence_sum: float = sum(cast(float, r["confidence"]) for r in results)
        overall_confidence = confidence_sum / len(results) if results else 0.0

        return {"categories": results, "overall_confidence": overall_confidence}

    def _calculate_placeholder_score(self, arr: np.ndarray, category: str) -> float:
        """Calculate a placeholder safety score.

        Uses basic heuristics (color distribution, skin detection) as a
        placeholder. Replace with real ML model inference in production.

        Args:
            arr: Numpy array of image pixels (H, W, 3).
            category: Category to score (nsfw, violence, hate).

        Returns:
            Safety score between 0.0 and 1.0 (higher = less safe).
        """
        # This is NOT a real moderation system
        # Replace with actual ML model inference

        # Basic skin tone detection heuristic (very rough)
        if category == "nsfw":
            # Check for high proportion of skin-like colors
            r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
            skin_like = (
                (r > 95)
                & (g > 40)
                & (b > 20)
                & (
                    np.maximum(r, np.maximum(g, b)) - np.minimum(r, np.minimum(g, b))
                    > 15
                )
                & (abs(r.astype(int) - g.astype(int)) > 15)
                & (r > g)
                & (r > b)
            )
            skin_ratio = np.mean(skin_like)
            # This is a very rough heuristic - NOT reliable
            return min(skin_ratio * 2, 1.0) * 0.3  # Scale down to avoid false positives

        elif category == "violence":
            # Check for high red content
            red_ratio = np.mean(arr[:, :, 0] > 150)
            return red_ratio * 0.2

        elif category == "hate":
            # Would need symbol/text detection
            return 0.05

        return 0.1

    def _get_threshold(self, sensitivity: str) -> float:
        """Get score threshold for given sensitivity.

        Args:
            sensitivity: Sensitivity level (low, medium, high).

        Returns:
            Score threshold where higher scores = unsafe.
        """
        thresholds = {"low": 0.8, "medium": 0.5, "high": 0.3}
        return thresholds.get(sensitivity, 0.5)

    def _get_recommendation(self, is_safe: bool, results: Dict[str, Any]) -> str:
        """Generate recommendation based on results.

        Creates actionable recommendation for content reviewers.

        Args:
            is_safe: Whether content passed safety checks.
            results: Analysis results with category data.

        Returns:
            Recommendation string for reviewer.
        """
        if is_safe:
            return "Content appears safe for general viewing"

        flagged = [cat["category"] for cat in results["categories"] if cat["flagged"]]

        if flagged:
            categories_str = ", ".join(flagged)
            return f"Content flagged for: {categories_str}. Manual review recommended."

        return "Content may require review"

    def _basic_analysis(
        self, image_bytes: bytes, options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Basic analysis when dependencies unavailable.

        Returns placeholder results when PIL/numpy not installed.

        Args:
            image_bytes: Raw image data.
            options: Configuration options (unused in fallback).

        Returns:
            Dictionary with warning and basic image info.
        """
        return {
            "safe": None,
            "confidence": 0,
            "categories": [],
            "warning": "Full moderation requires PIL and numpy",
            "image_size_bytes": len(image_bytes),
        }

    def on_load(self) -> None:
        """Called when plugin is loaded.

        Logs initialization and warns about placeholder implementation.
        """
        logger.info("Moderation plugin loaded")
        logger.warning(
            "Using heuristic analysis - replace with real ML model for production",
            extra={"plugin_name": "moderation"},
        )

    def on_unload(self) -> None:
        """Called when plugin is unloaded.

        Logs plugin shutdown.
        """
        logger.info("Moderation plugin unloaded")
