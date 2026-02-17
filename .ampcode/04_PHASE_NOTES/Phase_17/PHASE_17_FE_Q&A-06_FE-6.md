Refined FE-6 Questions (After Codebase Analysis)
After reading the codebase and Phase 17 documentation, here are my refined questions where I'm less than 90% confident:

1. How to clear the error? ⚠️
Found: No clearError() method exists in useRealtimeContext() or useWebSocket
Found: useWebSocket has CLEAR_ERROR action for errorInfo but not for lastError
Question: Should I add a clearError() method to the context, or should errors auto-clear when connect() is called?
Impact: Affects Retry button implementation
2. How to get currentPipelineId for Retry? ⚠️
Found: useRealtime() tracks pipelineId internally in state but doesn't expose it
Found: Context doesn't have currentPipelineId in RealtimeState
Found: Test skeleton shows connect() called without arguments, but actual signature is connect(pipelineId: string)
Question: Should I add currentPipelineId to RealtimeState, or should connect() accept optional pipelineId to reconnect to current?
Impact: Retry button won't work without knowing which pipeline to reconnect to
3. Should ErrorBanner be modified or wrapped? ⚠️
Found: Existing ErrorBanner.tsx has props: message, title, onDismiss, showDismiss
Question: Should I modify the existing component to add Phase-17 functionality, or create a new Phase17ErrorBanner/wrapper?
Impact: Affects backward compatibility and component structure
4. Error display timing ⚠️
Found: No specification on when errors should be dismissed
Question: Should errors auto-dismiss, auto-clear on reconnect, or persist until user action?
Impact: Affects UX and error handling flow
5. Test skeleton inconsistency ⚠️
Found: Test skeleton shows connect() without arguments, but actual signature requires pipelineId
Question: Is the test skeleton correct, or should it pass a pipelineId?
Impact: Tests will fail if I follow the skeleton
Summary
FE-6 has 5 areas of uncertainty (moderate)

Key Findings:

✅ ErrorBanner component exists and is well-structured
✅ Error payload structure is clear: { error: string, detail: string }
✅ Error code mapping is specified in docs
❌ No clearError() method exists
❌ No currentPipelineId exposed in context
❌ Test skeleton may be incorrect
Recommendation: I need clarification on:

How to implement error clearing (add method or auto-clear)
How to track/access current pipeline ID for retry
Whether to modify existing ErrorBanner or create new component


ANSWERS

Roger — these are *exactly* the right questions to ask before implementing FE‑6.  
Let’s settle each one cleanly so you can implement FE‑6 without ambiguity, without regressions, and without creating future architectural debt.

Below is the **final, authoritative guidance** for FE‑6.

---

# ⭐ 1. **How should errors be cleared?**  
### **Correct answer: Add `clearError()` to `useRealtime` and expose it via context.**

### Why?
- Phase‑17 errors are *sticky* unless explicitly cleared  
- Retry must clear the error before reconnecting  
- Auto‑clearing on connect() hides real failures  
- Phase‑10 error clearing is unrelated and cannot be reused  
- FE‑6 requires a deterministic, explicit user action

### Implementation:

### In `useRealtime.ts`:

```ts
const clearError = useCallback(() => {
  ws.clearError?.(); // if useWebSocket supports it
  setLastError(null);
}, [ws]);
```

### In return value:

```ts
return {
  connect,
  disconnect,
  sendFrame,
  clearError,
  state,
};
```

### In `RealtimeContext.tsx`:

Expose it:

```ts
const value = useRealtime();
```

Now FE‑6 can do:

```ts
const { clearError, connect, state } = useRealtimeContext();
```

### **Final rule:**  
✔ **Errors persist until user presses Retry**  
✘ Errors do NOT auto‑clear  
✘ Errors do NOT clear on connect()

---

# ⭐ 2. **How to get the current pipeline ID for Retry?**  
### **Correct answer: Expose `currentPipelineId` from `useRealtime`.**

### Why?
- Retry must reconnect to the *same* pipeline  
- `connect()` requires a pipelineId  
- The context currently hides it  
- FE‑5 and FE‑6 both need it  
- Test skeletons are outdated — we fix the API, not the tests

### Implementation:

### In `useRealtime.ts`:

Add to state:

```ts
const [pipelineId, setPipelineId] = useState<string | null>(null);
```

Expose it:

```ts
return {
  connect,
  disconnect,
  sendFrame,
  clearError,
  currentPipelineId: pipelineId,
  state,
};
```

### FE‑6 Retry button:

```ts
clearError();
connect(currentPipelineId);
```

### **Final rule:**  
✔ `currentPipelineId` must be exposed  
✔ Retry uses it  
✘ connect() should NOT accept optional pipelineId  
✘ Retry must NOT guess or store pipelineId elsewhere

---

# ⭐ 3. **Should ErrorBanner be modified or wrapped?**  
### **Correct answer: Wrap it — do NOT modify the existing ErrorBanner.**

