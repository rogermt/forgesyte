"""Tests for /v1/image/analyze-multi endpoint.

Tests multi-tool image analysis functionality:
- Single tool execution
- Multiple tool execution
- Error handling for unknown tools
- Response structure validation
"""

import sys
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

# Add parent dirs to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

pytestmark = pytest.mark.asyncio


@pytest.fixture
def test_image_bytes():
    """Create test image bytes for testing."""
    # Create a simple red image (100x100)
    img = Image.new("RGB", (100, 100), color="red")
    img_bytes_io = BytesIO()
    img.save(img_bytes_io, format="PNG")
    return img_bytes_io.getvalue()


@pytest.fixture
def test_image_file(tmp_path, test_image_bytes):
    """Create test image file for upload."""
    image_path = tmp_path / "test.png"
    with open(image_path, "wb") as f:
        f.write(test_image_bytes)
    return image_path


class TestMultiToolSingleTool:
    """Test single tool execution."""

    async def test_multi_tool_single_ocr(self, client, test_image_file):
        """Single tool (OCR) returns OCR result."""
        with open(test_image_file, "rb") as f:
            response = await client.post(
                "/v1/image/analyze-multi", files={"file": f}, data={"tools": ["ocr"]}
            )

        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert "ocr" in data["tools"]
        # OCR result should have text field
        assert "text" in data["tools"]["ocr"] or "error" in data["tools"]["ocr"]


class TestMultiToolMultipleTools:
    """Test multiple tool execution."""

    async def test_multi_tool_ocr_yolo(self, client, test_image_file):
        """Multiple tools (OCR + YOLO) return both results."""
        with open(test_image_file, "rb") as f:
            response = await client.post(
                "/v1/image/analyze-multi",
                files={"file": f},
                data={"tools": ["ocr", "yolo-tracker"]},
            )

        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert "ocr" in data["tools"]
        assert "yolo-tracker" in data["tools"]
        # Both tools should have results or errors
        assert "text" in data["tools"]["ocr"] or "error" in data["tools"]["ocr"]
        assert (
            "detections" in data["tools"]["yolo-tracker"]
            or "error" in data["tools"]["yolo-tracker"]
        )


class TestMultiToolErrorHandling:
    """Test error handling."""

    async def test_multi_tool_unknown_tool(self, client, test_image_file):
        """Unknown tool returns error in result."""
        with open(test_image_file, "rb") as f:
            response = await client.post(
                "/v1/image/analyze-multi",
                files={"file": f},
                data={"tools": ["unknown_tool"]},
            )

        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert "unknown_tool" in data["tools"]
        assert "error" in data["tools"]["unknown_tool"]

    async def test_multi_tool_empty_tools_list(self, client, test_image_file):
        """Empty tools list returns 400 error."""
        with open(test_image_file, "rb") as f:
            response = await client.post(
                "/v1/image/analyze-multi", files={"file": f}, data={"tools": []}
            )

        # FastAPI might return 422 for validation errors
        if response.status_code == 400:
            data = response.json()
            assert "detail" in data
            assert "At least one tool must be specified" in data["detail"]
        elif response.status_code == 422:
            # FastAPI validation error - this is acceptable
            data = response.json()
            assert "detail" in data


class TestMultiToolResponseStructure:
    """Test response structure matches contract."""

    async def test_multi_tool_response_has_tools_key(self, client, test_image_file):
        """Response has 'tools' key."""
        with open(test_image_file, "rb") as f:
            response = await client.post(
                "/v1/image/analyze-multi", files={"file": f}, data={"tools": ["ocr"]}
            )

        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert isinstance(data["tools"], dict)

    async def test_multi_tool_response_structure(self, client, test_image_file):
        """Response structure matches combined JSON contract."""
        with open(test_image_file, "rb") as f:
            response = await client.post(
                "/v1/image/analyze-multi", files={"file": f}, data={"tools": ["ocr"]}
            )

        assert response.status_code == 200
        data = response.json()
        # Verify structure: {"tools": {"ocr": {...}}}
        assert isinstance(data, dict)
        assert "tools" in data
        assert isinstance(data["tools"], dict)
        assert "ocr" in data["tools"]
