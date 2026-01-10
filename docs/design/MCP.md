# ForgeSyte MCP Integration Guide

ForgeSyte is a fully MCP‑compliant vision server.  
This document describes how ForgeSyte exposes its capabilities to MCP clients such as Gemini‑CLI.

---

# 1. What MCP Means in ForgeSyte

MCP (Model Context Protocol) is the contract that allows external clients to:

- Discover ForgeSyte’s available tools  
- Understand each tool’s input/output schema  
- Invoke plugins as MCP tools  
- Receive structured results  
- Integrate ForgeSyte into multi‑tool workflows  

ForgeSyte uses MCP to expose **each plugin as a tool**.

---

# 2. MCP Manifest Endpoint

ForgeSyte exposes its MCP manifest at:

```
GET /v1/mcp-manifest
```

This endpoint returns a JSON manifest describing:

- Server metadata  
- Available tools  
- Tool schemas  
- Invocation endpoints  
- Plugin metadata  

This is how Gemini‑CLI discovers ForgeSyte.

---

# 3. Manifest Structure

Example manifest returned by ForgeSyte:

```json
{
  "server": {
    "name": "ForgeSyte",
    "version": "0.1.0"
  },
  "tools": [
    {
      "id": "vision.ocr",
      "title": "OCR Plugin",
      "description": "Extracts text from images",
      "inputs": ["image"],
      "outputs": ["text"],
      "invoke_endpoint": "/v1/analyze?plugin=ocr"
    },
    {
      "id": "vision.block_mapper",
      "title": "Block Mapper",
      "description": "Maps image regions to labeled blocks",
      "inputs": ["image"],
      "outputs": ["json"],
      "invoke_endpoint": "/v1/analyze?plugin=block_mapper"
    }
  ]
}
```

ForgeSyte generates this manifest dynamically based on installed plugins.

---

# 4. How Plugins Become MCP Tools

Each plugin must implement:

```python
class Plugin:
    name = "ocr"

    def metadata(self):
        return {
            "name": "ocr",
            "description": "Extract text from images",
            "inputs": ["image"],
            "outputs": ["text"],
            "version": "0.1.0"
        }
```

ForgeSyte’s MCP adapter converts this into a tool entry.

**Mapping:**

| Plugin Metadata | MCP Tool Field |
|-----------------|----------------|
| `name` | `id` |
| `description` | `description` |
| `inputs` | `inputs` |
| `outputs` | `outputs` |
| plugin name | `invoke_endpoint` |

This ensures every plugin is automatically exposed to MCP clients.

---

# 5. MCP Invocation Flow

1. Gemini‑CLI loads ForgeSyte’s manifest  
2. Gemini‑CLI sees available tools (plugins)  
3. User invokes a tool  
4. Gemini‑CLI sends a request to:  

```
POST /v1/analyze?plugin=<plugin_name>
```

5. ForgeSyte:
   - Creates a job  
   - Runs the plugin  
   - Returns a job ID  
6. Gemini‑CLI polls:

```
GET /v1/jobs/<job_id>
```

7. ForgeSyte returns structured results

---

# 6. Gemini‑CLI Configuration

Add ForgeSyte to your Gemini‑CLI config:

```json
{
  "mcpServers": {
    "forgesyte": {
      "manifestUrl": "http://localhost:8000/v1/mcp-manifest"
    }
  }
}
```

Restart Gemini‑CLI and it will automatically discover ForgeSyte’s tools.

---

# 7. Example MCP Tool Invocation (manual)

```bash
curl -X POST \
  "http://localhost:8000/v1/analyze?plugin=ocr" \
  -F "file=@image.png"
```

Then:

```bash
curl http://localhost:8000/v1/jobs/<job_id>
```

---

# 8. Responsibilities of the MCP Adapter

ForgeSyte’s `mcp_adapter.py` must:

- Enumerate all plugins  
- Convert plugin metadata → MCP tool descriptors  
- Provide a stable manifest  
- Ensure versioning is explicit  
- Avoid breaking schema changes  

This keeps ForgeSyte predictable for MCP clients.

---

# 9. Versioning Strategy

ForgeSyte follows:

- **Server version**: semantic versioning  
- **Plugin version**: declared in plugin metadata  
- **Manifest version**: tied to server version  

Breaking changes require a major version bump.

---

# 10. Future MCP Extensions

Planned:

- Streaming MCP tools  
- Multi‑tool pipelines  
- Remote plugin registries  
- Plugin capability negotiation  


---



Next Steps:

