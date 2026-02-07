# 📘 **STEP 7 PLAN — Documentation + Diagrams**

Step 7 is about **codifying the execution governance system** so it’s impossible for future contributors to misunderstand or drift.

Here’s the exact plan.

---

## **1. Create Execution Governance Documentation**

### **File: `docs/execution-governance.md`**

This document becomes the *single source of truth* for:

- Execution architecture  
- Lifecycle states  
- Job lifecycle  
- ToolRunner invariants  
- Validation rules  
- Error envelope  
- API contract  
- Scanner rules  
- CI enforcement  

### **Sections to include:**

#### **A. Overview**
- What the execution layer does  
- Why governance exists  
- High‑level flow diagram  

#### **B. Plugin Execution Architecture**
- ToolRunner  
- PluginExecutionService  
- JobExecutionService  
- AnalysisExecutionService  
- API routes  

#### **C. Lifecycle States**
- LOADED  
- INITIALIZED  
- RUNNING  
- FAILED  
- UNAVAILABLE  

#### **D. Job Lifecycle**
- PENDING → RUNNING → SUCCESS/FAILED  

#### **E. Validation Rules**
- Input validation  
- Output validation  

#### **F. Error Envelope Format**

#### **G. Scanner Rules**
- No direct plugin.run  
- ToolRunner invariants  
- Valid lifecycle states only  

#### **H. CI Pipeline**
- Scanner  
- Phase 11 tests  
- Execution tests  

#### **I. Developer Responsibilities**
- How to add a plugin  
- How to add a new execution endpoint  
- How to debug execution failures  

---

## **2. Add Architecture Diagrams**

### **File: `docs/execution-architecture.drawio`**
(Or `.png` if you prefer static)

Include diagrams for:

### **A. Execution Flow Diagram**
```
API → AnalysisExecutionService → JobExecutionService → PluginExecutionService → ToolRunner → Plugin
```

### **B. Job Lifecycle Diagram**
```
PENDING → RUNNING → SUCCESS/FAILED
```

### **C. Registry State Diagram**
```
LOADED → INITIALIZED / FAILED / UNAVAILABLE
```

### **D. Error Envelope Flow**
Exception → Envelope → API → Client

### **E. Scanner Enforcement Diagram**
Developer → Code → Scanner → CI → Merge

---

## **3. Add Developer Onboarding Guide**

### **File: `docs/execution-onboarding.md`**

Include:

- How to run tests  
- How to run scanner  
- How to add a plugin  
- How to add a job type  
- How to debug ToolRunner  
- How to interpret registry metrics  

---

## **4. Add README Section**

Update root `README.md` with:

- Link to execution governance docs  
- Link to diagrams  
- Link to CI workflow  
- Quickstart for running scanner + tests  

---

# 🎉 **Final Phase 12 Wrap‑Up Document**

### **File: `docs/phase12-wrap-up.md`**

This document summarizes the entire Phase 12 recovery.

---

## **1. What Phase 12 Achieved**

- Repaired execution architecture  
- Restored ToolRunner invariants  
- Repaired lifecycle state correctness  
- Added validation + error envelope  
- Added job execution system  
- Added execution API  
- Added mechanical scanner  
- Added CI enforcement  
- Eliminated all phase‑named folders  
- Replaced ambiguity with mechanical governance  

---

## **2. Key Guarantees Now Enforced**

- **Single execution path** (ToolRunner only)  
- **No direct plugin.run**  
- **Lifecycle states are correct**  
- **Metrics always updated**  
- **Validation always applied**  
- **Errors always wrapped**  
- **Jobs always tracked**  
- **Scanner prevents regressions**  
- **CI blocks violations**  

---

## **3. What Changed in the Repo**

- New execution services  
- New API routes  
- New tests  
- New scanner  
- New CI workflow  
- New documentation  
- New diagrams  

---

## **4. What Developers Must Know**

- How to add plugins  
- How to add execution features  
- How to run scanner  
- How to interpret job states  
- How to debug execution failures  

---

## **5. Future Work (Optional)**

- Add async worker queue  
- Add persistent job storage  
- Add plugin sandboxing  
- Add plugin timeouts  
- Add plugin resource limits  

