# ⭐ PHASE 14 — FOLDER STRUCTURE

Complete directory structure for Phase 14 implementation.

---

## Server Structure

```
server/
├── app/
│   ├── models/
│   │   ├── pipeline_graph_models.py       # Core DAG models
│   │   └── __init__.py
│   │
│   ├── services/
│   │   ├── pipeline_registry_service.py   # Load/list/get pipelines
│   │   ├── dag_pipeline_service.py        # Validate/execute DAGs
│   │   ├── __init__.py
│   │   └── tests/
│   │       ├── test_pipeline_registry.py
│   │       ├── test_dag_pipeline.py
│   │       └── test_type_validation.py
│   │
│   ├── routes/
│   │   ├── routes_pipelines.py            # REST endpoints
│   │   └── __init__.py
│   │
│   ├── pipelines/                         # Pipeline definitions (JSON)
│   │   ├── player_tracking_v1.json
│   │   ├── ball_tracking_v1.json
│   │   ├── action_recognition_v1.json
│   │   └── README.md                      # Instructions for adding pipelines
│   │
│   └── main.py                            # Add pipeline routes to FastAPI
│
├── tests/
│   ├── pipelines/
│   │   ├── test_pipeline_models.py        # Unit tests
│   │   ├── test_pipeline_registry.py      # Registry tests
│   │   ├── test_pipeline_execution.py     # Execution tests
│   │   ├── test_type_validation.py        # Type checking
│   │   ├── test_dag_validation.py         # DAG validation
│   │   ├── test_pipeline_endpoints.py     # REST API tests
│   │   └── __init__.py
│   │
│   └── integration/
│       ├── test_pipeline_integration.py   # Cross-module integration
│       └── test_pipeline_with_plugins.py  # With real plugins
│
└── pyproject.toml                          # Add Phase 14 dependencies
```

---

## Web-UI Structure

```
web-ui/src/
├── types/
│   ├── pipeline_graph.ts                  # TypeScript types
│   ├── pipeline_execution.ts
│   └── __init__.ts
│
├── api/
│   ├── pipelines.ts                       # API client
│   └── __init__.ts
│
├── components/
│   ├── VideoTracker/
│   │   ├── PipelineSelector.tsx           # UI component
│   │   ├── PipelinePreview.tsx
│   │   ├── PipelineResults.tsx
│   │   ├── styles/
│   │   │   └── PipelineSelector.module.css
│   │   └── __init__.ts
│   │
│   └── __init__.ts
│
├── hooks/
│   ├── usePipelineList.ts                 # Custom hooks
│   ├── usePipelineExecution.ts
│   └── __init__.ts
│
└── tests/
    ├── PipelineSelector.test.tsx
    ├── usePipelineList.test.ts
    ├── pipelines.api.test.ts
    └── __init__.ts
```

---

## Documentation Structure

```
docs/
├── phases/
│   ├── PHASE_14_OVERVIEW.md               # High-level spec
│   ├── PHASE_14_ARCHITECTURE.md           # Technical architecture
│   ├── PHASE_14_DEVELOPER_GUIDE.md        # How to build pipelines
│   ├── PHASE_14_GOVERNANCE_RULES.md       # Enforcement rules
│   ├── PHASE_14_FOLDER_STRUCTURE.md       # This file
│   ├── PHASE_14_MIGRATION_PLAN.md         # Implementation timeline
│   ├── PHASE_14_ACCEPTANCE_CRITERIA.md    # Success criteria
│   └── PHASE_14_GLOSSARY.md               # Terminology
│
└── design/
    ├── PIPELINE_EXECUTION_FLOW.md         # Execution diagram
    ├── TYPE_SYSTEM.md                     # Type compatibility rules
    └── DAG_VALIDATION_RULES.md            # Cycle detection, etc.
```

---

## Pipeline Registry Structure

```
server/app/pipelines/
├── README.md                              # Instructions
├── EXAMPLE.json                           # Template
│
└── Built-in Pipelines (v1.0.0)
    ├── player_tracking_v1.json
    ├── ball_tracking_v1.json
    ├── action_recognition_v1.json
    ├── pose_estimation_v1.json
    └── motion_detection_v1.json
```

Example pipeline structure:

```
player_tracking_v1.json
├── id: "player_tracking_v1"
├── name: "Player Tracking v1"
├── description: "Detect and track players"
├── nodes: [...]
├── edges: [...]
├── entry_nodes: ["detect"]
├── output_nodes: ["track"]
└── metadata: { version, author, tags }
```

---

## Data Models File Structure

### `models/pipeline_graph_models.py`

```python
from pydantic import BaseModel
from typing import List, Dict, Optional

class PipelineNode(BaseModel):
    id: str
    plugin_id: str
    tool_id: str

class PipelineEdge(BaseModel):
    from_node: str
    to_node: str

class Pipeline(BaseModel):
    id: str
    name: str
    description: Optional[str]
    nodes: List[PipelineNode]
    edges: List[PipelineEdge]
    entry_nodes: List[str]
    output_nodes: List[str]
    metadata: Optional[Dict] = None

class ToolMetadata(BaseModel):
    plugin_id: str
    tool_id: str
    input_types: List[str]
    output_types: List[str]
    capabilities: List[str]

class PipelineValidationResult(BaseModel):
    valid: bool
    errors: List[str] = []

class PipelineExecutionResult(BaseModel):
    status: str  # "success" | "error"
    output: Optional[Dict] = None
    error: Optional[str] = None
    execution_time_ms: float
    node_logs: List[Dict]
```

