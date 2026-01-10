# Plugin Metadata Schema Documentation

**Last Updated**: 2026-01-10  
**Status**: Implemented and Validated  
**Version**: 1.0.0  

## Overview

The Plugin Metadata Schema defines the structure and validation rules for plugin metadata in ForgeSyte. This schema ensures consistent plugin information across the system and enables proper MCP (Model Context Protocol) integration with Gemini-CLI.

All plugins must implement a `metadata()` method that returns a dictionary conforming to this schema. The schema is enforced using Pydantic models with strict validation.

## Schema Definition

### PluginMetadata Model

```python
class PluginMetadata(BaseModel):
    name: str                                 # Required, non-empty
    description: str                          # Required, non-empty
    version: str = "1.0.0"                   # Optional, defaults to 1.0.0
    inputs: List[str] = ["image"]            # Optional, defaults to ["image"]
    outputs: List[str] = ["json"]            # Optional, defaults to ["json"]
    permissions: List[str] = []              # Optional, defaults to []
    config_schema: Optional[Dict[str, Any]] = None  # Optional configuration schema
```

## Field Specifications

### `name` (Required)

**Type**: `str`  
**Validation**: Non-empty string, minimum length 1  
**Constraints**: Cannot be empty or whitespace-only  
**Examples**:
- `"ocr"`
- `"motion_detector"`
- `"content-moderation"`
- `"object_detection_v2"`

**Naming Convention**: Use lowercase with underscores or hyphens. Avoid spaces and special characters (except `_` and `-`).

**Purpose**: Unique identifier for the plugin. Used in tool ID generation (e.g., `vision.{name}`), API endpoints, and MCP manifest.

---

### `description` (Required)

**Type**: `str`  
**Validation**: Non-empty string, minimum length 1  
**Constraints**: Cannot be empty or whitespace-only  
**Examples**:
- `"Extract text from images using OCR"`
- `"Detect motion between consecutive video frames"`
- `"Analyze images for potentially unsafe content"`

**Purpose**: Human-readable description of what the plugin does. Displayed in UI and MCP manifests. Should clearly explain the plugin's functionality and primary use case.

**Guidelines**:
- Keep descriptions concise but informative (50-200 characters ideal)
- Focus on what the plugin does, not how
- Avoid technical jargon where possible
- Start with a verb (e.g., "Detect", "Extract", "Analyze")

---

### `version` (Optional)

**Type**: `str`  
**Default**: `"1.0.0"`  
**Validation**: Semantic version format  
**Supported Formats**:
- `"1.0.0"` - Standard semantic version (major.minor.patch)
- `"2.0"` - Two-component version
- `"1.0.0-alpha"` - Prerelease version
- `"1.0.0+build.123"` - Build metadata
- `"1.0.0-beta.1+build.456"` - Combined prerelease and build metadata

**Examples**:
- `"1.0.0"` - First stable release
- `"2.3.1"` - Third patch release of version 2.3
- `"1.0.0-alpha"` - Alpha prerelease
- `"1.0.0-beta.2"` - Second beta prerelease
- `"2.1.0-rc1"` - Release candidate

**Purpose**: Tracks plugin version for compatibility and updates. Used by the system to manage plugin lifecycle and versioning.

