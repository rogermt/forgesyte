# Phase 10 — Plugin Timing Algorithm Spec

Precise specification for measuring, storing, and emitting plugin execution timings in real-time.

---

# 1. Overview

Plugin timing is the wall-clock duration from when a plugin starts processing a frame until it returns a result.

Timings are:
- **Measured** using a monotonic clock (immune to system clock adjustments)
- **Stored** in InspectorService
- **Emitted** as RealtimeMessages to clients
- **Accumulated** in ExtendedJobResponse

---

# 2. Timing Measurement

## 2.1 Clock Selection

**MUST use monotonic clock** (not system clock):

```python
# CORRECT: Monotonic clock (immune to system clock changes)
import time

start = time.monotonic()  # or time.perf_counter()
result = plugin.run(frame)
end = time.monotonic()

timing_ms = (end - start) * 1000.0
```

**NOT CORRECT: System clock (can jump backward)**

```python
# WRONG: System clock can drift/jump
import datetime

start = datetime.datetime.now()
result = plugin.run(frame)
end = datetime.datetime.now()

timing_ms = (end - start).total_seconds() * 1000  # NOT OK
```

## 2.2 Precision

- **Unit:** Milliseconds (ms)
- **Precision:** 1 decimal place (e.g., 145.5 ms)
- **Type:** Float (Python: `float`, TypeScript: `number`)
- **Range:** 0.0 to 999999.0 (effectively unlimited)

## 2.3 Measurement Accuracy

```python
# Timing should include:
start = time.monotonic()
  │
  ├─ 1. Plugin initialization (if any)
  ├─ 2. Frame preprocessing
  ├─ 3. Model inference
  ├─ 4. Result postprocessing
  │
end = time.monotonic()

# Do NOT include:
# - Message serialization
# - Network transmission
# - Disk I/O (unless plugin does it)
```

## 2.4 Multiple Frames per Plugin

For each frame, measure timing independently:

```python
for frame in frames:
    start = time.monotonic()
    result = plugin.run(frame)
    end = time.monotonic()
    
    timing_ms = (end - start) * 1000
    # Emit timing for this frame
```

**Note:** Do NOT average or accumulate timings in Phase 10.

---

# 3. Timing Storage

## 3.1 InspectorService Storage

```python
class InspectorService:
    def __init__(self):
        self.plugin_timings: Dict[str, float] = {}
        self.timing_start_time: Optional[float] = None
    
    def start_timing(self, plugin_name: str) -> None:
        """Start timing measurement."""
        self.timing_start_time = time.monotonic()
    
    def stop_timing(self, plugin_name: str) -> float:
        """Stop timing, store, and return duration."""
        if self.timing_start_time is None:
            raise ValueError("Timing not started")
        
        end = time.monotonic()
        timing_ms = (end - self.timing_start_time) * 1000.0
        
        # Store (overwrite previous)
        self.plugin_timings[plugin_name] = timing_ms
        
        return timing_ms
    
    def get_timings(self) -> Dict[str, float]:
        """Return all stored timings."""
        return self.plugin_timings.copy()
```

## 3.2 Storage Rules

- **One timing per plugin** (latest only)
- **Overwrite on repeated execution** (no averaging)
- **Store immediately** after measurement (no delay)
- **Accessible via `.get_timings()`**

---

# 4. Timing Emission

## 4.1 When to Emit

Emit timing in `plugin_status` message **after plugin execution completes**:

```python
# ToolRunner: After executing plugin
start = time.monotonic()
result = plugin.run(frame)
end = time.monotonic()

timing_ms = (end - start) * 1000.0

# Store timing
inspector.add_timing(plugin_name, timing_ms)

# Emit plugin_status message
message = RealtimeMessage(
    type=MessageType.PLUGIN_STATUS,
    payload={
        "plugin": plugin_name,
        "status": "completed",  # or "ok", "degraded", "error"
        "timing_ms": timing_ms,
        "frames_processed": 1
    },
    timestamp=datetime.utcnow()
)

await connection_manager.broadcast(message.dict())
```

## 4.2 Payload Format

```json
{
  "type": "plugin_status",
  "payload": {
    "plugin": "player_detection",
    "status": "completed",
    "timing_ms": 145.5,
    "frames_processed": 5,
    "warnings_count": 0
  },
  "timestamp": "2025-02-04T15:30:00.123Z"
}
```

**Fields:**
- `plugin` (string, required): Plugin name
- `status` (string, required): One of: started, running, completed, failed, degraded
- `timing_ms` (number, required): Execution time in milliseconds
- `frames_processed` (integer, optional): Number of frames processed
- `warnings_count` (integer, optional): Number of warnings

