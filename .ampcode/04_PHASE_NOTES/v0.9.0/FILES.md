Absolutely, Roger — now that you’ve provided **the real Phase‑15 and Phase‑16 deliveries**, we can finally produce the **correct, authoritative documentation set** without any drift, invention, or contamination from later phases.

Below is the **final, stable, canonical** set of documents you asked for:

- **OVERVIEW**  
- **HLD (High‑Level Design)**  
- **Functional Requirements**  
- **Non‑Functional Requirements**  
- **User Stories**  
- **Dev Plan (feature‑driven, no surprises)**  

Everything below is **grounded ONLY in the actual Phase‑15 and Phase‑16 deliveries you provided**, not in any imagined or future phases.

---

# ⭐ 1. OVERVIEW  
### *What Phase 15 + Phase 16 actually delivered — combined, clean, and correct*

## **Phase 15 — Synchronous Offline Batch Video Processing**
Phase 15 introduced:

- `POST /v1/video/process`  
- Synchronous MP4 upload  
- Frame extraction  
- YOLO + OCR pipeline (`yolo_ocr`)  
- 101 tests (unit, integration, stress, fuzz)  
- Strict governance (no async, no queues, no persistence)  
- Full documentation + demo scripts  

This was a **single‑shot, synchronous, stateless** video pipeline.

---

## **Phase 16 — Asynchronous Job‑Based Video Processing**
Phase 16 introduced:

- `POST /v1/video/submit`  
- `GET /v1/video/status/{job_id}`  
- `GET /v1/video/results/{job_id}`  
- Job queue (Redis or in‑memory)  
- Worker process  
- Persistent job state in DB  
- Object storage for MP4s  
- CI + smoke tests aligned to `/v1/*`  
- No breaking changes  
- No frontend changes  
- No plugin changes  
- No streaming  
- No Phase‑17 vocabulary  

Phase 16 is **infrastructure only**, wrapping Phase‑15’s synchronous pipeline inside an async job system.

---

# ⭐ 2. HIGH‑LEVEL DESIGN (HLD)

## **System Architecture**
```
Client
  → POST /v1/video/submit
      → Validate MP4
      → Save to object storage
      → Create job row in DB
      → Enqueue job_id
      → Return job_id

Worker
  → dequeue job_id
  → load job metadata
  → download MP4
  → run VideoFilePipelineService (Phase 15)
  → save results
  → mark completed

Client
  → GET /v1/video/status/{job_id}
  → GET /v1/video/results/{job_id}
```

## **Key Components**
- **API Layer**: `/v1/video/*`  
- **Queue Layer**: FIFO job queue  
- **Worker Layer**: Executes Phase‑15 pipeline  
- **Database Layer**: Persistent job state  
- **Object Storage**: MP4 storage  
- **Governance**: No streaming, no Phase‑17 vocabulary  

## **Phase 15 Integration**
Phase‑16 worker calls:

```
VideoFilePipelineService.process_video(...)
```

Exactly as Phase‑15 implemented it.

---

# ⭐ 3. FUNCTIONAL REQUIREMENTS (FR)

### **FR‑1: Video Submission**
System must accept MP4 uploads via `/v1/video/submit`.

### **FR‑2: Job Creation**
System must create a DB job row with status `pending`.

### **FR‑3: Job Queueing**
System must enqueue job_id for worker processing.

### **FR‑4: Worker Execution**
Worker must:
- dequeue job_id  
- load metadata  
- download MP4  
- run Phase‑15 pipeline  
- save results  
- update job status  

### **FR‑5: Status Retrieval**
`GET /v1/video/status/{job_id}` must return:
- status  
- progress  

### **FR‑6: Results Retrieval**
`GET /v1/video/results/{job_id}` must return:
- results if completed  
- 404 if not ready  

### **FR‑7: Persistence**
Job state must survive restarts.

### **FR‑8: Error Handling**
Failed jobs must store error_message and status `failed`.

### **FR‑9: Backward Compatibility**
No breaking changes to `/v1/*`.

---

# ⭐ 4. NON‑FUNCTIONAL REQUIREMENTS (NFR)

### **NFR‑1: Reliability**
- Worker crashes must not lose jobs  
- Queue must be durable  

### **NFR‑2: Scalability**
- Multiple workers may run concurrently  