**Guidelines**:
- Follow semantic versioning (https://semver.org/)
- Increment major version for breaking changes
- Increment minor version for new features (backward compatible)
- Increment patch version for bug fixes
- Use prerelease versions during development (alpha, beta, rc)

---

### `inputs` (Optional)

**Type**: `List[str]`  
**Default**: `["image"]`  
**Validation**: List of strings (can be empty)  
**Examples**:
- `["image"]` - Single image input
- `["image", "config"]` - Image plus configuration options
- `["image", "metadata"]` - Image plus metadata
- `[]` - No inputs (e.g., informational plugin)

**Common Input Types**:
- `"image"` - Image data (bytes or URL)
- `"config"` - Configuration/options
- `"metadata"` - Additional metadata
- `"context"` - Contextual information
- `"stream"` - Streaming data

**Purpose**: Declares what types of input the plugin accepts. Used by the UI to determine how to call the plugin and by MCP clients to understand plugin capabilities.

**Guidelines**:
- Use descriptive type names
- Keep the list minimal (1-3 inputs typical)
- Document in config_schema what each input means
- Empty list is valid for plugins that need no input

---

### `outputs` (Optional)

**Type**: `List[str]`  
**Default**: `["json"]`  
**Validation**: List of strings (can be empty)  
**Examples**:
- `["json"]` - Structured data output
- `["text", "confidence"]` - Text result with confidence score
- `["regions", "labels", "scores"]` - Multiple outputs
- `["safe", "categories", "confidence"]` - Safety check results
- `[]` - No outputs

**Common Output Types**:
- `"json"` - Structured JSON data
- `"text"` - Text/string output
- `"image"` - Image output
- `"regions"` - Detected regions/bounding boxes
- `"labels"` - Classification labels
- `"scores"` - Numerical confidence/probability scores
- `"events"` - Event stream
- `"metadata"` - Metadata about the result

**Purpose**: Declares what types of output the plugin produces. Used by consuming components to understand and process the plugin's results.

**Guidelines**:
- List all major output types
- Be specific (prefer "text" over "result")
- Order by importance/frequency
- Can be empty if plugin has side effects only

---

### `permissions` (Optional)

**Type**: `List[str]`  
**Default**: `[]`  
**Validation**: List of strings in format `"resource:action"`  
**Examples**:
- `["read:files"]` - Requires file read permission
- `["write:results", "read:files"]` - Read and write permissions
- `["gpu:access"]` - GPU access permission
- `["execute:model"]` - Model execution permission
- `["network:external"]` - External network access
- `[]` - No special permissions required

**Permission Format**: `"resource:action"`
- `resource`: What the permission applies to (e.g., files, gpu, network, model)
- `action`: What action is allowed (e.g., read, write, execute, access)

**Standard Permissions**:
- `"read:files"` - Read local files
- `"write:results"` - Write results to filesystem
- `"read:cache"` - Access cached data
- `"write:cache"` - Write to cache
- `"gpu:access"` - Access GPU resources
- `"network:external"` - Make external API calls
- `"execute:model"` - Load and execute ML models
- `"moderation"` - Apply content moderation
- `"analytics"` - Collect usage analytics

**Purpose**: Documents what system resources and capabilities the plugin needs. Used for:
- Security and access control
- Resource scheduling
- User warnings about plugin capabilities
- MCP client compatibility

**Guidelines**:
- List all required permissions
- Be specific about what's needed
- Use standard permission names when applicable
- Empty list for plugins with no special needs

---

### `config_schema` (Optional)

**Type**: `Optional[Dict[str, Any]]`  
**Default**: `None`  
**Validation**: Must be a dictionary or None (not required)  
**Structure**: JSON Schema-like format

**Example**:

```python
{
    "sensitivity": {
        "type": "float",
        "default": 0.8,
        "min": 0.0,
        "max": 1.0,
        "description": "Detection sensitivity (0=none, 1=maximum)"
    },
    "categories": {
        "type": "array",
        "default": ["nsfw", "violence", "hate"],
        "description": "Categories to check"
    },
    "mode": {
        "type": "string",
        "default": "fast",
        "enum": ["fast", "accurate"],
        "description": "Processing mode"
    },
    "language": {
        "type": "string",
        "default": "eng",
        "description": "OCR language code"
    },
    "cache_results": {
        "type": "boolean",
        "default": True,
        "description": "Cache analysis results"
    }
}
```

**Schema Field Structure**:
- `type`: Data type (`string`, `float`, `integer`, `boolean`, `array`, `object`)
- `default`: Default value
- `description`: Human-readable description
- `enum`: Valid values (for enums)
- `min`/`max`: Range constraints (for numbers)
- `min_length`/`max_length`: String length constraints

**Common Configuration Patterns**:

**Threshold/Sensitivity**:
```python
"sensitivity": {
    "type": "float",
    "default": 0.5,
    "min": 0.0,
    "max": 1.0,
    "description": "Detection sensitivity level"
}
```

**Categorical Options**:
```python
"mode": {
    "type": "string",
    "default": "auto",
    "enum": ["auto", "manual", "hybrid"],
    "description": "Processing mode"
}
```

**Collections**:
```python
"enabled_categories": {
    "type": "array",
    "default": ["cat1", "cat2"],
    "description": "Which categories to analyze"
}
```

**Purpose**: Defines optional configuration parameters that users can customize. Used by:
- UI to generate configuration forms
- Plugins to receive configuration options
- API documentation

**Guidelines**:
- Only include user-configurable options
- Provide sensible defaults
- Document all fields clearly
- Use JSON Schema conventions
- Keep schema simple and maintainable

---

## Validation Rules

The schema enforces the following validation rules:

### Required Fields
- `name`: Must be provided and non-empty
- `description`: Must be provided and non-empty

### Optional Fields (with defaults)
- `version`: Defaults to `"1.0.0"` if not provided
- `inputs`: Defaults to `["image"]` if not provided
- `outputs`: Defaults to `["json"]` if not provided
- `permissions`: Defaults to `[]` if not provided
- `config_schema`: Defaults to `None` if not provided

### Type Validation
- `name`: string
- `description`: string
- `version`: string
- `inputs`: list of strings
- `outputs`: list of strings
- `permissions`: list of strings
- `config_schema`: dict or None

### Value Validation
- `name`: Non-empty after stripping whitespace
- `description`: Non-empty after stripping whitespace
- `inputs`: Can be empty list
- `outputs`: Can be empty list
- `permissions`: Can be empty list
- `config_schema`: Can be empty dict or None

---

## Plugin Implementation Example

### Minimal Plugin

```python
class Plugin:
    name = "simple_plugin"
    description = "A simple plugin"
    
    def metadata(self) -> dict:
        return {
            "name": self.name,
            "description": self.description
        }
```

### Full-Featured Plugin

```python
class Plugin:
    name = "moderation"
    version = "1.0.0"
    description = "Detect unsafe or inappropriate content"
    
    def metadata(self) -> dict:
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
                    "description": "Detection sensitivity level"
                },
                "categories": {
                    "type": "array",
                    "default": ["nsfw", "violence", "hate"],
                    "description": "Categories to check"
                }
            }
        }
    
    def analyze(self, image_bytes: bytes, options: Optional[dict] = None) -> dict:
        # Implementation here
        pass
```

---

## MCP Integration

The metadata schema is used by the MCP adapter to build the manifest for Gemini-CLI:

1. **Validation**: Each plugin's metadata is validated against the PluginMetadata schema
2. **Tool ID**: Generated as `vision.{plugin_name}`
3. **Tool Title**: Defaults to `name` field
4. **Invoke Endpoint**: Generated as `/v1/analyze?plugin={name}`
5. **Error Handling**: Invalid plugins are logged and skipped

Example manifest generation:

```json
{
  "tools": [
    {
      "id": "vision.ocr",
      "title": "ocr",
      "description": "Extract text from images",
      "inputs": ["image"],
      "outputs": ["text"],
      "invoke_endpoint": "/v1/analyze?plugin=ocr",
      "permissions": ["read:files"]
    }
  ],
  "server": {
    "name": "forgesyte",
    "version": "0.1.0",
    "mcp_version": "1.0.0"
  }
}
```

---

## Testing

All plugins must ensure their metadata:

1. Can be validated against PluginMetadata schema
2. Returns all required fields (name, description)
3. Uses valid semantic versions
4. Provides accurate input/output type descriptions
5. Lists all required permissions
6. Has valid config_schema if provided

Test implementation:

```python
from app.models import PluginMetadata

def test_plugin_metadata():
    plugin = Plugin()
    metadata = plugin.metadata()
    
    # This will raise ValidationError if schema is invalid
    validated = PluginMetadata(**metadata)
    
    assert validated.name == "my_plugin"
    assert len(validated.outputs) > 0
```

---

## Backward Compatibility

The schema maintains backward compatibility:

- Plugins that only provide `name` and `description` still work
- All other fields have sensible defaults
- Invalid plugins are logged but don't break the system
- New fields can be added as optional without breaking existing plugins

---

## Best Practices

1. **Use Descriptive Names**: Choose plugin names that clearly indicate function
2. **Document Capabilities**: List all inputs and outputs explicitly
3. **Provide Defaults**: Use sensible config_schema defaults
4. **Test Metadata**: Validate metadata during plugin testing
5. **Keep Updated**: Update version and description when plugin changes
6. **List Permissions**: Always declare required permissions
7. **Semantic Versioning**: Follow semantic versioning for version field
8. **Clear Descriptions**: Write descriptions that non-technical users understand

---

## Troubleshooting

### "Invalid plugin metadata" Error

When you see this error in logs:
```
ERROR Invalid plugin metadata for 'my_plugin': 1 error(s) - ...
```

Common causes and fixes:

| Error | Cause | Fix |
|-------|-------|-----|
| `Field required` for name | Missing name in metadata() | Add `"name": self.name` |
| `Field required` for description | Missing description | Add `"description": "..."` |
| `string_too_short` for name | Empty name string | Provide non-empty name |
| `list_type` for inputs | inputs is not a list | Change `inputs` to list format |
| `dict_type` for config_schema | Not a dict | Make config_schema a dict or None |

### Plugin Not Appearing in Manifest

If a plugin isn't in the MCP manifest:
1. Check logs for validation errors
2. Run plugin metadata validation test
3. Verify all required fields are present
4. Ensure description is non-empty
5. Validate semantic version format

---

## References

- **Semantic Versioning**: https://semver.org/
- **JSON Schema**: https://json-schema.org/
- **Pydantic Validation**: https://docs.pydantic.dev/latest/
- **MCP Protocol**: See `docs/design/MCP.md`
- **Plugin Development**: See `PLUGIN_DEVELOPMENT.md`
