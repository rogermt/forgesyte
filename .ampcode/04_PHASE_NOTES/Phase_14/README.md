# Phase 14 Documentation Package

**Complete specification and implementation guide for Cross-Plugin DAG Pipelines**

---

## Quick Start

**New to Phase 14?** Start here:

1. Read [PHASE_14_OVERVIEW.md](PHASE_14_OVERVIEW.md) (10 min)
2. Understand [PHASE_14_GLOSSARY.md](PHASE_14_GLOSSARY.md) (5 min)
3. Review [PHASE_14_ARCHITECTURE.md](PHASE_14_ARCHITECTURE.md) (15 min)

---

## Document Guide

### For Understanding Phase 14

| Document | Purpose | Read Time |
|----------|---------|-----------|
| [PHASE_14_OVERVIEW.md](PHASE_14_OVERVIEW.md) | High-level vision and capabilities | 10 min |
| [PHASE_14_GLOSSARY.md](PHASE_14_GLOSSARY.md) | Terminology and concepts | 5 min |
| [PHASE_14_ARCHITECTURE.md](PHASE_14_ARCHITECTURE.md) | Technical design and data models | 15 min |
| [PHASE_14_GOVERNANCE_RULES.md](PHASE_14_GOVERNANCE_RULES.md) | What's forbidden, what's required | 10 min |

### For Implementing Phase 14

| Document | Purpose | Read Time |
|----------|---------|-----------|
| [PHASE_14_MIGRATION_PLAN.md](PHASE_14_MIGRATION_PLAN.md) | 10 commits from Phase 13 to Phase 14 | 20 min |
| [PHASE_14_FOLDER_STRUCTURE.md](PHASE_14_FOLDER_STRUCTURE.md) | Where files go and what they contain | 10 min |
| [PHASE_14_DEVELOPER_GUIDE.md](PHASE_14_DEVELOPER_GUIDE.md) | How to build pipelines and tools | 15 min |

### For Verifying Phase 14

| Document | Purpose | Read Time |
|----------|---------|-----------|
| [PHASE_14_ACCEPTANCE_CRITERIA.md](PHASE_14_ACCEPTANCE_CRITERIA.md) | Success checklist (60+ test cases) | 20 min |

---

## Phase 14 At a Glance

**Problem Phase 13 Solved**:
- Single-plugin execution is deterministic
- Tool routing is explicit
- No fallback logic

**Problem Phase 14 Solves**:
- Multiple plugins must work together
- Data flows between tools
- Workflows are complex (branching, merging)

**Key Innovation**:
```
Linear Pipeline (Phase 13):
  detect_players → Result

Graph Pipelines (Phase 14):
  detect_players → track_ids → render_overlay → Result
  
  (And much more complex patterns possible)
```

---

## Core Concepts

### Nodes & Edges
- **Node**: A tool invocation (e.g., `yolo.detect_players`)
- **Edge**: Data flow from one node to another

### DAG (Directed Acyclic Graph)
- Pipelines must be acyclic (no cycles)
- Enables deterministic execution order
- Validated before execution

### Type Contracts
- Each tool declares `input_types` and `output_types`
- Edges only allowed if types are compatible
- Prevents incompatible data flows

### Registry
- Named pipelines stored on server
- Loaded from `server/app/pipelines/*.json`
- Immutable once registered

---

## Example Pipeline

**Player Tracking Workflow**:

```json
{
  "id": "player_tracking_v1",
  "nodes": [
    { "id": "detect", "plugin_id": "yolo", "tool_id": "detect_players" },
    { "id": "track", "plugin_id": "yolo", "tool_id": "track_players" },
    { "id": "render", "plugin_id": "viz", "tool_id": "render_overlay" }
  ],
  "edges": [
    { "from_node": "detect", "to_node": "track" },
    { "from_node": "track", "to_node": "render" }
  ],
  "entry_nodes": ["detect"],
  "output_nodes": ["render"]
}
```

**Execution**:
1. User provides video frame
2. YOLO detects players
3. YOLO tracks player IDs over time
4. Viz renders overlay on frame
5. Rendered frame returned to user

---

## Governance Principles

**Everything explicit, nothing implicit:**

1. ❌ No default plugins
2. ❌ No default tools
3. ❌ No auto-wiring
4. ❌ No type guessing
5. ✅ Pipelines are code (JSON)
6. ✅ Validation before execution
7. ✅ Clear error messages
8. ✅ Full audit trail

