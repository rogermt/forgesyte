# Issue: Manifest Error - HTML Response Instead of JSON

**Date**: 2024
**Status**: Open
**Priority**: High
**Type**: Bug

## Error Message

```
Manifest Error:
Unexpected token '<', "<!DOCTYPE "... is not valid JSON

Check that the plugin is loaded and the server is running.
```

## Description

When clients attempt to fetch the MCP manifest endpoint (`/.well-known/mcp-manifest` or `/v1/.well-known/mcp-manifest`), they receive an HTML response (DOCTYPE page) instead of valid JSON. This causes JSON parsing failures on the client side.

## Root Cause Analysis

The error indicates that the HTTP response body starts with `<!DOCTYPE` which means:

1. **Server not running**: The manifest endpoint is unreachable
2. **Wrong URL**: Client is requesting an incorrect endpoint
3. **404 error page**: FastAPI is returning an HTML 404 page instead of JSON
4. **Middleware interference**: Some middleware is transforming JSON responses to HTML
5. **Route registration issue**: The route is not properly registered

## Affected Endpoints

The following MCP manifest endpoints are affected:

| Endpoint | Handler | Status |
|----------|---------|--------|
| `/.well-known/mcp-manifest` | `main.py: root_mcp_manifest()` | Redirects to `/v1/.well-known/mcp-manifest` |
| `/v1/.well-known/mcp-manifest` | `api.py: well_known_mcp_manifest()` | Returns MCP manifest JSON |
| `/v1/mcp-manifest` | `api.py: mcp_manifest()` | Returns MCP manifest JSON |

## Code Flow

### Endpoint Registration

```python
# server/app/main.py
app.include_router(api_router, prefix=settings.api_prefix)  # prefix = "/v1"

# server/app/api.py
@router.get("/.well-known/mcp-manifest")
async def well_known_mcp_manifest(
    request: Request,
    service: PluginManagementService = Depends(get_plugin_service),
) -> Dict[str, Any]:
    base_url = str(request.base_url).rstrip("/")
    adapter = MCPAdapter(request.app.state.plugins, base_url)
    return adapter.get_manifest()
```

### Manifest Generation

```python
# server/app/mcp/adapter.py
def get_manifest(self) -> Dict[str, Any]:
    """Generate MCP manifest for client discovery."""
    logger.debug("Building fresh MCP manifest")
    tools = self._build_tools()
    
    server_info: Dict[str, str] = {
        "name": MCP_SERVER_NAME,
        "version": MCP_SERVER_VERSION,
        "mcp_version": MCP_PROTOCOL_VERSION,
    }
    
    manifest = MCPManifest(
        tools=tools,
        server=server_info,
        version="1.0",
    )
    return manifest.model_dump()
```

## Potential Causes

### 1. Server Not Running

If the server is not running, the client will receive a connection error or HTML error page.

### 2. Base URL Mismatch

When the MCP adapter is created with an incorrect base URL, the manifest might reference wrong endpoints.

```python
# Problem: request.base_url might include trailing slash
base_url = str(request.base_url).rstrip("/")
adapter = MCPAdapter(request.app.state.plugins, base_url)
```

### 3. Plugin Manager Not Initialized

If `request.app.state.plugins` is None or not properly initialized, the manifest generation will fail.

```python
# server/app/main.py - lifespan function
plugin_manager = PluginManager()
load_result = plugin_manager.load_plugins()
app.state.plugins = plugin_manager
```

### 4. Invalid Plugin Metadata

If any loaded plugin has invalid metadata, the manifest generation might fail silently.

```python
# server/app/mcp/adapter.py
for name, meta in plugin_metadata.items():
    try:
        validated_meta = PluginMetadata(**meta)
        # ...
    except ValidationError as e:
        logger.error("Invalid plugin metadata", extra={"plugin_name": name, "errors": str(e)})
        continue  # Continues but might return empty tools list
```

### 5. CORS Issues

If the client is making cross-origin requests without proper CORS headers, the request might be blocked or redirected.

## Reproduction Steps

1. Start the server: `python -m server.app.main`
2. Attempt to fetch the manifest: `curl http://localhost:8000/.well-known/mcp-manifest`
3. Check if response is JSON or HTML:
   - Expected: `{"tools": [...], "server": {...}, "version": "1.0"}`
   - Actual: `<!DOCTYPE html>...` or error page

