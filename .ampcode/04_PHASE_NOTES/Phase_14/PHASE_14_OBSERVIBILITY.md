 here is the **single, unified, authoritative Phase 14 Observability Specification**, combining everything into one clean document.  
This replaces all the scattered pieces and gives you one canonical source of truth.

You can drop this directly into:

```
docs/phases/phase_14_observability.md
```

---

# **PHASE 14 — OBSERVABILITY SPECIFICATION**  
### *Unified Document Covering Logging, DuckDB, Schema, OTEL (Enhancement), and Grafana (Enhancement)*

---

# **1. Purpose**

Phase 14 introduces **cross‑plugin DAG pipelines**.  
Observability must evolve from Phase 13’s linear tool logs into a **graph‑aware, node‑aware, pipeline‑aware** system.

This document defines:

- Required log events  
- Required fields  
- How logs integrate with DuckDB  
- JSON schema for structured logs  
- Optional OpenTelemetry mapping (enhancement)  
- Optional Grafana dashboards (enhancement)  

This is the **canonical observability contract** for Phase 14.

---

# **2. Observability Goals**

Phase 14 observability must provide:

### **2.1 Debuggability**
Reconstruct exactly what happened in any DAG run.

### **2.2 Determinism**
Every node execution must be traceable with stable IDs.

### **2.3 Governance**
No hidden behavior. Logs must reflect the actual DAG.

### **2.4 Performance Insight**
Measure:

- per‑node duration  
- per‑plugin duration  
- pipeline duration  
- critical path  

### **2.5 Compatibility**
Must remain compatible with:

- Phase 13 linear pipelines  
- DuckDB ingestion  
- existing dashboards  

---

# **3. Core Concepts**

### **Pipeline Run**
A single execution of a named DAG pipeline.

### **Node Execution**
Execution of one `(plugin_id, tool_id)` node.

### **Edge**
Logical data flow between nodes.

### **Run ID**
A UUID generated per pipeline execution.

---

# **4. Required Log Events**

All events share:

```
timestamp
pipeline_id
run_id
pipeline_type = "dag"
```

## **4.1 pipeline_started**

Emitted once per run.

Fields:

- `entry_nodes`
- `output_nodes`
- `node_count`

---

## **4.2 pipeline_node_started**

Emitted once per node.

Fields:

- `node_id`
- `plugin_id`
- `tool_id`
- `step_index`
- `predecessor_node_ids`

---

## **4.3 pipeline_node_completed**

Emitted on success.

Fields:

- `node_id`
- `plugin_id`
- `tool_id`
- `step_index`
- `duration_ms`
- `output_keys` (top‑level keys of output payload)

---

## **4.4 pipeline_node_failed**

Emitted on failure.

Fields:

- `node_id`
- `plugin_id`
- `tool_id`
- `step_index`
- `duration_ms` (if measurable)
- `error_type`
- `error_message`

---

## **4.5 pipeline_completed**

Emitted on success.

Fields:

- `duration_ms`
- `node_count`
- `output_node_ids`

---

## **4.6 pipeline_failed**

Emitted on failure.

Fields:

- `duration_ms`
- `failed_node_id`
- `error_type`
- `error_message`

---

# **5. Logging Locations**

### **DagPipelineService.run_pipeline**
- emits:
  - `pipeline_started`
  - `pipeline_completed`
  - `pipeline_failed`

### **Node execution loop**
- emits:
  - `pipeline_node_started`
  - `pipeline_node_completed`
  - `pipeline_node_failed`

---

# **6. DuckDB Integration (Phase 14‑Native)**

Your existing DuckDB observability pipeline remains **unchanged**:

```
structured logs → parquet → DuckDB → SQL analytics
```

Phase 14 simply adds new columns and new event types.

DuckDB supports:

- schema evolution  
- nested JSON  
- arrays  
- semi‑structured logs  

No migration required.

### **6.1 New DuckDB Columns**

Add:

```
pipeline_id
run_id
node_id
step_index
event_type
predecessor_node_ids
output_keys
error_type
error_message
```

DuckDB will automatically ingest these.

### **6.2 Example DuckDB Queries**

