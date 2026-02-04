# ⭐ **2. Phase 10 RED Tests**  
### *File:* `PHASE_10_RED_TESTS.md`

```md
# Phase 10 — RED Tests

These tests define the required behavior for Phase 10 before implementation.
They MUST fail initially (RED), then pass once features are implemented (GREEN).

---

# 1. Backend RED Tests

## 1.1 test_realtime_endpoint.py

def test_realtime_endpoint_exists(client):
    response = client.get("/v1/realtime")
    assert response.status_code in (200, 307, 308)

Purpose:
- Ensures the real-time endpoint is registered.

---

## 1.2 test_job_progress_field.py

def test_job_response_includes_progress():
    from server.app.models_phase10 import ExtendedJobResponse
    model = ExtendedJobResponse(
        job_id="123",
        device_requested="cpu",
        device_used="cpu",
        fallback=False,
        frames=[],
        progress=50,
    )
    assert model.progress == 50

Purpose:
- Ensures progress field exists and is typed.

---

## 1.3 test_plugin_timing_field.py

def test_job_response_includes_plugin_timings():
    from server.app.models_phase10 import ExtendedJobResponse
    model = ExtendedJobResponse(
        job_id="123",
        device_requested="cpu",
        device_used="cpu",
        fallback=False,
        frames=[],
        plugin_timings={"ocr": 12.5},
    )
    assert "ocr" in model.plugin_timings

Purpose:
- Ensures plugin timing field exists.

---

# 2. Frontend RED Tests

## 2.1 realtime_endpoint.spec.ts

test("connects to realtime endpoint", async ({ page }) => {
  const connected = await page.evaluate(async () => {
    const ws = new WebSocket("ws://localhost:8000/v1/realtime");
    return new Promise(resolve => {
      ws.onopen = () => resolve(true);
      setTimeout(() => resolve(false), 2000);
    });
  });
  expect(connected).toBe(true);
});

---

## 2.2 progress_bar.spec.ts

test("progress bar renders", async ({ page }) => {
  await page.goto("/demo");
  const bar = page.locator("#progress-bar");
  await expect(bar).toBeVisible();
});

---

## 2.3 plugin_inspector.spec.ts

test("plugin inspector loads metadata", async ({ page }) => {
  await page.goto("/demo");
  const inspector = page.locator("#plugin-inspector");
  await expect(inspector).toBeVisible();
});
```

---

# ⭐ **3. Phase 10 Migration Checklist**  
### *File:* `PHASE_10_MIGRATION_CHECKLIST.md`

```md
# Phase 10 — Migration Checklist

This checklist ensures Phase 10 is implemented cleanly, without breaking
Phase 9 invariants.

---

# 1. Backend

- [ ] Create realtime/ folder
- [ ] Add WebSocket/SSE endpoint stub
- [ ] Add ExtendedJobResponse model (progress, plugin_timings, warnings)
- [ ] Add message_types.py for WebSocketMessage extensions
- [ ] Add connection_manager.py
- [ ] Add plugin inspector service
- [ ] Add tool runner for real-time plugin execution
- [ ] Ensure all Phase 9 typed models remain unchanged
- [ ] Ensure no breaking changes to required fields

---

# 2. Frontend

- [ ] Add RealtimeClient.ts
- [ ] Add RealtimeContext.tsx
- [ ] Add useRealtime.ts hook
- [ ] Add RealtimeOverlay.tsx
- [ ] Add ProgressBar.tsx (#progress-bar)
- [ ] Add PluginInspector.tsx (#plugin-inspector)
- [ ] Add RealtimeOverlay.stories.tsx
- [ ] Ensure Phase 9 UI IDs remain unchanged

---

# 3. Tests

- [ ] Add backend RED tests
- [ ] Add frontend RED tests
- [ ] Fix/replace failing web-ui pre-commit hook
- [ ] Add real-time integration tests
- [ ] Ensure all Phase 9 tests still pass

---

# 4. Governance

- [ ] No new governance rules added
- [ ] No schema drift detection added
- [ ] No breaking changes to Phase 9 invariants
- [ ] Document all new models in Phase 10 notes

---

# 5. Completion Criteria

Phase 10 is complete when:

- Real-time endpoint works
- Progress updates stream
- Plugin timings stream
- Real-time overlay updates
- Plugin inspector loads metadata
- All RED tests pass
- All Phase 9 invariants remain intact
```

---

