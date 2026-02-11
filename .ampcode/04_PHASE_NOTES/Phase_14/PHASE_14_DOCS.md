Roger, here you go — **Phase 14 delivered as three complete governance artifacts**, written in the same authoritative, canonical style as Phase 12 and Phase 13.

These are the **official Phase 14 documents**:

- **Phase 14 PR Template**  
- **Phase 14 Migration Checklist**  
- **Phase 14 Acceptance Tests**  

They assume the Phase 14 spec you approved:  
**Cross‑plugin DAG pipelines with explicit `(plugin_id, tool_id)` nodes and typed edges.**

Let’s lock them in.

---

# **PHASE 14 — PR TEMPLATE (Canonical)**  
Save as:  
`docs/phases/phase_14_pr_template.md`

```
# Phase 14 PR — Cross‑Plugin DAG Pipelines

## Summary
Explain the DAG‑pipeline feature implemented in this PR.

## Scope (Required)
This PR includes ONLY:
- DAG pipeline execution (nodes + edges)
- Cross‑plugin pipeline support
- Pipeline registry (CRUD)
- DAG validation (acyclic, type‑compatible)
- DAG execution engine (topological order)
- Logging for each node execution
- REST endpoints for listing and running pipelines
- UI pipeline selector (choose named pipeline)

## Out of Scope (Must NOT appear)
- UI DAG editor (drag‑and‑drop)
- Auto‑wiring tools based on heuristics
- Cross‑frame stateful pipelines
- Model selection
- Tool parameter UI
- Timeline scrubbing
- Video export
- Analytics, heatmaps, charts
- Any UI beyond the canonical VideoTracker spec

## Files Added / Updated
List all files touched, grouped by:
- server/app/services
- server/app/routes
- server/app/models
- web-ui/src/components
- web-ui/src/api
- docs/

## Validation
- [ ] Pipeline is a valid DAG (no cycles)
- [ ] All nodes specify plugin_id + tool_id
- [ ] All tools exist in their respective plugins
- [ ] All edges satisfy type compatibility
- [ ] Execution follows topological order
- [ ] Logs include pipeline_id, node_id, plugin_id, tool_id, step_index
- [ ] REST endpoint rejects invalid pipelines

## Tests
- [ ] test_dag_validation.py
- [ ] test_dag_execution.py
- [ ] test_pipeline_registry.py

## Reviewer Notes
- Ensure no implicit plugin selection
- Ensure no fallback to default tools
- Ensure no runtime graph mutation
- Ensure no cross‑plugin magic
```

---

# **PHASE 14 — MIGRATION CHECKLIST (Canonical)**  
Save as:  
`docs/phases/phase_14_migration_checklist.md`

```
# Phase 14 Migration Checklist — Cross‑Plugin DAG Pipelines

## 1. Pipeline Registry
- [ ] Create pipeline_registry_service.py
- [ ] Add CRUD for named pipelines
- [ ] Store pipeline definitions (nodes + edges)
- [ ] Validate plugin_id + tool_id existence
- [ ] Validate DAG structure (acyclic)
- [ ] Validate entry_nodes and output_nodes

## 2. DAG Execution Engine
- [ ] Create dag_pipeline_service.py
- [ ] Implement topological sort
- [ ] Merge predecessor outputs into node payload
- [ ] Execute each node via run_plugin_tool(plugin_id, tool_id, payload)
- [ ] Collect outputs from output_nodes
- [ ] Add logging for each node execution

## 3. Validation Rules
- [ ] Reject pipelines with cycles
- [ ] Reject pipelines with unknown plugins/tools
- [ ] Reject pipelines with incompatible input/output types
- [ ] Reject pipelines with missing entry_nodes or output_nodes
- [ ] Reject pipelines with cross‑plugin edges that violate type contracts

## 4. REST Endpoints
- [ ] GET /pipelines
- [ ] GET /pipelines/{pipeline_id}
- [ ] POST /pipelines/{pipeline_id}/run
- [ ] Validate pipeline before execution
- [ ] Return final merged output

## 5. UI Migration
- [ ] Add PipelineSelector.tsx
- [ ] Fetch pipelines via GET /pipelines
- [ ] Replace Phase 13 ad‑hoc tool list with named pipeline selection
- [ ] Send { pipeline_id, payload } to REST
- [ ] For streaming: include pipeline_id in each WS frame

## 6. Plugin Contract
- [ ] Each tool declares input/output types
- [ ] Tools must accept dict payload
- [ ] Tools must return dict payload
- [ ] Tools must be pure functions (no global state)

## 7. Logging
- [ ] Log pipeline_id
- [ ] Log node_id
- [ ] Log plugin_id + tool_id
- [ ] Log step_index
- [ ] Log input/output types

## 8. Tests
- [ ] DAG validation tests
- [ ] DAG execution tests
- [ ] Pipeline registry tests
- [ ] Cross‑plugin compatibility tests
- [ ] Error‑path tests (cycles, missing tools, type mismatch)

## 9. Governance
- [ ] Add dag_pipeline_rules.md
- [ ] Update contributor docs
- [ ] Reject PRs that introduce implicit plugin selection
```

