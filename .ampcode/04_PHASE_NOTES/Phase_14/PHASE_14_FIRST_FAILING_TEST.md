### Phase 14 — first failing test (red → green driver)

Save as: `server/app/tests/test_pipeline_dag_rest_first.py`

This assumes **no Phase 14 code exists yet** (or only skeletons). It encodes the *minimum* behavior: a named DAG pipeline, loaded from disk, executed via REST, across two plugins.

```python
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.app.main import app  # whatever your FastAPI entrypoint is


@pytest.fixture
def pipeline_dir(tmp_path: Path, monkeypatch):
    # Create a simple 2-node cross-plugin pipeline
    pipeline_data = {
        "id": "player_tracking_v1",
        "name": "Player tracking v1",
        "nodes": [
            {"id": "n1", "plugin_id": "yolo", "tool_id": "detect_players"},
            {"id": "n2", "plugin_id": "reid", "tool_id": "track_ids"},
        ],
        "edges": [
            {"from": "n1", "to": "n2"},
        ],
        "entry_nodes": ["n1"],
        "output_nodes": ["n2"],
    }
    (tmp_path / "player_tracking_v1.json").write_text(json.dumps(pipeline_data))

    # Point the registry at this temp dir (you’ll wire this in your DI)
    monkeypatch.setenv("PIPELINE_BASE_DIR", str(tmp_path))
    return tmp_path


def test_phase14_first_pipeline_runs_via_rest(pipeline_dir):
    client = TestClient(app)

    # When: we call the new DAG run endpoint
    resp = client.post(
        "/pipelines/player_tracking_v1/run",
        json={"payload": {"frame_id": 1, "image_bytes": "AAA"}},
    )

    # Then: it should succeed and return a result
    assert resp.status_code == 200
    data = resp.json()
    assert "result" in data
    # And the result should at least echo the input frame_id
    assert data["result"]["frame_id"] == 1
```

This test forces, in order:

- a pipeline registry that reads JSON from disk  
- a DAG service that can execute a 2-node pipeline  
- a REST route at `/pipelines/{id}/run`  
- wiring between FastAPI → registry → DAG service → plugins  
