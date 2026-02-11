# Phase 13 — VideoTracker Multi‑Tool Pipelines
## Folder Structure (Canonical)

This is the **required** folder structure for Phase 13.  
All new files must be placed exactly here.

```
forgesyte/
├── server/
│   ├── app/
│   │   ├── routes_video.py
│   │   ├── services/
│   │   │   ├── video_pipeline_service.py      # NEW (Phase 13)
│   │   │   ├── vision_analysis_service.py     # UPDATED (Phase 13)
│   │   │   ├── plugin_management_service.py   # unchanged contract
│   │   ├── models/
│   │   │   ├── pipeline_models.py             # NEW (Phase 13)
│   │   ├── utils/
│   │   │   ├── logging/
│   │   │   │   ├── pipeline_logging.py        # NEW (Phase 13)
│   │   ├── tests/
│   │   │   ├── test_video_pipeline_rest.py    # NEW
│   │   │   ├── test_video_pipeline_ws.py      # NEW
│   │   │   ├── test_pipeline_validation.py    # NEW
│
├── web-ui/
│   ├── src/
│   │   ├── components/
│   │   │   ├── VideoTracker/
│   │   │   │   ├── VideoTracker.tsx           # UPDATED (Phase 13)
│   │   │   │   ├── PipelineToolSelector.tsx   # NEW (Phase 13)
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts                # UPDATED (Phase 13)
│   │   ├── api/
│   │   │   ├── videoPipeline.ts               # NEW (Phase 13)
│   │   ├── types/
│   │   │   ├── pipeline.ts                    # NEW (Phase 13)
│
├── docs/
│   ├── phases/
│   │   ├── PHASE_13_FOLDER_STRUCTURE.md       # THIS FILE
│   │   ├── PHASE_13_PR_TEMPLATE.md
│   │   ├── PHASE_13_MIGRATION_CHECKLIST.md
│   ├── governance/
│   │   ├── pipeline_rules.md                  # NEW (Phase 13)
│   ├── onboarding/
│   │   ├── PHASE_13_DEV_ONBOARDING.md         # NEW (Phase 13)
│
└── tools/
    ├── validate_pipeline.py                   # NEW (Phase 13)
    ├── migrate_phase13.py                     # NEW (Phase 13)
```

## Rules

This structure is **mandatory**.  
Any deviation must be rejected in PR review.

### File Placement Rules

1. **All Phase 13 services** → `server/app/services/`
2. **All Phase 13 models** → `server/app/models/`
3. **All Phase 13 logging** → `server/app/utils/logging/`
4. **All Phase 13 tests** → `server/app/tests/`
5. **All Phase 13 components** → `web-ui/src/components/VideoTracker/`
6. **All Phase 13 hooks** → `web-ui/src/hooks/`
7. **All Phase 13 API clients** → `web-ui/src/api/`
8. **All Phase 13 types** → `web-ui/src/types/`
9. **All Phase 13 docs** → `docs/phases/` or `docs/governance/` or `docs/onboarding/`

### PR Review Checklist

When reviewing Phase 13 PRs, verify:

- [ ] New files are in correct folders
- [ ] No files placed in root directories
- [ ] Services follow naming convention: `*_service.py`
- [ ] Models follow naming convention: `*_models.py`
- [ ] Tests follow naming convention: `test_*.py`
- [ ] Components follow naming convention: `PascalCase.tsx`
- [ ] Types follow naming convention: `*.ts`

### End of Phase 13

When Phase 13 is complete, this folder structure is permanent.  
No further reorganization.