### **NFR‑3: Determinism**
- Worker transitions must be predictable  

### **NFR‑4: Performance**
- Job submission must return immediately  
- Worker must process videos efficiently  

### **NFR‑5: Maintainability**
- No Phase‑17 vocabulary  
- No namespace migration  
- No frontend changes  

### **NFR‑6: Observability**
- `/v1/health` must remain stable  
- Logs must show job transitions  

---

# ⭐ 5. USER STORIES

### **US‑1: Submit Video for Processing**
As a user, I want to upload a video and receive a job_id so I can check progress later.

### **US‑2: Check Job Status**
As a user, I want to query job status so I know whether processing is done.

### **US‑3: Retrieve Results**
As a user, I want to retrieve results once the job is completed.

### **US‑4: Fault‑Tolerant Processing**
As a developer, I want jobs to survive worker crashes so no work is lost.

### **US‑5: Deterministic Worker Behavior**
As a developer, I want predictable worker transitions for debugging and monitoring.

### **US‑6: Backward Compatibility**
As a developer, I want all `/v1/*` endpoints to remain unchanged during Phase 16.

---

# ⭐ 6. DEV PLAN — *Feature‑Driven, No Surprises*

This is the plan that prevents the “4‑day launch and the plugin selector is gone” disaster.

Each commit delivers **one feature**, fully testable, fully reviewable.

---

## **Commit 1 — Job Model + DB Migration**
- Add `jobs` table  
- Add job status enum  
- Add job metadata fields  

## **Commit 2 — Object Storage Integration**
- Add file save/load  
- Add storage abstraction  

## **Commit 3 — Queue Integration**
- Add enqueue/dequeue  
- Add in‑memory queue for dev  

## **Commit 4 — `/v1/video/submit` Endpoint**
- Validate MP4  
- Save file  
- Create job row  
- Enqueue job_id  
- Return job_id  

## **Commit 5 — Worker Skeleton**
- Worker loop  
- dequeue job_id  
- load job  
- mark running  

## **Commit 6 — Worker Executes Phase‑15 Video Pipeline**
- Download MP4  
- Run VideoFilePipelineService  
- Save results  

## **Commit 7 — Status Endpoint**
- `/v1/video/status/{job_id}`  
- Return status + progress  

## **Commit 8 — Results Endpoint**
- `/v1/video/results/{job_id}`  
- Return results or 404  

## **Commit 9 — Health Endpoint Stabilization**
- Ensure `/v1/health` works  
- CI uses `/v1/health`  

## **Commit 10 — Smoke Test**
- End‑to‑end: submit → worker → status → results  

## **Commit 11 — Documentation**
- Update RELEASE_NOTES  
- Update architecture docs  
- Add Phase‑16 poster  

---

# ⭐ FINAL STATEMENT

This is the **correct, authoritative, non‑invented** documentation set for:

- Phase 15 (synchronous batch video)  
- Phase 16 (async job system)  

Everything is grounded in the real deliveries you provided.

If you want, I can now produce:

- Phase 16 → Phase 17 delta  
- Phase 17 overview  
- Phase 17 plugin integration plan  
- Phase 17 frontend restoration plan  

Just tell me which direction you want to go next.

Roger — this is a **strategic pivot**, not a technical one, and you’re making exactly the right call.

You’re saying:

- “Phase 17” as a name is poisoned  
- It drifted, regressed, broke patterns, broke Gemini‑CLI MCP extension  
- It introduced architectural chaos  
- It should NOT be treated as a real phase  
- It should be renamed to **v0.9.0** (a pre‑release, unstable, integration‑in‑progress build)  
- The *real* release should be **v1.0.0**, with **no new features**, only:
  - refactoring  
  - cleanup  
  - pattern enforcement  
  - fixing regressions  
  - aligning Gemini‑CLI MCP extension  
  - stabilizing the architecture  

This is the correct governance move.

Below is the **formal, clean, authoritative restructuring** of your release plan.

---

# ⭐ **OFFICIAL VERSIONING DECISION**

## ✅ **Rename “Phase 17” → `v0.9.0`**
This version is:

- unstable  
- experimental  
- partially implemented  
- contains regressions  
- contains architectural drift  
- contains broken Gemini‑CLI MCP extension  
- contains inconsistent patterns  
- contains unreviewed code  
- contains missing UI elements (plugin selector, image upload)  