---

## Service Layer Structure

### `services/pipeline_registry_service.py`

```python
class PipelineRegistry:
    def __init__(self, pipeline_dir: str):
        # Load all .json files
        
    def list(self) -> List[Pipeline]:
        # Return all pipelines
        
    def get(self, pipeline_id: str) -> Optional[Pipeline]:
        # Get by ID
        
    def get_info(self, pipeline_id: str) -> Dict:
        # Return metadata, not the full pipeline
```

### `services/dag_pipeline_service.py`

```python
class DAGPipelineService:
    def validate(self, pipeline: Pipeline) -> PipelineValidationResult:
        # Check structure, cycles, types
        
    async def execute(
        self,
        pipeline: Pipeline,
        initial_payload: Dict,
        plugin_manager: PluginManager
    ) -> PipelineExecutionResult:
        # Execute in topological order
```

---

## Routes Structure

### `routes/routes_pipelines.py`

```python
router = APIRouter(prefix="/pipelines", tags=["pipelines"])

@router.get("/list")
async def list_pipelines():
    """List all available pipelines."""

@router.get("/{pipeline_id}/info")
async def get_pipeline_info(pipeline_id: str):
    """Get pipeline metadata."""

@router.post("/{pipeline_id}/validate")
async def validate_pipeline(pipeline_id: str):
    """Validate a pipeline."""

@router.post("/{pipeline_id}/run")
async def run_pipeline(pipeline_id: str, request: Dict):
    """Execute a pipeline."""

@router.post("/validate")
async def validate_pipeline_spec(spec: Dict):
    """Validate arbitrary pipeline spec."""
```

---

## Test Structure

### `tests/pipelines/test_pipeline_models.py`

```python
def test_pipeline_node_creation():
    # Test PipelineNode

def test_pipeline_validation():
    # Test Pipeline model validation

def test_edge_creation():
    # Test PipelineEdge
```

### `tests/pipelines/test_dag_validation.py`

```python
def test_detects_cycles():
    # Test cycle detection

def test_validates_entry_nodes():
    # Test entry node validation

def test_validates_output_nodes():
    # Test output node validation

def test_checks_type_compatibility():
    # Test type validation
```

### `tests/pipelines/test_pipeline_execution.py`

```python
@pytest.mark.asyncio
async def test_executes_linear_pipeline():
    # Test simple pipeline

@pytest.mark.asyncio
async def test_executes_branching_pipeline():
    # Test with multiple predecessors

@pytest.mark.asyncio
async def test_merges_payloads():
    # Test payload merging logic

@pytest.mark.asyncio
async def test_returns_output_node_results():
    # Test output collection
```

---

## Key Files to Modify

### Existing Files

- `app/main.py` → Add pipeline routes
- `pyproject.toml` → Add Phase 14 dependencies (none new, mostly already there)
- `app/models.py` → May reference pipelines

### New Files (Phase 14)

- `app/models/pipeline_graph_models.py` ← CREATE
- `app/services/pipeline_registry_service.py` ← CREATE
- `app/services/dag_pipeline_service.py` ← CREATE
- `app/routes/routes_pipelines.py` ← CREATE
- `app/pipelines/*.json` ← CREATE (example pipelines)
- All test files listed above ← CREATE

---

## File Dependencies

```
main.py
├── routes_pipelines.py
│   ├── dag_pipeline_service.py
│   │   ├── pipeline_graph_models.py
│   │   └── plugin_manager
│   └── pipeline_registry_service.py
│       └── pipeline_graph_models.py
│
└── plugin_manager (existing)
```

---

## Initialization Sequence

1. **FastAPI Startup** (`app/main.py`)
   - Create `PipelineRegistry` from `server/app/pipelines/`
   - Load all `.json` files
   - Validate each pipeline
   - Log any invalid pipelines
   - Store registry in `app.state.pipelines`

2. **Routes Registration**
   - Mount `routes_pipelines.py`
   - All endpoints available at `/pipelines/*`

3. **Ready to Accept Requests**
   - `/pipelines/list`
   - `/pipelines/{id}/run`
   - `/pipelines/{id}/info`

---

## Directory Checklist

- [ ] `app/models/pipeline_graph_models.py` created
- [ ] `app/services/pipeline_registry_service.py` created
- [ ] `app/services/dag_pipeline_service.py` created
- [ ] `app/routes/routes_pipelines.py` created
- [ ] `app/pipelines/` directory created
- [ ] Example pipelines in `app/pipelines/`
- [ ] `tests/pipelines/` directory created
- [ ] All test files created
- [ ] `docs/phases/PHASE_14_*.md` files created
- [ ] `main.py` updated to register routes
- [ ] Pre-commit checks pass
- [ ] All tests pass
