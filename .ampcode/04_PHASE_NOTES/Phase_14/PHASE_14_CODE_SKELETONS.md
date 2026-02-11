Here are clean Phase 14 code skeletons — empty classes, method signatures, and types only.

---

### `server/app/models/pipeline_graph_models.py`

```python
from typing import List, Dict, Literal
from pydantic import BaseModel


NodeId = str


class PipelineNode(BaseModel):
    id: NodeId
    plugin_id: str
    tool_id: str


class PipelineEdge(BaseModel):
    from_node: NodeId
    to_node: NodeId


class PipelineDefinition(BaseModel):
    id: str
    name: str
    nodes: List[PipelineNode]
    edges: List[PipelineEdge]
    entry_nodes: List[NodeId]
    output_nodes: List[NodeId]


class ToolCapability(BaseModel):
    id: str
    inputs: List[str]
    outputs: List[str]
    capabilities: List[str]
```

---

### `server/app/services/pipeline_registry_service.py`

```python
from typing import List
from .plugin_management_service import PluginManagementService
from ..models.pipeline_graph_models import PipelineDefinition


class PipelineRegistryService:
    def __init__(self, plugin_manager: PluginManagementService) -> None:
        self._plugin_manager = plugin_manager

    def list_pipelines(self) -> List[PipelineDefinition]:
        """Return all registered pipeline definitions."""
        raise NotImplementedError

    def get_pipeline(self, pipeline_id: str) -> PipelineDefinition:
        """Return a single pipeline definition by ID."""
        raise NotImplementedError

    def validate_pipeline(self, pipeline: PipelineDefinition) -> None:
        """Validate structure, plugins, tools, and types."""
        raise NotImplementedError
```

---

### `server/app/services/dag_pipeline_service.py`

```python
from typing import Dict, Any
from .pipeline_registry_service import PipelineRegistryService
from .plugin_management_service import PluginManagementService


class DagPipelineService:
    def __init__(
        self,
        registry: PipelineRegistryService,
        plugin_manager: PluginManagementService,
    ) -> None:
        self._registry = registry
        self._plugin_manager = plugin_manager

    def run_pipeline(self, pipeline_id: str, initial_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a validated DAG pipeline and return final output."""
        raise NotImplementedError

    def _topological_order(self, pipeline_id: str) -> list[str]:
        """Return node IDs in topological order."""
        raise NotImplementedError

    def _merge_predecessor_outputs(
        self,
        node_id: str,
        context: Dict[str, Dict[str, Any]],
        initial_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Merge outputs of predecessor nodes into a single payload."""
        raise NotImplementedError
```

---

### `server/app/routes/routes_pipelines.py`

```python
from typing import Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel
from ..services.pipeline_registry_service import PipelineRegistryService
from ..services.dag_pipeline_service import DagPipelineService

router = APIRouter()


class RunPipelineRequest(BaseModel):
    payload: Dict[str, Any]


@router.get("/pipelines")
async def list_pipelines():
    """List all available pipelines."""
    raise NotImplementedError


@router.get("/pipelines/{pipeline_id}")
async def get_pipeline(pipeline_id: str):
    """Get a single pipeline definition."""
    raise NotImplementedError


@router.post("/pipelines/{pipeline_id}/run")
async def run_pipeline(pipeline_id: str, req: RunPipelineRequest):
    """Run a DAG pipeline by ID."""
    raise NotImplementedError
```

---

### `web-ui/src/types/pipeline_graph.ts`

```ts
export type NodeId = string

export interface PipelineNode {
  id: NodeId
  pluginId: string
  toolId: string
}

export interface PipelineEdge {
  fromNode: NodeId
  toNode: NodeId
}

export interface PipelineDefinition {
  id: string
  name: string
  nodes: PipelineNode[]
  edges: PipelineEdge[]
  entryNodes: NodeId[]
  outputNodes: NodeId[]
}
```

---

### `web-ui/src/api/pipelines.ts`

```ts
import { PipelineDefinition } from "../types/pipeline_graph"

export async function listPipelines(): Promise<PipelineDefinition[]> {
  throw new Error("Not implemented")
}

export async function getPipeline(pipelineId: string): Promise<PipelineDefinition> {
  throw new Error("Not implemented")
}

export async function runPipeline(
  pipelineId: string,
  payload: Record<string, unknown>,
): Promise<any> {
  throw new Error("Not implemented")
}
```

---

### `web-ui/src/components/VideoTracker/PipelineSelector.tsx`

```tsx
import React from "react"
import { PipelineDefinition } from "../../types/pipeline_graph"

interface PipelineSelectorProps {
  pipelines: PipelineDefinition[]
  selectedPipelineId: string | null
  onChange: (pipelineId: string) => void
}

export const PipelineSelector: React.FC<PipelineSelectorProps> = ({
  pipelines,
  selectedPipelineId,
  onChange,
}) => {
  return (
    <select
      value={selectedPipelineId ?? ""}
      onChange={e => onChange(e.target.value)}
    >
      <option value="" disabled>
        Select pipeline…
      </option>
      {pipelines.map(p => (
        <option key={p.id} value={p.id}>
          {p.name}
        </option>
      ))}
    </select>
  )
}
```