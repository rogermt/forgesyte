# Issue #231: Race Condition Analysis

## Summary

This document provides a deep analysis of the proposed fix for Issue #231, a race condition in the video job status tracking that causes the UI to get stuck at 95% even after successful job completion.

---

## Root Cause Analysis

### The Claimed Problem

The proposed fix identifies a **race condition** caused by:

1. **Browser caching** - Serving stale HTTP responses
2. **Late-reconnecting WebSocket** - Resetting UI state after completion

### Codebase Verification

#### 1. WebSocket Hook Behavior (`web-ui/src/hooks/useJobProgress.ts:47-68`)

```typescript
const [status, setStatus] = useState<"pending" | "running" | "completed" | "failed">("pending");
// ...
jobCompletedRef.current = false;  // Reset on connect
```

**Finding:** The WebSocket hook resets `status` to `"pending"` on every new connection attempt (line 136-138 in the `connect` callback). This is the core issue - when a WebSocket reconnects, it has no memory of the previous job state.

#### 2. Status Derivation Logic (`web-ui/src/components/JobStatus.tsx:68-70`)

```typescript
const useWebSocket = isConnected && wsStatus !== "pending";
const currentProgress = useWebSocket ? wsProgress?.percent ?? null : pollProgress;
const currentStatus = useWebSocket ? wsStatus : pollStatus;
```

**Finding:** The UI **unconditionally prioritizes WebSocket status** when connected. This means:
- If HTTP polling confirms `completed`
- Then WebSocket reconnects with `wsStatus = "pending"` (fresh connection)
- The UI **ignores** the confirmed completion and shows `pending`

**This is a real bug.**

#### 3. HTTP Polling Guard (`web-ui/src/components/JobStatus.tsx:78-79`)

```typescript
// Skip polling if WebSocket is connected AND not completed
if (isConnected && wsStatus !== "completed") return;
```

**Finding:** When WebSocket is connected, HTTP polling is **completely skipped**. This means:
- If WebSocket disconnects mid-job
- Reconnects after job completion
- HTTP polling never runs to fetch the final state
- WebSocket sits at "pending" forever

**This is also a real bug.**

#### 4. API Client Caching (`web-ui/src/api/client.ts:125-132`)

```typescript
async getJob(jobId: string): Promise<Job> {
    const result = (await this.fetch(`/jobs/${jobId}`)) as Record<string, unknown>;
    return result.job ? (result.job as unknown as Job) : (result as unknown as Job);
}
```

**Finding:** No cache-busting measures. The `fetch()` call uses default browser caching behavior. Through a proxy like localtunnel (`loca.lt`), cached responses are likely.

#### 5. Server-Side Cache Headers (`server/app/api_routes/routes/jobs.py`)

**Finding:** No `Cache-Control` headers are set on `/v1/jobs/{job_id}` endpoint. FastAPI defaults allow caching.

---

## Proposed Fix Evaluation

### Fix 1: Cache-Busting in API Client

**Proposed Change:**
```typescript
const result = (await this.fetch(`/jobs/${jobId}?_t=${Date.now()}`, {
    cache: "no-store"
})) as Record<string, unknown>;
```

**Assessment: ✅ VALID AND CORRECT**

| Aspect | Evaluation |
|--------|------------|
| **Effectiveness** | `cache: "no-store"` forces browser to bypass cache |
| **Redundancy** | Query param `_t` is belt-and-suspenders (good for proxies) |
| **Compatibility** | Standard Fetch API, works in all modern browsers |
| **Performance Impact** | Minimal - only affects job status polling |

**Recommendation:** This fix should be implemented. It addresses the caching layer of the race condition.

---

### Fix 2: Terminal State Locking

**Proposed Change:**
```typescript
const isDone = pollStatus === "completed" || pollStatus === "failed";
const useWebSocket = !isDone && isConnected && wsStatus !== "pending";
const currentStatus = isDone ? pollStatus : (useWebSocket ? wsStatus : pollStatus);
```

**Assessment: ✅ VALID AND CORRECT**

| Aspect | Evaluation |
|--------|------------|
| **Logic Correctness** | Once HTTP confirms completion, WebSocket can't override |
| **State Machine** | Implements proper terminal state transitions |
| **Error Handling** | Includes `failed` as terminal state |
| **Race Prevention** | Eliminates the "late reconnect" race |

**However, there's a subtle issue:**

The current code **skips HTTP polling when WebSocket is connected** (line 78-79). If we lock on `pollStatus`, but polling never ran because WebSocket was connected, we never get the lock.

**Missing Piece:** The fix adds `pollStatus` to the dependency array but doesn't ensure polling runs when WebSocket reconnects mid-completion.

---

## Gap Analysis

### What the Proposed Fix Misses

