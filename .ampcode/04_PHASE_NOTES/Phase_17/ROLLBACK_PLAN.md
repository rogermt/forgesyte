# Phase 17: Rollback Plan

## Overview

This document describes how to rollback Phase 17 if issues arise after deployment.

## Rollback Strategy

Phase 17 introduces a new WebSocket endpoint that is independent from existing functionality. Rolling back is straightforward because:

1. **No database changes**: Phase 17 does not write to DuckDB
2. **No API changes**: Phase 17 does not modify `/v1/*` endpoints
3. **No breaking changes**: Existing Phase 15/16 functionality is unchanged
4. **Ephemeral state**: Sessions are in-memory only

## Rollback Methods

### Method 1: Disable WebSocket Endpoint (Recommended)

**When**: Minor issues with streaming, but Phase 15/16 must remain operational

**Steps**:

1. Comment out the WebSocket router in `server/app/main.py`:

```python
# from app.api_routes.routes.video_stream import router as video_stream_router
# app.include_router(video_stream_router)
```

2. Restart the server

**Result**: WebSocket endpoint is disabled, but Phase 15/16 continues to work

### Method 2: Revert Commit

**When**: Critical issues with streaming that cannot be quickly fixed

**Steps**:

1. Identify the commit that introduced the issue:

```bash
git log --oneline
```

2. Revert to the last known good commit:

```bash
git revert <commit-hash>
```

3. Push the revert:

```bash
git push origin feature/phase-17
```

**Result**: All Phase 17 changes are removed

### Method 3: Feature Flag

**When**: Need to quickly disable streaming without redeploying

**Steps**:

1. Add feature flag to `server/settings.py`:

```python
STREAMING_ENABLED = os.getenv("STREAMING_ENABLED", "false").lower() == "true"
```

2. Add guard in `server/app/main.py`:

```python
if STREAMING_ENABLED:
    from app.api_routes.routes.video_stream import router as video_stream_router
    app.include_router(video_stream_router)
```

3. Set environment variable:

```bash
export STREAMING_ENABLED=false
```

**Result**: Streaming is disabled via configuration

## Rollback Verification

After rollback, verify:

1. **Phase 15 functionality**:

```bash
cd server
uv run pytest app/tests/video -v --tb=short
```

2. **Phase 16 functionality**:

```bash
cd server
uv run pytest tests/api -v --tb=short
```

3. **WebSocket endpoint is disabled**:

```bash
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Host: localhost:8000" \
  http://localhost:8000/ws/video/stream?pipeline_id=yolo_ocr
```

Expected: 404 Not Found

## Known Issues and Solutions

### Issue: High Memory Usage

**Symptom**: Server memory usage increases over time

**Cause**: SessionManager instances not being destroyed

**Solution**: Verify `websocket.state.session = None` is called in finally block

**Rollback**: Disable WebSocket endpoint

### Issue: High Drop Rate

**Symptom**: Most frames are being dropped

**Cause**: Pipeline processing too slow

**Solution**: 
- Optimize pipeline performance
- Increase `STREAM_DROP_THRESHOLD`
- Reduce frame rate on client

**Rollback**: Disable WebSocket endpoint

### Issue: WebSocket Connection Fails

**Symptom**: Clients cannot connect to `/ws/video/stream`

**Cause**: Pipeline validation or plugin loading issue

**Solution**: Check logs for specific error message

**Rollback**: Check pipeline configuration or disable endpoint

## Rollback Decision Tree

```
Issue Detected
    │
    ├─ Is it Phase 15/16 related?
    │   ├─ Yes → Rollback entire Phase 17
    │   └─ No → Continue
    │
    ├─ Is it WebSocket endpoint specific?
    │   ├─ Yes → Disable WebSocket endpoint (Method 1)
    │   └─ No → Continue
    │
    ├─ Can you fix it quickly?
    │   ├─ Yes → Fix and redeploy
    │   └─ No → Use feature flag (Method 3)
    │
    └─ Critical issue?
        ├─ Yes → Revert commit (Method 2)
        └─ No → Monitor
```

## Post-Rollback Actions

After rollback:

1. Document the issue
2. Create GitHub issue
3. Fix the issue in a new commit
4. Re-enable streaming after fix is verified

## Testing Rollback

Test rollback procedure before deployment:

1. Deploy Phase 17
2. Simulate issue
3. Perform rollback
4. Verify Phase 15/16 still works
5. Re-enable Phase 17
6. Verify streaming works again

## Rollback Script

```bash
#!/bin/bash
# rollback_phase17.sh

echo "Rolling back Phase 17..."

# Disable WebSocket endpoint
sed -i 's/from app.api_routes.routes.video_stream import/# from app.api_routes.routes.video_stream import/' server/app/main.py
sed -i 's/app.include_router(video_stream_router)/# app.include_router(video_stream_router)/' server/app/main.py

# Restart server
cd server
uv run uvicorn app.main:app --reload

# Verify rollback
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Host: localhost:8000" \
  http://localhost:8000/ws/video/stream?pipeline_id=yolo_ocr

echo "Rollback complete"
```

## Support Contacts

If rollback fails or issues persist:

1. Check Phase 17 documentation: `.ampcode/04_PHASE_NOTES/Phase_17/`
2. Check GitHub issues for Phase 17
3. Contact the development team

## Notes

- Rollback is designed to be safe and reversible
- No data loss occurs during rollback
- Rollback does not affect Phase 15/16 functionality
- Rollback can be performed without downtime