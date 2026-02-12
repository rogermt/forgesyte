"""
Phase 14: Pipeline Registry Service

Manages loading and retrieval of named pipeline definitions from JSON files.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.pipeline_models.pipeline_graph_models import Pipeline

logger = logging.getLogger("pipelines.registry")


class PipelineRegistryService:
    """
    Loads and manages named pipeline definitions from JSON files.

    Pipelines are stored as JSON files in a directory. Each file represents
    one pipeline with a unique ID. The registry loads all JSON files on
    initialization and provides methods to list, get, and get info about pipelines.
    """

    def __init__(self, pipelines_dir: str) -> None:
        """
        Initialize the registry by loading all pipeline JSON files.

        Args:
            pipelines_dir: Path to directory containing pipeline JSON files
        """
        self._pipelines_dir = Path(pipelines_dir)
        self._pipelines: Dict[str, Pipeline] = {}
        self._load_pipelines()

    def _load_pipelines(self) -> None:
        """Load all valid pipeline JSON files from the pipelines directory."""
        if not self._pipelines_dir.exists():
            logger.warning(f"Pipelines directory does not exist: {self._pipelines_dir}")
            return

        for json_file in self._pipelines_dir.glob("*.json"):
            try:
                pipeline_data = json.loads(json_file.read_text())
                pipeline = Pipeline(**pipeline_data)
                self._pipelines[pipeline.id] = pipeline
                logger.info(f"Loaded pipeline: {pipeline.id}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in {json_file.name}: {e}")
            except Exception as e:
                logger.error(f"Failed to load pipeline {json_file.name}: {e}")

    def list(self) -> List[Dict[str, str]]:
        """
        List all registered pipelines.

        Returns:
            List of pipeline metadata dictionaries with keys: id, name
        """
        return [
            {"id": pipeline.id, "name": pipeline.name}
            for pipeline in self._pipelines.values()
        ]

    def get(self, pipeline_id: str) -> Optional[Pipeline]:
        """
        Get a pipeline by ID.

        Args:
            pipeline_id: Unique pipeline identifier

        Returns:
            Pipeline object if found, None otherwise
        """
        return self._pipelines.get(pipeline_id)

    def get_pipeline(self, pipeline_id: str) -> Optional[Pipeline]:
        """
        Get a pipeline by ID (alias for get()).

        Args:
            pipeline_id: Unique pipeline identifier

        Returns:
            Pipeline object if found, None otherwise
        """
        return self.get(pipeline_id)

    def get_info(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata about a pipeline.

        Args:
            pipeline_id: Unique pipeline identifier

        Returns:
            Dictionary with pipeline metadata if found, None otherwise
        """
        pipeline = self._pipelines.get(pipeline_id)
        if pipeline is None:
            return None

        return {
            "id": pipeline.id,
            "name": pipeline.name,
            "node_count": len(pipeline.nodes),
            "edge_count": len(pipeline.edges),
            "entry_nodes": pipeline.entry_nodes,
            "output_nodes": pipeline.output_nodes,
        }
