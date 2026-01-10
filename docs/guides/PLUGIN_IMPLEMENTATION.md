# Plugin Implementation Guide

This guide explains how to create ForgeSyte plugins that are automatically exposed as MCP tools.

---

## Overview

A ForgeSyte plugin is a Python class that:

1. Inherits from `Plugin` base class
2. Implements a `metadata()` method describing the plugin for MCP
3. Implements an `execute()` method containing the actual logic
4. Is automatically registered and exposed to MCP clients

Once registered, your plugin is automatically available to Gemini-CLI and other MCP clients without additional configuration.

---

## Plugin Structure

### Basic Template

```python
from server.app.plugins import Plugin
import logging

logger = logging.getLogger(__name__)


class MyPlugin(Plugin):
    """Description of your plugin."""

    name = "my-plugin"

    def metadata(self) -> dict:
        """Return plugin metadata for MCP discovery.
        
        This method tells MCP clients about your plugin's capabilities.
        """
        return {
            "name": "my-plugin",
            "title": "My Plugin",
            "description": "Brief description of what this plugin does",
            "inputs": ["image"],
            "outputs": ["json"],
            "version": "0.1.0",
            "permissions": []
        }

    async def execute(self, **kwargs) -> dict:
        """Execute the plugin logic.
        
        Args:
            **kwargs: Parameters from the job request
            
        Returns:
            Dictionary with results to return to the client
        """
        # Your implementation here
        return {"result": "..."}
```

---

## Detailed Example: OCR Plugin

Here's a complete example of an OCR plugin:

```python
"""OCR Plugin - Extract text from images using optical character recognition."""

from server.app.plugins import Plugin
import logging
from pathlib import Path
from typing import Optional
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


class OCRPlugin(Plugin):
    """Extract text from images using Tesseract OCR."""

    name = "ocr"

    def metadata(self) -> dict:
        """Return OCR plugin metadata for MCP discovery."""
        return {
            "name": "ocr",
            "title": "OCR (Optical Character Recognition)",
            "description": "Extracts text from images using Tesseract OCR",
            "inputs": ["image"],
            "outputs": ["text"],
            "version": "0.1.0",
            "permissions": ["file:read"]
        }

    async def execute(self, image_path: str, language: str = "eng") -> dict:
        """Extract text from an image.
        
        Args:
            image_path: Path to the image file
            language: Tesseract language code (default: "eng" for English)
            
        Returns:
            Dictionary containing:
                - text: Extracted text
                - confidence: Confidence score (0-100)
                - language: Detected or specified language
        """
        try:
            # Validate file exists
            path = Path(image_path)
            if not path.exists():
                return {
                    "error": f"File not found: {image_path}",
                    "status": "failed"
                }

            # Open image
            image = Image.open(path)

            # Extract text
            logger.info(f"Extracting text from {path.name} with language={language}")
            text = pytesseract.image_to_string(image, lang=language)

            # Get confidence
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            confidences = [int(c) for c in data["conf"] if int(c) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            logger.info(f"Successfully extracted {len(text)} characters")

            return {
                "text": text.strip(),
                "confidence": round(avg_confidence, 2),
                "language": language,
                "character_count": len(text),
                "status": "completed"
            }

        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
```

---

## Metadata Field Requirements

### Required Fields

```python
{
    "name": "plugin-name",          # Lowercase, hyphenated identifier
    "title": "Display Name",        # Human-readable name
    "description": "...",           # Brief description (1-2 sentences)
    "inputs": ["image"],            # List of input types
    "outputs": ["json"]             # List of output types
}
```

### Optional Fields

```python
{
    "version": "0.1.0",             # Semantic version
    "permissions": ["file:read"],   # Required permissions
    "tags": ["vision", "ocr"],      # Classification tags
    "author": "Your Name",          # Plugin author
    "homepage": "https://..."       # Documentation URL
}
```

### Field Validation Rules

| Field | Rules | Example |
|-------|-------|---------|
| `name` | lowercase, hyphens only, 3-50 chars | `"ocr"`, `"block-mapper"` |
| `title` | readable text, 5-100 chars | `"OCR Plugin"` |
| `description` | 10-500 chars | `"Extracts text from images"` |
| `inputs` | non-empty list | `["image"]`, `["image", "text"]` |
| `outputs` | non-empty list | `["json"]`, `["text", "image"]` |
| `version` | semantic versioning | `"0.1.0"`, `"1.2.3-alpha"` |

