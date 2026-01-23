# Video Tracker Web-UI Integration Plan

**Date:** Jan 2026  
**Owner:** Roger  
**Repos:** 
- forgesyte (backend + web-ui)
- forgesyte-plugins (YOLO tracker + motion_detector)

**TDD:** All changes follow test-first pattern (AGENTS.md)

---

## 📊 Current vs Target State

### Current
- `/analyze` endpoint (job-based, async, polling)
- `/plugins` list (GET)
- `/jobs/{id}` polling
- Web-UI hardcoded result extraction (boxes, radar)
- Video support: none

### Target
- **NEW:** `/plugins/{id}/manifest` endpoint (tool schemas)
- **NEW:** `/plugins/{id}/tools/{tool_name}/run` endpoint (direct tool execution, sync)
- Web-UI generic tool selector (discovers tools from manifest)
- Web-UI video frame processor (extracts + sends frames)
- Web-UI plugin-agnostic result renderer
- Both YOLO (frame-based) and motion_detector (streaming) supported

---

## 🎯 Critical Design Decisions

### 1. Two execution paths (not one)
| Mode | Endpoint | Use Case | Response |
|------|----------|----------|----------|
| **Job** | `/analyze` | Batch, long-running | Job ID + polling |
| **Direct** | `/plugins/{id}/tools/{tool}/run` | Real-time, video | JSON immediately |

### 2. No plugin-specific hardcoding
- Tool names come from manifest
- Result renderers loaded from plugin.json `entrypoints`
- Overlay logic generic (boxes, points, etc.)

### 3. Manifest is contract
- Frozen: tool names, input schema, output schema
- Changes to tool signature = new plugin version

---

## 📋 Phase 1: Backend `/plugins/{id}/manifest` endpoint

### Files to Modify
1. `forgesyte/server/app/api.py`
2. `forgesyte/server/app/services/plugin_management_service.py`
3. `forgesyte/server/tests/api/test_plugins.py`

### What to Add

#### Endpoint: `GET /plugins/{id}/manifest`

**Location:** `forgesyte/server/app/api.py` (after line 381)

```python
@router.get("/plugins/{id}/manifest")
async def get_plugin_manifest(
    plugin_id: str,
    plugin_service: PluginManagementService = Depends(get_plugin_service),
) -> Dict[str, Any]:
    """Get plugin manifest including tool schemas.
    
    Args:
        plugin_id: Plugin ID (e.g., "forgesyte-yolo-tracker")
        plugin_service: Service for plugin management
    
    Returns:
        Manifest dict with:
        {
            "name": "forgesyte-yolo-tracker",
            "version": "1.0.0",
            "description": "...",
            "tools": {
                "player_detection": {
                    "description": "...",
                    "inputs": {"frame_base64": "string", ...},
                    "outputs": {"detections": "array", ...}
                },
                ...
            }
        }
    
    Raises:
        HTTPException(404): Plugin not found
    """
    try:
        manifest = plugin_service.get_plugin_manifest(plugin_id)
        if not manifest:
            raise HTTPException(
                status_code=404,
                detail=f"Plugin '{plugin_id}' not found or has no manifest"
            )
        return manifest
    except Exception as e:
        logger.error(f"Error getting manifest for {plugin_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### Service Method: `PluginManagementService.get_plugin_manifest()`

**Location:** `forgesyte/server/app/services/plugin_management_service.py`

```python
def get_plugin_manifest(self, plugin_id: str) -> Optional[Dict[str, Any]]:
    """Get manifest from loaded plugin.
    
    Reads plugin's manifest.json if available.
    
    Args:
        plugin_id: Plugin ID
    
    Returns:
        Manifest dict or None if not found
    """
    plugin = self.get_plugin(plugin_id)
    if not plugin:
        return None
    
    # Try to read manifest.json from plugin module
    try:
        import json
        from pathlib import Path
        
        # Get plugin module path
        plugin_module = sys.modules.get(plugin.__module__)
        if not plugin_module:
            return None
        
        plugin_dir = Path(plugin_module.__file__).parent
        manifest_path = plugin_dir / "manifest.json"
        
        if manifest_path.exists():
            with open(manifest_path) as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load manifest for {plugin_id}: {e}")
    
    return None
