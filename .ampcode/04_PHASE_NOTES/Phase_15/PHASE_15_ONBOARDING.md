# Phase 15 Onboarding Guide

**Date**: 2026-02-13
**Phase**: 15 - Offline Batch Video Processing
**Target Audience**: New Contributors

---

## Welcome to Phase 15

This guide helps new contributors understand Phase 15: **Offline Batch Video Processing with YOLO + OCR**.

**What you'll learn**:
- What Phase 15 does
- How to use the video endpoint
- How to run tests
- How to contribute safely

---

## What is Phase 15?

Phase 15 adds **video file processing** to ForgeSyte. Before Phase 15, ForgeSyte could only process single images. Now, you can upload an MP4 file and get frame-by-frame analysis results.

### Key Concept: Batch Processing

Phase 15 is **batch-only**. This means:
- Upload video → Process all frames → Return all results
- Single request/response cycle
- No background processing
- No real-time updates

### What Phase 15 Does

1. **Upload**: User uploads MP4 file via API
2. **Extract**: Server extracts frames sequentially
3. **Process**: Each frame goes through YOLO + OCR pipeline
4. **Return**: Server returns aggregated results as JSON

### What Phase 15 Does NOT Do

- ❌ No job queues
- ❌ No async workers
- ❌ No database storage
- ❌ No real-time streaming
- ❌ No multi-frame tracking
- ❌ No visual output (bounding boxes, annotations)

These are **future phases**, not Phase 15.

---

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 18+ (for web-ui)
- Git

### Setup

```bash
# Clone repository
git clone <repo-url>
cd forgesyte

# Install server dependencies
cd server
uv sync

# Install web-ui dependencies
cd ../web-ui
npm install
```

### Run Tests

```bash
cd server
uv run pytest app/tests/video -v
```

Expected: 38 tests PASS

### Start Server

```bash
cd server
uv run uvicorn app.main:app --reload
```

Server starts at `http://localhost:8000`

---

## Using the Video Endpoint

### Basic Usage

Upload a video file:

```bash
curl -X POST http://localhost:8000/video/upload-and-run \
  -F "file=@my_video.mp4" \
  -F "pipeline_id=yolo_ocr"
```

### Response Format

```json
{
  "results": [
    {
      "frame_index": 0,
      "result": {
        "detections": [
          {
            "class": "person",
            "confidence": 0.95,
            "bbox": [x, y, width, height]
          }
        ],
        "text": "Extracted text from frame"
      }
    },
    {
      "frame_index": 1,
      "result": {...}
    }
  ]
}
```

### Parameters

- `file`: MP4 file (required)
- `pipeline_id`: Pipeline ID (required, currently only "yolo_ocr")

### Optional Parameters (Future)

These parameters are planned for future phases but not available in Phase 15:
- `frame_stride`: Process every Nth frame
- `max_frames`: Maximum frames to process

---

## Architecture

### High-Level Flow

```
User uploads MP4
        ↓
API Router (video_file.py)
        ↓
Video Service (video_file_pipeline_service.py)
        ↓
OpenCV extracts frames
        ↓
Each frame → DAG Pipeline (yolo_ocr)
        ↓
YOLO detection → OCR text extraction
        ↓
Aggregate results
        ↓
Return JSON to user
```

### Key Components

| Component | File | Purpose |
|-----------|------|---------|
| API Router | `server/app/api/routes/video_file.py` | Handles HTTP requests |
| Video Service | `server/app/services/video_file_pipeline_service.py` | Processes video files |
| DAG Engine | `server/app/pipeline_engine/` | Executes pipelines |
| YOLO Plugin | `server/app/plugins/yolo/` | Object detection |
| OCR Plugin | `server/app/plugins/ocr/` | Text extraction |

---

## Testing

### Running Tests

```bash
# All video tests
cd server
uv run pytest app/tests/video -v

# Unit tests only
uv run pytest app/tests/video/test_video_service.py -v

# Integration tests only
uv run pytest app/tests/video/test_video_integration.py -v

# Stress tests only
uv run pytest app/tests/video/stress/ -v

# Fuzz tests only
uv run pytest app/tests/video/fuzz/ -v
```

### Test Types

1. **Unit Tests**: Test service layer in isolation
2. **Integration Tests**: Test full API endpoint
3. **Stress Tests**: Test large-scale processing (1000 frames)
4. **Fuzz Tests**: Test malformed inputs

### Smoke Test

```bash
./scripts/smoke_test_video_batch.sh
```

This runs the full test suite with early failure detection.

---

## Contributing

### Governance Rules

Phase 15 has strict governance to prevent scope creep:

**Forbidden Vocabulary**:
- ❌ `job_id`, `queue`, `worker`, `celery`
- ❌ `redis`, `rabbitmq`, `database`, `postgres`
- ❌ `websocket`, `streaming`
- ❌ `tracking`, `reid`, `track_ids`

**Why?** These concepts belong to future phases (16+). Adding them now would break Phase 15's minimal scope.

### Code Style

Follow existing project conventions:
- **Python**: Black formatting, Ruff linting, MyPy type checking
- **TypeScript**: ESLint, strict TypeScript
- **File names**: Functional names only (no "phase15" in file names)

### Testing Requirements

- All new code must have tests
- Tests must follow TDD (write failing test first)
- Run pre-commit hooks before committing

### Pre-Commit Checks

```bash
cd server
uv run pre-commit run --all-files
```

This runs:
- Black formatting
- Ruff linting
- MyPy type checking
- ESLint (for web-ui)
- Pytest

---

## Common Tasks

### Add a New Test

1. Write failing test
2. Run test to verify it fails
3. Implement code to make test pass
4. Run test to verify it passes
5. Run pre-commit checks
6. Commit

```bash
# Example: Add a new unit test
cd server
# 1. Write test in app/tests/video/test_video_service.py
# 2. Run test
uv run pytest app/tests/video/test_video_service.py::test_new_feature -v
# 3. Implement code
# 4. Run test again
uv run pytest app/tests/video/test_video_service.py::test_new_feature -v
# 5. Run pre-commit
uv run pre-commit run --all-files
# 6. Commit
git add .
git commit -m "test: add new feature test"
```

### Fix a Bug

1. Write failing test for the bug
2. Run test to verify it fails
3. Fix the bug
4. Run test to verify it passes
5. Run pre-commit checks
6. Commit

### Add Documentation

Documentation goes in `.ampcode/04_PHASE_NOTES/Phase_15/`, not in functional directories.

---

## Troubleshooting

### Issue: Tests fail with "Module not found"

**Solution**:
```bash
cd server
uv sync
```

### Issue: Tests fail with "YOLO plugin not found"

**Solution**: This is expected in CPU-only dev environments. The smoke test gracefully handles this.

### Issue: Governance validation fails

**Solution**: Check for forbidden vocabulary:
```bash
cd server
uv run python tools/validate_video_batch_path.py
```

### Issue: Pre-commit hooks fail

**Solution**:
```bash
cd server
uv run pre-commit run --all-files
```

---

## Resources

### Documentation

- `PHASE_15_OVERVIEW.md` - Feature overview
- `PHASE_15_TESTING_GUIDE.md` - Testing procedures
- `PHASE_15_MIGRATION_GUIDE.md` - Migration instructions
- `PHASE_15_GOVERNANCE.md` - Governance rules
- `PHASE_15_ROLLBACK.md` - Rollback procedures

### Architecture

- `PHASE_15_ARCHITECTURE.txt` - ASCII diagram
- `PHASE_15_ARCHITECTURE.mmd` - Mermaid diagram
- `ARCHITECTURE.md` - Overall system architecture

### Development

- `PLUGIN_DEVELOPMENT.md` - Plugin development guide
- `docs/development/PYTHON_STANDARDS.md` - Python coding standards
- `CONTRIBUTING.md` - Contribution guidelines

---

## Demo Script

Run the demo script to see Phase 15 in action:

```bash
./scripts/demo_video_yolo_ocr.sh
```

This uploads a test video and displays the results.

---

## Next Steps

1. **Read the documentation**:
   - Start with `PHASE_15_OVERVIEW.md`
   - Read `PHASE_15_TESTING_GUIDE.md`
   - Review `PHASE_15_GOVERNANCE.md`

2. **Run the tests**:
   ```bash
   cd server
   uv run pytest app/tests/video -v
   ```

3. **Run the demo**:
   ```bash
   ./scripts/demo_video_yolo_ocr.sh
   ```

4. **Start contributing**:
   - Pick a task from the issue tracker
   - Write a test first
   - Implement the feature
   - Run pre-commit checks
   - Submit a PR

---

## Questions?

If you have questions:
- Check the documentation in `.ampcode/04_PHASE_NOTES/Phase_15/`
- Review existing tests in `server/app/tests/video/`
- Ask in the project chat or open an issue

---

## Summary

Phase 15 is a **minimal, focused** addition to ForgeSyte:
- ✅ Video file upload and processing
- ✅ YOLO + OCR pipeline
- ✅ Batch-only, synchronous execution
- ✅ 38 tests, all passing
- ✅ Strict governance to prevent scope creep

**Remember**: Phase 15 is about proving batch processing works. Future phases will add job queues, streaming, and persistence.

---

**Happy contributing!** 🚀