---

## Input/Output Types

### Common Input Types

| Type | Description | Example |
|------|-------------|---------|
| `image` | Image file (PNG, JPEG, etc.) | Photo, screenshot |
| `text` | Text input | Prompt, document |
| `json` | JSON data | Configuration, structured data |
| `binary` | Binary data | Any binary file |

### Common Output Types

| Type | Description | Example |
|------|-------------|---------|
| `json` | JSON-structured result | Extracted data, analysis |
| `text` | Plain text output | Extracted text, summary |
| `image` | Image file | Transformed image |
| `binary` | Binary data | Processed file |

### Examples

```python
# Image analysis plugin
"inputs": ["image"],
"outputs": ["json"]

# Text processing plugin
"inputs": ["text"],
"outputs": ["text"]

# Image transformation plugin
"inputs": ["image"],
"outputs": ["image"]

# Multi-input plugin
"inputs": ["image", "text"],
"outputs": ["json"]
```

---

## Plugin Registration

### Automatic Registration

ForgeSyte automatically discovers plugins in the `server/app/plugins/` directory:

```
server/app/plugins/
├── __init__.py
├── ocr.py          # Automatically discovered
├── block_mapper.py # Automatically discovered
└── utils.py        # Not a plugin
```

### Manual Registration

If your plugin is outside the default directory, register it manually:

```python
# In server/app/plugin_loader.py or your initialization code

from server.app.plugins.custom import MyPlugin

plugin_manager.register(MyPlugin())
```

---

## Execute Method Implementation

### Basic Signature

```python
async def execute(self, **kwargs) -> dict:
    """Process the plugin request.
    
    Args:
        **kwargs: Request parameters (file path, options, etc.)
        
    Returns:
        Dictionary with results
    """
    pass
```

### Parameter Handling

Parameters come from the job request. Common patterns:

```python
# Image file processing
async def execute(self, image_path: str, **kwargs) -> dict:
    """Process an image."""
    # image_path is provided by the job system
    return process_image(image_path)

# With options
async def execute(self, image_path: str, threshold: int = 128, **kwargs) -> dict:
    """Process image with adjustable threshold."""
    return process_with_threshold(image_path, threshold)

# Multiple inputs
async def execute(self, image_path: str, text_prompt: str, **kwargs) -> dict:
    """Process image with text guidance."""
    return analyze(image_path, text_prompt)
```

### Return Value Format

Always return a dictionary:

```python
# Success response
return {
    "status": "completed",
    "result": {
        "data": "...",
        "confidence": 0.95
    }
}

# Error response
return {
    "status": "failed",
    "error": "Description of what went wrong",
    "error_code": "SPECIFIC_ERROR"
}

# Processing response
return {
    "status": "processing",
    "progress": 45,  # Optional progress indicator
    "message": "Currently analyzing..."
}
```

---

## Error Handling

### Best Practices

```python
async def execute(self, image_path: str) -> dict:
    """Plugin with proper error handling."""
    try:
        # Validate inputs
        if not image_path:
            return {
                "status": "failed",
                "error": "image_path is required",
                "error_code": "MISSING_PARAMETER"
            }

        # Check file exists
        path = Path(image_path)
        if not path.exists():
            return {
                "status": "failed",
                "error": f"File not found: {image_path}",
                "error_code": "FILE_NOT_FOUND"
            }

        # Process
        result = process(path)

        # Return success
        return {
            "status": "completed",
            "result": result
        }

    except ValueError as e:
        # Handle validation errors
        logger.warning(f"Validation error: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "error_code": "VALIDATION_ERROR"
        }

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": "An unexpected error occurred",
            "error_code": "INTERNAL_ERROR"
        }
```

---

## Testing Your Plugin

### Unit Test Template