This is **not** a real phase.  
This is a **pre‑release integration build**.

### **v0.9.0 = Integration Chaos Sandbox**  
Not a milestone.  
Not a release.  
Not a phase.

---

## ✅ **Rename “Phase 18” → `v1.0.0`**
This version is:

- the **actual release**  
- no new features  
- pure stabilization  
- refactoring  
- cleanup  
- restoring patterns  
- fixing regressions  
- aligning Gemini‑CLI MCP extension  
- ensuring plugin system works  
- ensuring image + video flows work  
- ensuring UI is consistent  
- ensuring backend is consistent  
- ensuring tests pass  
- ensuring governance rules are enforced  

### **v1.0.0 = Real Release**  
Stable.  
Documented.  
Pattern‑aligned.  
MCP‑compatible.  
Production‑ready.

---

# ⭐ **WHAT v1.0.0 MUST DELIVER (NO NEW FEATURES)**

## 1. **Refactor & Cleanup**
- Remove drift  
- Remove dead code  
- Remove inconsistent patterns  
- Restore architectural clarity  
- Re‑align with Phase 15 + Phase 16 foundations  

## 2. **Fix Regressions**
- Restore plugin selector  
- Restore image upload  
- Restore tool selection  
- Fix broken Gemini‑CLI MCP extension  
- Fix Phase 17 regressions in plugin architecture  
- Fix missing UI elements  

## 3. **Stabilize Architecture**
- Ensure pipeline registry is correct  
- Ensure plugin_types are correct  
- Ensure Phase 15 video engine integration is correct  
- Ensure Phase 16 async job system is correct  

## 4. **Governance Enforcement**
- Enforce patterns  
- Enforce folder structure  
- Enforce naming conventions  
- Enforce contributor rules  
- Enforce forbidden vocabulary  

## 5. **Gemini‑CLI MCP Extension**
This is the **actual goal of the project**.

v1.0.0 must deliver:

- A stable MCP server  
- A stable MCP schema  
- A stable plugin interface  
- A stable tool interface  
- A stable pipeline interface  
- A stable image/video processing interface  
- A stable Gemini‑CLI extension  

---

# ⭐ **WHY THIS IS THE RIGHT MOVE**

### ✔ It resets the narrative  
Phase 17 was chaos.  
v0.9.0 is allowed to be chaos.

### ✔ It protects the release  
v1.0.0 becomes clean, stable, predictable.

### ✔ It aligns with semantic versioning  
- 0.x = unstable  
- 1.0 = stable release  

### ✔ It stops the drift  
No more “Phase 17 fantasy architecture”.

### ✔ It gives you a clean runway  
v1.0.0 becomes a **stabilization milestone**, not a feature dump.

### ✔ It protects Gemini‑CLI MCP  
The extension must be built on a stable backend.  
v1.0.0 gives you that.

---

# ⭐ **NEXT STEPS (I can generate these if you want)**

If you want, I can now produce:

### **1. v0.9.0 Release Notes (Phase 17 → renamed)**  
- What’s in  
- What’s broken  
- What’s experimental  
- What’s regressed  

### **2. v1.0.0 Release Plan**  
- Scope  
- Non‑scope  
- Deliverables  
- Architecture cleanup plan  
- MCP integration plan  
- UI restoration plan  

### **3. v1.0.0 Migration Plan**  
- Code cleanup  
- Folder structure cleanup  
- Plugin architecture cleanup  
- UI restoration  
- MCP extension alignment  

### **4. v1.0.0 Governance Rules**  
- No new features  
- Only stabilization  
- Only refactoring  
- Only regression fixes  

### **5. v1.0.0 Project Board**  
- Epics  
- Stories  
- Tasks  
- Acceptance criteria  

Just tell me which one you want next.

Roger — here is the **full, formal, production‑ready documentation set** you asked for.  
It reflects the **real history**:

- **Phase 15 = v0.8.0** (stable synchronous batch video)  
- **Phase 16 = v0.8.1** (stable async job system)  
- **Phase 17 = v0.9.0** (unstable, regressed, experimental, broken)  
- **Phase 18 = v1.0.0** (the real release: stabilization, cleanup, MCP alignment, no new features)

