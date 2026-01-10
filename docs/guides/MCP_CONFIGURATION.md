# MCP Configuration Guide

This guide explains how to configure and use ForgeSyte as an MCP server with Gemini-CLI and other MCP clients.

## Overview

ForgeSyte is a fully MCP (Model Context Protocol) compliant vision server that exposes all installed plugins as discoverable, invocable tools. This guide covers:

- Setting up Gemini-CLI to use ForgeSyte
- Understanding MCP endpoints
- Configuring plugin metadata
- Troubleshooting common issues

---

## 1. Gemini-CLI Configuration

### Quick Start

1. **Get the ForgeSyte manifest**:

```bash
cd forgesyte
python -m server.app.main &  # Start the server
```

2. **Add ForgeSyte to Gemini-CLI config**:

Edit your Gemini-CLI configuration file (typically `~/.gemini-cli/config.json` or similar):

```json
{
  "mcpServers": {
    "forgesyte": {
      "manifestUrl": "http://localhost:8000/v1/mcp-manifest"
    }
  }
}
```

3. **Verify ForgeSyte is discovered**:

```bash
gemini-cli tools list
```

You should see all ForgeSyte plugins listed as available tools.

---

## 2. MCP Endpoints

ForgeSyte exposes two key endpoints for MCP clients:

### GET `/v1/mcp-manifest`

Returns the MCP manifest describing all available tools.

**Response**:
```json
{
  "tools": [
    {
      "id": "vision.ocr",
      "title": "OCR Plugin",
      "description": "Extracts text from images",
      "inputs": ["image"],
      "outputs": ["text"],
      "invoke_endpoint": "/v1/analyze?plugin=ocr",
      "permissions": []
    }
  ],
  "server": {
    "name": "forgesyte",
    "version": "0.1.0",
    "mcp_version": "1.0.0"
  },
  "version": "1.0"
}
```

### GET `/v1/mcp-version`

Returns the MCP protocol version.

**Response**:
```json
{
  "mcp_version": "1.0.0"
}
```

---

## 3. Plugin Invocation Flow

### Step 1: Tool Discovery

When Gemini-CLI loads ForgeSyte's manifest, it learns about available tools:

```bash
curl http://localhost:8000/v1/mcp-manifest | jq '.tools'
```

### Step 2: Tool Invocation

To invoke a tool, send a POST request to its `invoke_endpoint`:

```bash
curl -X POST \
  "http://localhost:8000/v1/analyze?plugin=ocr" \
  -F "file=@image.png"
```

**Response** (job created):
```json
{
  "id": "job_abc123",
  "status": "queued",
  "plugin": "ocr",
  "created_at": "2024-01-10T12:00:00Z"
}
```

### Step 3: Polling Results

Poll the job endpoint to get results:

```bash
curl http://localhost:8000/v1/jobs/job_abc123
```

**Response** (when complete):
```json
{
  "id": "job_abc123",
  "status": "completed",
  "plugin": "ocr",
  "result": {
    "text": "Extracted text from image",
    "confidence": 0.95
  },
  "created_at": "2024-01-10T12:00:00Z",
  "completed_at": "2024-01-10T12:00:05Z"
}
```

---

## 4. Plugin Metadata Requirements

Every ForgeSyte plugin must implement a `metadata()` method that returns a dictionary with required fields:

```python
class MyPlugin(Plugin):
    name = "my-plugin"

    def metadata(self) -> dict:
        """Return plugin metadata for MCP discovery."""
        return {
            "name": "my-plugin",
            "title": "My Plugin",
            "description": "Brief description of what this plugin does",
            "inputs": ["image"],
            "outputs": ["json", "text"],
            "version": "0.1.0",
            "permissions": []  # Optional
        }

    async def execute(self, image_path: str) -> dict:
        """Plugin execution logic."""
        # Implementation here
        return {"result": "..."}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Plugin identifier (lowercase, hyphenated) |
| `title` | `str` | Human-readable plugin name |
| `description` | `str` | Brief description of functionality |
| `inputs` | `List[str]` | Input types (e.g., "image", "text") |
| `outputs` | `List[str]` | Output types (e.g., "json", "text") |
| `version` | `str` (optional) | Semantic version of the plugin |
| `permissions` | `List[str]` (optional) | Required permissions |

### Field Validation

ForgeSyte validates plugin metadata when generating the manifest:

- **Invalid fields** trigger a validation error (logged)
- **Missing required fields** cause the plugin to be skipped
- **Type mismatches** are caught and reported

---

## 5. MCP Tool Schema

Tools in the manifest are described using this schema:

```json
{
  "id": "vision.plugin-name",
  "title": "Plugin Name",
  "description": "What this tool does",
  "inputs": ["image"],
  "outputs": ["json"],
  "invoke_endpoint": "/v1/analyze?plugin=plugin-name",
  "permissions": []
}
```

The `id` field is automatically generated as `vision.{plugin_name}`.

---

## 6. Version Negotiation

### Server Version

ForgeSyte declares an MCP protocol version:

```python
# In server/app/mcp_adapter.py
MCP_PROTOCOL_VERSION = "1.0.0"
```

This version is included in the manifest response.

### Checking Version

```bash
curl http://localhost:8000/v1/mcp-version
# => {"mcp_version": "1.0.0"}
```

### Future Version Negotiation

When Gemini-CLI supports version negotiation, it may send:

```
GET /v1/mcp-manifest?mcp_version=2.0.0
```

The server can then:
1. Check the requested version
2. Return either:
   - A compatible manifest
   - An error indicating version incompatibility
3. Document upgrade paths

This strategy is prepared but not yet implemented.

---

## 7. Remote Server Configuration

To connect to ForgeSyte running on a remote server:

```json
{
  "mcpServers": {
    "forgesyte-remote": {
      "manifestUrl": "https://vision-server.example.com/v1/mcp-manifest"
    }
  }
}
```

Replace `https://vision-server.example.com` with your server's URL.

