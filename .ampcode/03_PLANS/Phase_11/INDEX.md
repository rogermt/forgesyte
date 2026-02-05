# Phase 11 Document Index

**This file maps all Phase 11 documents for builder reference.**

---

## Approval Files (For Roger to Review)

| File | Purpose |
|------|---------|
| [PHASE_11_PLANS.md](./PHASE_11_PLANS.md) | Authoritative plan - no guessing |
| [PHASE_11_PROGRESS.md](./PHASE_11_PROGRESS.md) | Progress tracker - 8 commits |

**These are the ONLY files Roger will approve.**

---

## Helper Documents (For Builder Reference)

| File | Purpose |
|------|---------|
| [PHASE_11_DIAGRAMS.md](./PHASE_11_DIAGRAMS.md) | Visual diagrams - state machine, flows, structures |
| [PHASE_11_TEST_SPEC.md](./PHASE_11_TEST_SPEC.md) | Test specifications - 40+ tests with code |
| [PHASE_11_CODE_SNIPPETS.md](./PHASE_11_CODE_SNIPPETS.md) | Code patterns - RWLock, Sandbox, etc. |

**These files help ME build the approval files.**

---

## Official Specification Documents

Located in `../../04_PHASE_NOTES/Phase_11/`:

| File | Purpose |
|------|---------|
| PHASE_11_ARCHITECTURE.md | System design |
| PHASE_11_IMPLEMENTATION_PLAN.md | 8-commit timeline |
| PHASE_11_CONCRETE_IMPLEMENTATION.md | Production code |
| PHASE_11_DEVELOPER_CONTRACT.md | 10 binding rules |
| PHASE_11_COMPLETION_CRITERIA.md | Definition of done |
| PHASE_11_VIDEOTRACKER_STABILITY.md | VideoTracker hardening |
| PHASE_11_RED_TESTS.md | Pre-implementation tests |
| PHASE_11_GREEN_TESTS.md | Post-implementation tests |
| PHASE_11_NOTES_01.md | Authoritative decisions |
| PHASE_11_NOTES_02.md | Governance model |

---

## Document Flow

```
                    ┌─────────────────────────┐
                    │  Specification Docs      │
                    │  (04_PHASE_NOTES/)      │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │  Helper Documents      │
                    │  - DIAGRAMS           │
                    │  - TEST_SPEC           │
                    │  - CODE_SNIPPETS       │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │  Approval Files        │
                    │  - PLANS.md            │
                    │  - PROGRESS.md         │
                    └─────────────────────────┘
```

---

## Quick Reference

### Core Decisions (from PHASE_11_PLANS.md)

| Setting | Value |
|---------|-------|
| Lock Type | RWLock |
| GPU Check | torch + nvidia-smi |
| Model Check | Read first 16 bytes |
| Timeout | 60s |
| Memory | 1GB |
| Validation Hook | Required |

### Commits (from PHASE_11_PROGRESS.md)

| # | Name | Status |
|---|------|--------|
| 1 | Scaffold modules | ⏳ |
| 2 | Wire Health API | ⏳ |
| 3 | PluginRegistry | ⏳ |
| 4 | SandboxRunner | ⏳ |
| 5 | Wire ToolRunner | ⏳ |
| 6 | Metrics | ⏳ |
| 7 | Timeout/Memory | ⏳ |
| 8 | Final tests | ⏳ |

### Tests (from PHASE_11_TEST_SPEC.md)

| Suite | Count |
|-------|-------|
| Import Failures | 3 |
| Init Failures | 2 |
| Dependency Checking | 6 |
| Health API | 8 |
| Sandbox Runner | 6 |
| ToolRunner Integration | 4 |
| VideoTracker Stability | 4 |
| Metrics | 3 |
| Timeout/Memory Guards | 4 |
| **Total** | **40+** |

---

## File Structure (from PHASE_11_DIAGRAMS.md)

```
server/app/plugins/
├── loader/
│   ├── plugin_loader.py
│   ├── plugin_registry.py ← RWLock!
│   ├── dependency_checker.py ← dual GPU!
│   └── plugin_errors.py
├── sandbox/
│   ├── sandbox_runner.py
│   ├── timeout.py ← 60s default
│   └── memory_guard.py ← 1GB default
├── lifecycle/
│   ├── lifecycle_state.py
│   └── lifecycle_manager.py
└── health/
    ├── health_model.py
    └── health_router.py
```

---

## Pre-Commit Command (MANDATORY)

```bash
cd server && uv run pytest -v
cd server && uv run ruff check --fix app/
cd server && uv run mypy app/ --no-site-packages
cd web-ui && npm run type-check && npm run lint
```

---

## Links

- [Plans](./PHASE_11_PLANS.md)
- [Progress](./PHASE_11_PROGRESS.md)
- [Diagrams](./PHASE_11_DIAGRAMS.md)
- [Test Spec](./PHASE_11_TEST_SPEC.md)
- [Code Snippets](./PHASE_11_CODE_SNIPPETS.md)