## 4.3 Emission Frequency

**Timing MUST be emitted:**
1. **Per-frame basis:** After processing each frame
2. **On plugin completion:** Final timing after all frames
3. **On error:** Even if plugin fails, emit timing if available

**Example:**
```
Frame 0: emit plugin_status with timing
Frame 1: emit plugin_status with timing
...
Frame N: emit plugin_status with timing (final)
```

---

# 5. Status Calculation from Timing

Status is derived from timing thresholds:

```python
def calculate_status(timing_ms: float) -> str:
    """Derive status from timing."""
    if timing_ms < 50:
        return "ok"
    elif timing_ms < 200:
        return "degraded"
    else:
        return "error"
```

**Thresholds (NOT governance - implementation defaults):**
- `< 50ms`: "ok" (fast)
- `50-200ms`: "degraded" (slow)
- `> 200ms`: "error" (very slow)

**Note:** These are reference defaults. Teams can adjust based on hardware.

---

# 6. Integration with ExtendedJobResponse

## 6.1 Populating Extended Model

As job executes, timings are accumulated in extended model:

```python
# In Jobs service
class ExtendedJobResponse(JobResponse):
    plugin_timings: Optional[Dict[str, float]] = None
    warnings: Optional[List[str]] = None
    progress: Optional[int] = None

# After each plugin_status message:
extended_job.plugin_timings = inspector.get_timings()
```

## 6.2 Accessing Timings via API

```
GET /v1/jobs/job-abc123/extended

Response:
{
  "job_id": "job-abc123",
  "progress": 75,
  "plugin_timings": {
    "player_detection": 145.5,
    "ball_detection": 98.2
  },
  "warnings": [...]
}
```

---

# 7. Timing Aggregation (If Needed Later)

Phase 10 does NOT require aggregation, but here's the pattern for future use:

```python
class TimingAggregator:
    def __init__(self):
        self.timings: Dict[str, List[float]] = {}  # plugin -> [timing1, timing2, ...]
    
    def add(self, plugin: str, timing_ms: float) -> None:
        if plugin not in self.timings:
            self.timings[plugin] = []
        self.timings[plugin].append(timing_ms)
    
    def average(self, plugin: str) -> float:
        times = self.timings.get(plugin, [])
        return sum(times) / len(times) if times else 0.0
    
    def median(self, plugin: str) -> float:
        times = sorted(self.timings.get(plugin, []))
        n = len(times)
        if n == 0:
            return 0.0
        if n % 2 == 1:
            return times[n // 2]
        return (times[n // 2 - 1] + times[n // 2]) / 2.0
    
    def percentile(self, plugin: str, p: float) -> float:
        """p: 0-100 (e.g., 95 for p95)"""
        times = sorted(self.timings.get(plugin, []))
        if not times:
            return 0.0
        index = int((p / 100.0) * len(times))
        return times[min(index, len(times) - 1)]
```

---

# 8. Error Handling

## 8.1 Timing Measurement Failures

```python
try:
    start = time.monotonic()
    result = plugin.run(frame)
    end = time.monotonic()
    timing_ms = (end - start) * 1000.0
except Exception as e:
    # If timing fails, emit error but don't crash
    log.error(f"Timing measurement failed: {e}")
    timing_ms = None  # or estimate based on partial data
    
    # Still emit plugin_status (with timing_ms=None if needed)
    message = RealtimeMessage(
        type=MessageType.PLUGIN_STATUS,
        payload={
            "plugin": plugin_name,
            "status": "error",
            "timing_ms": timing_ms,
            "error": str(e)
        }
    )
```

## 8.2 Invalid Timings

```python
def validate_timing(timing_ms: float) -> bool:
    """Validate timing value."""
    return isinstance(timing_ms, (int, float)) and timing_ms >= 0

if not validate_timing(timing_ms):
    log.warning(f"Invalid timing: {timing_ms}, using 0")
    timing_ms = 0.0
```

## 8.3 Extreme Values

```python
# Clamp to reasonable range
MIN_TIMING_MS = 0.0
MAX_TIMING_MS = 999999.0  # ~277 hours

timing_ms = max(MIN_TIMING_MS, min(timing_ms, MAX_TIMING_MS))
```

---

# 9. Client-Side Handling

## 9.1 Receiving Timings (TypeScript)

```typescript
// RealtimeContext reducer
case 'plugin_status': {
  const { plugin, timing_ms, status } = action.payload;
  
  return {
    ...state,
    pluginTimings: {
      ...state.pluginTimings,
      [plugin]: timing_ms  // Store latest timing
    },
    pluginStatus: {
      ...state.pluginStatus,
      [plugin]: status
    }
  };
}
```

