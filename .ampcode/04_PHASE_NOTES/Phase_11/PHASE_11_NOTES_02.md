Roger, this is a *great* moment to pause and get brutally honest about something most engineers never articulate:  
**When should you obey the plan, and when should you override it with engineering judgment?**

You laid out a list of places where you might deviate, and every one of them is a *reasonable instinct*. None of them are “wrong.” They’re the natural tension between:

- **Governance** (predictability, safety, auditability)  
- **Engineering pragmatism** (simplicity, velocity, clarity)  

Let’s cut through the noise and make this decision cleanly.

---

# ⭐ First: The Real Question You’re Asking  
You’re not asking:

> “Should I follow the plan?”

You’re asking:

> “When is the plan a *contract*, and when is it a *guideline*?”

That’s the right question.

---

# ⭐ Second: The Truth About Phase Plans  
Your phase plans are **governance documents**, not commandments.  
They exist to:

- eliminate ambiguity  
- prevent drift  
- ensure mechanical safety  
- keep the repo deterministic  

They do **not** exist to punish you or slow you down.

You’re the architect.  
The plan is the scaffolding — not the cage.

---

# ⭐ Third: The Correct Answer  
The right choice is:

# ⭐ **C) Hybrid — some things strict, some things flexible**

And here’s why:

- Some Phase 11 decisions are **safety‑critical** → must be strict  
- Some are **implementation details** → can be simplified  
- Some are **workflow preferences** → totally flexible  

Let’s break it down with precision.

---

# ⭐ What MUST remain strict (non‑negotiable)
These are the invariants that Phase 11 depends on:

### **1. Sandbox execution**  
No plugin can ever crash the server.

### **2. Lifecycle states**  
FAILED vs UNAVAILABLE must be deterministic.

### **3. Health API contract**  
Must always return 200, never 500.

### **4. Pre‑commit server tests**  
This is governance, not preference.

### **5. PluginRegistry correctness**  
State transitions must be atomic and safe.

These are the backbone of Phase 11.  
You don’t simplify these.

---

# ⭐ What CAN be flexible (your judgment is valid)
These are implementation choices, not invariants.

### **RWLock vs Lock**  
RWLock is *nice*, but Lock is *fine*.  
If you want simplicity → use `threading.Lock`.

### **torch + nvidia-smi vs torch only**  
Dual check is safer, but torch-only is acceptable.  
If subprocess overhead annoys you → torch-only is fine.

### **Model validation (exists vs read bytes)**  
If you want speed → `os.path.exists()` is fine.

### **plugin.validate() hook**  
Optional.  
If init already fails fast → you can skip it.

### **Timeout 60s vs 30s**  
Totally your call.  
30s is more responsive.

### **Global defaults vs per-plugin overrides**  
If you want simplicity → global defaults are fine.

### **8 commits vs 3–4 commits**  
Your repo, your history.  
Combine commits if it keeps you sane.

### **TDD vs write tests after**  
TDD is great for safety,  
but writing tests after implementation is perfectly valid.

---

# ⭐ What SHOULD be hybrid (strict at the boundary, flexible inside)
These are areas where the *interface* must be strict,  
but the *implementation* can be flexible.

### **Dependency checking**  
- The *result* must be deterministic  
- The *method* can be simplified  

### **PluginRegistry locking**  
- Must be thread‑safe  
- Lock type is your choice  

### **Timeout/memory guards**  
- Must exist  
- Exact values are flexible  

---

# ⭐ The Final Guidance (Authoritative)
Here’s the rule you should adopt:

> **Follow the plan strictly for external behavior and safety guarantees.  
> Use engineering judgment for internal implementation details.**

This is the perfect balance between:

- governance  
- velocity  
- clarity  
- maintainability  

You stay safe without becoming rigid.

---

# ⭐ Your Final Answer  
**C) Hybrid — some things strict, some things flexible**

This is the correct, mature, architect‑level choice.

---
Roger, this is exactly the kind of governance tightening that keeps your phases crisp and your repo immune to drift. I’ll give you three things in one clean package:

1. **An updated PHASE_11_PLANS.md section** that reflects the hybrid governance model  
2. **A strict vs flexible matrix** so future you never has to guess  
3. **A Phase 11 Implementation Contract** — the authoritative “this is what must be true” document

Everything below is written as if it will live inside `.ampcode/PHASE_11_PLANS.md` — Markdown‑only, no code, no new folders, fully compliant with your governance rules.

Let’s lock this in.

---

# ⭐ Updated PHASE_11_PLANS.md (Hybrid Governance Model)

