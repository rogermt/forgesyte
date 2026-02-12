Roger, here’s the **full Phase 14 governance pack** you asked for — three documents that lock the repo into a deterministic, contributor‑safe, drift‑proof system.

These are written exactly in the tone and structure you’ve been using across Phases 11–14.  
You can drop them straight into `docs/governance/`.

---

# 📄 **Phase 14 PR Template (Enforcing All Governance Rules)**  
`docs/governance/phase_14_pr_template.md`

---

# **Phase 14 Pull Request Template**

## **Summary**
Describe *exactly* what this PR changes.  
State whether it affects:

- plugins  
- pipelines  
- DAG engine  
- manifests  
- config  
- documentation  

---

## **Checklist — Phase 14 Governance Requirements**

### **1. Plugin Metadata**
- [ ] All modified plugins include valid `input_types`, `output_types`, `capabilities`
- [ ] No tool has empty metadata arrays
- [ ] No tool IDs or plugin IDs were renamed without justification

### **2. Pipeline Validity**
- [ ] All pipelines load successfully
- [ ] All pipelines pass the Phase 14 pipeline validator
- [ ] No cycles introduced
- [ ] All plugin/tool references are valid
- [ ] All edges are type‑compatible (`output_types ∩ input_types ≠ ∅`)

### **3. Capability Matrix**
- [ ] Ran `generate_plugin_capability_matrix.py`
- [ ] Committed updated `phase_14_plugin_capability_matrix.md`
- [ ] CI diff check passes

### **4. DAG Engine Stability**
- [ ] All Phase 14 DAG tests pass
- [ ] The “first failing test” passes (plugin resolution, merge, type flow)

### **5. Config Governance**
- [ ] No hard‑coded origins or environment‑specific values
- [ ] All new config values added to `settings.py`
- [ ] `.env` templates updated if needed

---

## **Testing**
Describe:

- unit tests added  
- integration tests added  
- manual tests performed  

---

## **Breaking Changes**
If any breaking changes exist, describe them here.  
If none, state:

> This PR introduces no breaking changes.

---

## **Reviewer Notes**
Anything reviewers should pay attention to.

---

