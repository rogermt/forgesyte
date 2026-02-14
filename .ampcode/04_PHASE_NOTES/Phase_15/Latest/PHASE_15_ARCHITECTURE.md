# ⭐ **1. POSTER‑STYLE INFOGRAPHIC (TEXT‑ONLY)**  
### *Phase 15 — YOLO + OCR Batch Edition*  
### *Offline MP4 Processing • Stateless • Governance‑Enforced*

```
┌──────────────────────────────────────────────────────────────────────┐
│                         PHASE 15 — AT A GLANCE                       │
│                 YOLO → OCR OFFLINE VIDEO BATCH PIPELINE              │
└──────────────────────────────────────────────────────────────────────┘
```

```
                   INPUT (MP4)
            ┌──────────────────────┐
            │  Client uploads MP4  │
            └───────────┬──────────┘
                        │
                        ▼
        ┌──────────────────────────────────────────┐
        │       FASTAPI ROUTER (SYNCHRONOUS)       │
        │  /video/upload-and-run                   │
        │  - Validates file type                   │
        │  - Stores temp file                      │
        │  - Stateless, offline-only               │
        └───────────────────┬──────────────────────┘
                            │
                            ▼
        ┌──────────────────────────────────────────┐
        │      VIDEOFILEPIPELINESERVICE            │
        │  - OpenCV frame extraction               │
        │  - JPEG encoding (raw bytes)             │
        │  - Payload: {frame_index, image_bytes}   │
        │  - Calls DAG per frame                   │
        └───────────────────┬──────────────────────┘
                            │
                            ▼
        ┌──────────────────────────────────────────┐
        │           DAG PIPELINE (YOLO → OCR)      │
        │  yolo_ocr.json                           │
        │  - detect_objects                         │
        │  - extract_text                           │
        │  Deterministic per-frame execution        │
        └───────────────────┬──────────────────────┘
                            │
                            ▼
        ┌──────────────────────────────────────────┐
        │              FINAL RESPONSE               │
        │  { "results": [ {frame_index, result} ] }│
        │  Schema frozen to prevent drift           │
        └──────────────────────────────────────────┘
```

```
┌──────────────────────────────────────────────────────────────────────┐
│                         GOVERNANCE GUARANTEES                        │
└──────────────────────────────────────────────────────────────────────┘
✔ No phase‑named files in functional directories  
✔ Phase‑named scripts allowed ONLY in scripts/  
✔ No job queues, persistence, tracking, or async  
✔ Forbidden vocabulary validator  
✔ Schema regression guard  
✔ Golden snapshot  
✔ Smoke test pipeline  
```

---

# ⭐ **2. DEVELOPER ONBOARDING PLACEMAT**  
### *A one‑page “everything you need to know to contribute safely” sheet*

```
┌──────────────────────────────────────────────────────────────┐
│                   PHASE 15 — DEV PLACEMAT                    │
└──────────────────────────────────────────────────────────────┘
```

### **Core Files to Know**
```
server/app/pipelines/yolo_ocr.json
server/app/services/video_file_pipeline_service.py
server/app/api/routes/video_file.py
```

### **Run the Endpoint**
```
curl -X POST http://localhost:8000/video/upload-and-run \
  -F "file=@tiny.mp4;type=video/mp4" \
  -F "pipeline_id=yolo_ocr"
```

### **Run All Video Tests**
```
pytest server/app/tests/video -q
```

### **Run the Smoke Test**
```
scripts/smoke_test_video_batch.sh
```

### **Governance Rules**
```
❌ No phase‑named files in server/app/** or server/tools/**
❌ No job queues, persistence, tracking, async
✔ Phase‑named scripts allowed only in scripts/
✔ Payload = {frame_index, image_bytes}
✔ Response = {results: [...]}
```

### **What Breaks CI**
```
• Adding extra fields to the response
• Using base64 instead of raw JPEG bytes
• Forgetting to clean up temp files
• Violating naming rules
• Forbidden vocabulary (job_id, queue, redis, websocket)
```

### **Tests You Must Pass**
```
✔ Unit tests (pure)
✔ Integration tests
✔ Error tests (422, 400, 404)
✔ Schema regression guard
✔ Golden snapshot
✔ Stress + fuzz tests
✔ Governance validator
✔ Smoke test
```

---

# ⭐ **3. PHASE‑15 ARCHITECTURE ASCII DIAGRAM (DETAILED)**

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           PHASE 15 ARCHITECTURE                            │
└────────────────────────────────────────────────────────────────────────────┘
```

```
User
  │
  ▼
┌──────────────────────────────────────────────────────────────┐
│ FastAPI Router: /video/upload-and-run                        │
│ - Validates multipart form                                   │
│ - Validates content type (mp4/quicktime)                     │
│ - Writes temp file                                           │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│ VideoFilePipelineService                                     │
│ - cap = cv2.VideoCapture(file)                               │
│ - for each frame:                                            │
│       ok, frame = cap.read()                                 │
│       if ok:                                                 │
│           _, buf = cv2.imencode(".jpg", frame)               │
│           payload = {frame_index, image_bytes}               │
│           dag_result = dag.run_pipeline("yolo_ocr", payload) │
│           results.append({frame_index, result})              │
│ - cap.release()                                              │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│ DAG Pipeline: yolo_ocr.json                                  │
│ - Node 1: detect_objects (YOLO)                              │
│ - Node 2: extract_text (OCR)                                 │
│ - Edge: detect → read                                        │
│ - Deterministic, stateless                                   │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│ Aggregator                                                    │
│ - Builds final response:                                      │
│       { "results": [ {frame_index, result}, ... ] }           │
│ - Schema regression guard ensures no drift                    │
└──────────────────────────────────────────────────────────────┘