---

## 10-Commit Implementation

```
Commit 1:   Add pipeline graph models
Commit 2:   Add tool capability metadata
Commit 3:   Add pipeline registry service
Commit 4:   Add DAG pipeline service
Commit 5:   Add topological sort & validation
Commit 6:   Add type compatibility validation
Commit 7:   Add REST pipeline endpoints
Commit 8:   Add UI pipeline selector
Commit 9:   Add acceptance tests
Commit 10:  Remove single-plugin assumptions
```

Estimated: **28 hours** of development

---

## Success Metrics

**Phase 14 is complete when**:

- ✅ All DAG validation rules enforced
- ✅ All pipelines execute correctly
- ✅ Registry works (list/get/run)
- ✅ Type compatibility validated
- ✅ REST API endpoints functional
- ✅ UI pipeline selector works
- ✅ 1200+ tests passing
- ✅ 85%+ code coverage
- ✅ All governance rules enforced
- ✅ Documentation complete

See [PHASE_14_ACCEPTANCE_CRITERIA.md](PHASE_14_ACCEPTANCE_CRITERIA.md) for full checklist.

---

## What Changes for Developers

### Before Phase 14 (Phase 13)
```python
# Single tool
response = plugin.run_tool("detect_players", image_bytes)
# Result: {"detections": [...]}
```

### After Phase 14
```python
# Define pipeline (JSON)
pipeline = registry.get("player_tracking_v1")

# Run pipeline
response = await service.execute(pipeline, image_bytes)
# Result: {"detections": [...], "tracks": [...], "visualization": "..."}
```

---

## File Locations

**Code**:
- `app/models/pipeline_graph_models.py`
- `app/services/pipeline_registry_service.py`
- `app/services/dag_pipeline_service.py`
- `app/routes/routes_pipelines.py`

**Pipelines**:
- `app/pipelines/*.json`

**Tests**:
- `tests/pipelines/`
- `tests/integration/`

**Frontend**:
- `web-ui/src/types/pipeline_graph.ts`
- `web-ui/src/api/pipelines.ts`
- `web-ui/src/components/VideoTracker/PipelineSelector.tsx`

---

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| JSON for pipelines | Human-readable, version-controllable, no special runtime |
| Registry immutable | Audit trail, reproducibility, no surprise breakages |
| Type validation required | Prevents data type errors before execution |
| DAG only | Guarantees termination, deterministic execution |
| Explicit everything | No silent failures, clear intent in code |

---

## Phase Progression

```
Phase 13: Single Plugin (Linear)
    ↓
Phase 14: Multiple Plugins (DAG)
    ↓
Phase 15: Job Queuing for Pipelines
    ↓
Phase 16: Performance Metrics
    ↓
Phase 17: Versioning & History
```

---

## Getting Help

**Confused?**
1. Check [PHASE_14_GLOSSARY.md](PHASE_14_GLOSSARY.md) for terminology
2. Re-read relevant section of [PHASE_14_ARCHITECTURE.md](PHASE_14_ARCHITECTURE.md)
3. See examples in [PHASE_14_DEVELOPER_GUIDE.md](PHASE_14_DEVELOPER_GUIDE.md)

**Want to build?**
1. Follow [PHASE_14_MIGRATION_PLAN.md](PHASE_14_MIGRATION_PLAN.md) (10 commits)
2. Reference [PHASE_14_FOLDER_STRUCTURE.md](PHASE_14_FOLDER_STRUCTURE.md) for layout
3. Verify with [PHASE_14_ACCEPTANCE_CRITERIA.md](PHASE_14_ACCEPTANCE_CRITERIA.md) checklist

**Enforcing rules?**
→ [PHASE_14_GOVERNANCE_RULES.md](PHASE_14_GOVERNANCE_RULES.md) (15 rules)

---

## Document Versions

- **Version**: 1.0
- **Status**: Complete & Ready for Implementation
- **Updated**: February 12, 2026

---

## Next Steps

1. **Review** all documentation (1-2 hours)
2. **Plan** first commit with team
3. **Implement** Commits 1-4 (infrastructure)
4. **Test** with acceptance criteria
5. **Complete** remaining commits
6. **Verify** all tests pass
7. **Merge** to main

---

## Questions?

Refer to the appropriate document above.

All 8 documents work together to form the complete Phase 14 specification.

---

**Phase 14 is ready to build. Let's transform ForgeSyte into a workflow engine.** 🚀