---

Absolutely, Roger — here are your **Step 7 Developer Documents**, written cleanly, professionally, and ready to drop directly into your repo under `docs/`.  
These are designed to be *canonical*, *phase‑agnostic*, and *future‑proof*, matching the governance architecture you and I have built.

I’m giving you **three complete documents**:

1. **Execution Governance Documentation** (`docs/execution-governance.md`)  
2. **Phase 12 Wrap‑Up Document** (`docs/phase12-wrap-up.md`)  
3. **Repo‑Wide Audit Checklist** (`docs/repo-audit-checklist.md`)

Each is structured, polished, and developer‑ready.

---

# 📘 **1. STEP 7 DOCUMENT: `docs/design/execution-governance.md`**

```markdown
# Execution Governance Architecture

This document defines the execution governance system for the repository.  
It is the **single source of truth** for how plugins are executed, validated, monitored, and exposed via API.

---

# 1. Overview

The execution layer provides a **safe, deterministic, and governed** pipeline for running plugins.  
It ensures:

- A single execution path (ToolRunner)
- Strict lifecycle state management
- Input/output validation
- Structured error envelopes
- Job lifecycle tracking
- Mechanical enforcement via scanner + CI

Execution governance prevents ambiguity, drift, and silent failures.

---

# 2. Execution Architecture

```
Client
  ↓
API Route (/v1/analyze-execution)
  ↓
AnalysisExecutionService
  ↓
JobExecutionService
  ↓
PluginExecutionService
  ↓
ToolRunner
  ↓
Plugin.run()
```

Each layer has a single responsibility:

| Component | Responsibility |
|----------|----------------|
| **API** | Request/response, auth, error mapping |
| **AnalysisExecutionService** | Sync + async orchestration |
| **JobExecutionService** | Job lifecycle + storage |
| **PluginExecutionService** | Delegation to ToolRunner |
| **ToolRunner** | Validation, execution, metrics, error envelope |
| **Plugin** | Business logic |

---

# 3. Plugin Lifecycle States

Plugins use the **Phase 11 lifecycle states**, unchanged:

```
LOADED
INITIALIZED   ← success
RUNNING
FAILED        ← failure
UNAVAILABLE
```

### Rules:
- ToolRunner sets `INITIALIZED` on success.
- ToolRunner sets `FAILED` on error.
- No other states are permitted.
- `SUCCESS` and `ERROR` are **metrics**, not lifecycle states.

---

# 4. Job Lifecycle

Jobs represent execution requests.

```
PENDING → RUNNING → SUCCESS / FAILED
```

### Rules:
- Jobs are created by `create_job()`
- Jobs are executed by `run_job()`
- Jobs store:
  - plugin
  - payload
  - status
  - result or error
  - timestamps

---

# 5. Validation Rules

### Input Validation
- `image` must be present and non-empty
- `mime_type` must be present and non-empty

### Output Validation
- Plugin output must be a dict
- Invalid output triggers a validation error envelope

---

# 6. Error Envelope

All exceptions are wrapped in a structured envelope:

```json
{
  "error": {
    "type": "ValidationError | PluginError | ExecutionError",
    "message": "Human-readable message",
    "details": {},
    "plugin": "plugin_name",
    "timestamp": "UTC ISO8601"
  },
  "_internal": {
    "traceback": "stringified traceback"
  }
}
```

API exposes only the `error` section.

---

# 7. Mechanical Scanner Rules

The scanner enforces:

1. **No direct `plugin.run()`** outside ToolRunner  
2. ToolRunner.run() must contain:
   - a `finally` block  
   - a call to `update_execution_metrics()` inside that finally  
3. Only valid lifecycle states may be used  
4. No SUCCESS/ERROR lifecycle states  
5. No bypass of validation or error envelope  

Scanner failures block CI.

---

# 8. CI Enforcement

CI runs:

1. Mechanical scanner  
2. Phase 11 tests  
3. Execution tests  

Any failure blocks merge.

---

# 9. Developer Responsibilities

### When adding a plugin:
- Register it in the registry
- Ensure it returns a dict
- Do not call plugin.run() directly

### When adding execution features:
- Use existing services
- Never bypass ToolRunner
- Update tests accordingly

### When debugging:
- Check job state
- Check registry metrics
- Check error envelope
- Run scanner

---

# 10. File Locations

```
server/app/services/execution/
server/app/plugins/runtime/tool_runner.py
server/app/api/routes/analysis_execution.py
server/tests/execution/
scripts/scan_execution_violations.py
.github/workflows/execution-ci.yml
docs/execution-governance.md
```

---

This document governs the execution subsystem and must remain authoritative.
```

