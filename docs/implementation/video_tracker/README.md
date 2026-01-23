# Video Tracker Web-UI Integration

**Status:** Ready for implementation  
**Owner:** Roger  
**Repos:** forgesyte, forgesyte-plugins  

This directory contains complete, copy-paste-ready implementation specifications for integrating video streaming + frame-based tool execution into ForgeSyte web-ui.

---

## 📋 Files

### Architecture
- **[PLAN_ARCHITECTURE.md](../../../PLAN_ARCHITECTURE.md)** — High-level decisions (5 core features)
- **[DECISIONS.md](./DECISIONS.md)** — Detailed rationale for each decision

### Backend
- **[BACKEND_MANIFEST_ENDPOINT.md](./BACKEND_MANIFEST_ENDPOINT.md)** — `/plugins/{id}/manifest`
- **[BACKEND_RUN_ENDPOINT.md](./BACKEND_RUN_ENDPOINT.md)** — `/plugins/{id}/tools/{tool}/run`
- **[BACKEND_CACHE_SERVICE.md](./BACKEND_CACHE_SERVICE.md)** — ManifestCacheService

### Web-UI Hooks
- **[HOOK_USE_VIDEO_PROCESSOR.md](./HOOK_USE_VIDEO_PROCESSOR.md)** — Frame extraction + buffering
- **[HOOK_USE_MANIFEST.md](./HOOK_USE_MANIFEST.md)** — Manifest discovery + caching

### Web-UI Components
- **[COMPONENT_TOOL_SELECTOR.md](./COMPONENT_TOOL_SELECTOR.md)** — Discover tools from manifest
- **[COMPONENT_CONFIDENCE_SLIDER.md](./COMPONENT_CONFIDENCE_SLIDER.md)** — Filter results by confidence
- **[COMPONENT_OVERLAY_TOGGLES.md](./COMPONENT_OVERLAY_TOGGLES.md)** — Show/hide layers
- **[COMPONENT_RESULT_OVERLAY.md](./COMPONENT_RESULT_OVERLAY.md)** — Multi-layer canvas rendering
- **[COMPONENT_RECORD_BUTTON.md](./COMPONENT_RECORD_BUTTON.md)** — MediaRecorder export
- **[PAGE_VIDEO_TRACKER.md](./PAGE_VIDEO_TRACKER.md)** — Main page (orchestrates all)

### Testing
- **[TESTS_BACKEND_CPU.md](./TESTS_BACKEND_CPU.md)** — Backend CPU-only tests (fast)
- **[TESTS_BACKEND_GPU.md](./TESTS_BACKEND_GPU.md)** — Backend GPU tests (RUN_MODEL_TESTS=1)
- **[TESTS_WEBUI_CPU.md](./TESTS_WEBUI_CPU.md)** — Web-UI CPU-only tests (fast)

### API & Types
- **[TYPES_PLUGIN.md](./TYPES_PLUGIN.md)** — TypeScript type definitions

---

## 🚀 Quick Start

1. **Review architecture:** Read [PLAN_ARCHITECTURE.md](../../../PLAN_ARCHITECTURE.md)
2. **Understand decisions:** Read [DECISIONS.md](./DECISIONS.md)
3. **Backend (Week 1):**
   - Implement [BACKEND_MANIFEST_ENDPOINT.md](./BACKEND_MANIFEST_ENDPOINT.md)
   - Implement [BACKEND_RUN_ENDPOINT.md](./BACKEND_RUN_ENDPOINT.md)
   - Implement [BACKEND_CACHE_SERVICE.md](./BACKEND_CACHE_SERVICE.md)
   - Run [TESTS_BACKEND_CPU.md](./TESTS_BACKEND_CPU.md)
4. **Web-UI (Week 2):**
   - Implement [HOOK_USE_VIDEO_PROCESSOR.md](./HOOK_USE_VIDEO_PROCESSOR.md)
   - Implement [HOOK_USE_MANIFEST.md](./HOOK_USE_MANIFEST.md)
   - Implement components (see list above)
   - Run [TESTS_WEBUI_CPU.md](./TESTS_WEBUI_CPU.md)
