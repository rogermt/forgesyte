# Issue #19: Frame Validation Error - Repeating Every Second During Streaming

**Status:** Open - Needs Investigation
**Severity:** Medium (Streaming works but errors logged repeatedly)
**Reported:** 2026-01-12
**Components:** Server (vision_analysis.py), WebSocket streaming

---

## Problem Statement

When streaming video frames via WebSocket (camera streaming), the server logs a frame validation error **every second**:

```
2026-01-12 19:09:04,973 - server.app.services.vision_analysis - ERROR - Frame validation failed
2026-01-12 19:09:05,911 - server.app.services.vision_analysis - ERROR - Frame validation failed
2026-01-12 19:09:06,856 - server.app.services.vision_analysis - ERROR - Frame validation failed
2026-01-12 19:09:07,797 - server.app.services.vision_analysis - ERROR - Frame validation failed
2026-01-12 19:09:08,732 - server.app.services.vision_analysis - ERROR - Frame validation failed
```

**Related Observations:**
- ✅ Camera preview works (frames are being sent)
- ✅ File upload analysis works (separate endpoint functions correctly)
- ❌ Repeating validation errors suggest a frame format issue
- ❌ No detailed error message about *which* field or *why* validation failed

---

## Root Cause Analysis

### Hypothesis 1: Frame Data Format Mismatch

**Location:** `server/app/services/vision_analysis.py` lines 94-97

```python
if "data" not in data:
    raise ValueError("Frame data missing 'data' field")

image_bytes = base64.b64decode(data["data"])
```

**Possible Issues:**
1. Client sending frame with different field name (`image_data` vs `data`)
2. Base64 decoding failing (invalid base64 format from camera)
3. Field exists but is `None` or empty string

### Hypothesis 2: Missing Frame ID or Options

**Location:** `server/app/services/vision_analysis.py` line 90

The code uses `data.get("frame_id", ...)` safely, but unknown if other fields are causing issues.

### Hypothesis 3: Insufficient Error Logging

**Current Error Output:**
```
"Frame validation failed",
extra={"client_id": client_id, "error": str(e)}
```

**Problem:** Only shows `error: str(e)`, which might be truncated or unhelpful.

**What We Don't See:**
- Actual frame data structure (what keys are present?)
- Base64 string length or first few chars
- Which specific validation failed

---

## Investigation Checklist

To diagnose this issue, we need:

- [ ] **Server logs with full error message** - What does `str(e)` actually say?
- [ ] **Network inspection** - What does the browser send in the WebSocket frame message?
- [ ] **Client-side frame data** - Check `CameraPreview.tsx` to see how it encodes frames
- [ ] **Base64 validation** - Is the camera producing valid base64 data?

---

## Code Locations

**Server Handler:**
- `server/app/services/vision_analysis.py` - `handle_frame()` method (lines 53-150)
- Error catch: lines 123-129

**Client Sender:**
- `web-ui/src/components/CameraPreview.tsx` - Where camera frames are captured and encoded
- `web-ui/src/hooks/useWebSocket.ts` - `sendFrame()` method (lines 220-238)

**WebSocket Protocol Definition:**
- `docs/design/WEBSOCKET_PROTOCOL_SPEC.md` - Frame message format specification

---

## Expected Frame Format

Per the WebSocket protocol spec, frame message should be:

```json
{
    "type": "frame",
    "frame_id": "uuid-string",
    "image_data": "base64_encoded_jpeg_or_png_data",
    "options": {}
}
```

**Server expects:** `data["data"]` (line 97)
**Client sends:** `image_data` (per useWebSocket.ts line 231)

**⚠️ POSSIBLE MISMATCH:** Client sends `image_data` but server looks for `data` field!

---

## Proposed Fix

### Step 1: Add Detailed Error Logging

```python
except ValueError as e:
    error_msg = f"Invalid frame data: {str(e)}"
    logger.error(
        "Frame validation failed",
        extra={
            "client_id": client_id,
            "error": str(e),
            "data_keys": list(data.keys()),  # NEW: Show what fields are present
            "data_structure": str(data),      # NEW: Full data for debugging
        },
    )
```

### Step 2: Fix Field Name Mismatch

**Current code (line 97):**
```python
image_bytes = base64.b64decode(data["data"])
```

**Should be:**
```python
# Try both field names for compatibility
image_data = data.get("image_data") or data.get("data")
if not image_data:
    raise ValueError("Frame data missing 'image_data' or 'data' field")

image_bytes = base64.b64decode(image_data)
```

### Step 3: Validate Base64 Format

```python
try:
    image_bytes = base64.b64decode(image_data)
except Exception as e:
    raise ValueError(f"Invalid base64 encoding: {str(e)}")
```

---

## Testing Plan

1. **Enable debug logging** to see exact frame data structure
2. **Inspect WebSocket messages** in browser Network tab
3. **Check field names** match between client and server
4. **Test with sample base64 data** to isolate base64 decoding issues
5. **Run with detailed error logging** to confirm the fix

---

## Success Criteria

- [ ] Frame validation errors stop appearing in logs
- [ ] Or, errors provide detailed diagnostic information if validation legitimately fails
- [ ] Server log shows frames being processed successfully
- [ ] Camera streaming continues to work with no errors

---

## Impact

**Current:** Repeating error messages every second make logs noisy and hard to debug real issues

**After Fix:** Only log errors when actual validation problems occur, with clear diagnostic information

---

## Related Issues

- #17 - WebSocket infinite reconnection (FIXED)
- #18 - WebUI test coverage (PARTIALLY FIXED)

---

**Created:** 2026-01-12  
**Analysis:** Based on server logs and code inspection  
**Next Step:** Get detailed error message from server and check WebSocket message format in browser
