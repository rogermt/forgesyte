Here we go—four last bricks to lock Phase 15 in.

---

### Phase‑15 architecture diagram in Mermaid

Save as `server/app/docs/PHASE_15_ARCHITECTURE.mmd`:

```mermaid
flowchart TD
    UI[Client / UI<br/>Upload MP4 + pipeline_id] -->|POST /video/upload-and-run| API[FastAPI Router<br/>(video_file.py)]

    API --> TMP[Save MP4 to temp file]
    TMP --> VFPS[VideoFilePipelineService<br/>(video_file_pipeline_service.py)]

    VFPS -->|OpenCV: read frames| FRAMES[Frames loop]
    FRAMES -->|for each frame| PAYLOAD[Build payload<br/>{frame_index, image_bytes}]
    PAYLOAD --> DAG[DagPipelineService<br/>(Phase 14 DAG engine)]

    DAG --> YOLO[YOLO plugin<br/>detect_objects]
    YOLO --> OCR[OCR plugin<br/>extract_text]
    OCR --> DAGOUT[DAG result<br/>{text, regions, ...}]

    DAGOUT --> COLLECT[Collect per-frame results]
    COLLECT --> RESP[HTTP Response<br/>{results: [{frame_index, result}, ...]}]
    RESP --> UI
```

---

### Phase‑15 end‑to‑end demo script

Save as `scripts/demo_phase15_yolo_ocr.sh`:

```bash
#!/bin/bash
set -e

echo "=== Phase 15 Demo: MP4 → YOLO → OCR ==="

echo "[1/5] Generate tiny.mp4 fixture (if missing)..."
python server/app/tests/fixtures/generate_tiny_mp4.py || true

echo "[2/5] Run Phase 15 smoke test..."
./scripts/smoke_test_phase15.sh

echo "[3/5] Start backend (in another terminal):"
echo "      uv run uvicorn server.app.main:app --reload"
read -p "Press Enter once backend is running..."

echo "[4/5] Call /video/upload-and-run..."
curl -X POST "http://localhost:8000/video/upload-and-run" \
  -F "file=@server/app/tests/fixtures/tiny.mp4;type=video/mp4" \
  -F "pipeline_id=yolo_ocr" \
  -o /tmp/phase15_result.json

echo "[5/5] Show first result:"
python - << 'EOF'
import json, pathlib
p = pathlib.Path("/tmp/phase15_result.json")
data = json.loads(p.read_text())
print("Results keys:", list(data.keys()))
print("First frame:", data["results"][0])
EOF

echo "=== Phase 15 demo complete. ==="
```

`chmod +x scripts/demo_phase15_yolo_ocr.sh`

---

### Phase‑15 GitHub Project board

Create a GitHub Project (v2) named: **“Phase 15 — MP4 → DAG → Results”** with columns:

- **Backlog**
  - Define YOLO+OCR payload contract  
  - Finalize `yolo_ocr.json` pipeline  
  - Write Phase‑15 docs (README, governance, onboarding)  

- **In Progress**
  - Implement `VideoFilePipelineService`  
  - Implement `/video/upload-and-run`  
  - Wire router into `main.py`  

- **Review**
  - Phase‑15 integration tests  
  - Phase‑15 smoke test script  
  - Phase‑15 UI upload flow  

- **Done**
  - Tiny MP4 fixture  
  - Mermaid architecture diagram  
  - Release notes  
  - Migration guide  

Each card links to the corresponding issue/PR; label them `phase:15`.

---

### Phase‑15 commit history plan

Target: small, reviewable, narrative commits:

1. **`phase15: add yolo_ocr pipeline definition`**  
   - Add `yolo_ocr.json`  
   - Ensure `validate_pipelines.py` passes.

2. **`phase15: define yolo+ocr payload contract`**  
   - Document payload in a small markdown file.  

3. **`phase15: add VideoFilePipelineService`**  
   - New service file + unit tests (if any).  

4. **`phase15: add /video/upload-and-run endpoint`**  
   - Router, DI wiring, error handling.  

5. **`phase15: add tiny mp4 fixture and generator`**  
   - `generate_tiny_mp4.py` + committed `tiny.mp4`.  

6. **`phase15: add integration tests for yolo_ocr mp4 flow`**  
   - `tests/phase15/` suite.  

7. **`phase15: add smoke test script and docs`**  
   - `scripts/smoke_test_phase15.sh`, README, governance.  

8. **`phase15: add architecture diagram and onboarding docs`**  
   - Mermaid, onboarding, migration, release notes.  

That sequence tells a clean story and keeps every diff atomic and reviewable.