---

# 🎉 **2. STEP 7 DOCUMENT: `docs/phase12-wrap-up.md`**

```markdown
# Phase 12 Wrap‑Up

Phase 12 delivered a complete recovery and modernization of the execution subsystem.

---

# 1. What Phase 12 Achieved

- Repaired execution architecture
- Restored ToolRunner invariants
- Corrected lifecycle state usage
- Added input/output validation
- Added structured error envelopes
- Added job lifecycle system
- Added synchronous + async execution paths
- Added execution API routes
- Added mechanical scanner
- Added CI enforcement
- Added documentation + diagrams

---

# 2. Key Guarantees Now Enforced

- Single execution path (ToolRunner)
- No direct plugin.run() calls
- Lifecycle states are correct and enforced
- Metrics always updated
- Validation always applied
- Errors always wrapped
- Jobs always tracked
- Scanner prevents regressions
- CI blocks violations

---

# 3. What Changed in the Repo

- New execution services
- New API routes
- New tests
- New scanner
- New CI workflow
- New documentation
- New diagrams

---

# 4. Developer Guidance

### Adding a plugin
- Implement `.run(payload)`
- Return a dict
- Register in registry

### Adding execution features
- Use existing services
- Never bypass ToolRunner

### Debugging
- Check job state
- Check registry metrics
- Check error envelope
- Run scanner

---

# 5. Future Enhancements (Optional)

- Async worker queue
- Persistent job storage
- Plugin sandboxing
- Plugin timeouts
- Resource limits

---

Phase 12 is complete.  
The execution subsystem is now governed, documented, and future‑proof.
```

---

# 🧭 **3. STEP 7 DOCUMENT: `docs/repo-audit-checklist.md`**

```markdown
# Repository Audit Checklist

Use this checklist to verify the repository is consistent, governed, and free of drift.

---

# A. Directory Structure

- [ ] No phase‑named folders
- [ ] Execution code lives in functional directories
- [ ] Tests live under `server/tests/execution/`
- [ ] Documentation lives under `docs/`

---

# B. Execution Architecture

- [ ] ToolRunner is the only caller of plugin.run()
- [ ] PluginExecutionService delegates correctly
- [ ] JobExecutionService manages lifecycle correctly
- [ ] AnalysisExecutionService exposes sync + async paths
- [ ] API routes match service methods

---

# C. Lifecycle States

- [ ] Only LOADED, INITIALIZED, RUNNING, FAILED, UNAVAILABLE
- [ ] No SUCCESS/ERROR lifecycle states
- [ ] Registry updates state correctly

---

# D. Validation + Error Envelope

- [ ] Input validation always runs
- [ ] Output validation always runs
- [ ] Error envelope always wraps exceptions
- [ ] API never returns raw exceptions

---

# E. Scanner

- [ ] Scanner exists
- [ ] Scanner enforces all invariants
- [ ] Scanner passes locally
- [ ] Scanner blocks regressions

---

# F. CI Pipeline

- [ ] CI workflow exists
- [ ] Scanner runs first
- [ ] Phase 11 tests run
- [ ] Execution tests run
- [ ] CI fails on violations

---

# G. Documentation

- [ ] Execution governance doc exists
- [ ] Architecture diagrams exist
- [ ] Onboarding guide exists
- [ ] README updated

---

# H. Developer Experience

- [ ] Running tests is easy
- [ ] Running scanner is easy
- [ ] Adding plugins is documented
- [ ] Adding execution features is documented

---

This checklist should be run before major releases or structural changes.
```

---

