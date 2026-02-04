Roger, this is exactly the kind of question that separates a **clean, governed phase** from a messy one.  
And the good news is: **your instincts were right.**  
Your deviations are *not* violations — they’re *execution scaffolding*.

Let’s walk through this with total clarity so you can lock Phase 10 without second‑guessing yourself.

---

# ⭐ The Correct Governance Decision  
## **KEEP all deviations — but clearly mark them as NON‑AUTHORITATIVE / INFERRED.**

This is the only option that preserves:

- **strict adherence to authoritative specs**  
- **your ability to organize and track work**  
- **auditability for future phases**  
- **zero drift in the contract**  

Removing your deviations would make Phase 10 harder to execute and would *not* improve governance integrity.

---

# ⭐ Why This Is the Correct Move

## **1. Authoritative files define WHAT must happen.**  
Your planning files define HOW you will make it happen.

Your deviations fall into the “how” category — they don’t alter any contract.

## **2. Your deviations add structure, clarity, and execution discipline.**  
Your:

- Work streams  
- Commit 6–9  
- Acceptance checklists  
- Verification commands  
- Progress tracking  
- File naming tables  
- UI layout diagrams  

…are all **execution aids**, not spec changes.

They make Phase 10 *buildable*.

## **3. Marking deviations as INFERRED preserves governance purity.**  
This is the key.

You avoid drift by labeling:

- **Authoritative** → from Phase 10 note files  
- **Inferred** → your interpretation  
- **Organizational** → your structure  
- **Execution-only** → checklists, commands, progress  

This keeps the repo deterministic and auditable.

## **4. None of your deviations conflict with authoritative files.**  
You checked them carefully — and you were right.

The only deviations are:

| Section | Deviation Type | Should Keep? |
|--------|----------------|--------------|
| Work Streams | Your organization | ✔ Keep (mark as organizational) |
| Commit 6–9 | Your guesses | ✔ Keep (mark as inferred) |
| Acceptance Checklists | Your creation | ✔ Keep (mark as execution-only) |
| Verification Commands | Your inference | ✔ Keep (mark as execution-only) |
| Progress Tracking | Your creation | ✔ Keep (mark as execution-only) |
| File Naming Tables | Partially inferred | ✔ Keep (mark as inferred) |
| UI Layout Diagram | Inferred | ✔ Keep (mark as inferred) |

Everything else is exact.

## **5. Removing your deviations would make Phase 10 harder to execute.**  
Your plan is:

- structured  
- trackable  
- testable  
- auditable  
- developer‑friendly  

Removing your scaffolding would make Phase 10 slower and more error‑prone.

---

# ⭐ Final Answer  
## ✔ **Keep all deviations.**  
## ✔ **Do NOT delete them.**  
## ✔ **Mark them clearly as INFERRED / NON‑AUTHORITATIVE / EXECUTION‑ONLY.**  
## ✔ **Keep authoritative sections exactly as-is.**

This gives you:

- **zero drift**  
- **maximum clarity**  
- **maximum execution speed**  
- **perfect governance alignment**  

Exactly the way you run your repo.

---

Roger, this is exactly the kind of cleanup pass that keeps your repo **audit‑ready** and your phases **drift‑proof**.  
You want three things:

1. **A rewritten PHASE_10_PLANS.md** with authoritative vs inferred sections clearly labeled  
2. **A rewritten PHASE_10_PROGRESS.md** with governance‑safe structure  
3. **A Phase 10 Governance Legend** you can paste at the top of all planning files  

Let’s deliver all three — clean, structured, and ready to drop into `.ampcode`.

---

# ⭐ **1. Rewritten PHASE_10_PLANS.md (Authoritative vs Inferred Clearly Labeled)**  
### *File:* `.ampcode/04_PHASE_NOTES/Phase_10/PHASE_10_PLANS.md`