Everything below is clean, structured, and ready to drop into your repo.

---

# ⭐ **1. v0.9.0 RELEASE NOTES (Phase 17 → Renamed)**  
### *This is the honest, factual record of what Phase 17 actually delivered.*

---

# **v0.9.0 — Experimental Integration Build (Formerly Phase 17)**  
**Status:** Unstable / Not for Production  
**Tagline:** “Integration chaos sandbox — not a real release.”

---

## ✅ **WHAT’S IN (Actual Deliveries)**

### **Backend**
- Partial plugin updates (minimal changes)
- Added `source_video_path` guard to 5 plugin run methods
- Partial image_bytes support in plugins
- Some attempts at pipeline‑aware config

### **Frontend**
- Partial rewrite targeting streaming (not delivered)
- Removal of:
  - plugin selector  
  - tool selector  
  - image upload  
- New UI components not wired to backend

### **Infrastructure**
- None (Phase 16 infra remained intact)

---

## ❌ **WHAT’S BROKEN**

### **Frontend**
- Plugin selector removed  
- Tool selector removed  
- Image upload removed  
- Video upload partially broken  
- UI cannot select pipelines  
- UI cannot select tools  
- UI cannot select plugins  

### **Backend**
- Plugin architecture partially inconsistent  
- Some plugin manifests outdated  
- Some plugin types mismatched  
- Gemini‑CLI MCP extension broken  
- No compatibility with Phase 16 async job system  
- No compatibility with Phase 15 synchronous pipeline  

---

## ⚠️ **WHAT’S EXPERIMENTAL**

- Early streaming experiments (not functional)
- Partial real‑time architecture (not integrated)
- Partial plugin refactor (incomplete)
- Partial pipeline config redesign (incomplete)

---

## ⛔ **WHAT’S REGRESSED**

- Frontend lost core functionality  
- Gemini‑CLI MCP extension no longer works  
- Plugin selector removed  
- Image upload removed  
- Tool selection removed  
- UI → backend contract broken  
- Plugin architecture drifted  
- Folder structure drifted  
- Coding patterns inconsistent  
- Tests not updated  
- No governance enforcement  

---

# ⭐ **2. v1.0.0 RELEASE PLAN**  
### *The real release. No new features. Only stabilization.*

---

# **v1.0.0 — Stable Release**  
**Goal:** Deliver a stable MCP‑compatible backend + frontend with clean architecture and zero regressions.

---

## 🎯 **SCOPE (What v1.0.0 WILL deliver)**

### **1. Architecture Cleanup**
- Remove Phase 17 drift  
- Restore Phase 15 + 16 correctness  
- Re‑align plugin architecture  
- Re‑align pipeline registry  
- Re‑align folder structure  
- Remove dead code  
- Remove experimental streaming code  

### **2. UI Restoration**
- Restore plugin selector  
- Restore tool selector  
- Restore image upload  
- Restore video upload  
- Restore pipeline selection  
- Ensure UI matches backend contract  

### **3. MCP Integration**
- Deliver a stable MCP server  
- Deliver a stable MCP schema  
- Deliver a stable Gemini‑CLI extension  
- Ensure plugin + pipeline interfaces are MCP‑compatible  

### **4. Regression Fixes**
- Fix broken plugins  
- Fix broken manifests  
- Fix broken pipeline configs  
- Fix broken UI flows  
- Fix broken MCP extension  

### **5. Governance Enforcement**
- Enforce patterns  
- Enforce naming conventions  
- Enforce folder structure  
- Enforce forbidden vocabulary  
- Enforce contributor rules  

---

## 🚫 **NON‑SCOPE (What v1.0.0 WILL NOT deliver)**

- No new features  
- No streaming  
- No real‑time inference  
- No new plugin types  
- No new pipelines  
- No new UI features  
- No new endpoints  
- No new architecture  

v1.0.0 is **stabilization only**.

---

## 📦 **DELIVERABLES**

- Stable backend  
- Stable frontend  
- Stable plugin system  
- Stable pipeline registry  
- Stable MCP server  
- Stable Gemini‑CLI extension  
- Full documentation  
- Full governance enforcement  
- Full test suite passing  

---

## 🧱 **ARCHITECTURE CLEANUP PLAN**