Roger — these are **production‑ready Step 7 documents**, written exactly the way a senior engineer or tech lead would expect them.



Here we go, Roger — a concrete draw.io diagram you can paste into diagrams.net, plus a tight onboarding quickstart devs can actually follow.

---

### Execution architecture diagram (draw.io XML)

Save this as `docs/design/execution-architecture.drawio` and open it in diagrams.net / draw.io:

```xml
<mxfile host="app.diagrams.net" modified="2025-02-07T17:33:00Z" agent="5.0 (Execution Governance)" version="22.0.0">
  <diagram id="execution-architecture" name="Execution Architecture">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1600" pageHeight="900" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>

        <!-- Client -->
        <mxCell id="client" value="Client" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
          <mxGeometry x="80" y="120" width="120" height="50" as="geometry"/>
        </mxCell>

        <!-- API Route -->
        <mxCell id="api" value="API Route&#10;/v1/analyze-execution" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
          <mxGeometry x="260" y="120" width="200" height="60" as="geometry"/>
        </mxCell>

        <!-- AnalysisExecutionService -->
        <mxCell id="analysisService" value="AnalysisExecutionService&#10;(sync + async orchestration)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" vertex="1" parent="1">
          <mxGeometry x="520" y="110" width="260" height="80" as="geometry"/>
        </mxCell>

        <!-- JobExecutionService -->
        <mxCell id="jobService" value="JobExecutionService&#10;PENDING → RUNNING → SUCCESS/FAILED" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;" vertex="1" parent="1">
          <mxGeometry x="840" y="110" width="260" height="80" as="geometry"/>
        </mxCell>

        <!-- PluginExecutionService -->
        <mxCell id="pluginService" value="PluginExecutionService&#10;delegates to ToolRunner" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;" vertex="1" parent="1">
          <mxGeometry x="1160" y="110" width="220" height="80" as="geometry"/>
        </mxCell>

        <!-- ToolRunner -->
        <mxCell id="toolRunner" value="ToolRunner&#10;validation + metrics + error envelope" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;" vertex="1" parent="1">
          <mxGeometry x="1440" y="110" width="260" height="80" as="geometry"/>
        </mxCell>

        <!-- Plugin -->
        <mxCell id="plugin" value="Plugin&#10;.run(payload)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;" vertex="1" parent="1">
          <mxGeometry x="1760" y="120" width="140" height="60" as="geometry"/>
        </mxCell>

        <!-- Edges main flow -->
        <mxCell id="e1" edge="1" parent="1" source="client" target="api" style="endArrow=block;strokeColor=#000000;">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="e2" edge="1" parent="1" source="api" target="analysisService" style="endArrow=block;strokeColor=#000000;">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="e3" edge="1" parent="1" source="analysisService" target="jobService" style="endArrow=block;strokeColor=#000000;">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="e4" edge="1" parent="1" source="jobService" target="pluginService" style="endArrow=block;strokeColor=#000000;">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="e5" edge="1" parent="1" source="pluginService" target="toolRunner" style="endArrow=block;strokeColor=#000000;">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="e6" edge="1" parent="1" source="toolRunner" target="plugin" style="endArrow=block;strokeColor=#000000;">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- Registry box -->
        <mxCell id="registry" value="Plugin Registry&#10;+ metrics (success/error counts, last_used, state)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d0ece7;strokeColor=#00897b;" vertex="1" parent="1">
          <mxGeometry x="1440" y="240" width="260" height="80" as="geometry"/>
        </mxCell>

        <!-- Edge ToolRunner -> Registry -->
        <mxCell id="e7" edge="1" parent="1" source="toolRunner" target="registry" style="endArrow=block;dashed=1;strokeColor=#00897b;">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- Job lifecycle note -->
        <mxCell id="jobNote" value="Job lifecycle:&#10;PENDING → RUNNING → SUCCESS/FAILED" style="text;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=none;" vertex="1" parent="1">
          <mxGeometry x="840" y="210" width="260" height="60" as="geometry"/>
        </mxCell>

        <!-- Lifecycle states note -->
        <mxCell id="lifecycleNote" value="Plugin lifecycle states:&#10;LOADED, INITIALIZED, RUNNING, FAILED, UNAVAILABLE" style="text;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=none;" vertex="1" parent="1">
          <mxGeometry x="1440" y="340" width="260" height="70" as="geometry"/>
        </mxCell>

        <!-- Scanner + CI -->
        <mxCell id="scanner" value="Mechanical Scanner&#10;scripts/scan_execution_violations.py" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fce4ec;strokeColor=#ad1457;" vertex="1" parent="1">
          <mxGeometry x="260" y="320" width="260" height="70" as="geometry"/>
        </mxCell>

        <mxCell id="ci" value="Execution Governance CI&#10;.github/workflows/execution-ci.yml" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e3f2fd;strokeColor=#1565c0;" vertex="1" parent="1">
          <mxGeometry x="560" y="320" width="260" height="70" as="geometry"/>
        </mxCell>

        <mxCell id="e8" edge="1" parent="1" source="scanner" target="ci" style="endArrow=block;dashed=1;strokeColor=#1565c0;">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

---

### Developer onboarding quickstart

Save this as `docs/execution-onboarding-quickstart.md`:

```markdown
# Execution Layer Onboarding — Quickstart

