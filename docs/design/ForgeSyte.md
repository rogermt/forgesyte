# 🚀 **How to Use ForgeSyte — Step‑by‑Step Explanation**

This is the version you can literally read aloud or paste into docs.

---

# 1. **What ForgeSyte *is***  
ForgeSyte is a **vision analysis server** that loads Python plugins (OCR, object detection, layout mapping, etc.) and exposes them as **MCP tools**.

MCP (Model Context Protocol) is what allows **Gemini‑CLI** to discover ForgeSyte and call its tools automatically.

So the simplest explanation is:

> “ForgeSyte is a pluggable vision engine that Gemini‑CLI can use as a tool.”

---

# 2. **What you need before using it**

To run ForgeSyte, you need:

- Python 3.10+  
- `uv` (Python environment + dependency manager)  
- Node.js (only if you want the React UI)  
- Gemini‑CLI (or any MCP client)

That’s it.

---

# 3. **How to start the ForgeSyte backend**

1. Clone the repo:

   ```bash
   git clone https://github.com/<your-org>/forgesyte.git
   cd forgesyte
   ```

2. Install backend dependencies:

   ```bash
   cd server
   uv sync
   ```

3. Start the server:

   ```bash
   uv run fastapi dev app/main.py
   ```

When it starts, ForgeSyte exposes:

- API base: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- MCP manifest: `http://localhost:8000/v1/mcp-manifest`

That last one is the important part.

---

# 4. **How ForgeSyte exposes MCP tools**

ForgeSyte automatically:

1. Loads all plugins from `server/app/plugins/`
2. Reads each plugin’s `metadata()`
3. Converts that metadata into MCP tool definitions
4. Serves them at:

   ```
   GET /v1/mcp-manifest
   ```

This manifest tells Gemini‑CLI:

- What tools exist  
- What they do  
- What inputs they accept  
- What outputs they return  
- Which endpoint to call  

So you can say:

> “ForgeSyte auto‑generates its MCP tool list from whatever plugins you install.”

---

# 5. **How to connect ForgeSyte to Gemini‑CLI**

This is the key step.

In your Gemini‑CLI config, add:

```json
{
  "mcpServers": {
    "forgesyte": {
      "manifestUrl": "http://localhost:8000/v1/mcp-manifest"
    }
  }
}
```

Then restart Gemini‑CLI.

Gemini will:

1. Fetch the manifest  
2. See tools like `vision.ocr`, `vision.block_mapper`, etc.  
3. Register them as callable tools  

From that point on, Gemini can call ForgeSyte automatically.

---

# 6. **What using ForgeSyte *feels like* inside Gemini**

Once Gemini knows about ForgeSyte, a user can say:

- “Use ForgeSyte to run OCR on this image.”  
- “Analyze this screenshot with the block mapper.”  
- “Extract text and summarize it.”  

Gemini will:

1. Pick the right ForgeSyte tool  
2. Send the image to `/v1/analyze?plugin=<plugin>`  
3. Wait for the job result  
4. Use the plugin’s output to answer the user  

So the user never has to think about endpoints or plugins.

---

# 7. **How a tool call works internally**

Here’s the mental model:

1. Gemini calls ForgeSyte’s analyze endpoint  
2. ForgeSyte creates a job  
3. The plugin runs  
4. ForgeSyte stores the result  
5. Gemini polls `/v1/jobs/<id>`  
6. Gemini uses the result in its answer  

You can summarize it as:

> “Gemini asks ForgeSyte to run a plugin, ForgeSyte does the work, and Gemini uses the result.”

---

# 8. **How to test ForgeSyte without Gemini**

You can demo it manually:

### Check the MCP manifest:

```bash
curl http://localhost:8000/v1/mcp-manifest | jq
```

### Run a plugin:

```bash
curl -X POST "http://localhost:8000/v1/analyze?plugin=ocr" \
     -F "file=@image.png"
```

### Poll the job:

```bash
curl http://localhost:8000/v1/jobs/<job_id>
```

This is exactly what Gemini‑CLI does behind the scenes.

---

# 9. **How plugins fit into the story**

A plugin is just a Python class:

```python
class Plugin:
    name = "ocr"

    def metadata(self): ...
    def analyze(self, image_bytes): ...
```

ForgeSyte:

- Loads it  
- Validates metadata  
- Exposes it as an MCP tool  

So you can explain:

> “To add a new capability, you just drop in a new plugin. ForgeSyte handles discovery and MCP exposure automatically.”

---

# 10. **A simple explanation you can use in conversation**

Here’s the polished version you can say to anyone:

> “ForgeSyte is a modular vision server that integrates with Gemini through MCP.  
> You run the ForgeSyte backend locally using uv. It loads all vision plugins and exposes them as MCP tools through a manifest endpoint.  
> Gemini‑CLI reads that manifest and automatically knows what tools ForgeSyte provides. When a user asks Gemini to analyze an image, Gemini calls the appropriate ForgeSyte plugin, waits for the job result, and uses that output to answer the user.  
> Adding new capabilities is as simple as writing a new plugin — ForgeSyte handles discovery, schema validation, and MCP exposure.”

---
