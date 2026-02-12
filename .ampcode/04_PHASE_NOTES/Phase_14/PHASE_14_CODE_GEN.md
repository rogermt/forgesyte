---

## 🔥 Phase 14 code generation (full implementation)

### `server/app/models/pipeline_graph_models.py`

```python
from typing import List, Dict, Literal, Set
from pydantic import BaseModel, Field, root_validator, validator

NodeId = str
TypeTag = str


class PipelineNode(BaseModel):
    id: NodeId
    plugin_id: str
    tool_id: str


class PipelineEdge(BaseModel):
    from_node: NodeId = Field(..., alias="from")
    to_node: NodeId = Field(..., alias="to")


class PipelineDefinition(BaseModel):
    id: str
    name: str
    nodes: List[PipelineNode]
    edges: List[PipelineEdge]
    entry_nodes: List[NodeId]
    output_nodes: List[NodeId]

    @root_validator
    def ensure_nodes_and_edges_consistent(cls, values: Dict) -> Dict:
        node_ids: Set[NodeId] = {n.id for n in values.get("nodes", [])}
        for edge in values.get("edges", []):
            if edge.from_node not in node_ids:
                raise ValueError(f"Edge from unknown node: {edge.from_node}")
            if edge.to_node not in node_ids:
                raise ValueError(f"Edge to unknown node: {edge.to_node}")
        for nid in values.get("entry_nodes", []):
            if nid not in node_ids:
                raise ValueError(f"Entry node not in nodes: {nid}")
        for nid in values.get("output_nodes", []):
            if nid not in node_ids:
                raise ValueError(f"Output node not in nodes: {nid}")
        return values


class ToolCapability(BaseModel):
    id: str
    inputs: List[TypeTag]
    outputs: List[TypeTag]
    capabilities: List[str] = []
```

> Note: `PipelineEdge` uses `from`/`to` in JSON but maps to `from_node`/`to_node` internally.

---

### `server/app/services/pipeline_registry_service.py`

```python
from typing import List, Dict
import json
import pathlib
from .plugin_management_service import PluginManagementService
from ..models.pipeline_graph_models import PipelineDefinition


class PipelineRegistryService:
    def __init__(self, plugin_manager: PluginManagementService, base_dir: str = "server/app/pipelines") -> None:
        self._plugin_manager = plugin_manager
        self._base_dir = pathlib.Path(base_dir)
        self._pipelines: Dict[str, PipelineDefinition] = {}
        self._load_pipelines()

    def _load_pipelines(self) -> None:
        if not self._base_dir.exists():
            return
        for path in self._base_dir.glob("*.json"):
            data = json.loads(path.read_text())
            pipeline = PipelineDefinition(**data)
            self.validate_pipeline(pipeline)
            self._pipelines[pipeline.id] = pipeline

    def list_pipelines(self) -> List[PipelineDefinition]:
        return list(self._pipelines.values())

    def get_pipeline(self, pipeline_id: str) -> PipelineDefinition:
        try:
            return self._pipelines[pipeline_id]
        except KeyError:
            raise ValueError(f"Pipeline '{pipeline_id}' not found")

    def validate_pipeline(self, pipeline: PipelineDefinition) -> None:
        # Structural validation is already done by PipelineDefinition
        # Here we validate plugins/tools existence and acyclicity.
        plugin_ids = {p.id for p in self._plugin_manager.list_plugins()}
        for node in pipeline.nodes:
            if node.plugin_id not in plugin_ids:
                raise ValueError(f"Unknown plugin_id '{node.plugin_id}' in node '{node.id}'")
            plugin = self._plugin_manager.get_plugin(node.plugin_id)
            if node.tool_id not in plugin.tools:
                raise ValueError(f"Unknown tool_id '{node.tool_id}' in node '{node.id}'")

        # Simple cycle detection via DFS
        graph = {n.id: [] for n in pipeline.nodes}
        for e in pipeline.edges:
            graph[e.from_node].append(e.to_node)

        visited = set()
        stack = set()

        def dfs(nid: str) -> None:
            if nid in stack:
                raise ValueError("Pipeline contains a cycle")
            if nid in visited:
                return
            stack.add(nid)
            for succ in graph.get(nid, []):
                dfs(succ)
            stack.remove(nid)
            visited.add(nid)

        for nid in graph:
            if nid not in visited:
                dfs(nid)
```