### **Backend**
- Remove Phase 17 drift  
- Restore Phase 15 + 16 correctness  
- Rebuild plugin architecture  
- Rebuild pipeline registry  
- Rebuild folder structure  
- Remove dead code  

### **Frontend**
- Restore plugin selector  
- Restore tool selector  
- Restore image upload  
- Restore video upload  
- Restore pipeline selection  

### **Tests**
- Rebuild test suite  
- Add regression tests  
- Add MCP tests  

---

## 🔌 **MCP INTEGRATION PLAN**

### **Backend**
- Implement MCP server  
- Implement MCP schema  
- Implement MCP tool interface  
- Implement MCP plugin interface  
- Implement MCP pipeline interface  

### **Gemini‑CLI Extension**
- Fix regressions  
- Align with new MCP server  
- Add tests  
- Add documentation  

---

## 🎨 **UI RESTORATION PLAN**

- Restore plugin selector  
- Restore tool selector  
- Restore image upload  
- Restore video upload  
- Restore pipeline selection  
- Ensure UI → backend contract is correct  

---

# ⭐ **3. v1.0.0 MIGRATION PLAN**

---

## 🧹 **CODE CLEANUP**
- Remove Phase 17 drift  
- Remove unused files  
- Remove experimental streaming code  
- Remove broken plugin code  
- Remove broken UI code  

---

## 📁 **FOLDER STRUCTURE CLEANUP**
- Reorganize plugins  
- Reorganize pipelines  
- Reorganize UI components  
- Reorganize MCP extension  

---

## 🔧 **PLUGIN ARCHITECTURE CLEANUP**
- Restore Phase 15 + 16 plugin correctness  
- Fix manifests  
- Fix plugin types  
- Fix tool definitions  
- Fix run methods  
- Fix image_bytes + video_path handling  

---

## 🎨 **UI RESTORATION**
- Restore plugin selector  
- Restore tool selector  
- Restore image upload  
- Restore video upload  
- Restore pipeline selection  

---

## 🔌 **MCP EXTENSION ALIGNMENT**
- Fix Gemini‑CLI extension  
- Align with MCP server  
- Add tests  
- Add documentation  

---

# ⭐ **4. v1.0.0 GOVERNANCE RULES**

---

## 🚫 **NO NEW FEATURES**
Only stabilization.

## 🔧 **ONLY REFACTORING**
Architecture cleanup only.

## 🛠️ **ONLY REGRESSION FIXES**
Fix what Phase 17 broke.

## 🧱 **PATTERN ENFORCEMENT**
- Folder structure  
- Naming conventions  
- Plugin architecture  
- Pipeline architecture  
- UI architecture  

## 📜 **STRICT GOVERNANCE**
- Forbidden vocabulary  
- Contributor rules  
- Code review rules  
- Documentation rules  

---

# ⭐ **5. v1.0.0 PROJECT BOARD**

---

# **EPICS**

### **Epic 1 — Architecture Cleanup**
Restore Phase 15 + 16 correctness.

### **Epic 2 — UI Restoration**
Restore plugin selector, tool selector, image upload, video upload.

### **Epic 3 — Plugin Architecture Fix**
Fix manifests, plugin types, tool definitions.

### **Epic 4 — MCP Integration**
Deliver stable MCP server + Gemini‑CLI extension.

### **Epic 5 — Governance Enforcement**
Enforce patterns, naming, folder structure.

---

# **USER STORIES**

### **Story 1 — As a user, I can upload images again.**
### **Story 2 — As a user, I can select plugins again.**
### **Story 3 — As a user, I can select tools again.**
### **Story 4 — As a user, I can upload videos again.**
### **Story 5 — As a developer, the plugin architecture is consistent.**
### **Story 6 — As a developer, the MCP extension works.**
### **Story 7 — As a developer, the UI matches backend contract.**
### **Story 8 — As a developer, the codebase follows patterns.**

---

# **TASKS**

- Remove Phase 17 drift  
- Restore Phase 15 + 16 correctness  
- Fix plugin manifests  
- Fix plugin types  
- Fix tool definitions  
- Restore UI components  
- Fix MCP extension  
- Add tests  
- Add documentation  

---

# **ACCEPTANCE CRITERIA**

- All regressions fixed  
- All UI restored  
- All plugins functional  
- All pipelines functional  
- MCP extension works  
- All tests pass  
- All governance rules enforced  
- No new features added  
- Codebase stable and clean  

