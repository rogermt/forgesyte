"""TEST-CHANGE: Tests for manifest validation model (Phase 12).

Validates PluginManifest Pydantic model enforces:
- Allowed plugin types
- Tool id validation
- Type normalization
"""

import pytest
from pydantic import ValidationError

from app.models_manifest import ALLOWED_PLUGIN_TYPES, ManifestTool, PluginManifest


class TestPluginManifest:
    """Tests for PluginManifest validation."""

    def test_valid_yolo_manifest(self) -> None:
        m = PluginManifest(
            name="tracker",
            version="1.0.0",
            type="yolo",
            tools=[ManifestTool(id="detect", title="Detect")],
        )
        assert m.type == "yolo"
        assert m.name == "tracker"

    def test_valid_ocr_manifest(self) -> None:
        m = PluginManifest(
            name="text-extractor",
            type="ocr",
            tools=[ManifestTool(id="extract_text")],
        )
        assert m.type == "ocr"

    def test_valid_custom_manifest(self) -> None:
        m = PluginManifest(
            name="my-plugin",
            type="custom",
            tools=[],
        )
        assert m.type == "custom"

    def test_default_type_is_custom(self) -> None:
        m = PluginManifest(name="test")
        assert m.type == "custom"

    def test_invalid_type_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Invalid plugin type"):
            PluginManifest(name="bad", type="unknown")

    def test_type_normalized_to_lowercase(self) -> None:
        m = PluginManifest(name="test", type="YOLO")
        assert m.type == "yolo"

    def test_type_stripped(self) -> None:
        m = PluginManifest(name="test", type="  ocr  ")
        assert m.type == "ocr"

    def test_extra_fields_allowed(self) -> None:
        m = PluginManifest(
            name="test",
            author="Roger",
            license="MIT",
            entrypoint="my.plugin",
        )
        assert m.name == "test"

    def test_allowed_plugin_types_set(self) -> None:
        assert ALLOWED_PLUGIN_TYPES == {"yolo", "ocr", "custom"}


class TestManifestTool:
    """Tests for ManifestTool validation."""

    def test_valid_tool(self) -> None:
        t = ManifestTool(id="detect", title="Detect", description="Detect objects")
        assert t.id == "detect"

    def test_empty_id_rejected(self) -> None:
        with pytest.raises(ValidationError, match="non-empty"):
            ManifestTool(id="")

    def test_whitespace_id_rejected(self) -> None:
        with pytest.raises(ValidationError, match="non-empty"):
            ManifestTool(id="   ")

    def test_dict_inputs_accepted(self) -> None:
        t = ManifestTool(
            id="analyze",
            inputs={"image_base64": "string"},
            outputs={"text": "string"},
        )
        assert isinstance(t.inputs, dict)

    def test_list_inputs_accepted(self) -> None:
        t = ManifestTool(id="detect", inputs=["image"], outputs=["json"])
        assert isinstance(t.inputs, list)


class TestNormalisationPluginType:
    """Tests that normalise_output routes correctly using plugin_type."""

    def test_ocr_bypasses_with_plugin_type(self) -> None:
        from app.schemas.normalisation import normalise_output

        ocr_output = {"text": "hello", "confidence": 0.99}
        result = normalise_output(ocr_output, plugin_type="ocr")
        assert result == ocr_output

    def test_custom_bypasses_with_plugin_type(self) -> None:
        from app.schemas.normalisation import normalise_output

        custom_output = {"result": "ok"}
        result = normalise_output(custom_output, plugin_type="custom")
        assert result == custom_output

    def test_yolo_normalises_with_plugin_type(self) -> None:
        from app.schemas.normalisation import normalise_output

        yolo_output = {
            "detections": [
                {
                    "xyxy": [100, 200, 150, 250],
                    "confidence": 0.95,
                    "class_name": "player",
                }
            ]
        }
        result = normalise_output(yolo_output, plugin_type="yolo")
        assert "frames" in result

    def test_plugin_name_fallback_still_works(self) -> None:
        from app.schemas.normalisation import normalise_output

        ocr_output = {"text": "hello"}
        result = normalise_output(ocr_output, plugin_name="ocr")
        assert result == ocr_output