---

### `server/app/services/dag_pipeline_service.py`

```python
from typing import Dict, Any, List
from .pipeline_registry_service import PipelineRegistryService
from .plugin_management_service import PluginManagementService
from ..models.pipeline_graph_models import PipelineDefinition
import logging

logger = logging.getLogger(__name__)


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
        order = self._topological_order(pipeline)
        context: Dict[str, Dict[str, Any]] = {}

        for step_index, node_id in enumerate(order):
            node = next(n for n in pipeline.nodes if n.id == node_id)
            payload = self._merge_predecessor_outputs(node_id, pipeline, context, initial_payload)

            plugin = self._plugin_manager.get_plugin(node.plugin_id)
            logger.info(
                "DAG pipeline node",
                extra={
                    "pipeline_id": pipeline.id,
                    "node_id": node.id,
                    "plugin_id": node.plugin_id,
                    "tool_id": node.tool_id,
                    "step_index": step_index,
                },
            )
            output = plugin.run_tool(node.tool_id, payload)
            context[node_id] = output

        # Merge outputs of output_nodes
        final: Dict[str, Any] = dict(initial_payload)
        for nid in pipeline.output_nodes:
            final.update(context.get(nid, {}))
        return final

    def _topological_order(self, pipeline: PipelineDefinition) -> List[str]:
        graph: Dict[str, List[str]] = {n.id: [] for n in pipeline.nodes}
        indegree: Dict[str, int] = {n.id: 0 for n in pipeline.nodes}
        for e in pipeline.edges:
            graph[e.from_node].append(e.to_node)
            indegree[e.to_node] += 1

        queue = [nid for nid, deg in indegree.items() if deg == 0]
        order: List[str] = []

        while queue:
            nid = queue.pop(0)
            order.append(nid)
            for succ in graph.get(nid, []):
                indegree[succ] -= 1
                if indegree[succ] == 0:
                    queue.append(succ)

        if len(order) != len(pipeline.nodes):
            raise ValueError("Pipeline contains a cycle or disconnected nodes")
        return order

    def _merge_predecessor_outputs(
        self,
        node_id: str,
        pipeline: PipelineDefinition,
        context: Dict[str, Dict[str, Any]],
        initial_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = dict(initial_payload)
        preds = [e.from_node for e in pipeline.edges if e.to_node == node_id]
        for pid in preds:
            payload.update(context.get(pid, {}))
        return payload
```

---

### `server/app/routes/routes_pipelines.py`

```python
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ..services.pipeline_registry_service import PipelineRegistryService
from ..services.dag_pipeline_service import DagPipelineService

router = APIRouter()


class RunPipelineRequest(BaseModel):
    payload: Dict[str, Any]


def get_registry() -> PipelineRegistryService:
    # Wire into your existing DI / app container
    raise NotImplementedError


def get_dag_service() -> DagPipelineService:
    # Wire into your existing DI / app container
    raise NotImplementedError


@router.get("/pipelines")
async def list_pipelines(
    registry: PipelineRegistryService = Depends(get_registry),
) -> List[Dict[str, Any]]:
    return [p.dict() for p in registry.list_pipelines()]


@router.get("/pipelines/{pipeline_id}")
async def get_pipeline(
    pipeline_id: str,
    registry: PipelineRegistryService = Depends(get_registry),
) -> Dict[str, Any]:
    try:
        pipeline = registry.get_pipeline(pipeline_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return pipeline.dict()


@router.post("/pipelines/{pipeline_id}/run")
async def run_pipeline(
    pipeline_id: str,
    req: RunPipelineRequest,
    dag_service: DagPipelineService = Depends(get_dag_service),
) -> Dict[str, Any]:
    try:
        result = dag_service.run_pipeline(pipeline_id, req.payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"result": result}
```

---

### `web-ui/src/types/pipeline_graph.ts`

(Already good; no change needed.)

---

### `web-ui/src/api/pipelines.ts`

