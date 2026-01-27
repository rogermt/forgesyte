# Server-Side Code Reference

## 1. useVideoProcessor Hook

**File:** `web-ui/src/hooks/useVideoProcessor.ts`

```typescript
import { useEffect, useRef, useState } from "react";

export type FrameResult = Record<string, unknown>;

interface UseVideoProcessorArgs {
  videoRef: React.RefObject<HTMLVideoElement>;
  pluginId: string;
  toolName: string;
  fps: number;
  device: string;
  enabled: boolean;
  bufferSize?: number;
}

export function useVideoProcessor({
  videoRef,
  pluginId,
  toolName,
  fps,
  device,
  enabled,
  bufferSize = 5,
}: UseVideoProcessorArgs) {
  const [latestResult, setLatestResult] = useState<FrameResult | null>(null);
  const [buffer, setBuffer] = useState<FrameResult[]>([]);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastTickTime, setLastTickTime] = useState<number | null>(null);
  const [lastRequestDuration, setLastRequestDuration] = useState<number | null>(null);

  const intervalRef = useRef<number | null>(null);
  const requestInFlight = useRef(false);

  // Extract frame as base64
  const extractFrame = (): string | null => {
    const video = videoRef.current;
    if (!video || video.readyState < 2) return null;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");
    if (!ctx) return null;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const dataUrl = canvas.toDataURL("image/jpeg");
    return dataUrl.split(",", 2)[1];
  };

  // ... processFrame implementation below
}
```

---

## 2. sendFrame() / processFrame()

**File:** `web-ui/src/hooks/useVideoProcessor.ts`

```typescript
  const processFrame = async () => {
    if (requestInFlight.current) return;
    
    if (!pluginId || !toolName) {
      console.error("Frame processing aborted: pluginId or toolName missing");
      return;
    }

    const frameBase64 = extractFrame();
    if (!frameBase64) return;

    requestInFlight.current = true;
    setProcessing(true);
    setLastTickTime(Date.now());

    const endpoint = `/v1/plugins/${pluginId}/tools/${toolName}/run`;
    
    const payload = {
      args: {
        frame_base64: frameBase64,
        device,
        annotated: false,
      },
    };

    const attempt = async (): Promise<Response | null> => {
      try {
        return await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      } catch (err) {
        console.error("Frame processing fetch error:", err);
        return null;
      }
    };

    const start = performance.now();
    let response = await attempt();

    if (!response) {
      await new Promise((r) => setTimeout(r, 200));
      response = await attempt();
    }

    const duration = performance.now() - start;
    setLastRequestDuration(duration);

    if (!response) {
      setError("Failed to connect to video processing service");
      requestInFlight.current = false;
      setProcessing(false);
      return;
    }

    try {
      const json = await response.json();
      
      if (response.ok && json.success !== false) {
        const result = json.result || json;
        setLatestResult(result);
        setBuffer((prev) => {
          const next = [...prev, result];
          return next.length > bufferSize ? next.slice(-bufferSize) : next;
        });
        setError(null);
      } else {
        setError(json.detail || json.error || `HTTP ${response.status}: Request failed`);
      }
    } catch {
      setError("Invalid response from video processing service");
    }

    requestInFlight.current = false;
    setProcessing(false);
  };

  // Interval management
  useEffect(() => {
    if (!enabled) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = null;
      return;
    }

    const interval = Math.max(1, Math.floor(1000 / fps));
    intervalRef.current = window.setInterval(processFrame, interval);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [enabled, fps, device, pluginId, toolName]);

  return { latestResult, buffer, processing, error, lastTickTime, lastRequestDuration };
}
```

---

## 3. Plugin Selection + Manifest Fetch

**File:** `server/app/api.py`