```python
"""Tests for MyPlugin."""

import pytest
from pathlib import Path
from server.app.plugins.my_plugin import MyPlugin


@pytest.fixture
def plugin():
    """Create a fresh plugin instance."""
    return MyPlugin()


@pytest.fixture
def test_image(tmp_path):
    """Create a test image."""
    from PIL import Image
    img = Image.new('RGB', (100, 100), color='red')
    path = tmp_path / "test.png"
    img.save(path)
    return str(path)


class TestMyPlugin:
    """Test suite for MyPlugin."""

    def test_metadata(self, plugin):
        """Test metadata is valid."""
        meta = plugin.metadata()
        
        assert meta["name"] == "my-plugin"
        assert "title" in meta
        assert "description" in meta
        assert "inputs" in meta
        assert "outputs" in meta
        assert len(meta["inputs"]) > 0
        assert len(meta["outputs"]) > 0

    @pytest.mark.asyncio
    async def test_execute_success(self, plugin, test_image):
        """Test successful execution."""
        result = await plugin.execute(image_path=test_image)
        
        assert result["status"] == "completed"
        assert "result" in result

    @pytest.mark.asyncio
    async def test_execute_missing_file(self, plugin):
        """Test error handling for missing file."""
        result = await plugin.execute(image_path="/nonexistent/file.png")
        
        assert result["status"] == "failed"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_execute_invalid_image(self, plugin, tmp_path):
        """Test error handling for invalid image."""
        # Create invalid image file
        bad_file = tmp_path / "invalid.png"
        bad_file.write_text("This is not a PNG file")
        
        result = await plugin.execute(image_path=str(bad_file))
        
        assert result["status"] == "failed"
```

### Integration Test

```python
"""Integration test with MCP adapter."""

from server.app.mcp_adapter import MCPAdapter
from server.app.plugin_loader import PluginManager


def test_plugin_appears_in_manifest():
    """Test that plugin is exposed in MCP manifest."""
    pm = PluginManager()
    adapter = MCPAdapter(pm)
    
    manifest = adapter.get_manifest()
    tools = manifest["tools"]
    tool_ids = [t["id"] for t in tools]
    
    assert "vision.my-plugin" in tool_ids
```

---

## Plugin Permissions

Plugins can declare required permissions:

```python
def metadata(self) -> dict:
    return {
        "name": "sensitive-plugin",
        "permissions": [
            "file:read",
            "file:write",
            "network:external",
            "database:access"
        ]
    }
```

### Permission Categories

| Category | Permissions | Description |
|----------|-------------|-------------|
| File I/O | `file:read`, `file:write` | Access to files |
| Network | `network:external`, `network:internal` | Network access |
| Database | `database:read`, `database:write` | Database access |
| Memory | `memory:high` | High memory usage |
| CPU | `cpu:heavy` | Heavy CPU usage |

---

## Advanced: Async Patterns

### Long-Running Operations

```python
async def execute(self, image_path: str) -> dict:
    """Plugin with progress reporting."""
    try:
        total_steps = 4
        
        # Step 1
        logger.info("Step 1: Loading image...")
        image = load_image(image_path)
        
        # Step 2
        logger.info("Step 2: Preprocessing...")
        processed = preprocess(image)
        
        # Step 3
        logger.info("Step 3: Analyzing...")
        analysis = await async_analyze(processed)
        
        # Step 4
        logger.info("Step 4: Formatting results...")
        result = format_results(analysis)
        
        return {
            "status": "completed",
            "result": result
        }

    except Exception as e:
        logger.error(f"Error: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }
```

### Parallel Processing

```python
import asyncio

async def execute(self, image_paths: list) -> dict:
    """Process multiple images in parallel."""
    try:
        # Process all images concurrently
        tasks = [process_image(p) for p in image_paths]
        results = await asyncio.gather(*tasks)
        
        return {
            "status": "completed",
            "result": {"images_processed": len(results), "results": results}
        }

    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }
```

---

## Dependencies Management

### Adding Dependencies

1. **Update requirements-plugins.txt** (if exists):

```
pytesseract==0.3.10
pillow==9.5.0
```

2. **Install with uv**:

```bash
cd server
uv pip install pytesseract pillow
```

3. **Verify import in plugin**:

```python
try:
    import pytesseract
except ImportError:
    raise ImportError(
        "pytesseract is required. Install with: uv pip install pytesseract"
    )
```