```ts
import { PipelineDefinition } from "../types/pipeline_graph"

const BASE = "/pipelines"

export async function listPipelines(): Promise<PipelineDefinition[]> {
  const res = await fetch(BASE)
  if (!res.ok) throw new Error("Failed to list pipelines")
  return res.json()
}

export async function getPipeline(pipelineId: string): Promise<PipelineDefinition> {
  const res = await fetch(`${BASE}/${encodeURIComponent(pipelineId)}`)
  if (!res.ok) throw new Error("Failed to get pipeline")
  return res.json()
}

export async function runPipeline(
  pipelineId: string,
  payload: Record<string, unknown>,
): Promise<any> {
  const res = await fetch(`${BASE}/${encodeURIComponent(pipelineId)}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ payload }),
  })
  if (!res.ok) throw new Error("Failed to run pipeline")
  return res.json()
}
```

---

### `web-ui/src/components/VideoTracker/PipelineSelector.tsx`

(Already good; you’ll just wire it into `VideoTracker` and `App.tsx` to replace / augment the Phase‑13 tool selection.)

---

## 🔥 Phase 14 test suite

You can split these into three files:

- `server/app/tests/test_dag_validation.py`
- `server/app/tests/test_dag_execution.py`
- `server/app/tests/test_pipeline_registry.py`

### `test_dag_validation.py`

```python
import pytest
from server.app.models.pipeline_graph_models import PipelineDefinition, PipelineNode, PipelineEdge
from server.app.services.pipeline_registry_service import PipelineRegistryService


class DummyPlugin:
    def __init__(self, tools):
        self.tools = tools

    def run_tool(self, tool_id, payload):
        return {"tool": tool_id, **payload}


class DummyPluginManager:
    def __init__(self):
        self._plugins = {"a": DummyPlugin(["t1"]), "b": DummyPlugin(["t2"])}

    def list_plugins(self):
        class P:  # simple struct
            def __init__(self, pid): self.id = pid
        return [P(pid) for pid in self._plugins.keys()]

    def get_plugin(self, plugin_id):
        return self._plugins[plugin_id]


def make_registry():
    return PipelineRegistryService(plugin_manager=DummyPluginManager(), base_dir="does_not_exist")


def test_rejects_unknown_plugin():
    registry = make_registry()
    pipeline = PipelineDefinition(
        id="p1",
        name="bad",
        nodes=[PipelineNode(id="n1", plugin_id="missing", tool_id="t1")],
        edges=[],
        entry_nodes=["n1"],
        output_nodes=["n1"],
    )
    with pytest.raises(ValueError):
        registry.validate_pipeline(pipeline)


def test_rejects_unknown_tool():
    registry = make_registry()
    pipeline = PipelineDefinition(
        id="p1",
        name="bad",
        nodes=[PipelineNode(id="n1", plugin_id="a", tool_id="missing")],
        edges=[],
        entry_nodes=["n1"],
        output_nodes=["n1"],
    )
    with pytest.raises(ValueError):
        registry.validate_pipeline(pipeline)


def test_rejects_cycle():
    registry = make_registry()
    pipeline = PipelineDefinition(
        id="p1",
        name="cycle",
        nodes=[
            PipelineNode(id="n1", plugin_id="a", tool_id="t1"),
            PipelineNode(id="n2", plugin_id="b", tool_id="t2"),
        ],
        edges=[
            PipelineEdge(from_node="n1", to_node="n2"),
            PipelineEdge(from_node="n2", to_node="n1"),
        ],
        entry_nodes=["n1"],
        output_nodes=["n2"],
    )
    with pytest.raises(ValueError):
        registry.validate_pipeline(pipeline)
```

---

### `test_dag_execution.py`

```python
import pytest
from server.app.models.pipeline_graph_models import PipelineDefinition, PipelineNode, PipelineEdge
from server.app.services.dag_pipeline_service import DagPipelineService
from server.app.services.pipeline_registry_service import PipelineRegistryService


class RecordingPlugin:
    def __init__(self, name):
        self.name = name
        self.tools = ["t1", "t2"]
        self.calls = []

    def run_tool(self, tool_id, payload):
        self.calls.append((tool_id, dict(payload)))
        # Append marker to payload
        out = dict(payload)
        out[self.name] = out.get(self.name, []) + [tool_id]
        return out


