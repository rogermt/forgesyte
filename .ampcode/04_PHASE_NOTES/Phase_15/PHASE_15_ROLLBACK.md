# Phase 15 Rollback Plan

**Date**: 2026-02-13
**Purpose**: Restore repository to Phase-14-compatible state

---

## Overview

This rollback plan provides step-by-step instructions to remove all Phase 15 changes and restore the repository to its Phase-14 state.

**IMPORTANT**: This rollback plan is for emergency use only. Consider the impact before proceeding.

---

## Files to Remove

### Router

```bash
rm server/app/api/routes/video_file.py
```

### Service

```bash
rm server/app/services/video_file_pipeline_service.py
```

### Video Tests (entire directory)

```bash
rm -rf server/app/tests/video/
```

### Fixtures

```bash
rm server/app/tests/fixtures/tiny.mp4
rm server/app/tests/fixtures/generate_tiny_mp4.py
```

### Governance Tooling

```bash
rm server/tools/forbidden_vocabulary.yaml
rm server/tools/validate_video_batch_path.py
```

### CI Workflow

```bash
rm .github/workflows/video_batch_validation.yml
```

### Pipeline (Optional)

```bash
# OPTIONAL: Remove if you want to revert pipeline changes
# NOTE: This may affect other tests if yolo_ocr pipeline is used elsewhere
rm server/app/pipelines/yolo_ocr.json
```

### Demo Script

```bash
rm scripts/demo_video_yolo_ocr.sh
```

### Smoke Test Script

```bash
rm scripts/smoke_test_video_batch.sh
```

### Documentation (Phase 15 docs)

```bash
rm .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_TESTING_GUIDE.md
rm .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ROLLBACK.md
rm .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_MIGRATION_GUIDE.md
rm .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_RELEASE_NOTES.md
rm .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ONBOARDING.md
rm .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ARCHITECTURE.txt
rm .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ARCHITECTURE.mmd
rm .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_GOVERNANCE.md
```

---

## Files to Modify

### Remove Router Include from main.py

**File**: `server/app/main.py`

**Remove this line**:
```python
from app.api.routes import video_file
```

**Remove this router registration**:
```python
app.include_router(video_file.router, prefix="/video", tags=["video"])
```

### Remove Dependencies from pyproject.toml

**File**: `server/pyproject.toml`

**Remove these dependencies**:
```toml
opencv-python-headless = "*"
pyyaml = "*"
types-PyYAML = "*"
```

---

## One-Command Rollback Script

Save this as `rollback_phase15.sh` and run it:

```bash
#!/bin/bash
set -e

echo "Rolling back Phase 15..."

# Remove files
rm -f server/app/api/routes/video_file.py
rm -f server/app/services/video_file_pipeline_service.py
rm -rf server/app/tests/video/
rm -f server/app/tests/fixtures/tiny.mp4
rm -f server/app/tests/fixtures/generate_tiny_mp4.py
rm -f server/tools/forbidden_vocabulary.yaml
rm -f server/tools/validate_video_batch_path.py
rm -f .github/workflows/video_batch_validation.yml
rm -f scripts/demo_video_yolo_ocr.sh
rm -f scripts/smoke_test_video_batch.sh

# Remove docs
rm -f .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_TESTING_GUIDE.md
rm -f .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ROLLBACK.md
rm -f .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_MIGRATION_GUIDE.md
rm -f .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_RELEASE_NOTES.md
rm -f .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ONBOARDING.md
rm -f .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ARCHITECTURE.txt
rm -f .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ARCHITECTURE.mmd
rm -f .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_GOVERNANCE.md

# Note: Manual steps required for main.py and pyproject.toml
echo ""
echo "MANUAL STEPS REQUIRED:"
echo "1. Remove video_file import from server/app/main.py"
echo "2. Remove video_file router registration from server/app/main.py"
echo "3. Remove opencv-python-headless from server/pyproject.toml"
echo "4. Remove pyyaml and types-PyYAML from server/pyproject.toml"
echo "5. OPTIONAL: Remove server/app/pipelines/yolo_ocr.json"
echo ""
echo "Rollback complete!"
```

---

## Verification After Rollback

### 1. Check for remaining Phase 15 files