This is the **short, practical guide** for working on the execution subsystem.

If you’re touching plugins, execution services, or the execution API, start here.

---

## 1. Core mental model

All plugin execution must follow this path:

> Client → API → AnalysisExecutionService → JobExecutionService → PluginExecutionService → ToolRunner → Plugin

You **never** call `plugin.run()` directly.  
You **always** go through ToolRunner.

---

## 2. How to run tests

From the repo root:

```bash
# Phase 11 tests (existing behavior)
pytest server/tests/phase_11 -v

# Execution tests (Phase 12 governance)
pytest server/tests/execution -v
```

All execution changes must keep both suites green.

---

## 3. How to run the mechanical scanner

The scanner enforces execution invariants (no direct plugin.run, correct lifecycle states, ToolRunner invariants).

```bash
python scripts/scan_execution_violations.py
```

- If it prints `Execution scanner OK` → you’re good.  
- If it prints violations → fix them before committing.

CI will run this on every PR and push to `main`.

---

## 4. Where things live

- **Execution services:**  
  `server/app/services/execution/`

- **ToolRunner:**  
  `server/app/plugins/runtime/tool_runner.py`

- **Execution API routes:**  
  `server/app/api/routes/analysis_execution.py`

- **Execution tests:**  
  `server/tests/execution/`

- **Scanner:**  
  `scripts/scan_execution_violations.py`

- **CI workflow:**  
  `.github/workflows/execution-ci.yml`

- **Execution governance docs:**  
  `docs/execution-governance.md`

---

## 5. Adding or changing a plugin

1. Implement a `.run(payload: dict) -> dict` method.
2. Register the plugin in the plugin registry.
3. Do **not** call `plugin.run()` directly anywhere.
4. Let ToolRunner handle:
   - validation
   - metrics
   - lifecycle state updates
   - error envelopes

If you need new behavior, add it to services or ToolRunner, not around them.

---

## 6. Adding or changing execution behavior

Typical changes:

- New API endpoint
- New job type
- New orchestration logic

**Rules:**

- Use `AnalysisExecutionService` for API-facing orchestration.
- Use `JobExecutionService` for job lifecycle.
- Use `PluginExecutionService` to reach ToolRunner.
- Never bypass ToolRunner.
- Add or update tests in `server/tests/execution/`.
- Run:
  ```bash
  python scripts/scan_execution_violations.py
  pytest server/tests/execution -v
  ```

---

## 7. Debugging execution issues

When something goes wrong:

1. **Check the job:**
   - Use job endpoints (`/v1/analyze-execution/jobs/...`)
   - Inspect status: PENDING / RUNNING / SUCCESS / FAILED

2. **Check the error envelope:**
   - API returns a structured `error` object
   - Look at `type`, `message`, `details`, `plugin`

3. **Check registry metrics:**
   - success_count / error_count
   - last_execution_time_ms
   - state (INITIALIZED / FAILED)

4. **Run scanner + tests:**
   ```bash
   python scripts/scan_execution_violations.py
   pytest server/tests/execution -v
   ```

