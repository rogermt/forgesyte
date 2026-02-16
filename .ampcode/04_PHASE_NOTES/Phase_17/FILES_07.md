Here you go, Roger — **four clean Phase‑17 engineering templates**, each in its own file, each ready to drop into:

```
.ampcode/04_PHASE_NOTES/Phase_17/
```

No overlap, no missing pieces, no silent changes.  
These are the canonical versions.

---

# ⭐ FILE 1 — **PHASE_17_FRAME_VALIDATOR_TEMPLATE.md**

```markdown
# Phase‑17 FrameValidator Template

This module validates incoming JPEG frames before they enter the pipeline.

---

## File: `server/app/services/streaming/frame_validator.py`

```python
import os

MAX_MB = int(os.getenv("STREAM_MAX_FRAME_SIZE_MB", 5))
MAX_BYTES = MAX_MB * 1024 * 1024

class FrameValidationError(Exception):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(detail)

def validate_jpeg(frame_bytes: bytes) -> None:
    """
    Validate JPEG frame:
    - Must start with SOI marker (0xFFD8)
    - Must end with EOI marker (0xFFD9)
    - Must be under max size
    """
    if not frame_bytes:
        raise FrameValidationError("invalid_frame", "Empty frame")

    if len(frame_bytes) > MAX_BYTES:
        raise FrameValidationError("frame_too_large", f"Frame exceeds {MAX_MB}MB")

    # JPEG SOI/EOI markers
    if not (frame_bytes.startswith(b"\xFF\xD8") and frame_bytes.endswith(b"\xFF\xD9")):
        raise FrameValidationError("invalid_frame", "Not a valid JPEG image")
```
```

---

# ⭐ FILE 2 — **PHASE_17_BACKPRESSURE_MODULE_TEMPLATE.md**

```markdown
# Phase‑17 Backpressure Module Template

This module centralizes backpressure logic for reuse and clarity.

---

## File: `server/app/services/streaming/backpressure.py`

```python
class Backpressure:
    """
    Stateless helpers for backpressure decisions.
    """

    @staticmethod
    def should_drop(processing_time_ms: float, drop_rate: float, drop_threshold: float) -> bool:
        """
        Drop frame if:
        - Processing time exceeds real‑time threshold (~100ms ≈ 10 FPS)
        - Drop rate exceeds configured threshold
        """
        if processing_time_ms > 100:
            return True
        if drop_rate > drop_threshold:
            return True
        return False

    @staticmethod
    def should_slow_down(drop_rate: float, slowdown_threshold: float) -> bool:
        """
        Emit slow‑down signal if drop rate exceeds slowdown threshold.
        """
        return drop_rate > slowdown_threshold
```
```

---

# ⭐ FILE 3 — **PHASE_17_PIPELINE_RUN_ON_FRAME_TEMPLATE.md**

```markdown
# Phase‑17 `run_on_frame()` Implementation Template

Adds frame‑level inference to the existing Phase‑15 pipeline service.

---

## File: `server/app/services/video_file_pipeline_service.py`

```python
from app.services.pipeline.dag_pipeline_service import DagPipelineService

class VideoFilePipelineService:
    """
    Existing Phase‑15 service extended for Phase‑17 frame‑level inference.
    """

    @staticmethod
    def is_valid_pipeline(pipeline_id: str) -> bool:
        return DagPipelineService.is_valid_pipeline(pipeline_id)

    def run_on_frame(self, pipeline_id: str, frame_bytes: bytes) -> dict:
        """
        Run the Phase‑15 DAG pipeline on a single JPEG frame.
        """
        try:
            result = DagPipelineService.run_pipeline(
                pipeline_id=pipeline_id,
                input_bytes=frame_bytes
            )
            return result
        except Exception as e:
            return {
                "error": "pipeline_failure",
                "detail": str(e)
            }
```
```

---

# ⭐ FILE 4 — **PHASE_17_FULL_FOLDER_SCAFFOLDING.md**

```markdown
# Phase‑17 Full Folder Scaffolding

This is the authoritative folder structure for all Phase‑17 components.

---

## Server Code

```
server/
└── app/
    ├── api_routes/
    │   └── routes/
    │       └── video_stream.py
    │
    ├── services/
    │   └── streaming/
    │       ├── session_manager.py
    │       ├── frame_validator.py
    │       ├── backpressure.py
    │       └── __init__.py
    │
    ├── services/
    │   └── video_file_pipeline_service.py   # extended with run_on_frame()
    │
    └── __init__.py
```

---

## Tests

```
server/tests/streaming/
    test_connect.py
    test_session_manager.py
    test_frame_validator.py
    test_receive_frames.py
    test_pipeline_integration.py
    test_backpressure_drop.py
    test_backpressure_slowdown.py
    test_error_handling.py
```

---

## Documentation

```
.ampcode/
└── 04_PHASE_NOTES/
    └── Phase_17/
        ├── PHASE_17_OVERVIEW.md
        ├── ARCHITECTURE.md
        ├── ENDPOINTS.md
        ├── SESSION_MODEL.md
        ├── NON_GOALS.md
        ├── ROLLBACK_PLAN.md
        ├── CONTRIBUTOR_EXAM.md
        ├── RELEASE_NOTES.md
        ├── PERFORMANCE_GUIDE.md
        ├── CLIENT_GUIDE.md
        ├── TEST_STRATEGY.md
        ├── BACKPRESSURE_DESIGN.md
        ├── FAILURE_MODES.md
        ├── METRICS_AND_LOGGING.md
        ├── SECURITY_NOTES.md
        ├── FUTURE_PHASE_LINKS.md
        ├── FRONTEND_UI_WIREFRAME.md
        ├── DEVELOPER_ONBOARDING_GUIDE.md
        ├── API_CONTRACT_POSTER.md
        └── PHASE_17_IMPLEMENTATION_BLUEPRINT.md
```

---

Roger — these four files complete the Phase‑17 scaffolding pack.  
You now have:

- Frame validation  
- Backpressure logic  
- Frame‑level pipeline execution  
- Full folder structure  

