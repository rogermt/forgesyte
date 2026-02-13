Roger, this is exactly the kind of precision I love — tightening the system until it’s mechanically safe, unambiguous, and future‑proof.  
Let’s walk through each clarification with **crisp, authoritative answers**, aligned with:

- Your Phase‑15 scope  
- Your Phase‑14 boundaries  
- Your repo structure  
- Your governance rules  
- Your “no Phase‑names in functional code” rule  

I’ll keep everything functional, explicit, and deterministic.

---

# ⭐ **PHASE‑15 CLARIFICATIONS — DEFINITIVE ANSWER SET**

---

# 🔷 API DESIGN

### **Q9 — Exact HTTP status codes?**  
**A9:**

| Scenario | Status Code | Reason |
|---------|-------------|--------|
| Invalid file type | **400 Bad Request** | Client error: unsupported content‑type |
| Invalid pipeline_id | **404 Not Found** | The resource (pipeline) does not exist |

This matches your Phase‑14 API semantics.

---

### **Q10 — Success response structure?**  
**A10:**

Return **only**:

```json
{ "results": [...] }
```

No `status`, no `ok`, no metadata.  
Phase‑15 is intentionally minimal.

---

# 🔷 PAYLOAD STRUCTURE

### **Q11 — YOLO→OCR type flow: exact type names?**  
**A11:**

YOLO output type (Phase‑14 standard):

```json
{
  "detections": [
    {
      "bbox": [x1, y1, x2, y2],
      "confidence": 0.92,
      "class": "text"
    }
  ]
}
```

OCR input type:

```json
{
  "image_bytes": "<JPEG bytes>",
  "detections": [...]
}
```

OCR output type:

```json
{
  "text": "Hello world",
  "regions": [
    { "bbox": [...], "text": "Hello" }
  ]
}
```

These names match your existing plugin contracts.

---

### **Q12 — Additional payload fields?**  
**A12:**

**No.**  
Only:

- `frame_index`
- `image_bytes`

Everything else is plugin‑internal.

---

# 🔷 CONFIGURATION

### **Q13 — OpenCV codec?**  
**A13:**

Use:

```python
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
```

This is the most portable MP4 codec for your environment.

---

### **Q14 — Temp file cleanup strategy?**  
**A14:**

- Use `NamedTemporaryFile(delete=False)`  
- Wrap processing in `try/finally`  
- In `finally`, call:

```python
tmp_path.unlink(missing_ok=True)
```

If the process crashes, OS cleanup handles the orphaned file.  
This is acceptable for Phase‑15 (no persistence, no job queue).

---

### **Q15 — Temp file location?**  
**A15:**

Use the system default temp directory:

```python
NamedTemporaryFile(delete=False, suffix=".mp4")
```

Do **not** create a custom folder.  
This avoids permission issues and keeps Phase‑15 simple.

---

# 🔷 TESTING

### **Q16 — Exact MP4 generator code?**  
**A16:**

Use this exact OpenCV snippet:

```python
import cv2
import numpy as np
from pathlib import Path

def generate_tiny_mp4(path: Path):
    width, height = 320, 240
    fps = 5
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))

    for i in range(3):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        cv2.putText(
            frame,
            f"Frame {i}",
            (50, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        writer.write(frame)

    writer.release()
```

This produces a deterministic 3‑frame 320×240 MP4.

---

### **Q17 — Exact pytest assertions?**  
**A17:**

Use:

```python
assert resp.status_code == 200
data = resp.json()
assert "results" in data
assert isinstance(data["results"], list)
assert len(data["results"]) >= 1

first = data["results"][0]
assert "frame_index" in first
assert "result" in first
assert isinstance(first["result"], dict)
```

This matches your Phase‑14 test style.

---

### **Q18 — Additional invalid scenarios to test?**  
**A18:**

Test these:

1. **Empty file upload**  
2. **Corrupted MP4** (write random bytes)  
3. **Missing pipeline_id**  
4. **Missing file field**  
5. **Non‑MP4 but video MIME type** (e.g., `video/avi`)  
6. **Pipeline exists but plugin missing** (simulate by renaming plugin folder temporarily)

These catch real‑world edge cases.

---

# 🔷 GOVERNANCE

### **Q19 — Forbidden vocabulary scanning: how exactly?**  
**A19:**

Scan **only** these functional paths:

```
server/app/api/routes/
server/app/services/
server/app/tests/video/
```

Load forbidden terms from YAML:

```yaml
forbidden_terms:
  - "\\bjob_id\\b"
  - "\\bqueue\\b"
  - "\\bworker\\b"
  ...
```

Then in Python:

```python
import yaml, re

with open("server/tools/forbidden_vocabulary.yaml") as f:
    vocab = yaml.safe_load(f)["forbidden_terms"]

for pattern in vocab:
    if re.search(pattern, file_text):
        fail(...)
```

This guarantees no Phase‑16 vocabulary leaks into Phase‑15 code.

---

### **Q20 — VSCode YAML structure for cSpell warnings?**  
**A20:**

Use this exact structure:

```
.vscode/settings.json
```

```json
{
  "cSpell.ignoreRegExpList": [
    "/\\bjob_id\\b/",
    "/\\bqueue\\b/",
    "/\\bworker\\b/",
    "/\\bbackground\\b/",
    "/\\basyncio\\b/",
    "/\\bcelery\\b/",
    "/\\brq\\b/",
    "/\\bredis\\b/",
    "/\\brabbitmq\\b/",
    "/\\bdatabase\\b/",
    "/\\bdb\\b/",
    "/\\bsql\\b/",
    "/\\bpostgres\\b/",
    "/\\bmongodb\\b/",
    "/\\binsert_one\\b/",
    "/\\bupdate_one\\b/",
    "/\\breid\\b/",
    "/\\btrack\\b/",
    "/\\btracking\\b/",
    "/\\btrack_ids\\b/",
    "/\\bmetrics\\b/",
    "/\\bexecution_time_ms\\b/",
    "/\\bperformance\\b/",
    "/\\bwebsocket\\b/",
    "/\\bstream\\b/",
    "/\\bstreaming\\b/"
  ]
}
```

This warns contributors in real time.

---



Just tell me.