```

#### Test

**Location:** `forgesyte/server/tests/api/test_plugins.py`

```python
def test_get_plugin_manifest(client):
    """Test GET /plugins/{id}/manifest returns tool schema."""
    response = client.get("/v1/plugins/forgesyte-yolo-tracker/manifest")
    
    assert response.status_code == 200
    manifest = response.json()
    
    assert "tools" in manifest
    assert "player_detection" in manifest["tools"]
    assert "inputs" in manifest["tools"]["player_detection"]
    assert "outputs" in manifest["tools"]["player_detection"]


def test_get_plugin_manifest_not_found(client):
    """Test 404 for nonexistent plugin."""
    response = client.get("/v1/plugins/nonexistent/manifest")
    assert response.status_code == 404
```

---

## 📋 Phase 2: Backend `/plugins/{id}/tools/{tool}/run` endpoint

### Files to Modify
1. `forgesyte/server/app/api.py`
2. `forgesyte/server/app/services/plugin_management_service.py`
3. `forgesyte/server/tests/api/test_plugins.py`

### What to Add

#### Data Model

**Location:** `forgesyte/server/app/models.py`

```python
from pydantic import BaseModel

class PluginToolRunRequest(BaseModel):
    """Request to run a plugin tool."""
    args: Dict[str, Any]  # {"frame_base64": "...", "device": "cpu", ...}


class PluginToolRunResponse(BaseModel):
    """Response from running a plugin tool."""
    tool_name: str
    plugin_id: str
    result: Dict[str, Any]  # Tool output
    processing_time_ms: int
