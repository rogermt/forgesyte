# Phase 6B & 6C Reconstruction Plan

## Status
**DOCUMENTED FROM PRIOR ANALYSIS**. Technical specifications extracted from ampcode notes.

---

## 📋 PHASE 6 FINAL FILES TO CREATE/UPDATE

### 1. **Test Files** (8 canonical tests total)

#### `web-ui/src/hooks/__tests__/useVideoProcessor.test.ts` (5 tests)
```
- submits a frame via analyzeImage
- starts polling after job submission
- returns result when job completes
- sets error when job fails
- times out after 30s
```
Key: Uses fake timers, mocks `client.analyzeImage` + `client.pollJob`

#### `web-ui/src/components/__tests__/VideoTracker.test.tsx` (3 tests)
```
- calls useVideoProcessor with pluginId + device
- renders error from hook
- renders Processing… when hook says processing
```
Key: Spies on `useVideoProcessor` hook

---

### 2. **Implementation Files**

#### `web-ui/src/api/client.ts` (ADD METHOD)
Must include new method:
```ts
async pollJob(jobId: string, intervalMs: number, timeoutMs: number)
```
- Polls with `intervalMs` (typically 250ms)
- Times out after `timeoutMs` (30000ms = 30s)
- Returns job when `status === "done"` or `"error"`
- Throws error on timeout

#### `web-ui/src/api/normalizers.ts` (SUPPORT FILE)
Normalize backend responses:
- `normalizeDetection(raw)` → canonical Detection shape
- `normalizePitchLine(raw)` → PitchLine shape
- `normalizeJobResult(raw)` → JobResult shape
- Handles missing fields, aliases (class→label, width→w, etc.)

#### `web-ui/src/hooks/useVideoProcessor.ts` (CORE HOOK)
Signature:
```ts
function useVideoProcessor({ pluginId, device }: UseVideoProcessorProps)
```
Returns:
```ts
{
  processing: boolean
  latestResult: any | null
  error: string | null
  submitFrame: (blob: Blob) => Promise<void>
}
```
Implementation:
- Calls `client.analyzeImage(blob, pluginId)`
- Gets `jobId` from response
- Calls `client.pollJob(jobId, 250, 30000)` IMMEDIATELY (not waiting for first interval)
- Also sets interval timer for continuous polling
- Updates state on completion/error/timeout

Key Detail: **Immediate polling is intentional** (reduces latency, handles fast jobs)

---

## 📘 PHASE 7 DEFINITION
**CSS Modules Migration:**
- Convert components to use CSS modules (no logic changes)
- Create `.module.css` files next to `.tsx` files
- Replace string classNames with `styles.*`
- No behavior changes, no job pipeline changes

---

## Notes

**Blocking Issues** (prevent Phase 6B completion):
1. Plugin endpoint stability (#100, #124)
2. Job pipeline schema validation
3. Web-UI integration testing

**Current Status**: Phase 6 baseline locked. Phase 6B/6C specs documented for future implementation.
