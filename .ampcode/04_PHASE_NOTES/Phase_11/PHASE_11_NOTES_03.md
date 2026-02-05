Clarifying Questions for Phase 11 Plans
Based on my review of the Phase notes and current plan docs, here are questions that would strengthen clarity:

1. VideoTracker GPU Detection Specificity
Current state: "Check GPU before init → mark UNAVAILABLE if missing"

Question: Should we distinguish between:

No GPU hardware at all (truly unavailable)
GPU present but driver broken (could fail at runtime)
CUDA toolkit missing but fixable?
This affects error messaging quality.

2. Lock Timeout Behavior Under Contention
Current assumption: RWLock sufficient for 10-50 req/sec

Question: When lock acquisition times out (your contingency):

Should Health API return 503 (temporarily unavailable)?
Or retry with exponential backoff?
Or mark plugin UNAVAILABLE?
This clarifies what "lock timeout" actually does.

3. Silent Init Failures Detection
Mentioned in 🟨 GUESSING (3.1): Plugin's __init__ catches exception internally

Question: Do we require a validate() hook AFTER __init__ succeeds?

If yes: Should this be part of the manifest?
If no: How do we detect "init succeeded but plugin is broken"?
Affects Commit 6 requirements.

4. Error Message Specificity for Dependency Chains
Current approach: "Module X not found"

Question: Should we do a chain inspection for indirect failures?

Example: import yolo succeeds, but import yolo.models fails due to missing CUDA
Should we report "CUDA missing" or "yolo initialization failed"?
Affects DependencyChecker complexity.

5. Auto-Recovery vs Manual Restart Justification
Current decision: Manual restart only (no auto-recovery)

Question: Is this because:

Restarting might hide deeper issues?
Auto-recovery could mask corrupt state?
Simpler for Phase 11, defer to Phase 12?
Affects user experience expectations.

6. Concurrent Access Pattern Reality Check
Assumption: < 50 requests/second to plugin APIs

Question: Are we counting:

ALL API calls (health checks + tool runs)?
Just tool execution requests?
Peak sustained or peak burst?
Affects lock strategy sufficiency.

7. Phase 11 Pre-Commit Hook Authority
Current state: "DO NOT ALTER per user instruction"

Question: Does this mean:

Don't change the WHAT the hook checks (tests, lint, types)?
Don't change the HOW it checks it (order, commands)?
Or both?
Affects whether we can optimize hook performance.

Roger, these are *excellent* clarifying questions — exactly the kind of thinking that prevents Phase 11 from accumulating hidden assumptions. I’ll answer each one decisively, in the same **strict vs flexible** governance model we just established.

I’ll also tell you *why* each answer belongs in the strict or flexible category so your plans stay coherent.

Let’s lock these down.

---

# **1. VideoTracker GPU Detection Specificity**  
**Your question:** Should we distinguish between:  
- No GPU hardware  
- GPU present but driver broken  
- CUDA toolkit missing  

### **Authoritative Answer:**  
**Yes — distinguish them.**

### **Why (Strict):**  
This affects user‑facing error messages and lifecycle state accuracy.  
It’s not “nice to have” — it’s part of plugin correctness.

### **Required distinctions:**  
- **No GPU hardware** → `UNAVAILABLE` (“No GPU detected”)  
- **GPU present but driver broken** → `FAILED` (“GPU driver error”)  
- **CUDA toolkit missing** → `UNAVAILABLE` (“CUDA not installed”)  

This gives you predictable behavior and better debugging.

**Strict.**

---

# **2. Lock Timeout Behavior Under Contention**  
**Your question:** What should happen if the registry lock times out?

### **Authoritative Answer:**  
**Health API returns 503 (temporarily unavailable).**

### **Why (Strict):**  
- Marking plugins UNAVAILABLE due to lock contention is incorrect  
- Retrying with backoff adds complexity without benefit  
- 503 is the correct semantic meaning: “system temporarily busy”  

**Strict.**

---

# **3. Silent Init Failures Detection**  
**Your question:** Do we require a `validate()` hook after `__init__`?

### **Authoritative Answer:**  
**Yes — require `validate()` for Phase 11.**

### **Why (Strict):**  
- Plugins can swallow exceptions internally  
- Pipelines in Phase 12 need deterministic plugin readiness  
- Validation is the only reliable way to detect “init succeeded but plugin is broken”  

### **Implementation:**  
- `validate()` is **required**  
- It is **not** part of the manifest  
- It is **called automatically** after init  

**Strict.**

---

# **4. Error Message Specificity for Dependency Chains**  
**Your question:** Should we inspect indirect import failures?

### **Authoritative Answer:**  
**Yes — report the *root cause* when possible.**

### **Why (Flexible):**  
- You don’t need a full dependency graph  
- But you *should* unwrap nested exceptions  

### **Implementation:**  
- If `import yolo.models` fails due to CUDA:  
  → “CUDA missing”  
- If import fails due to missing Python module:  
  → “Module X not found”  

**Flexible implementation, strict outcome.**

---

# **5. Auto-Recovery vs Manual Restart Justification**  
**Your question:** Why no auto‑recovery?

### **Authoritative Answer:**  
**Manual restart only.**

### **Why (Strict):**  
- Auto‑recovery hides real failures  
- Pipelines need deterministic behavior  
- Recovery logic belongs in Phase 12 orchestration, not Phase 11 loader  
- Prevents infinite crash loops  

**Strict.**

---

# **6. Concurrent Access Pattern Reality Check**  
**Your question:** What counts toward the 10–50 req/sec assumption?

### **Authoritative Answer:**  
**Count ALL plugin‑related operations:**

- Health checks  
- Plugin load  
- Plugin execution  
- Pipeline stage transitions (Phase 12)  
- Realtime plugin status updates  

### **Why (Strict):**  
This affects lock strategy and performance guarantees.

**Strict.**

---

# **7. Phase 11 Pre-Commit Hook Authority**  
**Your question:** What does “DO NOT ALTER” actually mean?

### **Authoritative Answer:**  
**You may NOT change WHAT the hook checks.  
You MAY change HOW it checks it.**

### **Strict:**  
- Must run server tests  
- Must block commits on failure  
- Must run before commit  

### **Flexible:**  
- You may reorder steps  
- You may optimize commands  
- You may speed up test selection  
- You may add caching  

This keeps governance intact while allowing engineering improvements.

---

# ⭐ **Summary Table (Strict vs Flexible)**

| Question | Strict or Flexible | Final Decision |
|---------|---------------------|----------------|
| GPU detection specificity | **Strict** | Distinguish hardware/driver/CUDA |
| Lock timeout behavior | **Strict** | Return 503 |
| Silent init detection (`validate()`) | **Strict** | Required |
| Dependency chain error specificity | **Flexible** | Root cause preferred |
| Auto-recovery | **Strict** | Manual restart only |
| Concurrency definition | **Strict** | Count all plugin-related ops |
| Pre-commit hook authority | **Hybrid** | WHAT strict, HOW flexible |

---