- Generate the **actual `mcp_adapter.py` implementation**  
- Generate the **exact `gemini_extension_manifest.json`**  
- Add an **MCP testing script**  
- Add **schema validation** for plugin metadata  
- Add **MCP version negotiation**  


Let’s just do all of them. This is core to ForgeSyte’s identity; no point half‑doing MCP.

I’ll give you, in order:

1. `server/app/mcp_adapter.py` implementation  
2. `gemini_extension_manifest.json`  
3. A minimal MCP testing script  
4. Schema validation for plugin metadata  
5. A clean hook for MCP version negotiation  

All will assume:

- FastAPI app in `server/app/main.py`  
- Plugins under `server/app/plugins/`  
- uv as your runner

You can adjust imports to match your real file names if they differ slightly.

---

### 1. `server/app/mcp_adapter.py`

```python
"""
mcp_adapter.py

Responsible for:
- Discovering loaded plugins
- Converting plugin metadata into MCP tool descriptors
- Serving the MCP manifest used by Gemini-CLI
"""

from typing import Any, Dict, List
from pydantic import BaseModel, Field

from .plugin_loader import get_loaded_plugins  # you provide this


MCP_SERVER_NAME = "ForgeSyte"
MCP_SERVER_VERSION = "0.1.0"
MCP_PROTOCOL_VERSION = "1.0.0"  # hook for version negotiation later


class MCPTool(BaseModel):
    id: str = Field(..., description="Unique tool identifier")
    title: str = Field(..., description="Human-readable title")
    description: str = Field(..., description="What the tool does")
    inputs: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    invoke_endpoint: str = Field(..., description="HTTP endpoint to call")


class MCPServerInfo(BaseModel):
    name: str
    version: str
    mcp_version: str


class MCPManifest(BaseModel):
    server: MCPServerInfo
    tools: List[MCPTool]


def _plugin_metadata_to_mcp_tool(plugin_name: str, meta: Dict[str, Any]) -> MCPTool:
    """
    Convert a plugin's metadata dict into an MCPTool model.
    Falls back to sane defaults if some fields are missing.
    """
    title = meta.get("title") or meta.get("name") or plugin_name
    description = meta.get("description") or f"ForgeSyte plugin: {plugin_name}"
    inputs = meta.get("inputs") or ["image"]
    outputs = meta.get("outputs") or ["json"]

    # Convention: /v1/analyze?plugin=<plugin_name>
    invoke_endpoint = f"/v1/analyze?plugin={plugin_name}"

    return MCPTool(
        id=f"vision.{plugin_name}",
        title=title,
        description=description,
        inputs=inputs,
        outputs=outputs,
        invoke_endpoint=invoke_endpoint,
    )


def build_mcp_manifest() -> MCPManifest:
    """
    Build the MCP manifest from currently loaded plugins.
    """
    plugins = get_loaded_plugins()  # expected: dict[str, PluginInstance]
    tools: List[MCPTool] = []

    for plugin_name, plugin_instance in plugins.items():
        try:
            meta = plugin_instance.metadata()
            tool = _plugin_metadata_to_mcp_tool(plugin_name, meta)
            tools.append(tool)
        except Exception as exc:
            # You may want to log this instead of silent skip
            # For now we skip invalid plugins to keep manifest valid
            print(f"[ForgeSyte] Failed to build MCP tool for plugin '{plugin_name}': {exc}")

    server_info = MCPServerInfo(
        name=MCP_SERVER_NAME,
        version=MCP_SERVER_VERSION,
        mcp_version=MCP_PROTOCOL_VERSION,
    )

    return MCPManifest(server=server_info, tools=tools)
```

And in `server/app/api.py` or `main.py`, add:

```python
from fastapi import FastAPI
from .mcp_adapter import build_mcp_manifest

app = FastAPI()


@app.get("/v1/mcp-manifest")
def get_mcp_manifest():
    manifest = build_mcp_manifest()
    return manifest.model_json_schema() if False else manifest.model_dump()  # plain JSON
```

If you don’t like the `model_json_schema()` trick, just return `manifest.model_dump()` (that’s usually what you want).

---

### 2. `gemini_extension_manifest.json`

This is the file Gemini‑CLI will use to know about ForgeSyte as an MCP server.

```json
{
  "name": "ForgeSyte",
  "description": "Modular AI-vision MCP server exposing pluggable vision tools.",
  "version": "0.1.0",
  "mcp": {
    "manifestUrl": "http://localhost:8000/v1/mcp-manifest"
  },
  "categories": [
    "vision",
    "analysis",
    "developer-tools"
  ],
  "author": {
    "name": "ForgeSyte",
    "url": "https://example.com/forgesyte"
  }
}
```

