"""Moderation Plugin - Content safety detection."""

import hashlib
import io
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

try:
    import numpy as np
    from PIL import Image

    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False


class Plugin:
    """Content moderation plugin for safety detection."""

    name = "moderation"
    version = "1.0.0"
    description = "Detect potentially unsafe or inappropriate content"

    def __init__(self):
        self.sensitivity = "medium"
        # In production, load a real model here
        self._model = None

    def metadata(self) -> Dict[str, Any]:
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
        """Analyze image for content safety."""
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
            logger.error(f"Moderation analysis failed: {e}")
            return {"safe": None, "error": str(e), "categories": [], "confidence": 0}

    def _analyze_content(
        self, img: Image.Image, categories: List[str], sensitivity: str
    ) -> Dict[str, Any]:
        """Analyze content for specified categories."""
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

        overall_confidence = sum(r["confidence"] for r in results) / len(results)

        return {"categories": results, "overall_confidence": overall_confidence}

    def _calculate_placeholder_score(self, arr: np.ndarray, category: str) -> float:
        """Calculate a placeholder safety score."""
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
                    (np.maximum(r, np.maximum(g, b)) - np.minimum(r, np.minimum(g, b)))
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
        """Get score threshold for given sensitivity."""
        thresholds = {"low": 0.8, "medium": 0.5, "high": 0.3}
        return thresholds.get(sensitivity, 0.5)

    def _get_recommendation(self, is_safe: bool, results: Dict) -> str:
        """Generate recommendation based on results."""
        if is_safe:
            return "Content appears safe for general viewing"

        flagged = [cat["category"] for cat in results["categories"] if cat["flagged"]]

        if flagged:
            return (
                f"Content flagged for: {', '.join(flagged)}. "
                f"Manual review recommended."
            )

        return "Content may require review"

    def _basic_analysis(self, image_bytes: bytes, options: Dict) -> Dict[str, Any]:
        """Basic analysis when dependencies unavailable."""
        return {
            "safe": None,
            "confidence": 0,
            "categories": [],
            "warning": "Full moderation requires PIL and numpy",
            "image_size_bytes": len(image_bytes),
        }

    def on_load(self):
        logger.info("Moderation plugin loaded (placeholder mode)")
        logger.warning(
            "Using heuristic analysis - replace with real ML model for production"
        )

    def on_unload(self):
        logger.info("Moderation plugin unloaded")
