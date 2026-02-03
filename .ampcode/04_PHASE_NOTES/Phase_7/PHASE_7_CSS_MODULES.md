Absolutely, Roger — here is the **exact Phase 7 CSS Modules Migration Plan**, rewritten cleanly and ready to hand to the dev *as-is*.  
This version is crisp, authoritative, and leaves **zero room for interpretation or drift**.

You can paste this directly into Slack, GitHub, or your dev chat.

---

# **Phase 7 – CSS Modules Migration Plan (Final, Enforced Version)**

## **🎯 Goal**

Migrate the `web-ui` from ad‑hoc/global styling to **CSS Modules**, with **zero changes** to runtime behaviour, logic, API contracts, or the Phase 6 test baseline.

This is a **pure presentation refactor** under strict guardrails.

---

# **🚫 Non‑Negotiable Guardrails**

### **No changes allowed to:**
- `web-ui/src/hooks/useVideoProcessor.ts`
- `web-ui/src/api/client.ts`
- `web-ui/src/api/pollJob.ts` and related helpers
- Any Phase 6 test files (no edits, no moves, no renames)
- Any server code
- Any CI workflows
- Any job pipeline behaviour
- Any API routes, payloads, or execution paths

### **Testing rules**
- **No new tests** in Phase 7  
- **No deleted tests**  
- **No renamed/moved tests**  
- **No `.skip`, `.only`, `xit`, `xdescribe`, `xtest`**  
- The **two APPROVED pre‑Phase‑7 skips** must remain exactly as-is

### **If any of the above must change → STOP and escalate**  
Use `PHASE_7_ESCALATION_TEMPLATE.md`.

---

# **🧭 Migration Strategy**

## **1. Tiered Component Migration**
We migrate components in controlled tiers:

### **Tier 1 – Leaf components**
- Buttons, badges, tags, simple wrappers  
- Example: `RecordButton`

### **Tier 2 – Mid‑level layout**
- Header, Sidebar, Nav, Panels, Layout shells

### **Tier 3 – Page‑level**
- Dashboard, Upload, Results, Settings

### **Tier 4 – Critical**
- `VideoTracker`  
- Any component that touches job results or job pipeline output

**Each tier builds confidence before touching more sensitive components.**

---

## **2. One PR per small, coherent scope**
- Prefer **1–3 components per PR**
- PR must be readable by scanning the diff
- No “big bang” migrations

---

## **3. Strict “CSS‑only” rule**
Allowed TSX changes:
- Add CSS module import  
- Replace `className="foo"` with `className={styles.foo}`  
- Remove old global class names  

Not allowed:
- No new props  
- No new state  
- No new hooks  
- No new logic  
- No refactors  
- No renames  
- No file moves  

---

## **4. Baseline Verification (before first Phase 7 PR)**

These must pass on the **Phase 6A clean baseline** and on **every Phase 7 PR**:

```
npm test -- --run
npm run lint
npm run type-check
uv run pre-commit run --all-files
```

If any fail → STOP and escalate.

---

# **🎨 CSS Modules Conventions**

### **File naming**
```
ComponentName.module.css
```

### **Import**
```ts
import styles from './ComponentName.module.css';
```

### **Usage**
```tsx
className={styles.root}
className={clsx(styles.root, styles.active)}
```

### **Prohibited**
- No global selectors (`body`, `html`, `*`)
- No `:global` unless explicitly justified and documented
- No CSS resets inside modules

---

# **📦 Component Migration Tiers (Summary)**

Full list is in `PHASE_7_COMPONENT_CHECKLIST.md`.

### **Tier 1**
- Buttons  
- Badges  
- Simple wrappers  
- Example: `RecordButton`

### **Tier 2**
- Header  
- Sidebar  
- Navigation  
- Panels  
- Layout shells  

### **Tier 3**
- Dashboard  
- Upload page  
- Results page  
- Settings  

### **Tier 4**
- `VideoTracker`  
- Any component that consumes job results  
- Any component that interacts with the job pipeline  

---

# **✅ Success Criteria**

Phase 7 is complete when:

- All targeted components use CSS Modules  
- **No regressions** in:
  - Job pipeline behaviour  
  - Upload/Analyze flow  
  - Results rendering  
- **All tests passing**  
  - Same test count as Phase 6  
  - Only the **two APPROVED pre‑Phase‑7 skips**  
- **CI green**  
- No changes to:
  - `useVideoProcessor`  
  - `client.ts`  
  - Job polling logic  

If any of these cannot be met → escalate before merging.

---