1. **WebSocket Reconnect After Completion**
   
   Scenario:
   1. Job completes at 100%
   2. WebSocket broadcasts completion
   3. WebSocket disconnects
   4. User refreshes page or navigates back
   5. WebSocket reconnects with `status = "pending"`
   6. HTTP polling is skipped (line 78-79)
   7. UI shows "pending" forever

   **Fix:** The polling guard should check if job was already seen as completed.

2. **Server-Side Cache Headers**

   The proposed fix only addresses client-side caching. Through localtunnel proxies, intermediate caches may still serve stale responses.

   **Recommendation:** Add `Cache-Control: no-store` on the server-side `/v1/jobs/{job_id}` endpoint.

---

## Recommended Implementation

### Change 1: API Client Cache-Busting (Frontend)

**File:** `web-ui/src/api/client.ts`

```typescript
async getJob(jobId: string): Promise<Job> {
    // v0.10.1: Add cache-busting to prevent stale responses through proxies
    const result = (await this.fetch(`/jobs/${jobId}?_t=${Date.now()}`, {
        cache: "no-store"
    })) as Record<string, unknown>;
    return result.job ? (result.job as unknown as Job) : (result as unknown as Job);
}
```

### Change 2: Terminal State Locking (Frontend)

**File:** `web-ui/src/components/JobStatus.tsx`

```typescript
// Determine which source to use
// FIX: If polling confirms the job is done, lock the state
const isDone = pollStatus === "completed" || pollStatus === "failed";
const useWebSocket = !isDone && isConnected && wsStatus !== "pending";

const currentProgress = isDone
    ? (pollStatus === "completed" ? 100 : pollProgress)
    : (useWebSocket ? wsProgress?.percent ?? null : pollProgress);

const currentStatus = isDone ? pollStatus : (useWebSocket ? wsStatus : pollStatus);
const currentError = isDone ? pollError : (wsError || pollError);
```

### Change 3: Polling Guard Update (Frontend)

**File:** `web-ui/src/components/JobStatus.tsx`

```typescript
useEffect(() => {
    if (!jobId) return;

    // FIX: Stop polling forever once we reach a terminal state
    if (pollStatus === "completed" || pollStatus === "failed") return;

    // Skip polling if WebSocket is connected AND not completed
    if (isConnected && wsStatus !== "completed") return;

    // ... rest of polling logic
}, [jobId, isConnected, wsStatus, pollStatus]); // FIX: added pollStatus
```

### Change 4: Server-Side Cache Headers (Backend)

**File:** `server/app/api_routes/routes/jobs.py`

```python
from fastapi import Response

@router.get("/v1/jobs/{job_id}", response_model=JobResultsResponse)
async def get_job(job_id: UUID, db: Session = Depends(get_db)) -> JobResultsResponse:
    """Get job status and results with no-cache headers."""
    # ... existing logic ...
    
    # Set cache control headers to prevent stale responses
    response = JobResultsResponse(...)
    # Note: FastAPI Response objects need manual header setting
    # Consider using middleware or dependency injection for consistent headers
```

**Better Approach:** Add middleware for all API endpoints:

**File:** `server/app/main.py`

```python
from starlette.middleware.base import BaseHTTPMiddleware

class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/v1/jobs"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
        return response

# Add in create_app():
app.add_middleware(NoCacheMiddleware)
```

---

## Testing Strategy

### Unit Tests

1. **Test terminal state locking:**
   - Mock `pollStatus = "completed"`
   - Mock `wsStatus = "pending"` (simulating reconnect)
   - Assert `currentStatus === "completed"`

2. **Test polling guard:**
   - Mock `pollStatus = "completed"`
   - Assert polling does not continue

### Integration Tests

1. **Simulate the race condition:**
   - Start video job
   - Mock WebSocket disconnection at 95%
   - Mock HTTP polling returning `completed`
   - Mock WebSocket reconnecting with `pending`
   - Assert UI shows `completed`

2. **Simulate through proxy:**
   - Configure test environment with caching proxy
   - Verify `no-store` headers prevent caching

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Performance regression | Low | Low | Cache-busting only affects status polling |
| State inconsistency | Low | Medium | Terminal state lock prevents this |
| Proxy interference | Medium | High | Server-side headers + client-side bypass |

---

## Conclusion

The proposed fix is **correct in principle** but **incomplete in implementation**.

**What works:**
- Cache-busting query parameter
- `cache: "no-store"` option
- Terminal state locking concept

**What needs improvement:**
- Ensure polling runs at least once after WebSocket reconnect
- Add server-side cache headers for defense-in-depth
- Consider persisting job status in localStorage for page refresh scenarios

**Verdict:** Implement the proposed fixes with the additional recommendations above. The root cause analysis is accurate, and the solution approach is sound.