5. **Integration (Week 3):**
   - Run [TESTS_BACKEND_GPU.md](./TESTS_BACKEND_GPU.md) on Kaggle
   - Test end-to-end: upload video → process → export

---

## 📊 Implementation Order

### Week 1: Backend
```bash
# Create feature branch
cd forgesyte/server
git checkout -b feature/video-tracker-endpoints

# 1. ManifestCacheService
# Implement: BACKEND_CACHE_SERVICE.md
# Test: TESTS_BACKEND_CPU.md

# 2. Manifest endpoint
# Implement: BACKEND_MANIFEST_ENDPOINT.md
# Test: TESTS_BACKEND_CPU.md

# 3. Run endpoint
# Implement: BACKEND_RUN_ENDPOINT.md
# Test: TESTS_BACKEND_CPU.md

# Quality checks
uv run ruff check app/ --fix
uv run black app/
uv run mypy app/ --no-site-packages
uv run pytest tests/api/ -v

# Commit
git add .
git commit -m "feat(plugins): Add manifest + tool run endpoints"
git push origin feature/video-tracker-endpoints
```

### Week 2: Web-UI
```bash
cd forgesyte/web-ui
git checkout -b feature/video-tracker-components

# 1. Types
# Implement: TYPES_PLUGIN.md

# 2. Hooks
# Implement: HOOK_USE_MANIFEST.md
# Test: TESTS_WEBUI_CPU.md

# Implement: HOOK_USE_VIDEO_PROCESSOR.md
# Test: TESTS_WEBUI_CPU.md

# 3. Components (in order)
# Implement: COMPONENT_TOOL_SELECTOR.md
# Test: TESTS_WEBUI_CPU.md

# Implement: COMPONENT_CONFIDENCE_SLIDER.md
# Test: TESTS_WEBUI_CPU.md

# Implement: COMPONENT_OVERLAY_TOGGLES.md
# Test: TESTS_WEBUI_CPU.md

# Implement: COMPONENT_RESULT_OVERLAY.md
# Test: TESTS_WEBUI_CPU.md

# Implement: COMPONENT_RECORD_BUTTON.md
# Test: TESTS_WEBUI_CPU.md

# 4. Page
# Implement: PAGE_VIDEO_TRACKER.md
# Test: TESTS_WEBUI_CPU.md

# Quality checks
npm run lint
npm run type-check
npm run test -- --run

# Commit
git add .
git commit -m "feat(video): Add VideoTracker with all components"
git push origin feature/video-tracker-components
```

### Week 3: Integration & GPU Testing
```bash
# GPU tests on Kaggle
cd forgesyte/server
RUN_MODEL_TESTS=1 pytest tests/integration/test_video_stream.py -v

# E2E test: Upload video → Process → Export
# (Manual test via browser or Cypress)
```

---

## ✅ Definition of Done

- [ ] All backend endpoints implemented + CPU tests pass
- [ ] All web-ui components implemented + CPU tests pass
- [ ] TypeScript: `npm run type-check` passes (no errors)
- [ ] Linting: `npm run lint` and `uv run ruff check` pass
- [ ] Integration: Upload video → process frames → export video (works)
- [ ] GPU tests: Real YOLO inference (RUN_MODEL_TESTS=1)
- [ ] No hardcoded plugin/tool names in web-ui
- [ ] Manifest discovery works (dynamic tool selection)
- [ ] Frame buffer maintains last 10 frames
- [ ] Confidence slider filters client-side
- [ ] Track ID persistence across frames
- [ ] Multi-layer overlay composition (players + ball + pitch + radar)
- [ ] Video export as WebM/MP4

---

## 🔗 Related Issues
- Feature: Video stream tracking in web-ui
- Epic: Plugin-agnostic architecture
- Design doc: `/home/rogermt/forgesyte/scratch/video-tracker-design.md`

---

## 📝 Notes

- All code is **copy-paste ready** (fully specified, no pseudocode)
- All tests are **CPU-only by default** (skip GPU tests)
- GPU tests only run with `RUN_MODEL_TESTS=1` (on Kaggle)
- Follow TDD: write tests first, then implement
- Follow AGENTS.md conventions (file naming, imports, structure)
- Each file is **self-contained** (list all imports, dependencies)

---

**Ready to implement?**
