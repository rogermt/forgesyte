# ⭐ PHASE 14 — GOVERNANCE RULES

## Core Principle

**Everything explicit, nothing implicit.**

No auto-wiring, no guessing, no fallback logic, no magic.

---

## Rule 1: No Implicit Plugin Selection

❌ **Forbidden**:
```python
# Don't guess which plugin
if plugin_id is None:
    plugin_id = "default_plugin"  # ❌ NO
```

✅ **Required**:
```python
# Must be explicit
if plugin_id is None:
    raise ValueError("pipeline node must specify plugin_id")
```

**Impact**: Every node must declare its plugin.

---

## Rule 2: No Implicit Tool Selection

❌ **Forbidden**:
```python
# Don't use first tool
if tool_id is None:
    tool_id = plugin.tools[0]  # ❌ NO
```

✅ **Required**:
```python
# Must be explicit
if tool_id is None:
    raise ValueError("pipeline node must specify tool_id")
```

**Impact**: Every node must declare its tool.

---

## Rule 3: No Auto-Wiring

❌ **Forbidden**:
```python
# Don't auto-connect adjacent nodes
for i in range(len(nodes) - 1):
    edges.append((nodes[i], nodes[i+1]))  # ❌ NO
```

✅ **Required**:
```python
# Edges must be explicit in JSON
{
  "edges": [
    { "from_node": "n1", "to_node": "n2" }
  ]
}
```

**Impact**: All data flow must be declared.

---

## Rule 4: No Type Guessing

❌ **Forbidden**:
```python
# Don't assume types match
if from_node.output_types != to_node.input_types:
    # Try anyway?  # ❌ NO
    pass
```

✅ **Required**:
```python
# Validate type compatibility before execution
if not (from_node.output_types & to_node.input_types):
    raise PipelineValidationError(
        f"Type mismatch: {from_node.id} → {to_node.id}"
    )
```

**Impact**: Type contracts are enforced, not ignored.

---

## Rule 5: Validate Before Execute

❌ **Forbidden**:
```python
# Don't try/catch during execution
async def run_pipeline(pipeline):
    try:
        return await execute(pipeline)  # ❌ Might fail mid-execution
    except Exception:
        pass
```

✅ **Required**:
```python
# Validate first, execute only if valid
pipeline.validate()  # Raises if invalid
return await pipeline.execute()  # Guaranteed to work
```

**Impact**: All errors are caught before execution.

---

## Rule 6: No Runtime Graph Mutation

❌ **Forbidden**:
```python
# Don't modify pipeline during execution
pipeline.nodes.append(new_node)  # ❌ NO
pipeline.edges.pop()  # ❌ NO
```

✅ **Required**:
```python
# Pipelines are immutable once loaded
# If you need changes, create a new pipeline version
{
  "id": "player_tracking_v2",  # New version
  "nodes": [...],
  "edges": [...]
}
```

**Impact**: Pipelines are deterministic and reproducible.

---

## Rule 7: No Cross-Plugin Magic

❌ **Forbidden**:
```python
# Don't assume cross-plugin communication
plugin_a.output → plugin_b.input  # ❌ How? Serialization?
```

✅ **Required**:
```python
# All cross-plugin edges must be explicit
{
  "edges": [
    {
      "from_node": "n1_from_pluginA",
      "to_node": "n2_from_pluginB"
    }
  ]
}
# Payload merging and type conversion are explicit
```

**Impact**: No hidden assumptions about data flow.

---

## Rule 8: Cycles Are Forbidden

❌ **Invalid**:
```
detect → track → detect  # Cycle ❌
```

✅ **Valid**:
```
detect → track → render  # DAG ✅
```

**Why**: Cycles cause infinite loops, undefined execution order.

**Validation**:
```python
if has_cycle(graph):
    raise PipelineValidationError("Pipeline contains cycle")
```

---

## Rule 9: All Nodes Must Be Reachable

❌ **Invalid**:
```json
{
  "nodes": ["n1", "n2", "n3"],
  "edges": [
    { "from_node": "n1", "to_node": "n2" }
  ],
  "output_nodes": ["n2"]
  // n3 is unreachable from entry_nodes
}
```