You can refine fields to match whatever Gemini‑CLI expects exactly, but that’s the shape you want: a stable name, version, and `manifestUrl` pointing at `/v1/mcp-manifest`.

---

### 3. MCP testing script

A tiny script you can run to sanity‑check the MCP manifest and a basic analyze+jobs flow.

Put this in `server/scripts/test_mcp.py` (or wherever you like):

```python
import json
from pathlib import Path

import httpx


BASE_URL = "http://localhost:8000"


def test_manifest():
    r = httpx.get(f"{BASE_URL}/v1/mcp-manifest", timeout=5.0)
    r.raise_for_status()
    manifest = r.json()
    print("MCP manifest:")
    print(json.dumps(manifest, indent=2))

    tools = manifest.get("tools", [])
    if not tools:
        raise SystemExit("No tools found in MCP manifest. Check plugin loading.")

    print(f"Found {len(tools)} tools.")
    return tools


def test_analyze_first_tool(tools):
    tool = tools[0]
    invoke = tool.get("invoke_endpoint")
    if not invoke:
        raise SystemExit("First tool has no invoke_endpoint.")

    # For now we just check the endpoint responds; you can extend
    url = f"{BASE_URL}{invoke}"
    print(f"Testing tool {tool['id']} via {url}")

    # No file upload here; just verify API behavior
    r = httpx.post(url, timeout=5.0)
    print("Status:", r.status_code)
    print("Body:", r.text[:500])


if __name__ == "__main__":
    tools = test_manifest()
    test_analyze_first_tool(tools)
```

Run with uv:

```bash
cd server
uv run python scripts/test_mcp.py
```

You’ll extend this later to actually upload files and follow job IDs, but this is enough to prevent “oops manifest is 500’ing” situations.

---

### 4. Schema validation for plugin metadata

You already care about explicit contracts. Let’s enforce them.

Add this to `mcp_adapter.py` (or a separate `schemas.py` if you prefer):

```python
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional


class PluginMetadata(BaseModel):
    name: str = Field(..., description="Plugin name")
    description: str = Field(..., description="Short description")
    inputs: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    version: Optional[str] = None
    # you can add tags, author, etc. later


def _plugin_metadata_to_mcp_tool(plugin_name: str, meta: Dict[str, Any]) -> MCPTool:
    # validate first
    try:
        validated = PluginMetadata(**meta)
    except ValidationError as ve:
        raise ValueError(f"Invalid metadata for plugin '{plugin_name}': {ve}") from ve

    title = validated.name or plugin_name
    description = validated.description
    inputs = validated.inputs or ["image"]
    outputs = validated.outputs or ["json"]

    invoke_endpoint = f"/v1/analyze?plugin={plugin_name}"

    return MCPTool(
        id=f"vision.{plugin_name}",
        title=title,
        description=description,
        inputs=inputs,
        outputs=outputs,
        invoke_endpoint=invoke_endpoint,
    )
```

Now any plugin with broken metadata fails fast, and the MCP manifest won’t quietly drift into nonsense.

---

### 5. MCP version negotiation hook

You don’t need full negotiation yet, but you should have a clear place to plug it in later.

In `mcp_adapter.py`, we already defined:

```python
MCP_PROTOCOL_VERSION = "1.0.0"
```

You can expose a tiny endpoint:

```python
# in api.py or main.py
from fastapi import FastAPI
from .mcp_adapter import MCP_PROTOCOL_VERSION

app = FastAPI()


@app.get("/v1/mcp-version")
def get_mcp_version():
    return {"mcp_version": MCP_PROTOCOL_VERSION}
```

And later, if Gemini‑CLI starts sending something like an `X-MCP-Version` header or query parameter, you can:

- Inspect it in `/v1/mcp-manifest`  
- Decide whether to adjust the manifest (e.g., hide tools that require newer features)  
- Possibly return a 400/426 with “upgrade required” semantics  

For now, just having a single, explicit version constant and a version endpoint keeps you honest and gives you a lever.

---

If you like, next step could be:

- I draft **`plugin_loader.get_loaded_plugins()`** in a style that fits your architecture  
- Or tighten the `mcp_adapter` to whatever FastAPI patterns you already use in `api.py` / `main.py`  

Which piece do you want locked in next: `plugin_loader`, the `/v1/analyze` + `/v1/jobs` API contracts, or the React `ws.ts` side talking to this?