---

# **PHASE 14 — ACCEPTANCE TESTS (Canonical)**  
Save as:  
`server/app/tests/test_phase14_acceptance.py`  
(or split into the three files listed below)

These tests verify the entire Phase 14 architecture.

---

## **1. DAG Validation Tests**

### **Test: rejects cycles**

```
Given: nodes A→B, B→A
When: validate_pipeline()
Then: raises “Pipeline contains a cycle”
```

### **Test: rejects unknown plugin**

```
Given: node.plugin_id = "nonexistent"
When: validate_pipeline()
Then: raises “Unknown plugin”
```

### **Test: rejects unknown tool**

```
Given: plugin exists but tool_id does not
When: validate_pipeline()
Then: raises “Unknown tool”
```

### **Test: rejects incompatible types**

```
Given:
  node1 outputs ["detections"]
  node2 inputs ["tracks"]
When: validate_pipeline()
Then: raises “Type mismatch: detections → tracks”
```

---

## **2. DAG Execution Tests**

### **Test: executes nodes in topological order**

```
Given:
  n1 → n2 → n3
  Each tool appends its node_id to payload["order"]
When: run_pipeline()
Then: payload["order"] == ["n1", "n2", "n3"]
```

### **Test: merges predecessor outputs**

```
Given:
  n1 → n3
  n2 → n3
  n1 outputs {"a": 1}
  n2 outputs {"b": 2}
When: run_pipeline()
Then: n3 receives {"a": 1, "b": 2}
```

### **Test: cross‑plugin pipeline executes correctly**

```
Given:
  n1: (plugin A, detect_players)
  n2: (plugin B, reid_track_ids)
  n3: (plugin C, render_overlay)
When: run_pipeline()
Then: all three plugins are invoked in order
```

---

## **3. Pipeline Registry Tests**

### **Test: list pipelines**

```
Given: registry contains 3 pipelines
When: GET /pipelines
Then: returns list of 3 pipeline definitions
```

### **Test: get pipeline by ID**

```
Given: pipeline_id="player_tracking_v2"
When: GET /pipelines/player_tracking_v2
Then: returns full DAG definition
```

### **Test: run pipeline via REST**

```
Given: valid pipeline
When: POST /pipelines/{id}/run
Then: returns final merged output
```

---

## **4. WebSocket Tests**

### **Test: WS frame must include pipeline_id**

```
Given: WS frame missing pipeline_id
When: handle_frame()
Then: raises “WebSocket frame missing 'pipeline_id'”
```

### **Test: WS executes DAG pipeline**

```
Given: pipeline with nodes n1 → n2
When: send frame with pipeline_id
Then: WS response contains output of n2
```

---

## **5. Logging Tests**

### **Test: logs each node execution**

```
Given: pipeline with 3 nodes
When: run_pipeline()
Then: logs contain 3 entries with:
  - pipeline_id
  - node_id
  - plugin_id
  - tool_id
  - step_index
```

---

Roger, these three documents — **PR template**, **migration checklist**, and **acceptance tests** — complete the Phase 14 governance package.