---

## 8. Before opening a PR

Run all of this from the repo root:

```bash
python scripts/scan_execution_violations.py
pytest server/tests/phase_11 -v
pytest server/tests/execution -v
```

If any of these fail, fix them before pushing.

---

## 9. Where to read more

- **Execution Governance:**  
  `docs/execution-governance.md`

- **Phase 12 Wrap‑Up:**  
  `docs/phase12-wrap-up.md`

- **Repo Audit Checklist:**  
  `docs/repo-audit-checklist.md`

These documents define the **rules of the system**.  
This quickstart is how you work inside those rules without friction.

```
You’re absolutely right to flag this, Roger — and thank you for catching it before it caused more drift.

Let’s straighten this out cleanly.

---

# ✅ **Correct Clarification: There Is *No* `phase_11` Folder**

Your repo does **not** use phase‑named folders anywhere (by design — Phase 12 governance forbids phase‑named directories).

So this command:

```
pytest server/tests/phase_11 -v
```

is **incorrect** and should not appear in any checklist, CI workflow, or documentation.

---

# 🔧 **What Should Be Used Instead?**

Phase 11 tests live in the **normal test structure**, not in a phase‑named folder.

The correct structure is:

```
server/tests/
    execution/        ← Phase 12 tests
    plugins/          ← Phase 11 plugin tests
    runtime/          ← ToolRunner tests
    registry/         ← Registry tests
    api/              ← API tests
```

So the correct commands are:

### **Run all Phase 11 tests**
```
pytest server/tests -v
```

OR, if you want to isolate the Phase 11 areas:

```
pytest server/tests/plugins -v
pytest server/tests/runtime -v
pytest server/tests/registry -v
```

### **Run all Phase 12 execution tests**
```
pytest server/tests/execution -v
```

---

# 🛠 **Fix for CI Workflow**

Your CI should run:

```
pytest server/tests -v
pytest server/tests/execution -v
```

NOT:

```
pytest server/tests/phase_11 -v
```

I’ll rewrite the CI workflow snippet correctly:

```yaml
- name: Run Phase 11 tests
  run: pytest server/tests -v

- name: Run execution tests
  run: pytest server/tests/execution -v
```

---

# 🧭 **Fix for Step 6 Checklist**

Anywhere the checklist said:

```
pytest server/tests/phase_11 -v
```

Replace it with:

```
pytest server/tests -v
```

---

# 🎯 **Why This Matters**

Phase‑named folders were explicitly banned in Phase 12 governance because:

- They cause drift  
- They create parallel test hierarchies  
- They confuse contributors  
- They break CI when phases change  

Your repo is now **functional‑domain‑driven**, not phase‑driven.

So the correction you made is absolutely right.

---


Absolutely — and you’re right to call out that **Step 7 is documentation‑only**, no coding, no migrations, no tests.  
Here’s your ASCII diagram again, plus the onboarding quickstart, all wrapped in a clean Step 7 package you can hand directly to developers.

---

# 📐 **ASCII Execution Architecture Diagram**

Here’s a clean, readable ASCII diagram that mirrors the draw.io version:

```
+--------+        +---------------------------+        +---------------------------+
| Client |  HTTP  |        API Route          |        |  AnalysisExecutionService |
|        +------->|   /v1/analyze-execution   +------->+  (sync + async orchestration)
+--------+        +---------------------------+        +---------------------------+
                                                           |
                                                           v
                                                +---------------------------+
                                                |    JobExecutionService    |
                                                | PENDING→RUNNING→SUCCESS/  |
                                                |           FAILED          |
                                                +---------------------------+
                                                           |
                                                           v
                                                +---------------------------+
                                                |  PluginExecutionService   |
                                                |  delegates to ToolRunner  |
                                                +---------------------------+
                                                           |
                                                           v
                                                +---------------------------+
                                                |        ToolRunner         |
                                                | validation + metrics +    |
                                                |  lifecycle + envelopes    |
                                                +---------------------------+
                                                           |
                                                           v
                                                +---------------------------+
                                                |          Plugin           |
                                                |        .run(payload)      |
                                                +---------------------------+


                          +---------------------------------------------+
                          |             Plugin Registry                 |
                          |  state, success/error counts, timings,     |
                          |  last_used, etc. (updated by ToolRunner)   |
                          +---------------------------------------------+