class RecordingPluginManager:
    def __init__(self):
        self._plugins = {
            "a": RecordingPlugin("a"),
            "b": RecordingPlugin("b"),
        }

    def list_plugins(self):
        class P:
            def __init__(self, pid): self.id = pid
        return [P(pid) for pid in self._plugins.keys()]

    def get_plugin(self, plugin_id):
        return self._plugins[plugin_id]


class InMemoryRegistry(PipelineRegistryService):
    def __init__(self, plugin_manager, pipeline):
        self._plugin_manager = plugin_manager
        self._base_dir = None
        self._pipelines = {pipeline.id: pipeline}


def test_executes_in_topological_order():
    pm = RecordingPluginManager()
    pipeline = PipelineDefinition(
        id="p1",
        name="order",
        nodes=[
            PipelineNode(id="n1", plugin_id="a", tool_id="t1"),
            PipelineNode(id="n2", plugin_id="b", tool_id="t2"),
        ],
        edges=[PipelineEdge(from_node="n1", to_node="n2")],
        entry_nodes=["n1"],
        output_nodes=["n2"],
    )
    registry = InMemoryRegistry(pm, pipeline)
    dag = DagPipelineService(registry, pm)

    result = dag.run_pipeline("p1", {"order": []})

    # Check call order
    assert pm._plugins["a"].calls[0][0] == "t1"
    assert pm._plugins["b"].calls[0][0] == "t2"
    # Check merged output
    assert "a" in result
    assert "b" in result


def test_merges_predecessor_outputs():
    pm = RecordingPluginManager()
    pipeline = PipelineDefinition(
        id="p2",
        name="merge",
        nodes=[
            PipelineNode(id="n1", plugin_id="a", tool_id="t1"),
            PipelineNode(id="n2", plugin_id="a", tool_id="t2"),
            PipelineNode(id="n3", plugin_id="b", tool_id="t1"),
        ],
        edges=[
            PipelineEdge(from_node="n1", to_node="n3"),
            PipelineEdge(from_node="n2", to_node="n3"),
        ],
        entry_nodes=["n1", "n2"],
        output_nodes=["n3"],
    )
    registry = InMemoryRegistry(pm, pipeline)
    dag = DagPipelineService(registry, pm)

    result = dag.run_pipeline("p2", {"base": True})
    # n3 should see merged outputs from n1 and n2 via plugin b's call
    b_calls = pm._plugins["b"].calls
    assert len(b_calls) == 1
    payload = b_calls[0][1]
    assert payload["base"] is True
    # a plugin outputs should have been merged into payload
    assert "a" in payload
```

---

### `test_pipeline_registry.py`

```python
import json
import tempfile
from pathlib import Path
from server.app.services.pipeline_registry_service import PipelineRegistryService
from server.app.models.pipeline_graph_models import PipelineDefinition, PipelineNode, PipelineEdge


class DummyPlugin:
    def __init__(self, tools):
        self.tools = tools

    def run_tool(self, tool_id, payload):
        return payload


class DummyPluginManager:
    def __init__(self):
        self._plugins = {"a": DummyPlugin(["t1"])}

    def list_plugins(self):
        class P:
            def __init__(self, pid): self.id = pid
        return [P("a")]

    def get_plugin(self, plugin_id):
        return self._plugins[plugin_id]


def test_loads_pipelines_from_disk(tmp_path: Path):
    pipeline_data = {
        "id": "p1",
        "name": "test",
        "nodes": [
            {"id": "n1", "plugin_id": "a", "tool_id": "t1"},
        ],
        "edges": [],
        "entry_nodes": ["n1"],
        "output_nodes": ["n1"],
    }
    (tmp_path / "p1.json").write_text(json.dumps(pipeline_data))

    pm = DummyPluginManager()
    registry = PipelineRegistryService(pm, base_dir=str(tmp_path))

    pipelines = registry.list_pipelines()
    assert len(pipelines) == 1
    p = registry.get_pipeline("p1")
    assert p.name == "test"
```