✅ **Valid**:
```json
{
  "nodes": ["n1", "n2", "n3"],
  "edges": [
    { "from_node": "n1", "to_node": "n2" },
    { "from_node": "n1", "to_node": "n3" }
  ],
  "output_nodes": ["n2", "n3"]
  // Both reachable from n1
}
```

**Validation**:
```python
for node in graph.nodes:
    if not is_reachable(graph, entry_nodes, node):
        raise PipelineValidationError(f"Node {node} is unreachable")
```

---

## Rule 10: Entry and Output Nodes Must Exist

❌ **Invalid**:
```json
{
  "nodes": ["n1", "n2"],
  "entry_nodes": ["nonexistent"]  // ❌
}
```

✅ **Valid**:
```json
{
  "nodes": ["n1", "n2"],
  "entry_nodes": ["n1"]  // ✅
}
```

**Validation**:
```python
for entry in pipeline.entry_nodes:
    if entry not in pipeline.nodes:
        raise PipelineValidationError(f"Entry node {entry} not in nodes")
```

---

## Rule 11: Type Metadata Is Required

❌ **Invalid**:
```python
class MyTool:
    def run(self, data):
        return {"result": data}
    # No input_types, output_types ❌
```

✅ **Valid**:
```python
class MyTool:
    input_types = ["video_frame"]
    output_types = ["detections"]
    
    def run(self, data):
        return {"result": data}
```

**Enforcement**:
- Tool registration fails if metadata missing
- Manifest validation requires it
- No metadata = tool not available for pipelines

---

## Rule 12: Logging Is Mandatory

Every pipeline execution must log:

```python
{
    "pipeline_id": "player_tracking_v2",
    "node_id": "detect",
    "plugin_id": "forgesyte-yolo-tracker",
    "tool_id": "detect_players",
    "step": 1,
    "status": "executing",
    "timestamp": "2026-02-12T10:30:45Z",
    "input_types": ["video_frame"],
    "output_types": ["detections"]
}
```

No silent failures. All execution is auditable.

---

## Rule 13: Error Messages Must Be Clear

❌ **Unclear**:
```
ValueError: Invalid pipeline
```

✅ **Clear**:
```
PipelineValidationError: Graph contains cycle: detect → track → detect
Nodes: ["detect", "track"]
Edges: [("detect", "track"), ("track", "detect")]
```

Users must understand what went wrong and why.

---

## Rule 14: Pipeline Registry Is Immutable

❌ **Forbidden**:
```python
registry.delete("player_tracking_v1")  # ❌ Can't delete
registry.update("player_tracking_v1", new_def)  # ❌ Can't update
```

✅ **Required**:
```python
# New version instead
registry.register("player_tracking_v2", new_def)  # ✅ New version
```

**Why**: Audit trail, reproducibility, no surprise breakages.

---

## Rule 15: No Unsigned Pipelines

❌ **Forbidden**:
```python
# Don't accept arbitrary JSON from users
user_pipeline = json.loads(request.body)
await execute(user_pipeline)  # ❌ NO
```

✅ **Required**:
```python
# Only execute pipelines from registry
pipeline = registry.get(pipeline_id)  # From registered store
await execute(pipeline)  # ✅ Guaranteed safe
```

**Why**: Security, validation, audit trail.

---

## Summary Table

| Rule | Forbidden | Required |
|------|-----------|----------|
| 1 | Implicit plugins | Explicit plugin_id |
| 2 | Implicit tools | Explicit tool_id |
| 3 | Auto-wiring | Explicit edges |
| 4 | Type guessing | Type validation |
| 5 | Execute-then-catch | Validate-then-execute |
| 6 | Runtime mutation | Immutable pipelines |
| 7 | Cross-plugin magic | Explicit data flow |
| 8 | Cycles | DAGs only |
| 9 | Unreachable nodes | All nodes reachable |
| 10 | Invalid entry/output | Nodes exist |
| 11 | Missing metadata | Required metadata |
| 12 | Silent execution | Mandatory logging |
| 13 | Vague errors | Clear error messages |
| 14 | Mutations | New versions only |
| 15 | Unsigned pipelines | Registry-only |

---

## Enforcement

These rules are enforced at:

1. **Load time**: Registry validation
2. **Registration time**: Manifest validation
3. **Execution time**: Runtime validation
4. **Audit time**: Logging verification

No rule can be bypassed.
