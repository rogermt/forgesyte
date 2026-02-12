---

## 🔥 Phase 14 PR descriptions per commit + plan tasks

Save this as `docs/phases/phase_14_commits.md`.

### **Commit 1 — Add pipeline graph models**

**PR description:**

> feat(phase-14): add pipeline graph models  
>  
> Adds Pydantic models for DAG pipelines, including nodes, edges, and pipeline definitions.  
> These models are the foundation for cross-plugin DAG execution in Phase 14.

**Plan tasks:**

- [ ] Add `PipelineNode`, `PipelineEdge`, `PipelineDefinition`, `ToolCapability`  
- [ ] Add basic structural validation (nodes/edges consistency)  
- [ ] No behavior, no services, no routes yet  

---

### **Commit 2 — Add tool capability metadata**

**PR description:**

> feat(phase-14): introduce tool capability metadata  
>  
> Adds a `ToolCapability` model and extends plugin tools to declare input/output types and capabilities.  
> This will be used in later commits to validate DAG edge compatibility.

**Plan tasks:**

- [ ] Add `ToolCapability` model (if not already)  
- [ ] Extend plugin/tool definitions to expose `input_types` / `output_types`  
- [ ] No validation yet, just data surface  

---

### **Commit 3 — Add pipeline registry service**

**PR description:**

> feat(phase-14): add pipeline registry service  
>  
> Implements `PipelineRegistryService` to load, store, and validate named pipelines from disk.  
> This provides a central registry for reusable DAG definitions.

**Plan tasks:**

- [ ] Implement `PipelineRegistryService`  
- [ ] Load `*.json` from `server/app/pipelines/`  
- [ ] Validate plugin/tool existence  
- [ ] Validate acyclicity  
- [ ] No execution yet  

---

### **Commit 4 — Add DAG pipeline service**

**PR description:**

> feat(phase-14): add DAG pipeline execution service  
>  
> Adds `DagPipelineService` to execute validated DAG pipelines in topological order, merging predecessor outputs and returning final merged results.

**Plan tasks:**

- [ ] Implement `DagPipelineService.run_pipeline()`  
- [ ] Implement `_topological_order()`  
- [ ] Implement `_merge_predecessor_outputs()`  
- [ ] Use `plugin_manager.get_plugin().run_tool()` per node  

---

### **Commit 5 — Wire REST endpoints for pipelines**

**PR description:**

> feat(phase-14): add REST endpoints for DAG pipelines  
>  
> Adds `/pipelines`, `/pipelines/{id}`, and `/pipelines/{id}/run` endpoints to list, inspect, and execute named DAG pipelines.

**Plan tasks:**

- [ ] Implement `routes_pipelines.py`  
- [ ] Wire DI for `PipelineRegistryService` and `DagPipelineService`  
- [ ] Return 404 for unknown pipeline  
- [ ] Return 400 for invalid execution  

---

### **Commit 6 — Add UI pipeline selector + API client**

**PR description:**

> feat(phase-14): add UI pipeline selector and API client  
>  
> Adds a `PipelineSelector` component and API helpers to list and run named pipelines from the UI.

**Plan tasks:**

- [ ] Implement `web-ui/src/api/pipelines.ts`  
- [ ] Implement `PipelineSelector.tsx`  
- [ ] Wire into `VideoTracker` / `App.tsx` to choose a pipeline  
- [ ] For now, still use Phase 13 linear pipelines for WS; REST uses DAG  

---

### **Commit 7 — Add DAG validation tests**

**PR description:**

> test(phase-14): add DAG validation tests  
>  
> Adds tests for pipeline validation, including cycles, unknown plugins/tools, and structural errors.

**Plan tasks:**

- [ ] Add `test_dag_validation.py`  
- [ ] Cover cycles, unknown plugin, unknown tool, bad entry/output nodes  

---

### **Commit 8 — Add DAG execution tests**

**PR description:**

> test(phase-14): add DAG execution tests  
>  
> Adds tests for DAG execution order, payload merging, and cross-plugin execution.

**Plan tasks:**

- [ ] Add `test_dag_execution.py`  
- [ ] Verify topological order  
- [ ] Verify merged predecessor outputs  
- [ ] Verify cross-plugin calls  

---

### **Commit 9 — Add pipeline registry tests**

**PR description:**

> test(phase-14): add pipeline registry tests  
>  
> Adds tests for loading pipelines from disk and retrieving them by ID.

**Plan tasks:**

- [ ] Add `test_pipeline_registry.py`  
- [ ] Verify JSON loading, listing, and get-by-id behavior  

---

### **Commit 10 — Governance + cleanup**

**PR description:**

> refactor(phase-14): enforce DAG pipeline governance  
>  
> Finalizes Phase 14 by ensuring no implicit behavior, no fallback logic, and no linear-only assumptions remain in the pipeline layer.

**Plan tasks:**

- [ ] Ensure no code path auto-selects tools or plugins  
- [ ] Ensure all DAG execution goes through `DagPipelineService`  
- [ ] Update docs and contributor guidelines  
- [ ] Add logging fields: pipeline_id, node_id, plugin_id, tool_id, step_index  

