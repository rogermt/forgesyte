# ⭐ **4. Phase 10 Final Merge PR Template**  
### *File:* `PHASE_10_FINAL_MERGE_PR_TEMPLATE.md`

```md
# Phase 10 — Final Merge PR

Phase 10 is now complete. This PR delivers real-time insights, plugin pipeline
upgrades, extended job models, and fixes the inherited web-ui pre-commit hook
issues. All Phase 9 invariants remain intact.

---

# ✅ Phase 10 Completion Summary

| Requirement | Status | Evidence |
|------------|--------|----------|
| Real-time endpoint | ✅ PASS | WebSocket/SSE live |
| Progress updates | ✅ PASS | UI + API verified |
| Plugin timings | ✅ PASS | Inspector panel shows timings |
| Real-time overlay | ✅ PASS | Streaming frames rendered |
| Plugin inspector | ✅ PASS | Metadata + timings displayed |
| Storybook story | ✅ PASS | RealtimeOverlay.stories.tsx |
| RED → GREEN tests | ✅ PASS | All Phase 10 tests passing |
| Pre-commit hook fixed | ✅ PASS | web-ui-tests stable |
| No Phase 9 regressions | ✅ PASS | All Phase 9 tests still passing |

---

# 🧩 What This PR Delivers

## 1. Real-Time Infrastructure
- WebSocket/SSE endpoint
- Connection manager
- Real-time message types
- Streaming frames, progress, warnings

## 2. Extended Job Model
- progress: int
- plugin_timings: dict[str, float]
- warnings: list[str]

## 3. Plugin Pipeline Upgrade
- Inspector service
- Real-time tool execution
- Plugin metadata integration

## 4. UI Enhancements
- Real-time overlay renderer
- Progress bar
- Plugin inspector panel
- Real-time connection indicators

## 5. Developer Experience
- Fixed web-ui pre-commit hook
- Real-time Storybook story
- Real-time integration tests

---

# 🛡️ Guardrails Confirmed

- No breaking changes to Phase 9 API
- No breaking changes to Phase 9 UI IDs
- No new governance rules added
- No schema drift detection added
- All Phase 9 tests still pass

---

# 📂 Notable Files Added

```
server/app/realtime/
server/app/models_phase10.py
server/app/api_phase10.py
web-ui/src/realtime/
web-ui/src/components/RealtimeOverlay.tsx
web-ui/src/components/ProgressBar.tsx
web-ui/src/components/PluginInspector.tsx
web-ui/src/stories/RealtimeOverlay.stories.tsx
```

---

# 📎 Merge Checklist

- [ ] All tests passing
- [ ] Storybook builds
- [ ] No skipped tests
- [ ] No Phase 9 invariants broken
- [ ] PR reviewed and approved

---

# Phase 10 is complete. Phase 11 may begin.
```

---

Roger, these four documents give you:

- A **complete Phase 10 scaffolding**
- A **full RED test suite**
- A **migration checklist**
- A **final merge PR template**

