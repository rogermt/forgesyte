"""OCR Plugin - Extract text from images using Tesseract."""

import io
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Try to import OCR dependencies
try:
    import pytesseract
    from PIL import Image

    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False
    logger.warning("pytesseract not installed - OCR will use fallback")


class Plugin:
    """OCR plugin for text extraction from images."""

    name = "ocr"
    version = "1.0.0"
    description = "Extract text from images using OCR"

    def __init__(self):
        self.supported_languages = ["eng", "fra", "deu", "spa", "ita"]

    def metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "inputs": ["image"],
            "outputs": ["text", "blocks", "confidence"],
            "permissions": [],
            "config_schema": {
                "language": {
                    "type": "string",
                    "default": "eng",
                    "enum": self.supported_languages,
                    "description": "OCR language",
                },
                "psm": {
                    "type": "integer",
                    "default": 3,
                    "description": "Page segmentation mode (0-13)",
                },
            },
        }

    def analyze(
        self, image_bytes: bytes, options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Extract text from an image."""
        options = options or {}

        if not HAS_TESSERACT:
            return self._fallback_analyze(image_bytes, options)

        try:
            # Load image
            img = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if necessary
            if img.mode not in ("L", "RGB"):
                img = img.convert("RGB")

            # Get OCR options
            lang = options.get("language", "eng")
            psm = options.get("psm", 3)

            # Configure tesseract
            config = f"--psm {psm}"

            # Extract text
            text = pytesseract.image_to_string(img, lang=lang, config=config)

            # Get detailed data with confidence
            data = pytesseract.image_to_data(
                img, lang=lang, config=config, output_type=pytesseract.Output.DICT
            )

            # Build blocks with positions
            blocks = []
            n_boxes = len(data["level"])
            for i in range(n_boxes):
                if int(data["conf"][i]) > 0:  # Filter low confidence
                    blocks.append(
                        {
                            "text": data["text"][i],
                            "confidence": float(data["conf"][i]),
                            "bbox": {
                                "x": data["left"][i],
                                "y": data["top"][i],
                                "width": data["width"][i],
                                "height": data["height"][i],
                            },
                            "level": data["level"][i],
                            "block_num": data["block_num"][i],
                            "line_num": data["line_num"][i],
                        }
                    )

            # Calculate average confidence
            confidences = [b["confidence"] for b in blocks if b["confidence"] > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            return {
                "text": text.strip(),
                "blocks": blocks,
                "confidence": avg_confidence,
                "language": lang,
                "image_size": {"width": img.width, "height": img.height},
            }

        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return {"error": str(e), "text": "", "blocks": [], "confidence": 0}

    def _fallback_analyze(self, image_bytes: bytes, options: Dict) -> Dict[str, Any]:
        """Fallback when tesseract is not available."""
        return {
            "text": "",
            "blocks": [],
            "confidence": 0,
            "warning": "Tesseract not installed. Install with: pip install pytesseract",
            "image_size_bytes": len(image_bytes),
        }

    def on_load(self):
        """Called when plugin is loaded."""
        if HAS_TESSERACT:
            try:
                version = pytesseract.get_tesseract_version()
                logger.info(f"OCR plugin loaded with Tesseract {version}")
            except Exception:
                logger.warning("Tesseract binary not found")
        else:
            logger.warning("OCR plugin loaded without Tesseract support")

    def on_unload(self):
        """Called when plugin is unloaded."""
        logger.info("OCR plugin unloaded")