```python
@router.get("/plugins/{plugin_id}/manifest")
async def get_plugin_manifest(
    plugin_id: str,
    plugin_service: PluginManagementService = Depends(get_plugin_service),
) -> Dict[str, Any]:
    """Get plugin manifest including tool schemas."""
    try:
        manifest = plugin_service.get_plugin_manifest(plugin_id)
        if not manifest:
            raise HTTPException(
                status_code=404,
                detail=f"Plugin '{plugin_id}' not found or has no manifest",
            )
        return manifest
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting manifest for plugin '{plugin_id}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error reading manifest: {str(e)}",
        ) from e


@router.get("/plugins")
async def list_plugins(
    service: PluginManagementService = Depends(get_plugin_service),
) -> Dict[str, Any]:
    """List all available vision plugins."""
    plugins = await service.list_plugins()
    return {
        "plugins": [PluginMetadata(**meta) for meta in plugins],
        "count": len(plugins),
    }
```

**File:** `server/app/services/plugin_management_service.py`

```python
def get_plugin_manifest(self, plugin_id: str) -> Optional[Dict[str, Any]]:
    """Get manifest from a loaded plugin (reads manifest.json)."""
    plugin = self.registry.get(plugin_id)
    if not plugin:
        return None

    try:
        plugin_module_name = plugin.__class__.__module__
        plugin_module = sys.modules.get(plugin_module_name)
        if not plugin_module or not hasattr(plugin_module, "__file__"):
            return None

        module_file = plugin_module.__file__
        if not module_file:
            return None

        plugin_dir = Path(module_file).parent
        manifest_path = plugin_dir / "manifest.json"

        if not manifest_path.exists():
            return None

        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        return manifest

    except Exception as e:
        logger.error(f"Error reading manifest for plugin '{plugin_id}': {e}")
        raise


async def list_plugins(self) -> List[Dict[str, Any]]:
    """List all available vision plugins with metadata."""
    plugins_dict = self.registry.list()
    return list(plugins_dict.values()) if isinstance(plugins_dict, dict) else plugins_dict
```

---

## 4. Analysis Trigger (processFrame on Server)

**File:** `server/app/api.py`

```python
@router.post("/plugins/{plugin_id}/tools/{tool_name}/run")
async def run_plugin_tool(
    plugin_id: str,
    tool_name: str,
    request: PluginToolRunRequest,
    plugin_service: PluginManagementService = Depends(get_plugin_service),
) -> PluginToolRunResponse:
    """Execute a plugin tool (sync endpoint for real-time frame processing)."""
    try:
        start_time = time.time()
        
        result = plugin_service.run_plugin_tool(
            plugin_id=plugin_id, tool_name=tool_name, args=request.args
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        return PluginToolRunResponse(
            tool_name=tool_name,
            plugin_id=plugin_id,
            result=result,
            processing_time_ms=processing_time_ms,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except TimeoutError as e:
        raise HTTPException(status_code=408, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Tool execution failed: {str(e)}",
        ) from e
```

**File:** `server/app/services/plugin_management_service.py`

```python
def run_plugin_tool(
    self,
    plugin_id: str,
    tool_name: str,
    args: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute a plugin tool with given arguments."""
    plugin = self.registry.get(plugin_id)
    if not plugin:
        raise ValueError(f"Plugin '{plugin_id}' not found")

    if not hasattr(plugin, tool_name) or not callable(getattr(plugin, tool_name)):
        raise ValueError(f"Tool '{tool_name}' not found in plugin '{plugin_id}'")

    tool_func = getattr(plugin, tool_name)

    try:
        if asyncio.iscoroutinefunction(tool_func):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    asyncio.wait_for(tool_func(**args), timeout=30.0)
                )
            finally:
                loop.close()
        else:
            result = tool_func(**args)

        return result

    except asyncio.TimeoutError as e:
        raise TimeoutError(f"Tool '{tool_name}' execution exceeded 30 second timeout") from e
    except TypeError as e:
        raise ValueError(f"Invalid arguments for tool '{tool_name}': {e}") from e
```

---

## Request/Response Example

**Request:**
```json
POST /v1/plugins/forgesyte-yolo-tracker/tools/player_detection/run
Content-Type: application/json

{
  "args": {
    "frame_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
    "device": "cpu",
    "annotated": false
  }
}
```

**Response:**
```json
{
  "tool_name": "player_detection",
  "plugin_id": "forgesyte-yolo-tracker",
  "result": {
    "detections": [{"x1": 100, "y1": 200, "x2": 150, "y2": 350, "confidence": 0.92}],
    "processing_time_ms": 42
  },
  "processing_time_ms": 45
}
```