```bash
# Check for video files
find server/app -name "*video*" -type f

# Check for forbidden vocabulary
grep -r "video_file" server/app/
grep -r "VideoFilePipelineService" server/app/
```

### 2. Run full test suite

```bash
cd server
uv run pytest -v
```

### 3. Run pre-commit checks

```bash
uv run pre-commit run --all-files
```

### 4. Check CI workflows

```bash
# Ensure video_batch_validation.yml is gone
ls .github/workflows/
```

---

## What Remains After Rollback

### Phase-14 Components (Untouched)

- **DAG Pipeline Engine**: `server/app/pipeline_engine/`
- **Plugin System**: `server/app/plugins/`
- **API Routes**: All existing routes except video
- **Service Layer**: All existing services except video
- **Tests**: All existing tests except video
- **CI Workflows**: `ci.yml`, `execution-ci.yml`, `governance-ci.yml`

### Golden Bundle (Optional Cleanup)

You may also want to remove the golden snapshot bundle:

```bash
rm -rf .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_GOLDEN_BUNDLE/
```

---

## Rollback Impact Assessment

### What Breaks

1. **Video Processing Endpoint**: `POST /video/upload-and-run` will no longer exist
2. **Video Tests**: All video tests will be removed
3. **Governance Validation**: Video-specific governance checks will be removed

### What Still Works

1. **Image Processing**: All existing image processing endpoints
2. **Plugin System**: All existing plugins (YOLO, OCR, etc.)
3. **DAG Engine**: All existing pipelines
4. **API Routes**: All non-video routes
5. **Tests**: All non-video tests

---

## Rollback Procedure

1. **Create a rollback branch**:
   ```bash
   git checkout -b rollback-phase15
   ```

2. **Run the rollback script**:
   ```bash
   chmod +x rollback_phase15.sh
   ./rollback_phase15.sh
   ```

3. **Manually edit files**:
   - Edit `server/app/main.py` to remove video_file import and router
   - Edit `server/pyproject.toml` to remove OpenCV and PyYAML dependencies

4. **Verify rollback**:
   ```bash
   cd server
   uv sync
   uv run pytest -v
   uv run pre-commit run --all-files
   ```

5. **Commit rollback**:
   ```bash
   git add .
   git commit -m "rollback: remove Phase 15 video batch processing"
   ```

6. **Push and create PR**:
   ```bash
   git push origin rollback-phase15
   gh pr create --base main --head rollback-phase15 --title "Rollback Phase 15"
   ```

---

## Emergency Rollback (Git Reset)

For emergency rollback to a pre-Phase 15 commit:

```bash
# Find the commit before Phase 15 started
git log --oneline | grep "phase15"

# Reset to that commit
git reset --hard <commit-hash-before-phase15>

# Force push (WARNING: destructive)
git push origin main --force
```

**WARNING**: This is destructive and should only be used in emergencies.

---

## Rollback Checklist

- [ ] All Phase 15 files removed
- [ ] Router import removed from main.py
- [ ] Router registration removed from main.py
- [ ] OpenCV dependency removed from pyproject.toml
- [ ] PyYAML dependencies removed from pyproject.toml
- [ ] Video tests directory removed
- [ ] Video fixtures removed
- [ ] Governance tooling removed
- [ ] CI workflow removed
- [ ] Documentation removed
- [ ] Full test suite passes
- [ ] Pre-commit checks pass
- [ ] No Phase 15 references remain in codebase

---

## Post-Rollback Validation

After rollback, verify:

1. **Server starts successfully**:
   ```bash
   cd server
   uv run uvicorn app.main:app --reload
   ```

2. **No video endpoint**:
   ```bash
   curl http://localhost:8000/docs
   # Verify /video/upload-and-run is NOT listed
   ```

3. **All existing tests pass**:
   ```bash
   cd server
   uv run pytest -v
   ```

4. **CI workflows pass**:
   - Check GitHub Actions for green status

---

## See Also

- `PHASE_15_SCOPE.md` - What Phase 15 added
- `PHASE_15_MIGRATION_GUIDE.md` - How to migrate to Phase 15
- `ARCHITECTURE.md` - Overall system architecture