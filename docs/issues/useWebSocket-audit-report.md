# useWebSocket Hook — Comprehensive Audit Report

**Date:** 2026-01-25  
**Related Issue:** [#95](https://github.com/rogermt/forgesyte/issues/95)  
**File:** `web-ui/src/hooks/useWebSocket.ts`  
**Tests:** `web-ui/src/hooks/useWebSocket.test.ts`

---

## Executive Summary

The `useWebSocket` hook has a critical bug causing the frontend to hang on "Loading Manifests" when no plugin is selected. Additionally, several other bugs, test coverage gaps, and code quality issues were identified.

---

## 🔴 Critical Bug: Empty Plugin ID (Issue #95)

### Problem

The WebSocket connects even when `plugin === ""`, causing:
1. Backend accepts connection but has no plugin context
2. No manifest is sent to frontend
3. UI hangs indefinitely on "Loading Manifests"

### Root Cause

| Location | Problem |
|----------|---------|
| Line 277 | `plugin` defaults to `""` |
| Lines 414-417 | `connect()` opens WebSocket without validating plugin |
| Lines 596-597 | `useEffect` calls `connect()` unconditionally on mount |

### Expected Behavior

| Scenario | Expected UI Behavior |
|----------|---------------------|
| No plugins installed | Upload button **disabled**, no error, status `idle` |
| Plugin list loaded but none selected | Upload button **disabled**, no error, status `idle` |
| Plugin selected | Upload button **enabled**, WebSocket connects |

### Fix

Add guard at start of `connect()`:
```ts
if (!cfg.plugin?.trim()) {
  // Don't connect, stay idle - UI layer handles disabled state
  return;
}
```

---

## 🟠 Bug: Stale Closure — `hasEverConnected`

### Problem

`ws.onmessage` (lines 451-464) captures `state.hasEverConnected` at closure creation time. After `MARK_EVER_CONNECTED` dispatches in `onopen`, the closure still sees `false`, so protocol errors after successful connection may be incorrectly hidden (`userVisible: false`).

### Fix

Use a ref for `hasEverConnected`:
```ts
const hasEverConnectedRef = useRef(false);
useEffect(() => { 
  hasEverConnectedRef.current = state.hasEverConnected;
}, [state.hasEverConnected]);
// Use hasEverConnectedRef.current in event handlers
```

---

## 🟠 Bug: NaN Stats Corruption

### Problem

Lines 479-488: If `processing_time_ms` is missing or non-number, stats become `NaN`.

### Fix

Validate before use:
```ts
if (typeof result.processing_time_ms !== "number") {
  dispatch({ type: "SET_ERROR", errorInfo: { kind: "PROTOCOL", ... }});
  return;
}
```

---

## 🟡 Potential Issue: Timer Duplication

### Problem

`scheduleReconnectErrorDisplay()` is called from both `onerror` and `onclose`. If not properly cleared, late errors can surface after recovery.

### Fix

Ensure `clearTimers()` clears all timers including the delayed error display timer (it does — line 364-367).

---

## Test Coverage Gaps

| Missing Test | Priority | Description |
|--------------|----------|-------------|
| Empty plugin doesn't connect | 🔴 Critical | Assert WebSocket not created, status stays `idle` |
| Plugin change triggers connect | 🔴 High | Rerender with plugin, assert connection |
| Max retries → FAILED state | 🟠 Medium | Simulate repeated abnormal closes |
| Connection timeout fires | 🟠 Medium | Don't simulateOpen, advance timers |
| Reconnect timer canceled on unmount | 🟠 Medium | Unmount after abnormal close |
| Invalid JSON sets PROTOCOL error | 🟠 Medium | Send raw non-JSON string |
| Malformed result doesn't corrupt stats | 🟠 Medium | Missing processing_time_ms |
| Delayed error display canceled on success | 🟡 Low | onerror then simulateOpen |

---

## Test Quality Issues

| Issue | Location | Fix |
|-------|----------|-----|
| `simulateMessage` always JSON.stringifies | Lines 55-57 | Add `simulateRawMessage(raw: string)` helper |
| `MockWebSocket.close` uses `setTimeout` | Lines 43-48 | Use synchronous close or handle with fake timers |
| `Math.random` jitter not mocked | N/A | Mock for deterministic backoff tests |
| Reconnection tests don't verify constructor count | N/A | Assert `global.WebSocket` call count |

---

## Fix Priority

| Priority | Item | Effort |
|----------|------|--------|
| 🔴 P0 | Empty plugin guard (stay `idle`, don't connect) | S |
| 🔴 P0 | Test for empty plugin | S |
| 🟠 P1 | `hasEverConnected` stale closure (use ref) | S |
| 🟠 P1 | `processing_time_ms` validation | S |
| 🟡 P2 | Add missing test coverage | M |
| 🟡 P2 | Improve MockWebSocket for edge cases | M |

**Total Effort Estimate:** 2-3 hours

---

## Files to Modify

- `web-ui/src/hooks/useWebSocket.ts` — Bug fixes
- `web-ui/src/hooks/useWebSocket.test.ts` — New tests + mock improvements
- `web-ui/src/components/VideoTracker.tsx` — Disable Upload button when no plugin (UI layer)
- `web-ui/src/App.tsx` — Disable file input when no plugin selected (UI layer)

---

## Sign-off Criteria

- [ ] Empty plugin → no WebSocket attempt, status stays `idle`
- [ ] Upload button disabled when no plugin selected
- [ ] Plugin selected → WebSocket connects with correct plugin ID
- [ ] Backend logs show `"plugin": "yolo-tracker"` or `"ocr"`
- [ ] Manifests load correctly
- [ ] UI transitions past "Loading Manifests"
- [ ] All new tests pass
- [ ] Lint and type check pass