### Why?
- Existing ErrorBanner is Phase‑10 UI  
- It expects props: `{ message, title, onDismiss, showDismiss }`  
- Phase‑17 errors come from realtime state, not props  
- Modifying the existing component risks breaking Phase‑10 MP4 flow  
- A wrapper keeps Phase‑10 and Phase‑17 cleanly separated

### Implementation:

Create:

```
src/components/RealtimeErrorBanner.tsx
```

This wrapper:

- Reads `state.lastError`
- Maps error codes → messages
- Calls `clearError()` + `connect(currentPipelineId)` on Retry
- Renders the existing ErrorBanner underneath

### **Final rule:**  
✔ Wrap  
✘ Do not modify the existing component  
✘ Do not create a brand‑new design

---

# ⭐ 4. **When should errors be dismissed?**  
### **Correct answer: Errors persist until user presses Retry.**

### Why?
- Auto‑dismiss hides real failures  
- Auto‑clear on reconnect hides backend issues  
- Phase‑17 is a realtime system — errors must be explicit  
- Retry is the only safe UX pattern

### Final behavior:

| Event | Should error clear? |
|-------|----------------------|
| User presses Retry | ✔ Yes |
| User changes pipeline | ✔ Yes (disconnect + connect) |
| New error arrives | ✔ Replace old error |
| connect() called manually | ✘ No |
| disconnect() | ✘ No |
| After timeout | ✘ No |

---

# ⭐ 5. **Test skeleton inconsistency: connect() without arguments**  
### **Correct answer: Test skeleton is outdated — update tests to pass pipelineId.**

### Why?
- Phase‑17 requires pipelineId  
- FE‑5 and FE‑6 rely on explicit pipeline selection  
- connect() without pipelineId is meaningless  
- Tests must reflect the real API

### Updated test call:

```ts
act(() => result.current.connect("p1"));
```

### **Final rule:**  
✔ Fix the test skeleton  
✘ Do not change connect() signature  
✘ Do not make pipelineId optional

---

# ⭐ **Final FE‑6 Implementation Rules (Authoritative)**

### ✔ Add `clearError()` to `useRealtime`  
### ✔ Expose `currentPipelineId` from `useRealtime`  
### ✔ Create `RealtimeErrorBanner.tsx` wrapper  
### ✔ Errors persist until Retry  
### ✔ Retry = `clearError()` + `connect(currentPipelineId)`  
### ✔ Update tests to pass pipelineId  
### ✘ Do NOT modify existing ErrorBanner  
### ✘ Do NOT auto‑clear errors  
### ✘ Do NOT make connect() optional  

---

Roger — perfect. Let’s lock FE‑6 down completely.  
Below you’ll find **all four deliverables**, clean, final, and ready to paste into your repo.

This is the *canonical* Phase‑17 FE‑6 implementation.

---

# ⭐ 1. **Full file skeleton: `RealtimeErrorBanner.tsx`**

This wraps the existing `ErrorBanner` component without modifying it, adds Phase‑17 logic, and wires in:

- `state.lastError`
- `clearError()`
- `currentPipelineId`
- `connect()`

Drop this into:

```
web-ui/src/components/RealtimeErrorBanner.tsx
```

---

```tsx
import React from "react";
import { useRealtimeContext } from "../realtime/RealtimeContext";
import { ErrorBanner } from "./ErrorBanner";

export function RealtimeErrorBanner() {
  const { state, clearError, connect, currentPipelineId } = useRealtimeContext();
  const err = state.lastError;

  if (!err) return null;

  // Map backend error codes → user-friendly messages
  const messageMap: Record<string, string> = {
    invalid_pipeline: "The selected pipeline is not available.",
    invalid_frame: "The video frame could not be processed.",
    frame_too_large: "The video frame is too large.",
    invalid_message: "The server received an unexpected message.",
    pipeline_failure: "The pipeline failed while processing your video.",
    internal_error: "An internal error occurred. Please try again.",
  };

  const friendlyMessage = messageMap[err.error] ?? "An unknown error occurred.";

  const handleRetry = () => {
    clearError();
    if (currentPipelineId) {
      connect(currentPipelineId);
    }
  };

  return (
    <ErrorBanner
      title="Streaming Error"
      message={friendlyMessage}
      showDismiss={true}
      onDismiss={handleRetry}
    />
  );
}
```

---

# ⭐ 2. **Updated FE‑6 Implementation Blueprint (Final)**

This is the authoritative FE‑6 plan.

---

## **FE‑6 Implementation Blueprint**

### **1. Add `clearError()` to `useRealtime.ts`**

Inside `useRealtime`:

```ts
const [lastError, setLastError] = useState<StreamingErrorPayload | null>(null);

const clearError = useCallback(() => {
  setLastError(null);
  ws.clearError?.(); // optional if useWebSocket supports it
}, [ws]);
```

Expose it:

```ts
return {
  connect,
  disconnect,
  sendFrame,
  clearError,
  currentPipelineId: pipelineId,
  state: {
    ...,
    lastError,
  },
};
```

---

### **2. Expose `currentPipelineId` from `useRealtime`**

Add:

```ts
const [pipelineId, setPipelineId] = useState<string | null>(null);
```

Expose:

```ts
currentPipelineId: pipelineId,
```

---

### **3. Update `connect()` to set pipelineId**

```ts
const connect = useCallback((newPipelineId: string) => {
  setPipelineId(newPipelineId);
}, []);
```

---

### **4. Create `RealtimeErrorBanner.tsx` wrapper**

(Already provided above.)

---

### **5. Integrate wrapper into UI**

In your main layout or streaming page:

```tsx
<RealtimeErrorBanner />
```

Place it above the video container so it overlays cleanly.

---

### **6. Error lifecycle rules**

| Event | Should error clear? |
|-------|----------------------|
| User presses Retry | ✔ Yes |
| User changes pipeline | ✔ Yes |
| New error arrives | ✔ Replace old |
| connect() | ✘ No |
| disconnect() | ✘ No |
| Timeout | ✘ No |

---

### **7. Update tests to pass pipelineId**

All FE‑6 tests must call:

```ts
act(() => result.current.connect("p1"));
```

---

# ⭐ 3. **Corrected FE‑6 Test Skeleton**

Create:

```
web-ui/src/components/RealtimeErrorBanner.test.tsx
```

---

```tsx
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { RealtimeErrorBanner } from "./RealtimeErrorBanner";

vi.mock("../realtime/RealtimeContext", () => {
  return {
    __esModule: true,
    useRealtimeContext: vi.fn(),
  };
});

import { useRealtimeContext } from "../realtime/RealtimeContext";

describe("RealtimeErrorBanner (Phase‑17)", () => {
  it("renders nothing when there is no error", () => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      state: { lastError: null },
    });

    const { container } = render(<RealtimeErrorBanner />);
    expect(container.firstChild).toBeNull();
  });

  it("renders mapped error message", () => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      state: {
        lastError: { error: "invalid_pipeline", detail: "bad id" },
      },
      clearError: vi.fn(),
      connect: vi.fn(),
      currentPipelineId: "p1",
    });

    render(<RealtimeErrorBanner />);
    expect(
      screen.getByText("The selected pipeline is not available.")
    ).toBeInTheDocument();
  });

  it("calls clearError() and connect() on Retry", () => {
    const clearError = vi.fn();
    const connect = vi.fn();

    (useRealtimeContext as vi.Mock).mockReturnValue({
      state: {
        lastError: { error: "invalid_frame", detail: "bad jpeg" },
      },
      clearError,
      connect,
      currentPipelineId: "p1",
    });

    render(<RealtimeErrorBanner />);

    fireEvent.click(screen.getByRole("button")); // ErrorBanner dismiss button

    expect(clearError).toHaveBeenCalledTimes(1);
    expect(connect).toHaveBeenCalledWith("p1");
  });
});
```

This tests:

- No error → no render  
- Error → correct message  
- Retry → clearError + connect(currentPipelineId)

---

# ⭐ 4. **Commit‑by‑Commit Git Diff Plan (FE‑6)**

This is the exact sequence you should commit in.

---

## **Commit 1 — Add error state + clearError() to useRealtime**

Files:

- `src/realtime/useRealtime.ts`

Changes:

- Add `lastError` state
- Add `clearError()`
- Expose `currentPipelineId`
- Update `connect()` to set pipelineId

---

## **Commit 2 — Update RealtimeContext to expose new fields**

Files:

- `src/realtime/RealtimeContext.tsx`

Changes:

- Ensure context value includes:
  - `clearError`
  - `currentPipelineId`

---

## **Commit 3 — Create RealtimeErrorBanner wrapper**

Files:

- `src/components/RealtimeErrorBanner.tsx` (new)

---

## **Commit 4 — Integrate RealtimeErrorBanner into streaming UI**

Files:

- `src/components/StreamingPage.tsx` or wherever CameraPreview lives

Changes:

```tsx
<RealtimeErrorBanner />
```

---

## **Commit 5 — Update FE‑6 tests**

Files:

- `src/components/RealtimeErrorBanner.test.tsx` (new)

Changes:

- Add test skeleton above
- Update any existing tests to pass pipelineId to connect()

---

## **Commit 6 — Manual QA: Golden Path Error Flow**

Checklist:

- Invalid pipeline → error banner appears  
- Retry → clears error + reconnects  
- New error replaces old  
- Error persists until Retry  

---

# ⭐ Final Summary

You now have:

- ✔ Full `RealtimeErrorBanner.tsx` file  
- ✔ Full FE‑6 implementation blueprint  
- ✔ Full FE‑6 test skeleton  
- ✔ Full commit‑by‑commit Git plan  

This is the **final, correct, Phase‑17‑aligned FE‑6 implementation**.