#### Critical path:
```sql
SELECT node_id, duration_ms
FROM logs
WHERE pipeline_id = 'player_tracking_v1'
  AND event_type = 'pipeline_node_completed'
ORDER BY step_index;
```

#### Plugin bottlenecks:
```sql
SELECT plugin_id, AVG(duration_ms) AS avg_ms
FROM logs
WHERE event_type = 'pipeline_node_completed'
GROUP BY plugin_id
ORDER BY avg_ms DESC;
```

#### Node failure rate:
```sql
SELECT node_id, COUNT(*) AS failures
FROM logs
WHERE event_type = 'pipeline_node_failed'
GROUP BY node_id;
```

---

# **7. JSON Logging Schema (Canonical)**

Save as:

```
docs/phases/phase_14_logging_schema.json
```

This schema defines all Phase 14 log events.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Phase 14 DAG Pipeline Logs",
  "type": "object",
  "oneOf": [
    { "$ref": "#/definitions/pipeline_started" },
    { "$ref": "#/definitions/pipeline_node_started" },
    { "$ref": "#/definitions/pipeline_node_completed" },
    { "$ref": "#/definitions/pipeline_node_failed" },
    { "$ref": "#/definitions/pipeline_completed" },
    { "$ref": "#/definitions/pipeline_failed" }
  ],
  "definitions": {
    "base": {
      "type": "object",
      "properties": {
        "timestamp": { "type": "string", "format": "date-time" },
        "pipeline_id": { "type": "string" },
        "run_id": { "type": "string" },
        "pipeline_type": { "type": "string", "enum": ["dag"] }
      },
      "required": ["timestamp", "pipeline_id", "run_id", "pipeline_type"]
    }
  }
}
```

*(Truncated here for readability — full schema already provided earlier.)*

---

# **8. Error Handling Rules**

### **8.1 Node failure**
- Stop entire pipeline.
- Emit `pipeline_node_failed`.
- Emit `pipeline_failed`.
- Return 400/500 to caller.

### **8.2 Validation failure**
- Emit `pipeline_failed` with `failed_node_id = null`.

### **8.3 Partial results**
- Not returned in Phase 14.
- Full pipeline must succeed.

---

# **9. Backward Compatibility**

Phase 13 linear pipelines continue to work.

Logs include:

```
pipeline_type = "linear"
```

Phase 14 DAG logs include:

```
pipeline_type = "dag"
```

Dashboards can filter by type.

---

# **10. Optional Enhancements (Not Phase 14 Scope)**

These are **separate issues**, not part of Phase 14.

---

## **10.1 OpenTelemetry Integration (Enhancement)**

Map:

- Pipeline run → OTEL trace  
- Node execution → OTEL span  

Attributes:

```
pipeline.id
pipeline.run_id
pipeline.node_id
plugin.id
tool.id
step_index
duration_ms
error.type
error.message
```

No sampling or exporters included in Phase 14.

---

## **10.2 Grafana Dashboard Design (Enhancement)**

### Dashboard 1 — Pipeline Overview
- Run count by pipeline  
- Success vs failure  
- Average duration  

### Dashboard 2 — Node Performance
- Slowest nodes  
- Duration distribution  
- Critical path  

### Dashboard 3 — Failures
- Failures by node  
- Recent failed runs  

### Dashboard 4 — Cross‑Plugin Analysis
- Plugin bottlenecks  
- Cross‑plugin transitions  
- Plugin error rates  

---

# **11. Summary**

Phase 14 observability:

- Adds DAG‑aware logs  
- Adds node‑aware logs  
- Adds pipeline lifecycle logs  
- Integrates seamlessly with DuckDB  
- Enables deep analytics  
- Remains backward compatible  
- Requires no ingestion changes  
- Provides a foundation for OTEL + Grafana enhancements  

This is the **canonical observability contract** for Phase 14.

---

Here we go, all three in one place, tight and concrete.

---

### Phase 14 observability implementation patch

#### 1. Extend `DagPipelineService` with lifecycle + node logs

```python
# server/app/services/dag_pipeline_service.py
import logging
import time
import uuid
from typing import Dict, Any, List
from .pipeline_registry_service import PipelineRegistryService
from .plugin_management_service import PluginManagementService
from ..models.pipeline_graph_models import PipelineDefinition