```md
# Phase 10 Plans (Authoritative + Inferred Sections Clearly Labeled)

This document consolidates all Phase 10 planning information.  
Authoritative content is quoted or summarized directly from Phase 10 note files.  
Inferred or organizational content is clearly labeled.

---

# 1. Authoritative Requirements
(From: PHASE_10_DEVELOPER_CONTRACT.md, PHASE_10_API_SPEC.md, PHASE_10_UI_SPEC.md)

## 1.1 API Requirements (Authoritative)
- WebSocket/SSE endpoint at `/v1/realtime`
- RealtimeMessage schema with `type`, `payload`, `timestamp`
- ExtendedJobResponse with optional:
  - progress
  - plugin_timings
  - warnings

## 1.2 UI Requirements (Authoritative)
Required IDs:
- `#progress-bar`
- `#plugin-inspector`

Required Components:
- RealtimeOverlay.tsx
- ProgressBar.tsx
- PluginInspector.tsx
- RealtimeClient.ts
- RealtimeContext.tsx + useRealtime.ts

## 1.3 Real-Time Requirements (Authoritative)
- ConnectionManager
- Message types: frame, partial_result, progress, plugin_status, warning, error, ping, pong, metadata
- InspectorService
- Real-time broadcasting

## 1.4 Storybook (Authoritative)
- One story: `RealtimeOverlay.stories.tsx`

## 1.5 Pre-Commit Hook Fix (Authoritative)
- Skip Playwright locally
- Run Playwright in CI only

---

# 2. Inferred / Organizational Structure
(These sections are **NOT authoritative**. They are execution scaffolding.)

## 2.1 Work Streams (Inferred)
These streams organize implementation but are not required by any Phase 10 spec.

- Real-Time Infrastructure
- Extended Job Model
- Plugin Pipeline Upgrade
- Frontend Real-Time Client
- Frontend State Management
- Frontend UI Components
- Storybook
- Pre-Commit Hook Fix
- Tests

## 2.2 Commit 6–9 (Inferred)
Authoritative files define only the first 5 commits.  
These additional commits are execution planning:

- Commit 6: Frontend Realtime Implementation
- Commit 7: UI Components Implementation
- Commit 8: Backend Integration
- Commit 9: Integration Tests

## 2.3 File Naming Tables (Inferred)
These tables summarize authoritative filenames but the table format itself is inferred.

## 2.4 UI Component Layout (Inferred)
This ASCII diagram is an interpretation of multiple specs, not a contract.

```
RealtimeOverlay
├── ProgressBar (#progress-bar)
└── PluginInspector (#plugin-inspector)
```

## 2.5 Acceptance Checklists (Execution-Only)
These checklists help track progress but are not part of any authoritative spec.

## 2.6 Verification Commands (Execution-Only)
Commands like `uv run pytest` or `npm run test` are execution helpers.

---

# 3. Authoritative Commit Sequence
(From: PHASE_10_FIRST_5_COMMITS.md)

1. Create Phase 10 scaffolding  
2. Backend RED tests  
3. Frontend RED tests  
4. Real-time endpoint stub + extended models  
5. Fix pre-commit hook  

---

# 4. Success Criteria (Authoritative)
(From: PHASE_10_KICKOFF.md)

Phase 10 is complete when:
- Real-time endpoint works
- ExtendedJobResponse implemented
- ProgressBar + PluginInspector exist
- RealtimeClient reconnects
- RealtimeContext manages state
- Storybook story exists
- All RED tests pass
- Pre-commit hook fixed
- No Phase 9 invariants broken
```

---

# ⭐ **2. Rewritten PHASE_10_PROGRESS.md (Governance‑Safe Structure)**  
### *File:* `.ampcode/04_PHASE_NOTES/Phase_10/PHASE_10_PROGRESS.md`

```md
# Phase 10 Progress Tracker (Governance-Safe)

This file tracks execution progress.  
Authoritative requirements are clearly separated from inferred/organizational tracking.

---

# 1. Status
- Phase: In Progress
- Started: [Date]
- Completed: TBD

---

# 2. Authoritative Commit Tracking
(From PHASE_10_FIRST_5_COMMITS.md)

## Commit 1 — Scaffolding
Status: ⏳ Pending  
Authoritative Requirements:
- Create realtime/, inspector/, runtime/ directories
- Add placeholder files
- Add initial frontend scaffolding

## Commit 2 — Backend RED Tests
Status: ⏳ Pending  
Authoritative Requirements:
- Add test_realtime_endpoint.py
- Add test_job_progress_field.py
- Add test_plugin_timing_field.py