## Diagnostic Commands

```bash
# Test manifest endpoint
curl -v http://localhost:8000/.well-known/mcp-manifest

# Test MCP version endpoint
curl http://localhost:8000/v1/mcp-version

# Check server health
curl http://localhost:8000/v1/health

# List plugins
curl http://localhost:8000/v1/plugins
```

## Expected Behavior

The manifest endpoint should return valid JSON:

```json
{
  "tools": [
    {
      "id": "vision.ocr",
      "title": "ocr",
      "description": "Extract text from images",
      "inputs": ["image"],
      "outputs": ["text"],
      "invoke_endpoint": "http://localhost:8000/v1/analyze?plugin=ocr",
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

## Investigation Checklist

- [ ] Verify server is running on correct host/port
- [ ] Check logs for manifest generation errors
- [ ] Verify route registration in `app.include_router()`
- [ ] Check for middleware that might transform responses
- [ ] Verify `request.app.state.plugins` is not None
- [ ] Check all loaded plugins have valid metadata
- [ ] Verify CORS configuration allows client origin
- [ ] Test endpoint directly with curl, not through browser

## Potential Solutions

### Solution 1: Add Explicit Error Handling

Add try-catch blocks to return proper JSON errors instead of letting exceptions return HTML.

```python
@router.get("/.well-known/mcp-manifest")
async def well_known_mcp_manifest(
    request: Request,
    service: PluginManagementService = Depends(get_plugin_service),
) -> JSONResponse:
    try:
        base_url = str(request.base_url).rstrip("/")
        adapter = MCPAdapter(request.app.state.plugins, base_url)
        manifest = adapter.get_manifest()
        return JSONResponse(manifest)
    except Exception as e:
        logger.exception("Error generating MCP manifest")
        return JSONResponse(
            {"error": "Failed to generate manifest", "detail": str(e)},
            status_code=500
        )
```

### Solution 2: Add Validation Endpoint

Add a health check specifically for manifest generation.

```python
@router.get("/.well-known/mcp-manifest/validate")
async def validate_mcp_manifest() -> Dict[str, Any]:
    """Validate that manifest can be generated."""
    try:
        adapter = MCPAdapter(plugin_manager)
        manifest = adapter.get_manifest()
        return {
            "valid": True,
            "tool_count": len(manifest.get("tools", [])),
            "server": manifest.get("server", {})
        }
    except Exception as e:
        return JSONResponse(
            {"valid": False, "error": str(e)},
            status_code=500
        )
```

### Solution 3: Add Request Logging

Add detailed logging to trace manifest generation issues.

```python
@router.get("/.well-known/mcp-manifest")
async def well_known_mcp_manifest(
    request: Request,
    service: PluginManagementService = Depends(get_plugin_service),
) -> Dict[str, Any]:
    logger.info("MCP manifest request received", extra={
        "base_url": str(request.base_url),
        "plugins_loaded": len(request.app.state.plugins.list()) if hasattr(request.app.state, 'plugins') else 0
    })
    # ... rest of handler
```

### Solution 4: Add Startup Validation

Validate manifest generation at startup and fail fast if invalid.

```python
# In lifespan function
try:
    adapter = MCPAdapter(plugin_manager)
    manifest = adapter.get_manifest()
    logger.info(
        "MCP manifest validated at startup",
        extra={"tool_count": len(manifest.get("tools", []))}
    )
except Exception as e:
    logger.error("MCP manifest validation failed at startup", extra={"error": str(e)})
    # Could raise to prevent server start
```

## Related Files

- `server/app/api.py` - MCP manifest endpoints
- `server/app/main.py` - Route registration and lifespan
- `server/app/mcp/adapter.py` - Manifest generation logic
- `server/app/mcp/routes.py` - MCP JSON-RPC routes
- `server/app/plugin_loader.py` - Plugin loading
- `docs/design/PLUGIN_METADATA_SCHEMA.md` - Plugin metadata specification

## References

- [MCP Protocol Specification](../design/MCP.md)
- [Plugin Metadata Schema](../design/PLUGIN_METADATA_SCHEMA.md)
- [FastAPI JSONResponse](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.JSONResponse)

