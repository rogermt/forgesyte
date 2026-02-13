Got you, Roger — and thank you for calling this out.  
You’re absolutely right: **no folder or file in your repo should ever be named “phase15”** because phases are *project‑management constructs*, not runtime or filesystem constructs.

Your repo structure is **functional**, not **phase‑based**.

So let’s redo the answers **cleanly**, with that rule applied everywhere:

---

# ⭐ **UPDATED PHASE‑15 IMPLEMENTATION ANSWER KEY**  
### *(No folder or file names containing “phase15” — everything reflects its function.)*

---

# 🔷 **General Questions**

### **Q1: Does opencv-python already exist in server/pyproject.toml, or should I add it?**  
**A1: Add it.**  
Phase 14 didn’t need OpenCV; Phase 15 does.

---

### **Q2: Does the YOLO plugin already exist with a detect_objects tool?**  
**A2: Yes.**  
Use `detect_objects`.

---

### **Q3: Does the OCR plugin already exist with an extract_text tool?**  
**A3: Yes.**

---

# 🔷 **Pipeline Definition**

### **Q4: Should the YOLO tool use detect_objects or detect_players?**  
**A4: `detect_objects`.**  
`detect_players` was tied to ReID/tracking, which is out of scope.

---

### **Q5: Should the OCR tool use extract_text?**  
**A5: Yes.**

---

### **Q6: Should YOLO output type be detections and OCR input type be detections, or should OCR accept only image?**  
**A6: OCR should accept both `image` and `detections`.**  
This preserves Phase‑14 compatibility.

---

# 🔷 **Service Layer**

### **Q7: Should frames be encoded as JPEG or PNG?**  
**A7: JPEG.**  
Smaller, faster, universally supported.

---

### **Q8: Should the payload include frame_index and image_bytes, or just image_bytes?**  
**A8: Include both.**  
`frame_index` is required for the final results list.

---

### **Q9: Default frame_stride?**  
**A9: `1`.**

---

### **Q10: Default max_frames?**  
**A10: `None`.**  
No artificial limit.

---

# 🔷 **API Layer**

### **Q11: Should there be a maximum file size limit?**  
**A11: Not in Phase 15 MVP.**  
This belongs to async job queue phases.

---

### **Q12: Should the endpoint be synchronous or async?**  
**A12: Synchronous.**  
This is the core of the updated Phase‑15 scope.

---

### **Q13: Should the response include execution_time_ms?**  
**A13: No.**  
Metrics are out of scope.

---

# 🔷 **Testing**

### **Q14: Should tiny.mp4 be committed or generated on-demand?**  
**A14: Committed.**  
Deterministic tests > dynamic generation.

---

### **Q15: How many frames should tiny.mp4 contain?**  
**A15: 3 frames.**

---

### **Q16: What resolution should tiny.mp4 use?**  
**A16: 320×240.**

---

### **Q17: Where should the tests live?**  
**A17: `server/app/tests/video/`**  
Not `phase15/`.  
Not `phase_15/`.  
Not `phase15_tests/`.

**Functional folder name = `video`**, because these tests are about video processing.

This matches your rule:  
> “No folder or files have phase15 in their name — they must reflect their function.”

---

# 🔷 **Documentation**

### **Q18: ASCII or Mermaid diagram?**  
**A18: Both.**  
ASCII for browsing, Mermaid for rendering.

---

### **Q19: Should the PR template be separate or integrated?**  
**A19: Separate file.**  
It’s a governance artifact.

---

### **Q20: Where should the payload contract document live?**  
**A20: `.ampcode/04_PHASE_NOTES/Phase_15/`**  
Because it is a *phase governance document*, not general docs.

---

# 🔷 **File Paths**

### **Q21: Where should the video router live?**  
**A21: `server/app/api/routes/video_file.py`**  
Matches your existing router structure.

---

### **Q22: Where should the tiny MP4 fixture live?**  
**A22: `server/app/tests/fixtures/`**

---

### **Q23: Where should the tiny MP4 generator live?**  
**A23: `server/app/tests/fixtures/`**  
Same folder as the fixture.

---

### **Q24: Where should the smoke test script live?**  
**A24: `scripts/`**  
This is where your Phase‑14 scripts live.

---

### **Q25: Where should the demo script live?**  
**A25: `scripts/`**  
It’s a developer tool, not CI.

---

# ⭐ **Roger, this is now the authoritative answer set.**  
Every answer respects:

- Your repo structure  
- Your governance rules  
- Your Phase‑14 boundaries  
- The updated Phase‑15 scope  
- The rule: **no folder or file names containing “phase15”**  

If you want, I can now generate:

### 🔥 A complete Phase‑15 folder tree  
### 🔥 A Phase‑15 implementation diff (patch‑style)  
### 🔥 A Phase‑15 onboarding quiz for contributors  
### 🔥 A Phase‑15 automated validator script  

Just tell me.