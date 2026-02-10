"""TEST-CHANGE: Multi-plugin output normalisation — OCR/YOLO compatibility.

Ensures OCR output bypasses YOLO-specific normalisation logic,
while YOLO plugins still receive strict schema enforcement.
"""

from app.schemas.normalisation import normalise_output


def test_ocr_output_bypasses_yolo_schema():
    """OCR output must passthrough without YOLO schema enforcement."""
    ocr_output = {"text": "hello world", "confidence": 0.99, "blocks": []}

    # OCR output should be passed through as-is
    # (normalisation layer routes based on plugin type)
    result = normalise_output(ocr_output, plugin_name="ocr")

    # OCR output should be returned unchanged
    assert result == ocr_output, "OCR output must bypass normalisation"
    assert "text" in result
    assert "confidence" in result


def test_yolo_output_normalises_correctly():
    """YOLO plugins must receive strict detections schema."""
    yolo_output = {
        "detections": [
            {"xyxy": [100, 200, 150, 250], "confidence": 0.95, "class_name": "player"}
        ]
    }

    result = normalise_output(yolo_output, plugin_name="forgesyte-yolo-tracker")

    # YOLO output should be normalised into frames[] structure
    assert "frames" in result, "YOLO output must be normalised with frames[] structure"
    assert isinstance(result["frames"], list)
    assert len(result["frames"]) == 1
    assert "boxes" in result["frames"][0]