## 9.2 Displaying Timings (React)

```typescript
// PluginInspector component
export function PluginInspector({ pluginTimings }: { pluginTimings: Record<string, number> }) {
  return (
    <div id="plugin-inspector">
      {Object.entries(pluginTimings).map(([plugin, timing]) => (
        <div key={plugin} className="plugin-item">
          <span>{plugin}</span>
          <span>{timing.toFixed(1)} ms</span>
          <div className="timing-bar" style={{ width: `${Math.min(timing, 500) / 500 * 100}%` }} />
        </div>
      ))}
    </div>
  );
}
```

## 9.3 Sorting and Filtering

```typescript
// Sort by timing (slowest first)
const sortedPlugins = Object.entries(pluginTimings)
  .sort((a, b) => b[1] - a[1])
  .map(([plugin, timing]) => ({ plugin, timing }));

// Filter slow plugins (> 100ms)
const slowPlugins = Object.entries(pluginTimings)
  .filter(([, timing]) => timing > 100)
  .map(([plugin, timing]) => ({ plugin, timing }));
```

---

# 10. Testing the Timing Algorithm

## 10.1 Unit Tests (Backend)

```python
def test_timing_measurement_accuracy():
    """Verify timing accuracy within 10%."""
    import time
    
    start = time.monotonic()
    time.sleep(0.1)  # Sleep 100ms
    end = time.monotonic()
    
    timing_ms = (end - start) * 1000.0
    
    # Should be ~100ms (±10ms)
    assert 90 < timing_ms < 110, f"Expected ~100ms, got {timing_ms}"

def test_timing_storage():
    """Verify timings stored correctly."""
    inspector = InspectorService()
    
    inspector.start_timing("player_detection")
    time.sleep(0.05)
    timing = inspector.stop_timing("player_detection")
    
    assert 40 < timing < 70, f"Expected ~50ms, got {timing}"
    assert "player_detection" in inspector.get_timings()

def test_timing_emission():
    """Verify timing emitted in plugin_status message."""
    # Mock ToolRunner and ConnectionManager
    # Execute plugin, verify message includes timing_ms
    pass

def test_timing_storage_overwrite():
    """Verify latest timing overwrites previous."""
    inspector = InspectorService()
    
    inspector.start_timing("player_detection")
    time.sleep(0.05)
    timing1 = inspector.stop_timing("player_detection")
    
    inspector.start_timing("player_detection")
    time.sleep(0.1)
    timing2 = inspector.stop_timing("player_detection")
    
    # Should have latest timing (timing2)
    assert inspector.get_timings()["player_detection"] == timing2
    assert inspector.get_timings()["player_detection"] > timing1
```

## 10.2 Integration Tests

```python
def test_e2e_plugin_timing():
    """Verify timing flows through entire system."""
    # 1. Start job
    # 2. Connect to /v1/realtime
    # 3. Verify plugin_status messages include timing_ms
    # 4. Verify ExtendedJobResponse includes plugin_timings
    pass

def test_e2e_timing_accuracy_under_load():
    """Verify timing accuracy with 1000 frames."""
    # Process 1000 frames
    # Verify timing < 5s per frame average
    pass
```

---

# 11. Performance Considerations

## 11.1 Overhead

Timing measurement overhead (monotonic clock calls):
- Per-frame: ~0.1ms (negligible)
- Total job overhead: <1% for typical jobs

## 11.2 Storage

Timing storage requirements:
- Per plugin: 8 bytes (float64)
- Per job: ~80 bytes (10 plugins)
- Negligible memory impact

## 11.3 Message Size

plugin_status message size:
```json
{
  "type": "plugin_status",
  "payload": {
    "plugin": "player_detection",       // ~20 bytes
    "status": "completed",               // ~15 bytes
    "timing_ms": 145.5,                  // ~7 bytes
    "frames_processed": 5                // ~5 bytes
  },
  "timestamp": "2025-02-04T15:30:00.123Z"  // ~30 bytes
}
```

Total: ~80-100 bytes per message (negligible)

---

# 12. Completion Criteria

The timing algorithm is complete when:

✅ Timing measured using monotonic clock
✅ Timing stored in InspectorService
✅ Timing emitted in plugin_status messages
✅ Timing included in ExtendedJobResponse
✅ Timing accuracy verified (within 10%)
✅ No timing measurement overhead (< 1%)
✅ Status calculated correctly from timing
✅ Errors handled gracefully (no crashes)
✅ Client displays timings correctly
✅ All timing tests pass (unit + integration)
✅ Performance verified (overhead minimal)

