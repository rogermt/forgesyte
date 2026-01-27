# Plugin Data Flow Comparison: OCR vs YOLO Tracker

## Summary

| Aspect | OCR Plugin | YOLO Tracker (Video/Frame) |
|--------|-----------|---------------------------|
| **Works?** | ✅ Yes | ❌ 500 Error |
| **Input format** | `image_bytes: bytes` | `frame_base64: str` |
| **Called via** | `analyze()` method | `player_detection()` tool method |
| **Endpoint** | `/v1/analyze?plugin=ocr` (legacy) | `/v1/plugins/yolo-tracker/tools/player_detection/run` |

---

## Flow Diagrams

### OCR Flow (Working ✅)

```
Web-UI                    Server                         OCR Plugin
  │                         │                               │
  │── POST /analyze ───────>│                               │
  │   body: FormData        │                               │
  │   (image file)          │                               │
  │                         │── plugin.analyze(image_bytes) │
  │                         │   (raw bytes from file)      ─>│
  │                         │                               │── Image.open(BytesIO)
  │                         │                               │── pytesseract.ocr()
  │                         │<── AnalysisResult ────────────│
  │<── JSON response ───────│                               │
```

### YOLO Tracker Video Flow (BROKEN ❌)

```
Web-UI                         Server                         YOLO Plugin
  │                              │                               │
  │── useVideoProcessor ────────>│                               │
  │   extractFrame() →           │                               │
  │   canvas.toDataURL() →       │                               │
  │   base64 string              │                               │
  │                              │                               │
  │── POST /plugins/{id}/tools/{tool}/run ───────────────────────>│
  │   body: {                    │                               │
  │     args: {                  │                               │
  │       frame_base64: "..."    │── plugin.player_detection(   │
  │     }                        │      frame_b64=args.frame_b64)│
  │   }                          │                              ─>│
  │                              │                               │── _decode_frame_base64_safe()
  │                              │                               │   ❌ FAILS HERE?
  │                              │<── 500 Error ─────────────────│
  │<── 500 Error ────────────────│                               │
```

---

## Key Differences

### 1. Input Format

| OCR | YOLO |
|-----|------|
| `image_bytes: bytes` (raw file bytes) | `frame_base64: str` (base64 encoded) |
| Received from FormData file upload | Received from JSON body |
| `Image.open(BytesIO(image_bytes))` | `base64.b64decode() → cv2.imdecode()` |

### 2. Endpoint Used

| OCR | YOLO |
|-----|------|
| `/v1/analyze?plugin=ocr` (legacy) | `/v1/plugins/yolo-tracker/tools/player_detection/run` (new) |
| Goes through `AnalysisService` | Goes through `PluginManagementService.run_plugin_tool()` |

### 3. Method Signature

**OCR Plugin (line 113-114):**
```python
def analyze(self, image_bytes: bytes, options: Optional[dict[str, Any]] = None) -> AnalysisResult:
```

**YOLO Plugin Tool (line 359):**
```python
def player_detection(self, frame_b64: str, device: str = "cpu", annotated: bool = False) -> Dict[str, Any]:
```

### 4. How Web-UI Calls Each

**OCR (Image Upload):**
```typescript
// FormData with file
const formData = new FormData();
formData.append("file", imageFile);
fetch("/v1/analyze?plugin=ocr", { method: "POST", body: formData });
```

**YOLO (Video Frame Processing):**
```typescript
// useVideoProcessor.ts line 85-90
const payload = {
  args: {
    frame_base64: frameBase64,  // ← extracted from canvas.toDataURL()
    device,
    annotated: false,
  },
};
fetch(`/v1/plugins/${pluginId}/tools/${toolName}/run`, {
  method: "POST",
  body: JSON.stringify(payload),
});
```

---

## Shared Code Path

Both eventually reach `PluginManagementService`, but:

| Step | OCR | YOLO |
|------|-----|------|
| Entry point | `/v1/analyze` → `AnalysisService.analyze()` | `/v1/plugins/{id}/tools/{tool}/run` → `PluginManagementService.run_plugin_tool()` |
| Plugin lookup | `registry.get("ocr")` | `registry.get("yolo-tracker")` |
| Method call | `plugin.analyze(image_bytes)` | `getattr(plugin, tool_name)(**args)` |
| Args format | Raw bytes | Dict with string keys |

---

## Why OCR Works But YOLO Doesn't

### Hypothesis 1: Argument Name Mismatch

**Web-UI sends:**
```json
{ "args": { "frame_base64": "iVBOR...", "device": "cpu", "annotated": false } }
```

**Plugin method expects:**
```python
def player_detection(self, frame_b64: str, ...)  # ← frame_b64 not frame_base64
```

⚠️ **MISMATCH**: `frame_base64` vs `frame_b64`

### Hypothesis 2: No Server-Side Logging

The `/plugins/{id}/tools/{tool}/run` endpoint uses `logger.debug()` which doesn't show by default.

### Hypothesis 3: Model Loading Crash

When `player_detection()` is called, it loads YOLO model which may crash with stub models.

---

## Recommended Fixes

### Fix 1: Align Argument Names

In `plugin.py`, change:
```python
# FROM:
def player_detection(self, frame_b64: str, device: str = "cpu", annotated: bool = False)

# TO:
def player_detection(self, frame_base64: str, device: str = "cpu", annotated: bool = False)
```

### Fix 2: Add Server Logging

In `server/app/api.py` line 573, change:
```python
# FROM:
logger.debug(f"Executing tool...")

# TO:
logger.info(f"Executing tool...")
```

### Fix 3: Add Error Handling in Plugin

Wrap tool method to catch model loading errors and return JSON error instead of crashing.

---

## Test Command

To verify which flow works:

```bash
# Test OCR (should work)
curl -X POST "http://localhost:8000/v1/analyze?plugin=ocr" -F "file=@test.png"

# Test YOLO tool (broken)
curl -X POST "http://localhost:8000/v1/plugins/yolo-tracker/tools/player_detection/run" \
  -H "Content-Type: application/json" \
  -d '{"args": {"frame_base64": "iVBORw0KGgo...", "device": "cpu"}}'
```
