Roger, this is exactly the kind of question a disciplined architect asks before locking Phase 10.  
Let’s cut through the noise and give you a **clear, authoritative answer** that respects your Phase‑based governance system.

You asked:

> Should I update the plans to match authoritative files, keep my guesses, or partially fix?

Here’s the truth:

# ⭐ You should choose **Option A: Update the plans to match the authoritative files exactly.**

And here’s why — in your repo, **authoritative files are law**.  
Your entire governance philosophy is:

> “Specs are the source of truth. Plans must match specs. Deviations cause drift.”

Phase 10 is a high‑risk phase (real‑time, pipeline upgrades, pre‑commit fixes).  
This is *not* the moment to introduce ambiguity or inferred behavior.

Let’s walk through each deviation and what you should do.

---

# ⭐ **1. Commit Sequence Deviation → MUST FIX**

Authoritative:

```
Commit 4: Real-Time Endpoint Stub + Extended Models
Commit 5: Fix Web-UI Pre-Commit Hook
```

Your plan:

```
Commit 4: Endpoint + Models
Commit 5: Fix Pre-Commit Hook
```

This one is actually correct — you matched the authoritative sequence.  
Your “deviation” is just a misunderstanding.

✔ No correction needed  
✔ Your plan already matches the authoritative file

---

# ⭐ **2. Missing Final Merge PR Template → MUST FIX**

This *is* a real deviation.

Authoritative file exists:

```
PHASE_10_FINAL_MERGE_PR_TEMPLATE.md
```

Your plan does not reference it.

You should:

✔ Add a section in your Phase 10 plan referencing the Final Merge PR Template  
✔ Ensure your Phase 10 merge process uses that template  
✔ Add it to your Phase 10 folder scaffolding

This is required for governance consistency.

---

# ⭐ **3. File Naming Deviation → MUST FIX**

Authoritative RED tests:

```
test_realtime_endpoint.py
test_job_progress_field.py
test_plugin_timing_field.py
```

Your inferred names:

```
test_realtime_endpoint_exists.py
test_job_progress_field.py
test_job_plugin_timings_field.py
```

This is a **real deviation** and must be corrected.

Why?

- Your repo enforces deterministic naming  
- Test discovery depends on predictable patterns  
- Phase‑based governance requires exact alignment  

✔ Update your plan to use the authoritative filenames  
✔ Update your scaffolding  
✔ Update your commit descriptions  

---

# ⭐ **4. UI Layout Inference → KEEP, but mark as inference**

Your layout:

```
RealtimeOverlay
Frame Viewer
├── ProgressBar
└── PluginInspector
```

This is **not** in any authoritative file.  
But it is a **valid architectural inference** based on:

- Phase 10 UI Spec  
- Real‑time flow diagram  
- Component responsibilities  

You should:

✔ Keep the layout  
✔ Add a note: “This layout is inferred, not authoritative”  
✔ Do NOT treat it as a contract  
✔ Do NOT enforce it in governance  

This is the correct way to handle inferred architecture.

---

# ⭐ **5. Reconnection Strategy → ALREADY CORRECT**

Your plan:

> Exponential backoff (1s, 2s, 4s, 8s, 16s)

Authoritative:

> Documented in PHASE_10_UI_SPEC.md section 2.1

✔ No correction needed  
✔ Your plan matches the authoritative spec  
✔ Keep it as-is

---

# ⭐ **Final Recommendation**

You should choose:

# ⭐ **Option A — Update the plans to match authoritative files exactly.**

And additionally:

- Keep your UI layout, but mark it as inference  
- Keep your reconnection strategy  
- Fix filenames  
- Add the missing Final Merge PR Template  
- Confirm commit sequence (it already matches)

This keeps your repo:

- deterministic  
- drift‑free  
- spec‑aligned  
- Phase‑governed  
- future‑proof  

Exactly the way you like it.

---

