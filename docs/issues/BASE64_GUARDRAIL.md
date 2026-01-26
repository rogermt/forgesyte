# Issue: Add Base64 Format Guardrails to VideoTracker

## Problem

The VideoTracker was failing with **500 Internal Server Error** when processing video frames. The root cause was:

1. **Frontend Issue**: `extractFrame()` was returning `canvas.toDataURL("image/jpeg")` which includes the `data:image/jpeg;base64,` prefix
2. **Backend Issue**: The YOLO tracker plugin expected raw base64 without the prefix, causing `base64.b64decode()` to fail

## Solution

### Frontend Guardrail (Already Implemented)
**File**: `web-ui/src/hooks/useVideoProcessor.ts`

The `extractFrame()` function now strips the data URL prefix:
```typescript
const dataUrl = canvas.toDataURL("image/jpeg");
const rawBase64 = dataUrl.split(",", 2)[1];
return rawBase64;
```

**Benefits**:
- Prevents regressions
- Stops accidental prefix reintroduction
- Fails CI immediately (tests verify raw base64)

### Backend Guardrail (Already Implemented)
**File**: `plugins/forgesyte-yolo-tracker/src/forgesyte_yolo_tracker/plugin.py`

The `_decode_frame_base64()` function now defensively handles data URLs:
```python
def _decode_frame_base64(frame_b64: str) -> np.ndarray:
    # Backend Guardrail: Strip data URL prefix if present
    if frame_b64.startswith("data:"):
        logger.debug(f"Stripping data URL prefix from frame")
        frame_b64 = frame_b64.split(",", 1)[1]
    
    # Validate and decode...
```

**Benefits**:
- Makes YOLO immune to bad input
- Prevents 500 errors
- Ensures stable decoding

### Runtime Logging (Already Implemented)

**Frontend**: Console logs for fetch errors and frame processing
**Backend**: Structured logging for frame debugging

```
Decoding frame: 12345 chars, first 20: /9j/4AAQSkZJRgABAQEA...
Frame decoded successfully: shape=(1080, 1920, 3)
```

## Files Changed

### Frontend (ForgeSyte main repo)
- `web-ui/src/hooks/useVideoProcessor.ts` - Strip data URL prefix
- `web-ui/src/hooks/useVideoProcessor.test.ts` - Add guardrail tests

### Backend (forgesyte-plugins repo)
- `plugins/forgesyte-yolo-tracker/src/forgesyte_yolo_tracker/plugin.py` - Add guardrail + logging
- `plugins/forgesyte-yolo-tracker/tests/test_base64_guardrail.py` - Guardrail tests

## Branches

- **Frontend**: `blackboxai/fix/base64-format`
- **Backend**: `blackboxai/fix/base64-guardrail`

## Tests

### Frontend Tests
```bash
cd web-ui && npm test -- --run "Base64 Format Guardrail"
```

### Backend Tests
```bash
cd /home/rogermt/forgesyte-plugins
pytest plugins/forgesyte-yolo-tracker/tests/test_base64_guardrail.py -v
```

## Verification

1. **Manual Test**: Upload video, press Play, verify no 500 errors
2. **Automated Tests**: All tests pass
3. **Logs**: Check server logs for frame decoding messages

## Prevention

This guardrail setup ensures:
1. **If frontend regresses**: Backend still works (defensive)
2. **If backend regresses**: Frontend tests fail (offensive)
3. **Debugging**: Runtime logs show exactly what's being sent

## References

- Issue #101: [VideoTracker] Fix endpoint from /plugins/run to /v1/plugins/{id}/tools/{name}/run
