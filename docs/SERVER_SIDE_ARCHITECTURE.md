# ForgeSyte Server-Side Architecture

This document provides a comprehensive overview of the server-side code for the ForgeSyte modular vision analysis system. It covers the client-side hooks, server endpoints, plugin system, and analysis flow.

## Table of Contents

1. [useVideoProcessor Hook](#usevideoprocessor-hook)
2. [Frame Processing (sendFrame/processFrame)](#frame-processing-sendframeprocessframe)
3. [Plugin Selection & Manifest Fetching](#plugin-selection--manifest-fetching)
4. [Analysis Trigger & Execution](#analysis-trigger--execution)
5. [API Endpoints](#api-endpoints)
6. [Service Layer Architecture](#service-layer-architecture)
7. [Plugin System](#plugin-system)

---

## useVideoProcessor Hook

**File:** `web-ui/src/hooks/useVideoProcessor.ts`

The `useVideoProcessor` hook manages video frame extraction and analysis in React applications.

### Hook Interface

```typescript
interface UseVideoProcessorArgs {
  videoRef: React.RefObject<HTMLVideoElement>;  // Reference to video element
  pluginId: string;                              // Plugin identifier
  toolName: string;                              // Tool within plugin to execute
  fps: number;                                   // Frames per second to process
  device: string;                                // Device (cpu/cuda)
  enabled: boolean;                              // Enable/disable processing
  bufferSize?: number;                           // Result buffer size (default: 5)
}

interface UseVideoProcessorReturn {
  latestResult: FrameResult | null;              // Most recent analysis result
  buffer: FrameResult[];                         // Rolling buffer of results
  processing: boolean;                           // Currently processing frame
  error: string | null;                          // Error message if failed
  lastTickTime: number | null;                   // Timestamp of last tick
  lastRequestDuration: number | null;            // Last request duration (ms)
}
```

### Frame Extraction

```typescript
const extractFrame = (): string | null => {
  const video = videoRef.current;
  if (!video || video.readyState < 2) return null;

  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;

  const ctx = canvas.getContext("2d");
  if (!ctx) return null;

  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  // Get data URL and strip the prefix to get raw base64
  const dataUrl = canvas.toDataURL("image/jpeg");
  const rawBase64 = dataUrl.split(",", 2)[1];

  return rawBase64;
};
```

### State Management

```typescript
export function useVideoProcessor({
  videoRef,
  pluginId,
  toolName,
  fps,
  device,
  enabled,
  bufferSize = 5,
}: UseVideoProcessorArgs): UseVideoProcessorReturn {
  const [latestResult, setLatestResult] = useState<FrameResult | null>(null);
  const [buffer, setBuffer] = useState<FrameResult[]>([]);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastTickTime, setLastTickTime] = useState<number | null>(null);
  const [lastRequestDuration, setLastRequestDuration] = useState<number | null>(null);

  const intervalRef = useRef<number | null>(null);
  const requestInFlight = useRef(false);
  
  // ... implementation
}
```

---

## Frame Processing (sendFrame/processFrame)

### Main Processing Loop

```typescript
const processFrame = async () => {
  if (requestInFlight.current) return;
  
  // Guard against empty pluginId or toolName
  if (!pluginId || !toolName) {
    console.error("Frame processing aborted: pluginId or toolName missing");
    return;
  }

  const frameBase64 = extractFrame();
  if (!frameBase64) return;

  requestInFlight.current = true;
  setProcessing(true);
  setLastTickTime(Date.now());

  // Build the correct endpoint URL
  const endpoint = `/v1/plugins/${pluginId}/tools/${toolName}/run`;
  
  // Payload structure matching the API spec
  const payload = {
    args: {
      frame_base64: frameBase64,
      device,
      annotated: false,
    },
  };
```

### Request with Retry Logic

```typescript
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
    // Retry once after 200ms delay
    await new Promise((r) => setTimeout(r, 200));
    response = await attempt();
  }

  const duration = performance.now() - start;
  setLastRequestDuration(duration);
```

### Response Handling

```typescript
  if (!response) {
    setError("Failed to connect to video processing service");
    requestInFlight.current = false;
    setProcessing(false);
    return;
  }

  try {
    const json = await response.json();
    
    // Handle different response formats
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
```

### Interval Management

```typescript
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
```

---

## Plugin Selection & Manifest Fetching

### Plugin Manifest Endpoint

**File:** `server/app/api.py`

```python
@router.get("/plugins/{plugin_id}/manifest")
async def get_plugin_manifest(
    plugin_id: str,
    plugin_service: PluginManagementService = Depends(get_plugin_service),
) -> Dict[str, Any]:
    """Get plugin manifest including tool schemas.

    The manifest describes what tools a plugin exposes, their input schemas,
    and output schemas. This enables the web-ui to dynamically discover and
    call tools without hardcoding plugin logic.

    Returns:
        Manifest dict:
        {
            "id": "forgesyte-yolo-tracker",
            "name": "YOLO Football Tracker",
            "version": "1.0.0",
            "description": "...",
            "tools": {
                "player_detection": {
                    "description": "...",
                    "inputs": {...},
                    "outputs": {...}
                },
                ...
            }
        }
    """
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
```

### Manifest Fetching Implementation

**File:** `server/app/services/plugin_management_service.py`

```python
def get_plugin_manifest(self, plugin_id: str) -> Optional[Dict[str, Any]]:
    """Get manifest from a loaded plugin.

    Reads the plugin's manifest.json file if available.
    """
    # Find plugin in registry by ID
    plugin = self.registry.get(plugin_id)
    if not plugin:
        return None

    # Try to read manifest.json from plugin module
    try:
        plugin_module_name = plugin.__class__.__module__
        plugin_module = sys.modules.get(plugin_module_name)
        if not plugin_module or not hasattr(plugin_module, "__file__"):
            logger.warning(f"Could not locate module for plugin '{plugin_id}'")
            return None

        module_file = plugin_module.__file__
        if not module_file:
            return None

        plugin_dir = Path(module_file).parent
        manifest_path = plugin_dir / "manifest.json"

        if not manifest_path.exists():
            logger.warning(f"No manifest.json found for plugin '{plugin_id}'")
            return None

        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        return manifest

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in manifest for '{plugin_id}': {e}")
        raise
    except Exception as e:
        logger.error(f"Error reading manifest for plugin '{plugin_id}': {e}")
        raise
```

### Plugin Selection Service

```python
async def list_plugins(self) -> List[Dict[str, Any]]:
    """List all available vision plugins with metadata."""
    try:
        plugins_dict = self.registry.list()
        plugins_list = (
            list(plugins_dict.values())
            if isinstance(plugins_dict, dict)
            else plugins_dict
        )
        return plugins_list
    except Exception as e:
        logger.exception("Failed to list plugins", extra={"error": str(e)})
        raise
```

---

## Analysis Trigger & Execution

### Tool Execution Endpoint

**File:** `server/app/api.py`

```python
@router.post(
    "/plugins/{plugin_id}/tools/{tool_name}/run",
    response_model=PluginToolRunResponse,
)
async def run_plugin_tool(
    plugin_id: str,
    tool_name: str,
    request: PluginToolRunRequest,
    plugin_service: PluginManagementService = Depends(get_plugin_service),
) -> PluginToolRunResponse:
    """Execute a plugin tool directly (synchronous).

    Runs a specified tool from a plugin with the provided arguments.
    This is a synchronous endpoint used for real-time frame processing.
    """
    try:
        # Record start time
        start_time = time.time()

        # Execute tool
        logger.debug(
            f"Executing tool '{tool_name}' on plugin '{plugin_id}' "
            f"with {len(request.args)} args"
        )

        result = plugin_service.run_plugin_tool(
            plugin_id=plugin_id, tool_name=tool_name, args=request.args
        )

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        return PluginToolRunResponse(
            tool_name=tool_name,
            plugin_id=plugin_id,
            result=result,
            processing_time_ms=processing_time_ms,
        )

    except ValueError as e:
        logger.warning(f"Tool execution validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e

    except TimeoutError as e:
        logger.error(f"Tool execution timeout: {e}")
        raise HTTPException(status_code=408, detail=str(e)) from e

    except Exception as e:
        logger.error(
            f"Unexpected error executing tool '{tool_name}' "
            f"on plugin '{plugin_id}': {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Tool execution failed: {str(e)}",
        ) from e
```

### Tool Execution Implementation

**File:** `server/app/services/plugin_management_service.py`

```python
def run_plugin_tool(
    self,
    plugin_id: str,
    tool_name: str,
    args: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute a plugin tool with given arguments."""
    # 1. Find plugin in registry
    plugin = self.registry.get(plugin_id)
    if not plugin:
        plugins_dict = self.registry.list()
        available = (
            list(plugins_dict.keys())
            if isinstance(plugins_dict, dict)
            else [getattr(p, "name", "unknown") for p in plugins_dict]
        )
        raise ValueError(f"Plugin '{plugin_id}' not found. Available: {available}")

    # 2. Validate tool exists
    if not hasattr(plugin, tool_name) or not callable(getattr(plugin, tool_name)):
        available_tools = [
            attr
            for attr in dir(plugin)
            if not attr.startswith("_") and callable(getattr(plugin, attr))
        ]
        raise ValueError(
            f"Tool '{tool_name}' not found in plugin '{plugin_id}'. "
            f"Available: {available_tools}"
        )

    # 3. Get tool function
    tool_func = getattr(plugin, tool_name)

    # 4. Execute tool (handle async/sync)
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
    except Exception as e:
        raise Exception(f"Tool execution error: {str(e)}") from e
```

### WebSocket Frame Processing

**File:** `server/app/services/vision_analysis.py`

```python
async def handle_frame(
    self, client_id: str, plugin_name: str, data: Dict[str, Any]
) -> None:
    """Process a single frame through a vision plugin."""
    # Validate plugin exists
    active_plugin = self.plugins.get(plugin_name)
    if not active_plugin:
        error_msg = f"Plugin '{plugin_name}' not found"
        await self.ws_manager.send_personal(
            client_id, {"type": "error", "message": error_msg}
        )
        return

    frame_id = data.get("frame_id", str(uuid.uuid4()))

    try:
        # Decode base64 image data
        image_data = data.get("image_data") or data.get("data")
        if not image_data:
            raise ValueError("Frame data missing required field: 'image_data' or 'data'")

        image_bytes = base64.b64decode(image_data)

        # Time the analysis execution
        start_time = time.time()
        result = active_plugin.analyze(image_bytes, data.get("options", {}))
        processing_time = (time.time() - start_time) * 1000

        # Send results back to client
        await self.ws_manager.send_frame_result(
            client_id, frame_id, plugin_name, result, processing_time
        )

    except ValueError as e:
        error_msg = f"Invalid frame data: {str(e)}"
        await self.ws_manager.send_personal(
            client_id,
            {"type": "error", "message": error_msg, "frame_id": frame_id},
        )

    except Exception as e:
        error_msg = f"Analysis failed: {str(e)}"
        await self.ws_manager.send_personal(
            client_id,
            {"type": "error", "message": error_msg, "frame_id": frame_id},
        )
```

---

## API Endpoints

### Image Analysis Endpoint

```python
@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_image(
    request: Request,
    file: Optional[UploadFile] = None,
    plugin: str = Query(..., description="Vision plugin identifier"),
    image_url: Optional[str] = Query(None, description="URL of image to analyze"),
    options: Optional[str] = Query(None, description="JSON string of plugin options"),
    auth: Dict[str, Any] = Depends(require_auth(["analyze"])),
    service: AnalysisService = Depends(get_analysis_service),
) -> Dict[str, Any]:
    """Submit an image for analysis using specified vision plugin."""
    # Validate plugin is not empty
    if not plugin or not plugin.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plugin name is required",
        )

    # Read uploaded file if provided
    file_bytes = await file.read() if file else None

    # Parse JSON options string into dict
    parsed_options: Dict[str, Any] = {}
    if options:
        try:
            parsed_options = json.loads(options)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON in options",
            ) from e

    # Delegate to service layer for analysis orchestration
    result = await service.process_analysis_request(
        file_bytes=file_bytes,
        image_url=image_url,
        body_bytes=await request.body() if not file else None,
        plugin=plugin,
        options=parsed_options,
    )

    return result
```

### Job Management Endpoints

```python
@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: str,
    auth: Dict[str, Any] = Depends(require_auth(["analyze"])),
    service: JobManagementService = Depends(get_job_service),
) -> JobResponse:
    """Retrieve status and results for a specific analysis job."""

@router.get("/jobs")
async def list_jobs(
    status: Optional[JobStatus] = None,
    plugin: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    auth: Dict[str, Any] = Depends(require_auth(["analyze"])),
    service: JobManagementService = Depends(get_job_service),
) -> Dict[str, Any]:
    """List recent analysis jobs with optional filtering."""

@router.delete("/jobs/{job_id}")
async def cancel_job(
    job_id: str,
    auth: Dict[str, Any] = Depends(require_auth(["analyze"])),
    service: JobManagementService = Depends(get_job_service),
) -> Dict[str, Any]:
    """Cancel a queued or processing analysis job."""
```

### Plugin Management Endpoints

```python
@router.get("/plugins")
async def list_plugins(
    service: PluginManagementService = Depends(get_plugin_service),
) -> Dict[str, Any]:
    """List all available vision plugins."""

@router.get("/plugins/{name}", response_model=PluginMetadata)
async def get_plugin_info(
    name: str,
    service: PluginManagementService = Depends(get_plugin_service),
) -> PluginMetadata:
    """Retrieve detailed information about a specific plugin."""

@router.post("/plugins/{name}/reload")
async def reload_plugin(
    name: str,
    auth: Dict[str, Any] = Depends(require_auth(["admin"])),
    service: PluginManagementService = Depends(get_plugin_service),
) -> Dict[str, Any]:
    """Reload a specific plugin (admin only)."""
```

---

## Service Layer Architecture

### Analysis Service

**File:** `server/app/services/analysis_service.py`

```python
class AnalysisService:
    """Service for coordinating image analysis request handling."""

    def __init__(
        self, processor: TaskProcessor, acquirer: ImageAcquisitionService
    ) -> None:
        self.processor = processor
        self.acquirer = acquirer

    async def process_analysis_request(
        self,
        file_bytes: Optional[bytes],
        image_url: Optional[str],
        body_bytes: Optional[bytes],
        plugin: str,
        options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Process an image analysis request from multiple possible sources."""
        # 1. Acquire image from appropriate source
        image_bytes = await self._acquire_image(file_bytes, image_url, body_bytes)

        if not image_bytes:
            raise ValueError("No valid image provided")

        # 2. Submit job to task processor
        job_id = await self.processor.submit_job(
            image_bytes=image_bytes, plugin_name=plugin, options=options
        )

        return {
            "job_id": job_id,
            "status": "queued",
            "plugin": plugin,
            "image_size": len(image_bytes),
        }

    async def _acquire_image(
        self,
        file_bytes: Optional[bytes],
        image_url: Optional[str],
        body_bytes: Optional[bytes],
    ) -> Optional[bytes]:
        """Acquire image bytes from the first available source."""
        # Source 1: File upload (most direct)
        if file_bytes:
            return file_bytes

        # Source 2: Remote URL (with retry logic)
        if image_url:
            return await self.acquirer.fetch_image_from_url(image_url)

        # Source 3: Base64 in request body
        if body_bytes:
            return base64.b64decode(body_bytes)

        return None
```

### Task Processor

**File:** `server/app/tasks.py`

```python
class TaskProcessor:
    """Orchestrates asynchronous image analysis task processing."""

    def __init__(
        self,
        plugin_manager: PluginRegistry,
        job_store: JobStoreProtocol,
        max_workers: int = 4,
    ):
        self.plugin_manager = plugin_manager
        self.job_store = job_store
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    async def submit_job(
        self,
        image_bytes: bytes,
        plugin_name: str,
        options: Optional[dict[str, Any]] = None,
        callback: Optional[Callable[[dict[str, Any]], Any]] = None,
    ) -> str:
        """Submit a new image analysis job."""
        if not image_bytes:
            raise ValueError("image_bytes cannot be empty")
        if not plugin_name:
            raise ValueError("plugin_name is required")

        job_id = str(uuid.uuid4())
        
        # Create job record
        job_data: dict[str, Any] = {
            "job_id": job_id,
            "status": JobStatus.QUEUED,
            "result": None,
            "error": None,
            "created_at": datetime.utcnow(),
            "completed_at": None,
            "plugin": plugin_name,
            "progress": 0.0,
        }
        await self.job_store.create(job_id, job_data)

        # Dispatch background task without blocking
        asyncio.create_task(
            self._process_job(job_id, image_bytes, plugin_name, options or {})
        )

        return job_id

    async def _process_job(
        self,
        job_id: str,
        image_bytes: bytes,
        plugin_name: str,
        options: dict[str, Any],
    ) -> None:
        """Process a job asynchronously."""
        await self.job_store.update(
            job_id, {"status": JobStatus.RUNNING, "progress": 0.1}
        )

        # Get plugin
        plugin = self.plugin_manager.get(plugin_name)
        if not plugin:
            error_msg = f"Plugin '{plugin_name}' not found"
            await self.job_store.update(
                job_id,
                {"status": JobStatus.ERROR, "error": error_msg},
            )
            return

        try:
            # Run CPU-intensive work in thread pool
            start_time = time.perf_counter()
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._executor, plugin.analyze, image_bytes, options
            )
            processing_time_ms = (time.perf_counter() - start_time) * 1000

            # Update with successful result
            result_dict = (
                result.model_dump() if hasattr(result, "model_dump") else result
            )
            await self.job_store.update(
                job_id,
                {
                    "status": JobStatus.DONE,
                    "result": {**result_dict, "processing_time_ms": processing_time_ms},
                    "completed_at": datetime.utcnow(),
                    "progress": 1.0,
                },
            )

        except Exception as e:
            await self.job_store.update(
                job_id,
                {
                    "status": JobStatus.ERROR,
                    "error": f"Unexpected error: {str(e)}",
                    "completed_at": datetime.utcnow(),
                },
            )
```

---

## Plugin System

### Plugin Interface Protocol

**File:** `server/app/plugin_loader.py`

```python
@runtime_checkable
class PluginInterface(Protocol):
    """Protocol defining the plugin contract."""

    name: str

    def metadata(self) -> Dict[str, Any]:
        """Return plugin metadata."""
        ...

    def analyze(
        self, image_bytes: bytes, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze an image and return results."""
        ...

    def on_load(self) -> None:
        """Called when plugin is loaded."""
        ...

    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        ...
```

### Base Plugin Implementation

```python
class BasePlugin(ABC):
    """Base class for plugins with common functionality."""

    name: str = "base"
    version: str = "1.0.0"
    description: str = "Base plugin"

    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=2)

    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def analyze(
        self, image_bytes: bytes, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        pass

    async def analyze_async(
        self, image_bytes: bytes, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Async wrapper for analysis."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, self.analyze, image_bytes, options or {}
        )

    def on_load(self) -> None:
        """Called when plugin is loaded."""
        logger.info("Plugin loaded", extra={"plugin_name": self.name})

    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        logger.info("Plugin unloaded", extra={"plugin_name": self.name})
        self._executor.shutdown(wait=False)

    def validate_image(self, image_bytes: bytes) -> bool:
        """Validate image data format."""
        if not image_bytes or len(image_bytes) < 100:
            return False
        headers: Dict[bytes, str] = {
            b"\xff\xd8\xff": "jpeg",
            b"\x89PNG": "png",
            b"GIF8": "gif",
            b"RIFF": "webp",
        }
        for header in headers:
            if image_bytes[: len(header)] == header:
                return True
        return False
```

### Plugin Manager

```python
class PluginManager:
    """Manages plugin discovery, loading, and lifecycle."""

    def __init__(self) -> None:
        self.plugins: Dict[str, PluginInterface] = {}

    def load_plugins(self) -> Dict[str, Dict[str, str]]:
        """Load all plugins from entry points."""
        loaded: Dict[str, str] = {}
        errors: Dict[str, str] = {}

        ep_loaded, ep_errors = self.load_entrypoint_plugins()
        loaded.update(ep_loaded)
        errors.update(ep_errors)

        return {"loaded": loaded, "errors": errors}

    def get(self, name: str) -> Optional[PluginInterface]:
        """Get a plugin by name."""
        return self.plugins.get(name)

    def list(self) -> Dict[str, Dict[str, Any]]:
        """List all plugins with their metadata."""
        result = {}
        for name, plugin in self.plugins.items():
            metadata = plugin.metadata()
            if hasattr(metadata, "model_dump"):
                metadata = metadata.model_dump()
            result[name] = metadata
        return result

    def reload_plugin(self, name: str) -> bool:
        """Reload a specific plugin."""
        if name in self.plugins:
            plugin = self.plugins[name]
            try:
                plugin.on_unload()
            except Exception as e:
                logger.warning(f"Error during plugin unload: {e}")
            del self.plugins[name]
            return True
        return False

    def reload_all(self) -> Dict[str, Dict[str, str]]:
        """Reload all plugins."""
        for plugin in self.plugins.values():
            try:
                plugin.on_unload()
            except Exception as e:
                logger.warning(f"Error unloading plugin: {e}")
        self.plugins.clear()
        return self.load_plugins()
```

### Manifest Cache Service

**File:** `server/app/services/manifest_cache_service.py`

```python
class ManifestCacheEntry:
    """Single cached manifest with TTL."""

    def __init__(self, manifest: Dict[str, Any], ttl_seconds: int = 300):
        self.manifest = manifest
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds

    def is_expired(self) -> bool:
        age = time.time() - self.created_at
        return age > self.ttl_seconds


class ManifestCacheService:
    """Cache plugin manifests with TTL."""

    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, ManifestCacheEntry] = {}
        self._lock = threading.RLock()

    def get(
        self,
        plugin_id: str,
        loader_func: Callable[[str], Optional[Dict[str, Any]]],
    ) -> Optional[Dict[str, Any]]:
        """Get manifest from cache or load from disk."""
        with self._lock:
            # Check cache
            if plugin_id in self._cache:
                entry = self._cache[plugin_id]
                if not entry.is_expired():
                    return entry.manifest
                else:
                    del self._cache[plugin_id]

            # Cache miss or expired, load from disk
            manifest = loader_func(plugin_id)

            if manifest:
                entry = ManifestCacheEntry(manifest, self.ttl_seconds)
                self._cache[plugin_id] = entry

            return manifest

    def clear(self, plugin_id: Optional[str] = None) -> None:
        """Clear cache entry or entire cache."""
        with self._lock:
            if plugin_id:
                if plugin_id in self._cache:
                    del self._cache[plugin_id]
            else:
                self._cache.clear()
```

---

## Data Flow Diagram

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Video HTML    │────▶│  useVideoProcessor│────▶│  /v1/plugins/   │
│   Element       │     │   (React Hook)   │     │  {id}/tools/    │
└─────────────────┘     └────────┬─────────┘     │  {tool}/run     │
                                 │               └────────┬────────┘
                    extractFrame()│                        │
                                 │                        ▼
                        ┌────────▼─────────┐     ┌─────────────────┐
                        │  canvas.toDataURL│     │  run_plugin_tool│
                        │  → base64 string │     │  (API Handler)  │
                        └──────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
                                          ┌─────────────────────────┐
                                          │ PluginManagementService │
                                          │ .run_plugin_tool()      │
                                          └────────────┬────────────┘
                                                       │
                                         ┌─────────────┴─────────────┐
                                         ▼                           ▼
                        ┌────────────────────────┐    ┌─────────────────────┐
                        │ PluginRegistry.get()   │    │ Tool Function       │
                        │ (find plugin)          │    │ (plugin.detect())   │
                        └───────────┬────────────┘    └─────────────────────┘
                                    │
                        ┌───────────▼───────────┐
                        │ async/sync execution  │
                        │ with timeout          │
                        └───────────────────────┘
```

---

## Request/Response Examples

### Tool Execution Request

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

### Tool Execution Response

```json
{
  "tool_name": "player_detection",
  "plugin_id": "forgesyte-yolo-tracker",
  "result": {
    "detections": [
      {
        "x1": 100,
        "y1": 200,
        "x2": 150,
        "y2": 350,
        "confidence": 0.92,
        "class": "player"
      }
    ],
    "processing_time_ms": 42
  },
  "processing_time_ms": 45
}
```

---

## Error Handling

### Common Errors

| Error Code | Description | Handling |
|------------|-------------|----------|
| 400 | Invalid arguments | Validate input, check manifest schema |
| 404 | Plugin/tool not found | Check plugin availability |
| 408 | Tool execution timeout | Reduce frame rate or optimize |
| 500 | Internal server error | Check server logs |

### Retry Logic

```typescript
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

let response = await attempt();
if (!response) {
  await new Promise((r) => setTimeout(r, 200));
  response = await attempt();
}
```

---

## Summary

This document covers the complete server-side architecture for the ForgeSyte vision analysis system:

1. **useVideoProcessor Hook**: Handles frame extraction from video, base64 encoding, and API calls
2. **Frame Processing**: Implements retry logic, error handling, and result buffering
3. **Plugin Selection & Manifest**: Dynamic plugin discovery via manifest.json files
4. **Analysis Trigger**: Synchronous tool execution via REST API
5. **API Endpoints**: RESTful endpoints for analysis, job management, and plugin operations
6. **Service Layer**: Modular services for analysis, job processing, and plugin management
7. **Plugin System**: Protocol-based plugin interface with dynamic loading and lifecycle management

All components work together to provide a scalable, extensible vision analysis platform with real-time frame processing capabilities.