---

Roger, here it is — **the full GitHub‑ready package**, clean, structured, and aligned with your new release strategy:

- **v0.9.0 Release Notes**  
- **v1.0.0 Release Plan**  
- **v1.0.0 Migration Guide**  
- **v1.0.0 Governance Rules**  
- **v1.0.0 Project Board**  

Everything below is written exactly the way a senior architect would prepare it for a real repo.

---

# ⭐ **1. GitHub Project Board (v1.0.0 Stabilization)**  
### *Columns + Epics + Cards — ready to paste into GitHub Projects*

## **Columns**
1. **Backlog**  
2. **Ready**  
3. **In Progress**  
4. **Review**  
5. **Testing**  
6. **Done**

---

## **Epics (as Labels or Milestones)**

### **Epic: Architecture Cleanup**
- Remove Phase‑17 drift  
- Restore Phase‑15/16 correctness  
- Fix folder structure  
- Remove dead code  
- Fix pipeline registry  

### **Epic: UI Restoration**
- Restore plugin selector  
- Restore tool selector  
- Restore image upload  
- Restore video upload  
- Restore pipeline selection  

### **Epic: Plugin Architecture Fix**
- Fix manifests  
- Fix plugin types  
- Fix tool definitions  
- Fix image_bytes + video_path handling  

### **Epic: MCP Integration**
- Implement MCP server  
- Implement MCP schema  
- Align Gemini‑CLI extension  
- Add MCP tests  

### **Epic: Governance Enforcement**
- Enforce naming conventions  
- Enforce folder structure  
- Enforce forbidden vocabulary  
- Enforce contributor rules  

---

## **Example Cards (Tasks)**

### **Architecture Cleanup**
- Remove unused Phase‑17 streaming code  
- Remove broken plugin experiments  
- Restore Phase‑15 pipeline correctness  
- Rebuild pipeline registry  
- Normalize folder structure  

### **UI Restoration**
- Re‑add plugin selector component  
- Re‑add tool selector component  
- Re‑add image upload flow  
- Re‑add video upload flow  
- Reconnect UI → backend pipeline_id  

### **Plugin Architecture Fix**
- Fix plugin manifests  
- Fix plugin types  
- Fix run() signatures  
- Fix image_bytes handling  
- Fix video_path guard logic  

### **MCP Integration**
- Implement MCP server  
- Implement MCP schema  
- Implement MCP tool interface  
- Implement MCP plugin interface  
- Fix Gemini‑CLI extension  
- Add MCP integration tests  

### **Governance**
- Add folder structure validator  
- Add naming convention validator  
- Add forbidden vocabulary rules  
- Add contributor guidelines  

---

# ⭐ **2. CHANGELOG**

```
# CHANGELOG.md

## v1.0.0 (Upcoming)
### Added
- MCP server implementation
- MCP schema + tool interface
- Restored plugin selector, tool selector, image upload, video upload
- Full UI → backend pipeline integration
- Governance enforcement (naming, structure, vocabulary)

### Changed
- Refactored plugin architecture to restore Phase‑15/16 correctness
- Rebuilt pipeline registry
- Cleaned folder structure
- Fixed Gemini‑CLI MCP extension

### Removed
- Phase‑17 streaming experiments
- Broken plugin prototypes
- Dead code and unused modules

### Fixed
- Regressions introduced in v0.9.0
- Plugin manifest inconsistencies
- Pipeline config mismatches
- UI regressions (missing selectors, missing upload flows)
- MCP extension failures

---

## v0.9.0 (Formerly Phase 17)
### Added
- Partial plugin updates
- Minimal video_path guard logic
- Partial image_bytes support

### Changed
- Partial frontend rewrite (incomplete)

### Removed
- Plugin selector (regression)
- Tool selector (regression)
- Image upload (regression)

### Broken
- Gemini‑CLI MCP extension
- UI → backend contract
- Plugin architecture consistency

---

## v0.8.1 (Phase 16)
### Added
- Async job submission
- Worker execution
- Persistent job state
- Results retrieval

### Changed
- None (backward compatible)

---

## v0.8.0 (Phase 15)
### Added
- Synchronous batch video processing
- YOLO + OCR pipeline
- 101 tests (unit, integration, stress, fuzz)
- Governance enforcement
```

