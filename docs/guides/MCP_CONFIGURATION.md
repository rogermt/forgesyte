# MCP Configuration Guide

This guide explains how to configure and use ForgeSyte as an MCP server with Gemini-CLI and other MCP-aware clients.

## Overview

ForgeSyte is an MCP (Model Context Protocol) compatible vision server that exposes all installed plugins as discoverable, invocable tools. This guide covers:

- Installing ForgeSyte as a Gemini CLI extension
- Configuring Gemini-CLI to talk to ForgeSyte
- Understanding ForgeSyte’s MCP endpoints
- Plugin metadata and tool discovery
- Troubleshooting common issues

---

## 1. Gemini-CLI configuration

There are two pieces to the story:

1. **Installing ForgeSyte as a Gemini CLI extension** (so Gemini knows it exists)  
2. **Configuring MCP servers in Gemini’s user settings** (so Gemini knows how to talk to it)

### 1.1 Install ForgeSyte as a Gemini CLI extension

This server is designed to be installed as an extension in [Gemini CLI](https://github.com/google-gemini/gemini-cli).

```bash
# From GitHub
gemini extensions install https://github.com/rogermt/forgesyte

# From local path
gemini extensions install /path/to/forgesyte
```

This lets Gemini-CLI treat ForgeSyte as a first-class extension (for updates, discovery, etc.).

### 1.2 Add ForgeSyte to Gemini-CLI MCP config

Next, configure Gemini-CLI so it knows **where** to reach ForgeSyte over HTTP.

1. **Start ForgeSyte locally**:

```bash
cd forgesyte/server
uv sync
uv run fastapi dev app/main.py
```

By default, ForgeSyte listens on:

- `http://localhost:8000`

2. **Add ForgeSyte to Gemini-CLI MCP servers**:

Edit your Gemini-CLI **user configuration** file  
(typical example: `~/.gemini-cli/settings.json` or similar, depending on your install):

```json
{
  "mcpServers": {
    "forgesyte": {
      "manifestUrl": "http://localhost:8000/v1/mcp-manifest"
    }
  }
}
```

Key points:

- This JSON is **Gemini user config**, not ForgeSyte’s own manifest file.
- `forgesyte` is the logical server name.
- `manifestUrl` points to ForgeSyte’s MCP manifest endpoint at `/v1/mcp-manifest`.

3. **Verify ForgeSyte is discovered**:

```bash
gemini-cli tools list
```

You should see all ForgeSyte plugins listed as available tools.

> If the command name differs in your version of Gemini-CLI, use the equivalent “list tools” command.

---

## 2. MCP endpoints exposed by ForgeSyte

ForgeSyte exposes endpoints that MCP clients (and you, for debugging) can call.

### 2.1 GET `/v1/mcp-manifest`

Returns the MCP manifest describing all available tools.

**Example response**:

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

### 2.2 GET `/v1/mcp-version`

Returns the MCP protocol version that ForgeSyte declares.

**Response**:

```json
{
  "mcp_version": "1.0.0"
}
```

---

## 3. Plugin invocation flow

### 3.1 Tool discovery

When Gemini-CLI starts and reads your MCP config, it:

1. Calls `manifestUrl` (`/v1/mcp-manifest`)  
2. Learns which tools are available  
3. Registers them under the `forgesyte` server

You can see the raw manifest yourself:

```bash
curl http://localhost:8000/v1/mcp-manifest | jq '.tools'
```

### 3.2 Tool invocation

Each tool has an `invoke_endpoint` (conventionally `/v1/analyze?plugin=<name>`).

Example: invoking the OCR plugin manually:

```bash
curl -X POST \
  "http://localhost:8000/v1/analyze?plugin=ocr" \
  -F "file=@image.png"
```

**Job created response**:

```json
{
  "id": "job_abc123",
  "status": "queued",
  "plugin": "ocr",
  "created_at": "2024-01-10T12:00:00Z"
}
```

### 3.3 Poll results

Poll the job endpoint until completion:

```bash
curl http://localhost:8000/v1/jobs/job_abc123
```

**Completed example**:

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

Gemini-CLI follows a similar flow internally when it invokes ForgeSyte tools.

---

## 4. Plugin metadata requirements

Each ForgeSyte plugin must implement a `metadata()` method that returns a dictionary with required fields. This metadata is used to build the MCP manifest and drive tool discovery.

```python
class MyPlugin:
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

    def analyze(self, image_bytes: bytes) -> dict:
        """Plugin execution logic."""
        # Implementation here
        return {"result": "..."}
```

### Required metadata fields

| Field         | Type         | Description                                   |
|--------------|--------------|-----------------------------------------------|
| `name`       | `str`        | Plugin identifier (lowercase, hyphenated)     |
| `title`      | `str`        | Human-readable plugin name                    |
| `description`| `str`        | Brief description of functionality            |
| `inputs`     | `List[str]`  | Input types (e.g. `"image"`, `"text"`)        |
| `outputs`    | `List[str]`  | Output types (e.g. `"json"`, `"text"`)        |
| `version`    | `str` (opt.) | Plugin version (semantic)                     |
| `permissions`| `List[str]` (opt.) | Required permissions (if any)         |

ForgeSyte validates metadata when generating the manifest. Invalid or incomplete metadata may cause a plugin to be skipped.

---

## 5. Tool schema in the manifest

Tools in the manifest follow this schema:

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

- `id` is usually `vision.{plugin_name}`.
- `invoke_endpoint` is where the MCP client sends requests.

---

## 6. Version and compatibility

ForgeSyte declares an MCP protocol version:

```python
# In server/app/mcp_adapter.py
MCP_PROTOCOL_VERSION = "1.0.0"
```

You can inspect it via:

```bash
curl http://localhost:8000/v1/mcp-version
# => {"mcp_version": "1.0.0"}
```

Future clients may request specific MCP versions; ForgeSyte is structured so negotiated behavior can be added later.

---

## 7. Troubleshooting

### ForgeSyte tools not visible in Gemini-CLI

- Confirm ForgeSyte is running:

  ```bash
  curl http://localhost:8000/
  ```

- Confirm `manifestUrl` is correct in `mcpServers` config.
- Inspect the manifest directly:

  ```bash
  curl http://localhost:8000/v1/mcp-manifest | jq '.tools'
  ```

- Check ForgeSyte logs for plugin loading or metadata errors.

### Invocation 404

- The `plugin` query parameter may not match a loaded plugin.
- The `/v1/analyze` route might be misconfigured or missing.

### Manifest 500

- Likely a plugin with invalid metadata.
- Check logs for `ValidationError` or plugin import errors.

---

## 8. Development workflow recap

1. Start ForgeSyte with uv (`uv run fastapi dev app/main.py`).
2. Install ForgeSyte as a Gemini extension (`gemini extensions install ...`).
3. Add ForgeSyte under `mcpServers` with `manifestUrl`.
4. Implement plugins with proper `metadata()` and `analyze()`.
5. Use `/v1/mcp-manifest` + `/v1/analyze` + `/v1/jobs` to debug end-to-end.

---

## 9. Related docs

- `docs/guides/PLUGIN_IMPLEMENTATION.md` – How to write plugins  
- `docs/guides/MCP_API_REFERENCE.md` – Detailed endpoint descriptions  
- `docs/design/MCP.md` – Internal design and rationale
```

---
