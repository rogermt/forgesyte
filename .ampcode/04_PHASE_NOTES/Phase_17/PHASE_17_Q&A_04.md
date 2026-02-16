

---

### 1. Prometheus integration approach

Go with your instinct.

**Decision: Option A — `prometheus_client` directly.**

- Use:
  ```python
  from prometheus_client import Counter, Gauge
  ```
- Expose metrics via whatever endpoint Phase‑18/ops decides later.
- Phase‑17 only owns:
  - defining counters/gauges
  - incrementing them in the WebSocket handler.

---

### 2. `is_valid_pipeline()` implementation

We want the **pipeline validity check** to live where the rest of the DAG orchestration logic lives.

**Decision: Option B — delegate to `DagPipelineService.is_valid_pipeline()`.**

If `DagPipelineService.is_valid_pipeline()` doesn’t exist yet, add it there and then:

```python
@staticmethod
def is_valid_pipeline(pipeline_id: str) -> bool:
    return DagPipelineService.is_valid_pipeline(pipeline_id)
```

So:

- Add `is_valid_pipeline()` to `DagPipelineService` if missing.
- `VideoFilePipelineService.is_valid_pipeline()` is a thin delegator.

---

### 3. `run_on_frame()` method signature

We want consistency with `run_on_file()` and room for future state.

**Decision: Option A — instance method.**

```python
def run_on_frame(
    self,
    pipeline_id: str,
    frame_index: int,
    frame_bytes: bytes,
) -> dict:
    payload = {
        "frame_index": frame_index,
        "image_bytes": frame_bytes,
    }
    return DagPipelineService.run_pipeline(pipeline_id=pipeline_id, payload=payload)
```

- Instance method.
- Same style as `run_on_file()`.
- Payload matches your confirmed Phase‑15 structure.

---

### 4. Backpressure timing measurement

We only care about **server‑side processing time**, not network RTT.

**Decision: measure from “before pipeline call” to “after pipeline result”.**

Roughly:

```python
start_ms = session.now_ms()
result = pipeline.run_on_frame(...)
end_ms = session.now_ms()
processing_time_ms = end_ms - start_ms
session.last_processed_ts = end_ms
```

- Use `processing_time_ms` for backpressure decisions.
- Do **not** include client/network time.

---

### 5. Environment variable naming

You already have a backend pattern without prefixes.

**Decision: Option A — no prefix, as already drafted.**

Use:

- `STREAM_DROP_THRESHOLD`
- `STREAM_SLOWDOWN_THRESHOLD`
- `STREAM_MAX_FRAME_SIZE_MB`
- `STREAM_MAX_SESSIONS` (if you implement it)

Read via `os.getenv(...)` with sane defaults.

---

### 6. Test directory structure

We want Phase‑17 streaming tests clearly isolated and discoverable.

**Decision: Option A — new `server/tests/streaming/` directory.**

- `server/tests/streaming/test_connect.py`
- `server/tests/streaming/test_session_manager.py`
- `server/tests/streaming/test_frame_validator.py`
- `server/tests/streaming/test_pipeline_integration.py`
- `server/tests/streaming/test_backpressure_drop.py`
- `server/tests/streaming/test_backpressure_slowdown.py`
- `server/tests/streaming/test_error_handling.py`
- `server/tests/streaming/test_logging_and_metrics.py`

Existing `websocket/` or `realtime/` tests remain untouched.

---

### 7. WebSocket route registration location

We already converged on the Phase‑17 pattern.

**Decision: Option B — new `video_stream.py` under `api_routes/routes/`.**

- File: `server/app/api_routes/routes/video_stream.py`
- Define:

  ```python
  router = APIRouter()

  @router.websocket("/ws/video/stream")
  async def video_stream(...):
      ...
  ```

- Include via your existing router aggregation (e.g. `api_router.include_router(video_stream.router)`).

No changes to existing `/v1/stream` routes.

---

### 8. FPSThrottler dynamic FPS adjustment

We want minimal change and clear semantics.

**Decision: Option B — add `setMaxFps()` to `FPSThrottler`.**

Extend:

```ts
class FPSThrottler {
  private maxFps: number;
  private getTime: () => number;
  private lastRun: number | null;

  constructor(maxFps: number, getTime = () => performance.now()) {
    this.maxFps = maxFps;
    this.getTime = getTime;
    this.lastRun = null;
  }

  setMaxFps(maxFps: number) {
    this.maxFps = maxFps;
  }

  throttle(callback: () => void) {
    const now = this.getTime();
    const minInterval = 1000 / this.maxFps;
    if (this.lastRun === null || now - this.lastRun >= minInterval) {
      this.lastRun = now;
      callback();
    }
  }
}
```

Then, on `{ "warning": "slow_down" }`, the frontend can call `throttler.setMaxFps(lowerValue)`.

---

### Quick summary of decisions

- **Prometheus:** `prometheus_client` directly.
- **`is_valid_pipeline()`:** add to `DagPipelineService`, delegate from `VideoFilePipelineService`.
- **`run_on_frame()`:** instance method, builds `{frame_index, image_bytes}` payload.
- **Backpressure timing:** server‑side processing only, around pipeline call.
- **Env vars:** `STREAM_*` without extra prefix.
- **Tests:** new `server/tests/streaming/` directory.
- **Route:** new `video_stream.py` under `api_routes/routes/`.
- **FPSThrottler:** add `setMaxFps()` for dynamic adjustment.

You’re clear to proceed with your recommendations—they now *are* the canonical decisions.