### Optional Dependencies

For optional features:

```python
try:
    import advanced_library
    HAS_ADVANCED = True
except ImportError:
    HAS_ADVANCED = False


async def execute(self, image_path: str) -> dict:
    if HAS_ADVANCED:
        return await execute_advanced(image_path)
    else:
        return await execute_basic(image_path)
```

---

## Performance Optimization

### Caching

```python
from functools import lru_cache

class MyPlugin(Plugin):
    @lru_cache(maxsize=128)
    def load_model(self):
        """Load expensive model once."""
        logger.info("Loading model...")
        return load_ml_model()

    async def execute(self, image_path: str) -> dict:
        model = self.load_model()  # Cached after first call
        return analyze_with_model(image_path, model)
```

### Lazy Loading

```python
class MyPlugin(Plugin):
    _model = None

    def get_model(self):
        """Load model only when needed."""
        if self._model is None:
            logger.info("Initializing model...")
            self._model = load_ml_model()
        return self._model

    async def execute(self, image_path: str) -> dict:
        model = self.get_model()
        return analyze_with_model(image_path, model)
```

---

## Documentation Best Practices

### Plugin Docstring

```python
class MyPlugin(Plugin):
    """
    Brief one-line description.
    
    Detailed description of what the plugin does, how it works, and what
    it's useful for. Can span multiple sentences or paragraphs.
    
    Examples:
        Basic usage:
        
        >>> plugin = MyPlugin()
        >>> result = await plugin.execute(image_path="/path/to/image.png")
        >>> print(result)
    """
```

### Method Docstrings

```python
async def execute(self, image_path: str, threshold: int = 128) -> dict:
    """
    Process an image with threshold adjustment.
    
    This method analyzes the image and applies a threshold for binarization.
    
    Args:
        image_path: Path to the input image file
        threshold: Binarization threshold (0-255, default: 128)
        
    Returns:
        Dictionary containing:
            - status: "completed" or "failed"
            - result: Analysis results (if successful)
            - error: Error message (if failed)
            
    Raises:
        FileNotFoundError: If image_path doesn't exist
        ValueError: If threshold is not in valid range
        
    Examples:
        >>> result = await plugin.execute("/path/to/image.png", threshold=100)
        >>> print(result["status"])
        "completed"
    """
```

---

## Publishing Your Plugin

### Distribution

1. **Standalone file**:
   - Copy `my_plugin.py` to `server/app/plugins/`

2. **Package**:
   - Create separate package repository
   - Distribute via pip

3. **Contributing to ForgeSyte**:
   - Create PR to the main repository
   - Follow contribution guidelines

### Documentation

Include in your plugin:

- Purpose and use cases
- Example outputs
- Performance characteristics
- Dependencies and system requirements
- License information

---

## Troubleshooting

### Plugin Not Appearing in Manifest

**Problem**: Plugin class is registered but not in MCP manifest.

**Solution**:
1. Check `metadata()` returns valid dict
2. Verify all required fields present
3. Check server logs for validation errors
4. Ensure plugin is registered before manifest generation

### Metadata Validation Errors

**Problem**: "Invalid plugin metadata" error in logs.

**Solution**:
1. Verify field types (name should be string, inputs/outputs should be lists)
2. Check field lengths (name: 3-50 chars, title: 5-100 chars)
3. Ensure inputs and outputs are non-empty lists
4. Test with sample metadata:

```python
from server.app.models import PluginMetadata

meta = plugin.metadata()
try:
    validated = PluginMetadata(**meta)
    print("✓ Metadata is valid")
except Exception as e:
    print(f"✗ Validation error: {e}")
```

### Execution Errors

**Problem**: Plugin returns "failed" status consistently.

**Solution**:
1. Check file paths are absolute
2. Verify dependencies are installed
3. Add comprehensive error logging
4. Test locally before deploying

---

## Related Documentation

- **[MCP Configuration Guide](./MCP_CONFIGURATION.md)** - How to configure ForgeSyte
- **[MCP API Reference](./MCP_API_REFERENCE.md)** - Complete API documentation
- **[Plugin Metadata Schema](../design/PLUGIN_METADATA_SCHEMA.md)** - Detailed schema spec

