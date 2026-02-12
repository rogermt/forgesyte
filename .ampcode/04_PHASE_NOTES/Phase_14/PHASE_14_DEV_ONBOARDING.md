
# 📘 **Phase 14 Developer Onboarding Guide**  
`docs/governance/phase_14_developer_onboarding.md`

---

# **Phase 14 Developer Onboarding Guide**

Welcome to the Phase 14 codebase.  
This guide explains how to work safely within the governed DAG + plugin ecosystem.

---

## **1. Repo Structure (High‑Level)**

```
server/
  app/
    services/        # DAG engine, plugin manager, pipeline registry
    pipelines/       # Pipeline definitions (JSON)
    settings.py      # Phase 14 config system
    main.py          # FastAPI entrypoint
plugins/
  <plugin_id>/
    manifest.json    # Phase 14 metadata
    tools/           # Tool implementations
docs/
  governance/        # All Phase 14 governance docs
tools/
  validate_plugins.py
  validate_pipelines.py
  generate_plugin_capability_matrix.py
```

---

## **2. Core Concepts**

### **Plugins**
- Provide tools  
- Tools declare:
  - `input_types`
  - `output_types`
  - `capabilities`

### **Pipelines**
- DAGs of plugin tools  
- Must be acyclic  
- Must be type‑compatible  

### **DAG Engine**
- Executes pipelines node‑by‑node  
- Merges predecessor outputs (last‑wins)  
- Emits structured logs  

---

## **3. Daily Workflow**

### **Step 1 — Start backend**
```
uvicorn server.app.main:app --reload
```

### **Step 2 — Start frontend**
```
VITE_API_URL=http://localhost:8000/v1 \
VITE_WS_URL=ws://localhost:8000/v1/stream \
npm run dev
```

### **Step 3 — Validate plugins**
```
python tools/validate_plugins.py
```

### **Step 4 — Validate pipelines**
```
python tools/validate_pipelines.py
```

### **Step 5 — Run tests**
```
pytest
```

### **Step 6 — Update capability matrix**
```
python tools/generate_plugin_capability_matrix.py
```

---

## **4. Adding a New Tool**

1. Add tool to plugin manifest  
2. Add `input_types`, `output_types`, `capabilities`  
3. Implement tool in Python  
4. Run validators  
5. Update capability matrix  
6. Add tests  

---

## **5. Adding a New Pipeline**

1. Create JSON in `server/app/pipelines/`  
2. Validate with `validate_pipelines.py`  
3. Add tests  
4. Update docs if needed  

---

## **6. Common Mistakes**

- Missing metadata in manifest  
- Type mismatches between nodes  
- Cycles in pipeline  
- Forgetting to regenerate capability matrix  
- Hard‑coding CORS origins  

---

# 🚨 **Phase 14 Breaking Change Policy**  
`docs/governance/phase_14_breaking_change_policy.md`

---

# **Phase 14 Breaking Change Policy**

This document defines what constitutes a breaking change in the Phase 14 ecosystem and how such changes must be handled.

---

## **1. What Counts as a Breaking Change**

### **1.1 Plugin Metadata Changes**
- Renaming a plugin ID  
- Renaming a tool ID  
- Changing `input_types`  
- Changing `output_types`  
- Removing a tool  
- Removing a plugin  

### **1.2 Pipeline Changes**
- Removing a node  
- Changing a node’s plugin/tool  
- Changing edge structure  
- Changing entry/output nodes  
- Introducing type incompatibility  

### **1.3 DAG Engine Changes**
- Changing merge semantics  
- Changing error propagation  
- Changing logging schema  
- Changing execution order  

### **1.4 Config Changes**
- Removing config values  
- Changing default CORS origins  
- Changing API prefix  

---

## **2. Required Steps for Breaking Changes**

### **Step 1 — Open a “Breaking Change Proposal” PR**
Must include:

- motivation  
- impact analysis  
- migration plan  
- updated capability matrix  
- updated pipeline definitions  
- updated tests  

### **Step 2 — Update All Affected Pipelines**
Every pipeline referencing the changed tool/plugin must be updated.

### **Step 3 — Update Capability Matrix**
Run:

```
python tools/generate_plugin_capability_matrix.py
```

### **Step 4 — Update Tests**
- DAG tests  
- Plugin tests  
- Pipeline validator tests  

### **Step 5 — Update Documentation**
- pipeline design guide  
- compatibility report  
- metadata schema  

### **Step 6 — CI Must Pass**
All validators + tests must pass.

---

## **3. Forbidden Breaking Changes**

These changes are **not allowed** without a major version bump:

- Removing a widely‑used type (`detections`, `tracks`, etc.)  
- Changing merge semantics  
- Changing pipeline JSON schema  
- Changing plugin manifest schema  

---

## **4. Emergency Fixes**

If a breaking change is required to fix a critical bug:

- Must be approved by maintainers  
- Must include a migration script  
- Must include a rollback plan  

---

# 🎯 Summary

You now have:

### ✔ Phase 14 PR template  
### ✔ Phase 14 developer onboarding guide  
### ✔ Phase 14 breaking change policy  

Together with the CI gate, validators, and capability matrix, this forms a **complete governance system** for Phase 14.