---

## 8. Troubleshooting

### Manifest Returns 500 Error

**Symptom**: Calling `/v1/mcp-manifest` returns an HTTP 500 error.

**Solution**:
1. Check that ForgeSyte server is running:
   ```bash
   curl http://localhost:8000/health
   ```
2. Check server logs for plugin loading errors
3. Verify plugins implement the `metadata()` method

### Tool Not Appearing in List

**Symptom**: A plugin is installed but doesn't appear in the manifest.

**Solution**:
1. Verify the plugin's `metadata()` method returns a valid dict
2. Check for validation errors in server logs
3. Ensure the plugin is registered with the PluginManager

### Invocation Fails with 404

**Symptom**: Invoking a tool returns HTTP 404.

**Solution**:
1. Verify the plugin name matches the `invoke_endpoint`
2. Check that `/v1/analyze` endpoint is implemented
3. Ensure the plugin is still loaded (not unloaded)

### Version Mismatch

**Symptom**: Gemini-CLI reports version incompatibility.

**Solution**:
1. Check `GET /v1/mcp-version` returns expected version
2. Verify Gemini-CLI client version supports MCP 1.0.0
3. Update either client or server as needed

---

## 9. Development Workflow

### Adding a New Plugin

1. Create plugin class with `metadata()` method
2. Register with PluginManager
3. Restart ForgeSyte server
4. Verify manifest includes new tool:
   ```bash
   curl http://localhost:8000/v1/mcp-manifest | jq '.tools[] | select(.id == "vision.new-plugin")'
   ```

### Testing Plugin Metadata

Validate plugin metadata before deployment:

```python
from server.app.mcp_adapter import PluginMetadata

plugin_meta = my_plugin.metadata()
try:
    validated = PluginMetadata(**plugin_meta)
    print("✓ Metadata is valid")
except ValidationError as e:
    print(f"✗ Metadata invalid: {e}")
```

### Manual Testing

Use the validation script to test the full MCP flow:

```bash
cd server
uv run scripts/validate_mcp.py
```

This validates:
- Manifest generation
- Tool discovery
- Plugin metadata
- Version endpoints

---

## 10. Performance Considerations

### Manifest Caching

For servers with many plugins, consider implementing manifest caching:

```python
# Optional: Cache manifest for 5 minutes
@app.get("/v1/mcp-manifest")
@cache(ttl=300)
def get_mcp_manifest():
    return adapter.get_manifest()
```

### Plugin Discovery

ForgeSyte discovers plugins on startup. If you need dynamic plugin loading:

1. Consider invalidating manifest cache
2. Re-initialize the adapter
3. Notify connected MCP clients of changes

---

## 11. Security Considerations

### Exposing Plugins Securely

When deploying ForgeSyte in production:

1. **Authentication**: Protect `/v1/mcp-manifest` with API key or OAuth
2. **Authorization**: Restrict which plugins each client can invoke
3. **Rate Limiting**: Limit tool invocation rates per client
4. **HTTPS**: Always use HTTPS for remote servers

### Plugin Permissions

Plugins can declare required permissions:

```python
def metadata(self) -> dict:
    return {
        "name": "sensitive-plugin",
        "permissions": ["file:read", "network:external"]
    }
```

Clients can then evaluate whether to grant access.

---

## 12. Related Documentation

- **[Plugin Implementation Guide](./PLUGIN_IMPLEMENTATION.md)** - How to write ForgeSyte plugins
- **[MCP API Reference](./MCP_API_REFERENCE.md)** - Complete API endpoint documentation
- **[Design Specification](../design/MCP.md)** - MCP architecture and design decisions