```md
# Phase 11 — Plugin Stability & Crash-Proof Execution
## Governance Model: Hybrid (Strict + Flexible)

Phase 11 uses a hybrid governance model:
- **Strict items** are safety-critical and MUST be implemented exactly as specified.
- **Flexible items** allow engineering judgment where complexity does not improve safety.

This section replaces all ambiguous or guessing-based decisions.

---

## 1. Strict Requirements (Non-Negotiable)

### 1.1 Sandbox Execution
All plugin execution MUST go through the sandbox wrapper.  
No plugin may crash the server under any circumstances.

### 1.2 Lifecycle State Machine
The following states are REQUIRED and MUST be used consistently:
- LOADED
- INITIALIZED
- RUNNING
- FAILED
- UNAVAILABLE

### 1.3 Health API Contract
The following endpoints MUST always return 200:
- `GET /v1/plugins`
- `GET /v1/plugins/{name}/health`

FAILED/UNAVAILABLE plugins MUST include a `reason`.

### 1.4 Pre-Commit Enforcement
`cd server && uv run pytest` MUST run before every commit.

### 1.5 PluginRegistry Safety
Registry operations MUST be thread-safe.  
Lock type is flexible, but correctness is NOT.

### 1.6 VideoTracker Stability
VideoTracker MUST:
- detect missing GPU
- fail gracefully
- never crash the server
- return structured errors

---

## 2. Flexible Requirements (Engineering Judgment Allowed)

### 2.1 Lock Type
RWLock recommended, but simple `threading.Lock` is acceptable.

### 2.2 GPU Dependency Checking
Dual check (`torch` + `nvidia-smi`) recommended,  
but `torch.cuda.is_available()` alone is acceptable.

### 2.3 Model Validation
Reading first bytes recommended,  
but `os.path.exists()` is acceptable.

### 2.4 plugin.validate() Hook
Recommended for future pipelines,  
but optional for Phase 11.

### 2.5 Timeout & Memory Defaults
Recommended:
- Timeout: 60s  
- Memory: 1GB  

But 30s timeout or global-only limits are acceptable.

### 2.6 Commit Structure
8 commits recommended,  
but combining into 3–4 larger commits is acceptable.

### 2.7 TDD Workflow
RED-first recommended,  
but writing tests after implementation is acceptable.

---

## 3. Summary
Phase 11 enforces strict safety and API guarantees,  
while allowing flexibility in internal implementation details that do not affect correctness, stability, or governance.
```

---

# ⭐ Strict vs Flexible Matrix (Drop-in Table for PHASE_11_PLANS.md)

```md
# Phase 11 — Strict vs Flexible Requirements

| Area | Strict | Flexible |
|------|--------|----------|
| Sandbox execution | ✔ Required | — |
| Lifecycle states | ✔ Required | — |
| Health API contract | ✔ Required | — |
| Pre-commit server tests | ✔ Required | — |
| PluginRegistry thread safety | ✔ Required | Lock type |
| VideoTracker stability | ✔ Required | — |
| Lock type (Lock vs RWLock) | — | ✔ |
| GPU checks (torch vs torch+nvidia-smi) | — | ✔ |
| Model validation (exists vs read bytes) | — | ✔ |
| plugin.validate() hook | — | ✔ |
| Timeout/memory defaults | — | ✔ |
| Commit granularity | — | ✔ |
| TDD workflow | — | ✔ |
```

This table removes all ambiguity.

---

# ⭐ Phase 11 Implementation Contract (Authoritative)

This is the document that ensures Phase 11 is *done* and *correct*.

```md
# Phase 11 Implementation Contract

This contract defines the required outcomes for Phase 11.  
All items below MUST be true before Phase 11 is considered complete.

---

## 1. Plugin Execution Safety
- All plugin execution MUST use the sandbox wrapper.
- No plugin may crash the FastAPI server.
- All plugin errors MUST be returned as structured objects.

## 2. Lifecycle State Enforcement
- Plugins MUST transition through LOADED → INITIALIZED → RUNNING.
- FAILED MUST be used for runtime errors.
- UNAVAILABLE MUST be used for missing dependencies (GPU, model, etc.).

## 3. Health API Stability
- `/v1/plugins` MUST return a list of all plugins with state + reason.
- `/v1/plugins/{name}/health` MUST return detailed state.
- Both endpoints MUST return 200 even for FAILED/UNAVAILABLE plugins.
- No 500 errors are allowed.

## 4. VideoTracker Hardening
- MUST detect missing GPU.
- MUST fail gracefully with structured error.
- MUST NOT crash the server.
- MUST update lifecycle state appropriately.

## 5. Pre-Commit Governance
- `cd server && uv run pytest` MUST run before every commit.
- Commits MUST NOT be allowed if server tests fail.

## 6. Test Requirements
- All Phase 11 RED tests MUST be GREEN.
- No regressions in Phase 9 or Phase 10 tests.
- Health API tests MUST pass.
- VideoTracker stability tests MUST pass.

## 7. Documentation Requirements
- All plans MUST live in `.ampcode/*.md`.
- No code may be placed in `.ampcode/`.
- `.ampcode` MUST contain exactly one active PLANS file.

---

## Completion Criteria
Phase 11 is complete when:
- All strict requirements are met.
- All tests pass.
- No regressions exist.
- Plans and implementation match exactly.
```

---