logger = logging.getLogger("pipelines.dag")


class DagPipelineService:
    def __init__(
        self,
        registry: PipelineRegistryService,
        plugin_manager: PluginManagementService,
    ) -> None:
        self._registry = registry
        self._plugin_manager = plugin_manager

    def run_pipeline(self, pipeline_id: str, initial_payload: Dict[str, Any]) -> Dict[str, Any]:
        pipeline = self._registry.get_pipeline(pipeline_id)
        run_id = str(uuid.uuid4())
        started_at = time.time()

        self._log_pipeline_started(pipeline, run_id)

        try:
            order = self._topological_order(pipeline)
            context: Dict[str, Dict[str, Any]] = {}

            for step_index, node_id in enumerate(order):
                node = next(n for n in pipeline.nodes if n.id == node_id)
                preds = [e.from_node for e in pipeline.edges if e.to_node == node_id]

                self._log_node_started(pipeline, run_id, node.id, node.plugin_id, node.tool_id, step_index, preds)
                node_started_at = time.time()

                payload = self._merge_predecessor_outputs(node_id, pipeline, context, initial_payload)

                plugin = self._plugin_manager.get_plugin(node.plugin_id)
                try:
                    output = plugin.run_tool(node.tool_id, payload)
                except Exception as exc:
                    duration_ms = (time.time() - node_started_at) * 1000
                    self._log_node_failed(
                        pipeline,
                        run_id,
                        node.id,
                        node.plugin_id,
                        node.tool_id,
                        step_index,
                        duration_ms,
                        type(exc).__name__,
                        str(exc),
                    )
                    raise

                duration_ms = (time.time() - node_started_at) * 1000
                context[node_id] = output or {}
                self._log_node_completed(
                    pipeline,
                    run_id,
                    node.id,
                    node.plugin_id,
                    node.tool_id,
                    step_index,
                    duration_ms,
                    list((output or {}).keys()),
                )

            final: Dict[str, Any] = dict(initial_payload)
            for nid in pipeline.output_nodes:
                final.update(context.get(nid, {}))

            duration_ms = (time.time() - started_at) * 1000
            self._log_pipeline_completed(pipeline, run_id, duration_ms)
            return final

        except Exception as exc:
            duration_ms = (time.time() - started_at) * 1000
            self._log_pipeline_failed(
                pipeline,
                run_id,
                duration_ms,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
            raise

    # existing _topological_order and _merge_predecessor_outputs unchanged

    def _log_pipeline_started(self, pipeline: PipelineDefinition, run_id: str) -> None:
        logger.info(
            "pipeline_started",
            extra={
                "event_type": "pipeline_started",
                "pipeline_type": "dag",
                "pipeline_id": pipeline.id,
                "run_id": run_id,
                "entry_nodes": pipeline.entry_nodes,
                "output_nodes": pipeline.output_nodes,
                "node_count": len(pipeline.nodes),
            },
        )

    def _log_pipeline_completed(self, pipeline: PipelineDefinition, run_id: str, duration_ms: float) -> None:
        logger.info(
            "pipeline_completed",
            extra={
                "event_type": "pipeline_completed",
                "pipeline_type": "dag",
                "pipeline_id": pipeline.id,
                "run_id": run_id,
                "duration_ms": duration_ms,
                "node_count": len(pipeline.nodes),
                "output_node_ids": pipeline.output_nodes,
            },
        )

    def _log_pipeline_failed(
        self,
        pipeline: PipelineDefinition,
        run_id: str,
        duration_ms: float,
        error_type: str,
        error_message: str,
        failed_node_id: str | None = None,
    ) -> None:
        logger.error(
            "pipeline_failed",
            extra={
                "event_type": "pipeline_failed",
                "pipeline_type": "dag",
                "pipeline_id": pipeline.id,
                "run_id": run_id,
                "duration_ms": duration_ms,
                "failed_node_id": failed_node_id,
                "error_type": error_type,
                "error_message": error_message,
            },
        )

    def _log_node_started(
        self,
        pipeline: PipelineDefinition,
        run_id: str,
        node_id: str,
        plugin_id: str,
        tool_id: str,
        step_index: int,
        predecessor_node_ids: list[str],
    ) -> None:
        logger.info(
            "pipeline_node_started",
            extra={
                "event_type": "pipeline_node_started",
                "pipeline_type": "dag",
                "pipeline_id": pipeline.id,
                "run_id": run_id,
                "node_id": node_id,
                "plugin_id": plugin_id,
                "tool_id": tool_id,
                "step_index": step_index,
                "predecessor_node_ids": predecessor_node_ids,
            },
        )

    def _log_node_completed(
        self,
        pipeline: PipelineDefinition,
        run_id: str,
        node_id: str,
        plugin_id: str,
        tool_id: str,
        step_index: int,
        duration_ms: float,
        output_keys: list[str],
    ) -> None:
        logger.info(
            "pipeline_node_completed",
            extra={
                "event_type": "pipeline_node_completed",
                "pipeline_type": "dag",
                "pipeline_id": pipeline.id,
                "run_id": run_id,
                "node_id": node_id,
                "plugin_id": plugin_id,
                "tool_id": tool_id,
                "step_index": step_index,
                "duration_ms": duration_ms,
                "output_keys": output_keys,
            },
        )

    def _log_node_failed(
        self,
        pipeline: PipelineDefinition,
        run_id: str,
        node_id: str,
        plugin_id: str,
        tool_id: str,
        step_index: int,
        duration_ms: float,
        error_type: str,
        error_message: str,
    ) -> None:
        logger.error(
            "pipeline_node_failed",
            extra={
                "event_type": "pipeline_node_failed",
                "pipeline_type": "dag",
                "pipeline_id": pipeline.id,
                "run_id": run_id,
                "node_id": node_id,
                "plugin_id": plugin_id,
                "tool_id": tool_id,
                "step_index": step_index,
                "duration_ms": duration_ms,
                "error_type": error_type,
                "error_message": error_message,
            },
        )
```

---

### Phase 14 observability test suite

Add a small log-capturing helper and tests.

#### 1. Pytest log capture for DAG runs

```python
# server/app/tests/test_phase14_observability.py
import logging
from typing import Any, Dict, List

from server.app.models.pipeline_graph_models import PipelineDefinition, PipelineNode, PipelineEdge
from server.app.services.dag_pipeline_service import DagPipelineService
from server.app.services.pipeline_registry_service import PipelineRegistryService


class RecordingPlugin:
    def __init__(self, name: str) -> None:
        self.name = name
        self.tools = ["t1"]

    def run_tool(self, tool_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(payload)
        out[self.name] = tool_id
        return out


class DummyPluginManager:
    def __init__(self) -> None:
        self._plugins = {
            "a": RecordingPlugin("a"),
            "b": RecordingPlugin("b"),
        }

    def list_plugins(self):
        class P:
            def __init__(self, pid: str) -> None:
                self.id = pid
        return [P(pid) for pid in self._plugins.keys()]

    def get_plugin(self, plugin_id: str):
        return self._plugins[plugin_id]


class InMemoryRegistry(PipelineRegistryService):
    def __init__(self, plugin_manager, pipeline: PipelineDefinition):
        self._plugin_manager = plugin_manager
        self._base_dir = None
        self._pipelines = {pipeline.id: pipeline}


def _make_pipeline() -> PipelineDefinition:
    return PipelineDefinition(
        id="p_obs",
        name="obs",
        nodes=[
            PipelineNode(id="n1", plugin_id="a", tool_id="t1"),
            PipelineNode(id="n2", plugin_id="b", tool_id="t1"),
        ],
        edges=[PipelineEdge(from_node="n1", to_node="n2")],
        entry_nodes=["n1"],
        output_nodes=["n2"],
    )


def test_observability_emits_pipeline_and_node_events(caplog):
    pm = DummyPluginManager()
    pipeline = _make_pipeline()
    registry = InMemoryRegistry(pm, pipeline)
    dag = DagPipelineService(registry, pm)

    caplog.set_level(logging.INFO, logger="pipelines.dag")

    result = dag.run_pipeline("p_obs", {"x": 1})
    assert result["x"] == 1
    assert result["b"] == "t1"

    events: List[Dict[str, Any]] = []
    for rec in caplog.records:
        if getattr(rec, "pipeline_type", None) == "dag":
            events.append(rec.__dict__)

    # pipeline_started + pipeline_completed + 2x node_started + 2x node_completed
    event_types = [e["event_type"] for e in events]
    assert "pipeline_started" in event_types
    assert "pipeline_completed" in event_types
    assert event_types.count("pipeline_node_started") == 2
    assert event_types.count("pipeline_node_completed") == 2

    # all share same pipeline_id and run_id
    pipeline_ids = {e["pipeline_id"] for e in events}
    run_ids = {e["run_id"] for e in events}
    assert pipeline_ids == {"p_obs"}
    assert len(run_ids) == 1


def test_observability_emits_failure_events(caplog):
    class FailingPlugin(RecordingPlugin):
        def run_tool(self, tool_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            raise RuntimeError("boom")

    pm = DummyPluginManager()
    pm._plugins["b"] = FailingPlugin("b")

    pipeline = _make_pipeline()
    registry = InMemoryRegistry(pm, pipeline)
    dag = DagPipelineService(registry, pm)

    caplog.set_level(logging.INFO, logger="pipelines.dag")

    import pytest
    with pytest.raises(RuntimeError):
        dag.run_pipeline("p_obs", {"x": 1})

    events = [rec.__dict__ for rec in caplog.records if getattr(rec, "pipeline_type", None) == "dag"]
    event_types = [e["event_type"] for e in events]

    assert "pipeline_started" in event_types
    assert "pipeline_failed" in event_types
    assert "pipeline_node_failed" in event_types
```

---

### Phase 14 DuckDB SQL cookbook (20 queries)

Assume a `logs` table with Phase 14 fields.

1. **All DAG events for a pipeline run**

```sql
SELECT *
FROM logs
WHERE pipeline_type = 'dag'
  AND pipeline_id = 'player_tracking_v1'
  AND run_id = '...'
ORDER BY timestamp;
```

2. **Pipeline run durations**

```sql
SELECT pipeline_id,
       AVG(duration_ms) AS avg_ms,
       PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) AS p95_ms
FROM logs
WHERE event_type = 'pipeline_completed'
GROUP BY pipeline_id;
```

3. **Node durations per pipeline**

```sql
SELECT pipeline_id, node_id, AVG(duration_ms) AS avg_ms
FROM logs
WHERE event_type = 'pipeline_node_completed'
GROUP BY pipeline_id, node_id
ORDER BY avg_ms DESC;
```

4. **Slowest nodes overall**

```sql
SELECT node_id, plugin_id, tool_id,
       AVG(duration_ms) AS avg_ms
FROM logs
WHERE event_type = 'pipeline_node_completed'
GROUP BY node_id, plugin_id, tool_id
ORDER BY avg_ms DESC
LIMIT 20;
```

5. **Failure count per node**

```sql
SELECT pipeline_id, node_id, COUNT(*) AS failures
FROM logs
WHERE event_type = 'pipeline_node_failed'
GROUP BY pipeline_id, node_id
ORDER BY failures DESC;
```

6. **Failure rate per pipeline**

```sql
WITH runs AS (
  SELECT pipeline_id, run_id,
         MAX(CASE WHEN event_type = 'pipeline_completed' THEN 1 ELSE 0 END) AS completed,
         MAX(CASE WHEN event_type = 'pipeline_failed' THEN 1 ELSE 0 END) AS failed
  FROM logs
  WHERE pipeline_type = 'dag'
  GROUP BY pipeline_id, run_id
)
SELECT pipeline_id,
       SUM(failed) AS failed_runs,
       SUM(completed) AS successful_runs,
       SUM(failed)::DOUBLE / NULLIF(SUM(failed) + SUM(completed), 0) AS failure_rate
FROM runs
GROUP BY pipeline_id;
```

7. **Average step index per node (position in pipeline)**

```sql
SELECT pipeline_id, node_id, AVG(step_index) AS avg_step
FROM logs
WHERE event_type LIKE 'pipeline_node_%'
GROUP BY pipeline_id, node_id
ORDER BY avg_step;
```

8. **Critical path approximation (sum of node durations)**

```sql
SELECT pipeline_id, run_id, SUM(duration_ms) AS approx_critical_path_ms
FROM logs
WHERE event_type = 'pipeline_node_completed'
GROUP BY pipeline_id, run_id
ORDER BY approx_critical_path_ms DESC;
```

9. **Top failing plugins**

```sql
SELECT plugin_id, COUNT(*) AS failures
FROM logs
WHERE event_type = 'pipeline_node_failed'
GROUP BY plugin_id
ORDER BY failures DESC;
```

10. **Top failing tools**

```sql
SELECT plugin_id, tool_id, COUNT(*) AS failures
FROM logs
WHERE event_type = 'pipeline_node_failed'
GROUP BY plugin_id, tool_id
ORDER BY failures DESC;
```

11. **Pipelines with most nodes**

```sql
SELECT pipeline_id, MAX(node_count) AS max_nodes
FROM logs
WHERE event_type = 'pipeline_started'
GROUP BY pipeline_id
ORDER BY max_nodes DESC;
```

12. **Average duration per plugin within pipelines**

```sql
SELECT pipeline_id, plugin_id, AVG(duration_ms) AS avg_ms
FROM logs
WHERE event_type = 'pipeline_node_completed'
GROUP BY pipeline_id, plugin_id
ORDER BY avg_ms DESC;
```

13. **Recent failed runs**

```sql
SELECT timestamp, pipeline_id, run_id, failed_node_id, error_type, error_message
FROM logs
WHERE event_type = 'pipeline_failed'
ORDER BY timestamp DESC
LIMIT 50;
```

14. **Node output key cardinality**

```sql
SELECT pipeline_id, node_id,
       AVG(CARDINALITY(output_keys)) AS avg_output_keys
FROM logs
WHERE event_type = 'pipeline_node_completed'
GROUP BY pipeline_id, node_id
ORDER BY avg_output_keys DESC;
```

15. **Per-frame performance (Phase 15 extension, if frame_index logged)**

```sql
SELECT frame_index, SUM(duration_ms) AS total_ms
FROM logs
WHERE pipeline_type = 'dag'
  AND event_type = 'pipeline_node_completed'
GROUP BY frame_index
ORDER BY total_ms DESC;
```

16. **Time series of pipeline durations**

```sql
SELECT DATE_TRUNC('minute', timestamp) AS minute,
       AVG(duration_ms) AS avg_ms
FROM logs
WHERE event_type = 'pipeline_completed'
GROUP BY minute
ORDER BY minute;
```

17. **Distribution of node durations**

```sql
SELECT width_bucket(duration_ms, 0, 2000, 20) AS bucket,
       COUNT(*) AS count
FROM logs
WHERE event_type = 'pipeline_node_completed'
GROUP BY bucket
ORDER BY bucket;
```

18. **Pipelines most used in last 24h**

```sql
SELECT pipeline_id, COUNT(DISTINCT run_id) AS runs
FROM logs
WHERE event_type = 'pipeline_started'
  AND timestamp > NOW() - INTERVAL '1 day'
GROUP BY pipeline_id
ORDER BY runs DESC;
```

19. **Average duration per step index**

```sql
SELECT step_index, AVG(duration_ms) AS avg_ms
FROM logs
WHERE event_type = 'pipeline_node_completed'
GROUP BY step_index
ORDER BY step_index;
```

20. **Correlate failures with duration**

```sql
SELECT node_id,
       AVG(CASE WHEN event_type = 'pipeline_node_completed' THEN duration_ms END) AS avg_success_ms,
       AVG(CASE WHEN event_type = 'pipeline_node_failed' THEN duration_ms END) AS avg_failure_ms
FROM logs
WHERE event_type IN ('pipeline_node_completed', 'pipeline_node_failed')
GROUP BY node_id
ORDER BY avg_failure_ms DESC NULLS LAST;
```

This gives you the full loop: implementation, tests, and analytics—Phase 14 observability as a closed, deterministic system.