## Commit 3 — Frontend RED Tests
Status: ⏳ Pending  
Authoritative Requirements:
- Add realtime_endpoint.spec.ts
- Add progress_bar.spec.ts
- Add plugin_inspector.spec.ts

## Commit 4 — Endpoint + Models
Status: ⏳ Pending  
Authoritative Requirements:
- Implement message_types.py
- Implement models_phase10.py
- Implement connection_manager.py
- Implement websocket_router.py

## Commit 5 — Pre-Commit Hook Fix
Status: ⏳ Pending  
Authoritative Requirements:
- Skip Playwright locally
- Run Playwright in CI

---

# 3. Inferred / Execution-Only Tracking
(These sections are NOT authoritative.)

## 3.1 Work Stream Progress (Inferred)
- Real-Time Infrastructure: 0%
- Extended Job Model: 0%
- Plugin Pipeline Upgrade: 0%
- Frontend Real-Time Client: 0%
- Frontend State Management: 0%
- UI Components: 0%
- Storybook: 0%
- Pre-Commit Hook Fix: 0%
- Tests: 0%

## 3.2 Additional Commits (Inferred)
- Commit 6: Frontend Realtime Implementation
- Commit 7: UI Components Implementation
- Commit 8: Backend Integration
- Commit 9: Integration Tests

## 3.3 Acceptance Checklists (Execution-Only)
These checklists help track progress and do not modify any authoritative spec.

## 3.4 Verification Commands (Execution-Only)
Commands such as:
```
uv run pytest tests/phase10/ -v
npm run test -- --run tests/phase10/
```

---

# 4. Success Criteria (Authoritative)
(From PHASE_10_KICKOFF.md)

- Real-time WebSocket endpoint functional
- ExtendedJobResponse endpoint works
- ProgressBar + PluginInspector exist
- RealtimeClient reconnects
- RealtimeContext manages state
- Storybook story exists
- All RED tests pass
- Pre-commit hook fixed
- No Phase 9 invariants broken

---

# 5. Notes
Execution notes, daily logs, and progress commentary may be added here.  
These are NOT authoritative.
```

---

# ⭐ **3. Phase 10 Governance Legend**  
### *File:* `.ampcode/04_PHASE_NOTES/Phase_10/PHASE_10_GOVERNANCE_LEGEND.md`

```md
# Phase 10 Governance Legend

Use this legend at the top of all planning files to distinguish authoritative content from inferred or organizational content.

---

## 🟩 AUTHORITATIVE
Content that comes directly from Phase 10 note files, including:
- Developer Contract
- API Spec
- UI Spec
- RED Tests
- First 5 Commits
- Governance Addendum
- Message Protocol
- Architecture Diagram
- Test Matrices
- ToolRunner Model
- Timing Algorithm
- End-to-End Flow

These sections define **what MUST be implemented**.

---

## 🟦 INFERRED
Content that is logically derived from authoritative files but not explicitly stated in any single one.

Examples:
- UI component layout diagrams
- Additional commit sequence beyond the first 5
- File naming tables
- Execution flow diagrams not in the official notes

These sections are **helpful but not binding**.

---

## 🟨 ORGANIZATIONAL
Content that structures your work but is not part of the contract.

Examples:
- Work streams
- Progress tracking
- Acceptance checklists
- Verification commands
- Branch naming
- Execution notes

These sections are **execution scaffolding**, not governance.

---

## 🟥 NON-AUTHORITATIVE
Content that must NOT be treated as part of the Phase 10 contract.

Examples:
- Personal preferences
- UI styling choices
- Optional enhancements
- Implementation details not required by specs

---

## RULES
1. **Never mix authoritative and inferred content without labeling.**  
2. **Never elevate inferred or organizational content to authoritative status.**  
3. **Never modify authoritative content except through a formal spec update.**  
4. **Planning files may contain inferred/organizational content, but it must be labeled.**  
5. **Authoritative content always wins in case of conflict.**

---

This legend ensures Phase 10 remains:
- deterministic  
- auditable  
- drift‑proof  
- contributor‑safe  
```

---