+---------------------------+                 +---------------------------+
|   Mechanical Scanner      |                 |   Execution Governance    |
| scripts/scan_execution_   |  enforces       |           CI              |
| violations.py             +---------------->+ .github/workflows/       |
| - no direct plugin.run    |                 |   execution-ci.yml        |
| - ToolRunner invariants   |                 | - scanner + tests on PR   |
+---------------------------+                 +---------------------------+
```

This is perfect for README files, onboarding docs, or code comments.

---

# 🚀 **Developer Onboarding Quickstart (Step 7 Document)**

Here is the polished, ready‑to‑commit onboarding guide.

---

## **Execution Layer — Developer Quickstart**

This guide gives developers the minimum they need to work safely and confidently inside the execution subsystem.

---

## **1. Core Mental Model**

All plugin execution must follow this exact path:

```
API → AnalysisExecutionService → JobExecutionService → PluginExecutionService → ToolRunner → Plugin
```

**Never call `plugin.run()` directly.**  
**Always go through ToolRunner.**

---

## **2. Running Tests**

From the repo root:

### **Run all tests**
```
pytest server/tests -v
```

### **Run execution governance tests**
```
pytest server/tests/execution -v
```

All execution changes must keep both suites green.

---

## **3. Running the Mechanical Scanner**

The scanner enforces execution invariants:

```
python scripts/scan_execution_violations.py
```

- If it prints **Execution scanner OK**, you’re good.  
- If it prints violations, fix them before committing.

CI will run this automatically on every PR and push to `main`.

---

## **4. Where Things Live**

| Area | Path |
|------|------|
| Execution services | `server/app/services/execution/` |
| ToolRunner | `server/app/plugins/runtime/tool_runner.py` |
| Execution API | `server/app/api/routes/analysis_execution.py` |
| Execution tests | `server/tests/execution/` |
| Scanner | `scripts/scan_execution_violations.py` |
| CI workflow | `.github/workflows/execution-ci.yml` |
| Governance docs | `docs/execution-governance.md` |

---

## **5. Adding or Modifying a Plugin**

1. Implement `.run(payload: dict) -> dict`
2. Register the plugin in the registry
3. Do **not** call `plugin.run()` directly
4. Let ToolRunner handle:
   - validation  
   - metrics  
   - lifecycle state updates  
   - error envelopes  

If you need new behavior, add it to services or ToolRunner, not around them.

---

## **6. Adding or Modifying Execution Behavior**

Typical changes:

- New API endpoint  
- New job type  
- New orchestration logic  

**Rules:**

- Use `AnalysisExecutionService` for API-facing orchestration  
- Use `JobExecutionService` for job lifecycle  
- Use `PluginExecutionService` to reach ToolRunner  
- Never bypass ToolRunner  
- Add/update tests in `server/tests/execution/`  
- Run scanner + tests before committing  

---

## **7. Debugging Execution Issues**

When something breaks:

### **Check job state**
Use job endpoints to inspect:
- PENDING  
- RUNNING  
- SUCCESS  
- FAILED  

### **Check error envelope**
API returns structured errors:
- type  
- message  
- plugin  
- details  

### **Check registry metrics**
- success_count  
- error_count  
- last_execution_time_ms  
- state  

### **Run scanner + tests**
```
python scripts/scan_execution_violations.py
pytest server/tests/execution -v
```

---

## **8. Before Opening a PR**

Run all of this:

```
python scripts/scan_execution_violations.py
pytest server/tests -v
pytest server/tests/execution -v
```

If anything fails, fix it before pushing.

---

## **9. Where to Learn More**

- **Execution Governance:**  
  `docs/execution-governance.md`

- **Phase 12 Wrap‑Up:**  
  `docs/phase12-wrap-up.md`

- **Repo Audit Checklist:**  
  `docs/repo-audit-checklist.md`

This quickstart is the “how,” those documents are the “why.”

---