```

#### Endpoint: `POST /plugins/{id}/tools/{tool}/run`

**Location:** `forgesyte/server/app/api.py`

```python
@router.post("/plugins/{id}/tools/{tool}/run", response_model=PluginToolRunResponse)
async def run_plugin_tool(
    plugin_id: str,
    tool: str,
    request: PluginToolRunRequest,
    plugin_service: PluginManagementService = Depends(get_plugin_service),
) -> PluginToolRunResponse:
    """Execute a plugin tool directly (synchronous).
    
    Args:
        plugin_id: Plugin ID (e.g., "forgesyte-yolo-tracker")
        tool: Tool name (e.g., "player_detection")
        request: Tool arguments
    
    Returns:
        PluginToolRunResponse with result
    
    Raises:
        HTTPException(404): Plugin or tool not found
        HTTPException(400): Invalid arguments
        HTTPException(500): Execution failed
    
    Example:
        POST /v1/plugins/forgesyte-yolo-tracker/tools/player_detection/run
        {
            "args": {
                "frame_base64": "iVBORw0KGgo...",
                "device": "cpu",
                "annotated": false
            }
        }
    """
    try:
        start_time = time.time()
        
        result = plugin_service.run_plugin_tool(
            plugin_id=plugin_id,
            tool_name=tool,
            args=request.args
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return PluginToolRunResponse(
            tool_name=tool,
            plugin_id=plugin_id,
            result=result,
            processing_time_ms=processing_time
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error running tool {tool} on {plugin_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### Service Method: `PluginManagementService.run_plugin_tool()`

**Location:** `forgesyte/server/app/services/plugin_management_service.py`

```python
def run_plugin_tool(
    self, 
    plugin_id: str, 
    tool_name: str,
    args: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute a plugin tool with given arguments.
    
    Args:
        plugin_id: Plugin ID
        tool_name: Tool name (must match manifest)
        args: Tool arguments (matches manifest input schema)
    
    Returns:
        Tool result (dict, matches manifest output schema)
    
    Raises:
        ValueError: Plugin/tool not found or invalid args
    """
    plugin = self.get_plugin(plugin_id)
    if not plugin:
        raise ValueError(f"Plugin '{plugin_id}' not found")
    
    # Get plugin's tool function
    # Assumes plugin module has functions named like: player_detection, ball_detection, etc.
    tool_func = getattr(plugin, tool_name, None)
    if not tool_func or not callable(tool_func):
        raise ValueError(
            f"Tool '{tool_name}' not found in plugin '{plugin_id}'. "
            f"Check manifest and plugin module."
        )
    
    # Execute tool (may be async)
    if asyncio.iscoroutinefunction(tool_func):
        # For async tools, run in executor
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(tool_func(**args))
    else:
        # Sync execution
        result = tool_func(**args)
    
    return result
```

#### Test

**Location:** `forgesyte/server/tests/api/test_plugins.py`

```python
def test_run_plugin_tool_player_detection(client, mock_plugin):
    """Test POST /plugins/{id}/tools/{tool}/run executes tool."""
    response = client.post(
        "/v1/plugins/test-plugin/tools/player_detection/run",
        json={
            "args": {
                "frame_base64": "test_base64_data",
                "device": "cpu",
                "annotated": False
            }
        }
    )
    
    assert response.status_code == 200
    result = response.json()
    
    assert result["tool_name"] == "player_detection"
    assert result["plugin_id"] == "test-plugin"
    assert "result" in result
    assert "processing_time_ms" in result


def test_run_plugin_tool_not_found(client):
    """Test 404 for nonexistent tool."""
    response = client.post(
        "/v1/plugins/test-plugin/tools/nonexistent/run",
        json={"args": {}}
    )
    assert response.status_code == 400 or response.status_code == 404
```

---

## 📋 Phase 3: Web-UI API client additions

### Files to Modify
1. `forgesyte/web-ui/src/api/client.ts`

### What to Add

```typescript
export class ForgeSyteAPIClient {
  // ... existing methods ...

  async getPluginManifest(pluginId: string): Promise<any> {
    """Get plugin manifest with tool schemas."""
    const result = await this.fetch(`/plugins/${pluginId}/manifest`);
    return result;
  }

  async runPluginTool(
    pluginId: string,
    toolName: string,
    args: Record<string, any>
  ): Promise<{
    tool_name: string;
    plugin_id: string;
    result: Record<string, any>;
    processing_time_ms: number;
  }> {
    """Execute a plugin tool directly (synchronous)."""
    const result = await this.fetch(
      `/plugins/${pluginId}/tools/${toolName}/run`,
      {
        method: "POST",
        body: JSON.stringify({ args }),
      }
    );
    return result as any;
  }
}
```

---

## 📋 Phase 4: Web-UI components

### Phase 4.1: `useVideoProcessor` hook

**File:** `forgesyte/web-ui/src/hooks/useVideoProcessor.ts`

```typescript
interface UseVideoProcessorProps {
  pluginId: string;
  toolName: string;
  device?: string;
  annotated?: boolean;
  fps?: number;
}

interface ProcessedFrame {
  frameIndex: number;
  frameId: string;
  result: Record<string, any>;
  processing_time_ms: number;
  timestamp: number;
}

export function useVideoProcessor(options: UseVideoProcessorProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [frames, setFrames] = useState<ProcessedFrame[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Extract frame from <video> element + convert to base64
  const extractFrameBase64 = useCallback(
    (videoElement: HTMLVideoElement): string => {
      const canvas = document.createElement("canvas");
      canvas.width = videoElement.videoWidth;
      canvas.height = videoElement.videoHeight;

      const ctx = canvas.getContext("2d");
      if (!ctx) throw new Error("Could not get canvas context");

      ctx.drawImage(videoElement, 0, 0);
      const dataUrl = canvas.toDataURL("image/jpeg", 0.8);
      return dataUrl.split(",")[1]; // Remove "data:image/jpeg;base64,"
    },
    []
  );

  // Send frame to backend tool
  const processFrame = useCallback(
    async (frameBase64: string, frameIndex: number) => {
      try {
        setIsProcessing(true);
        setError(null);

        const response = await apiClient.runPluginTool(
          options.pluginId,
          options.toolName,
          {
            frame_base64: frameBase64,
            device: options.device || "cpu",
            annotated: options.annotated || false,
          }
        );

        const processed: ProcessedFrame = {
          frameIndex,
          frameId: `frame-${Date.now()}-${frameIndex}`,
          result: response.result,
          processing_time_ms: response.processing_time_ms,
          timestamp: Date.now(),
        };

        setFrames((prev) => [...prev, processed]);
        return processed;
      } catch (err) {
        const errMsg =
          err instanceof Error ? err.message : "Processing failed";
        setError(errMsg);
        throw err;
      } finally {
        setIsProcessing(false);
      }
    },
    [options]
  );

  return {
    isProcessing,
    frames,
    error,
    extractFrameBase64,
    processFrame,
  };
}
```

**Test:** `forgesyte/web-ui/src/hooks/useVideoProcessor.test.ts` (TDD)

### Phase 4.2: `ToolSelector` component

**File:** `forgesyte/web-ui/src/components/ToolSelector.tsx`

```typescript
interface ToolSelectorProps {
  pluginId: string;
  selectedTool: string;
  onToolChange: (toolName: string) => void;
  disabled?: boolean;
}

export function ToolSelector({
  pluginId,
  selectedTool,
  onToolChange,
  disabled,
}: ToolSelectorProps) {
  const [manifest, setManifest] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadManifest = async () => {
      try {
        setLoading(true);
        const data = await apiClient.getPluginManifest(pluginId);
        setManifest(data);
        setError(null);

        // Auto-select first tool if none selected
        if (!selectedTool && data.tools) {
          const firstTool = Object.keys(data.tools)[0];
          onToolChange(firstTool);
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load manifest"
        );
      } finally {
        setLoading(false);
      }
    };

    loadManifest();
  }, [pluginId, selectedTool, onToolChange]);

  if (loading) return <div>Loading tools...</div>;
  if (error) return <div style={{ color: "red" }}>Error: {error}</div>;
  if (!manifest) return <div>No manifest</div>;

  const tools = Object.keys(manifest.tools || {});

  return (
    <div>
      <label>Tool:</label>
      <select
        value={selectedTool}
        onChange={(e) => onToolChange(e.target.value)}
        disabled={disabled}
      >
        {tools.map((tool) => (
          <option key={tool} value={tool}>
            {tool}
          </option>
        ))}
      </select>

      {selectedTool && manifest.tools[selectedTool] && (
        <div style={{ fontSize: "12px", marginTop: "8px", color: "#999" }}>
          <p>{manifest.tools[selectedTool].description}</p>
        </div>
      )}
    </div>
  );
}
```

**Test:** `forgesyte/web-ui/src/components/ToolSelector.test.tsx` (TDD)

### Phase 4.3: `VideoTracker` page component

**File:** `forgesyte/web-ui/src/pages/VideoTracker.tsx`

```typescript
export function VideoTracker() {
  const [selectedPlugin, setSelectedPlugin] = useState("");
  const [selectedTool, setSelectedTool] = useState("");
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  const { isProcessing, frames, error, extractFrameBase64, processFrame } =
    useVideoProcessor({
      pluginId: selectedPlugin,
      toolName: selectedTool,
      device: "cpu",
      fps: 2, // 2 FPS for video
    });

  const handleVideoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setVideoFile(file);
      if (videoRef.current) {
        videoRef.current.src = URL.createObjectURL(file);
      }
    }
  };

  const handleProcessFrame = async () => {
    if (!videoRef.current || !selectedPlugin || !selectedTool) {
      alert("Select plugin, tool, and load video first");
      return;
    }

    const frameBase64 = extractFrameBase64(videoRef.current);
    await processFrame(frameBase64, frames.length);
  };

  return (
    <div style={{ padding: "20px" }}>
      <h1>Video Tracker</h1>

      <div style={{ marginBottom: "20px" }}>
        <PluginSelector
          selectedPlugin={selectedPlugin}
          onPluginChange={setSelectedPlugin}
          disabled={isProcessing}
        />
      </div>

      {selectedPlugin && (
        <div style={{ marginBottom: "20px" }}>
          <ToolSelector
            pluginId={selectedPlugin}
            selectedTool={selectedTool}
            onToolChange={setSelectedTool}
            disabled={isProcessing}
          />
        </div>
      )}

      <div style={{ marginBottom: "20px" }}>
        <label>Upload Video:</label>
        <input type="file" accept="video/*" onChange={handleVideoUpload} />
      </div>

      <video
        ref={videoRef}
        controls
        style={{ maxWidth: "100%", marginBottom: "20px" }}
      />

      <button
        onClick={handleProcessFrame}
        disabled={isProcessing || !videoFile || !selectedTool}
      >
        {isProcessing ? "Processing..." : "Process Frame"}
      </button>

      {error && <div style={{ color: "red" }}>Error: {error}</div>}

      {frames.length > 0 && (
        <div style={{ marginTop: "20px" }}>
          <h2>Results ({frames.length} frames)</h2>
          {frames.map((frame) => (
            <div key={frame.frameId} style={{ marginBottom: "16px" }}>
              <div>Frame #{frame.frameIndex}</div>
              <div>{frame.processing_time_ms}ms</div>
              <pre style={{ fontSize: "11px", overflow: "auto" }}>
                {JSON.stringify(frame.result, null, 2)}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

**Test:** `forgesyte/web-ui/src/pages/VideoTracker.test.tsx` (TDD)

---

## 📊 Implementation Order

### Week 1: Backend
- [ ] Phase 1: `/plugins/{id}/manifest` endpoint + tests
- [ ] Phase 2: `/plugins/{id}/tools/{tool}/run` endpoint + tests
- [ ] Integration test: Upload image frame, get detections

### Week 2: Web-UI
- [ ] Phase 4.1: `useVideoProcessor` hook + tests
- [ ] Phase 4.2: `ToolSelector` component + tests
- [ ] Phase 4.3: `VideoTracker` page + tests
- [ ] Integration test: Upload video, process frames, view results

### Week 3: Polish
- [ ] Add FPS control
- [ ] Add overlay canvas (boxes on video)
- [ ] Add result toggles (players/ball/pitch/radar)
- [ ] Motion_detector WebSocket support

---

## ❓ Questions Needing Answers

1. **Async tool execution:** Should `/plugins/{id}/tools/{tool}/run` be truly sync or can it spawn a background job?
2. **Frame size limits:** Max frame size for base64 in request body? (Suggest: 10MB)
3. **Plugin discovery:** Should manifest be cached or fetched on each request?
4. **Result renderers:** Should plugin.json point to custom result components, or use generic overlay?
5. **Error handling:** If tool fails mid-stream, stop or skip frame?
6. **Batch processing:** Support multiple frames in one request? Or one-at-a-time?

---

## 📝 Git Workflow

```bash
# Backend
cd forgesyte/server
git checkout -b feature/video-tracker-endpoints

# TDD: Write tests first
uv run pytest tests/api/test_plugins.py -v  # Should fail

# Implement
# ... modify api.py, plugin_management_service.py ...

# Tests pass
uv run pytest tests/api/test_plugins.py -v

# Quality checks
uv run ruff check app/ --fix
uv run black app/
uv run mypy app/

# Commit
git add .
git commit -m "feat(plugins): Add /plugins/{id}/manifest and /plugins/{id}/tools/{tool}/run endpoints"

# Web-UI
cd forgesyte/web-ui
git checkout -b feature/video-tracker-components

# Similar TDD flow...
npm run test  # TDD fails
# ... implement components ...
npm run test  # Pass
npm run lint
npm run type-check

git commit -m "feat(video): Add VideoTracker page, ToolSelector, useVideoProcessor"
```

---

## ✅ Definition of Done

- [ ] All tests pass (backend + web-ui)
- [ ] No TypeScript errors (`type-check` passes)
- [ ] Linting clean (`ruff`, `eslint`)
- [ ] API documented (docstrings + comments)
- [ ] Integration test: video upload → frame processing → results displayed
- [ ] No hardcoded plugin names in web-ui
- [ ] Plugin manifest discovery works
- [ ] Both YOLO and motion_detector discoverable

---

**Ready to implement?**
