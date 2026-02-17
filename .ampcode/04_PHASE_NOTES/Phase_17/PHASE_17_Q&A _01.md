

---

# ⭐ 1. **WebSocket Implementation Choice**

### ✅ Use a **new SessionManager**, not the existing ConnectionManager.

**Why:**

- `ConnectionManager` is built for **topic‑based broadcast**, not per‑connection state.
- Phase‑17 requires **isolated, ephemeral, per‑connection session state**.
- Backpressure, frame counters, timestamps, and dropped‑frame metrics must be **per session**, not global.
- Reusing ConnectionManager would create cross‑session leakage and violate Phase‑17’s isolation model.

**Decision:**  
✔ Keep `ConnectionManager` untouched  
✔ Implement `SessionManager` exactly as Phase‑17 docs specify

---

# ⭐ 2. **VideoFilePipelineService API**

### The correct approach is:

### ✅ Add a new method: `run_on_frame(pipeline_id, frame_bytes)`

**Why:**

- Phase‑15 pipeline is already the canonical inference engine.
- Phase‑17 must reuse Phase‑15 logic, not bypass it.
- A new service would duplicate logic and create drift.
- Calling DAG pipeline directly from WebSocket would break layering.

**Decision:**  
✔ Extend `VideoFilePipelineService` with `run_on_frame()`  
✔ Internally call the DAG pipeline exactly as Phase‑15 does  
✔ Keep Phase‑15 as the single source of truth

---

# ⭐ 3. **Pipeline Selection**

### The cleanest, most stable approach is:

### ✅ Pipeline ID is provided as a **query parameter** when connecting.

Example:

```
ws://localhost:8000/ws/video/stream?pipeline_id=yolo_ocr
```

**Why:**

- WebSocket protocols don’t have a “first message handshake” standard.
- Query params are simple, explicit, and stateless.
- Avoids per‑frame overhead.
- Avoids mixing control messages with frame messages.

**Decision:**  
✔ Use query parameter  
✔ Validate pipeline_id on connect  
✔ Reject connection if invalid

---

# ⭐ 4. **Backpressure Thresholds**

### These values should be:

### ✅ Configurable via environment variables  
### ❗ But default to the values in the Phase‑17 docs

**Defaults:**

- Drop threshold: **10%**
- Slow‑down threshold: **30%**

**Why:**

- Different hardware will behave differently.
- Contributors need tunable thresholds for testing.
- Defaults give deterministic behavior.

**Decision:**  
✔ Use env vars:  
`STREAM_DROP_THRESHOLD=0.10`  
`STREAM_SLOWDOWN_THRESHOLD=0.30`  
✔ Fall back to defaults if unset

---

# ⭐ 5. **Frame Size Limit**

### Same rule as backpressure:

### ✅ Configurable, but default to **5MB**

**Why 5MB:**

- Safe for 640×480 JPEG at quality 0.8  
- Prevents memory exhaustion  
- Matches typical webcam frame sizes  

**Decision:**  
✔ Use env var: `STREAM_MAX_FRAME_SIZE_MB=5`  
✔ Default to 5MB

---

# ⭐ 6. **Concurrent Sessions**

### Phase‑17 target:

### ✅ Support **10 concurrent sessions** on typical dev hardware  
### ❗ No hard limit enforced in code  
### ❗ But configurable via env var

**Why:**

- 10 sessions is realistic for CPU‑only inference.
- Phase‑17 is not distributed or GPU‑accelerated.
- Hard limits belong in Phase‑18+.

**Decision:**  
✔ Document “10 sessions recommended”  
✔ No enforced limit  
✔ Add optional env var: `STREAM_MAX_SESSIONS`

---

# ⭐ 7. **Performance Targets**

### < 40ms round‑trip is:

### ✅ A best‑effort target  
### ❗ Not a strict requirement  
### ❗ No performance tests required in Phase‑17

**Why:**

- Performance varies by hardware.
- Phase‑17 is functional, not performance‑critical.
- Phase‑18+ (GPU scheduling) will change performance characteristics anyway.

**Decision:**  
✔ Document the target  
✔ No automated performance tests  
✔ Manual verification only

---

# ⭐ 8. **Testing Framework**

### Use the existing pattern:

### ✅ `TestClient.websocket_connect`  
### ❗ No new testing framework  
### ❗ No async test harness required

**Why:**

- Existing WebSocket tests already use this pattern.
- It’s stable, simple, and works with FastAPI.
- Keeps Phase‑17 consistent with the rest of the repo.

**Decision:**  
✔ Follow existing WebSocket test structure  
✔ Add tests under `server/tests/websocket/`  
✔ Use the same fixture patterns

---

# ⭐ Final Summary (All Decisions Locked In)

| Question | Decision |
|---------|----------|
| WebSocket manager | New SessionManager (not ConnectionManager) |
| Pipeline API | Add `run_on_frame()` to VideoFilePipelineService |
| Pipeline selection | Query parameter on connect |
| Backpressure thresholds | Configurable, defaults 10% / 30% |
| Frame size limit | Configurable, default 5MB |
| Concurrent sessions | Target 10, no hard limit |
| Performance target | Best‑effort, no perf tests |
| Testing pattern | Use existing TestClient websocket tests |

---

Roger, these decisions keep Phase‑17:

- deterministic  
- governed  
- consistent with Phase‑15/16  
- easy to test  
- easy to maintain  
- future‑proof for Phase‑18  