---

# ⭐ **3. v1.0.0 MIGRATION GUIDE**

```
# v1.0.0 MIGRATION GUIDE

## Overview
v1.0.0 is a stabilization release. No new features. Only:
- cleanup
- refactoring
- regression fixes
- MCP alignment
- UI restoration

---

## 1. Code Cleanup
- Remove Phase‑17 streaming code
- Remove unused plugin experiments
- Remove dead modules
- Remove broken UI components
- Remove unused pipeline definitions

---

## 2. Folder Structure Cleanup
- Consolidate plugins under /plugins
- Consolidate pipelines under /pipelines
- Move UI components into /web-ui/components
- Normalize naming conventions
- Remove duplicate or legacy folders

---

## 3. Plugin Architecture Cleanup
- Restore Phase‑15/16 plugin correctness
- Fix manifests
- Fix plugin types
- Fix tool definitions
- Fix run() signatures
- Fix image_bytes + video_path handling

---

## 4. UI Restoration
- Restore plugin selector
- Restore tool selector
- Restore image upload
- Restore video upload
- Restore pipeline selection
- Reconnect UI → backend pipeline_id

---

## 5. MCP Extension Alignment
- Implement MCP server
- Implement MCP schema
- Implement MCP tool interface
- Implement MCP plugin interface
- Fix Gemini‑CLI extension
- Add MCP integration tests

---

## 6. Testing
- Add regression tests
- Add MCP tests
- Add UI → backend integration tests
- Ensure all Phase‑15/16 tests pass
```

---

# ⭐ **4. v1.0.0 GOVERNANCE RULES**

```
# v1.0.0 GOVERNANCE RULES

## 1. No New Features
v1.0.0 is stabilization only.

## 2. Only Refactoring
Architecture cleanup only.

## 3. Only Regression Fixes
Fix what v0.9.0 broke.

## 4. Pattern Enforcement
- Folder structure
- Naming conventions
- Plugin architecture
- Pipeline architecture
- UI architecture

## 5. Forbidden Vocabulary
- No streaming
- No WebSockets
- No GPU scheduling
- No distributed workers
- No Phase‑17 vocabulary

## 6. Contributor Rules
- All PRs must include tests
- All PRs must include documentation
- All PRs must pass governance checks
- All PRs must be atomic and reviewable
```

---

# ⭐ **5. v1.0.0 PROJECT BOARD (Detailed)**

## **Epic 1 — Architecture Cleanup**
### Stories
- Restore Phase‑15/16 correctness
- Remove Phase‑17 drift
- Fix pipeline registry
- Normalize folder structure

### Tasks
- Remove streaming code
- Remove broken plugin experiments
- Rebuild pipeline registry
- Clean folder structure

### Acceptance Criteria
- No Phase‑17 code remains
- All pipelines load correctly
- Folder structure is normalized

---

## **Epic 2 — UI Restoration**
### Stories
- Restore plugin selector
- Restore tool selector
- Restore image upload
- Restore video upload

### Tasks
- Rebuild plugin selector component
- Rebuild tool selector component
- Rebuild upload flows
- Reconnect UI → backend

### Acceptance Criteria
- UI can select plugin + tools
- UI can upload image + video
- UI can run pipelines end‑to‑end

---

## **Epic 3 — Plugin Architecture Fix**
### Stories
- Fix manifests
- Fix plugin types
- Fix tool definitions

### Tasks
- Normalize manifests
- Fix plugin types
- Fix run() signatures

### Acceptance Criteria
- All plugins load
- All tools run
- No manifest errors

---

## **Epic 4 — MCP Integration**
### Stories
- Implement MCP server
- Implement MCP schema
- Fix Gemini‑CLI extension

### Tasks
- Build MCP server
- Build MCP schema
- Align Gemini‑CLI extension

### Acceptance Criteria
- Gemini‑CLI works end‑to‑end
- MCP tests pass

---

## **Epic 5 — Governance Enforcement**
### Stories
- Enforce naming conventions
- Enforce folder structure
- Enforce forbidden vocabulary

### Tasks
- Add validators
- Add CI checks

### Acceptance Criteria
- All PRs pass governance checks
- No forbidden vocabulary
- No structural drift

---
