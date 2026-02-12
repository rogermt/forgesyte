"""
Phase 14: DAG Pipeline Service

Core execution engine for DAG-based cross-plugin pipelines.
Includes observability logging for all pipeline events.
"""
import logging
import time
import uuid
from typing import Dict, Any, List

from app.pipeline_models.pipeline_graph_models import (
    Pipeline,
    PipelineValidationResult,
)

logger = logging.getLogger("pipelines.dag")


class DagPipelineService:
    """
    Executes DAG-based pipelines with observability logging.
    
    This service:
    - Validates pipeline structure (cycles, reachability)
    - Executes nodes in topological order
    - Merges outputs from predecessor nodes
    - Logs all execution events for observability
    """

    def __init__(self, registry, plugin_manager) -> None:
        """
        Initialize the DAG pipeline service.
        
        Args:
            registry: PipelineRegistryService instance
            plugin_manager: Plugin manager with get_plugin() method
        """
        self._registry = registry
        self._plugin_manager = plugin_manager

    def run_pipeline(self, pipeline_id: str, initial_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a pipeline by ID.
        
        Args:
            pipeline_id: Unique pipeline identifier
            initial_payload: Initial input data for the pipeline
            
        Returns:
            Merged output from all output nodes
            
        Raises:
            Exception: If pipeline execution fails
        """
        pipeline = self._registry.get_pipeline(pipeline_id)
        if pipeline is None:
            raise ValueError(f"Pipeline not found: {pipeline_id}")

        run_id = str(uuid.uuid4())
        started_at = time.time()

        self._log_pipeline_started(pipeline, run_id)

        try:
            # Get topological order
            order = self._topological_order(pipeline)
            
            # Execute nodes in order
            context: Dict[str, Dict[str, Any]] = {}
            
            for step_index, node_id in enumerate(order):
                node = next(n for n in pipeline.nodes if n.id == node_id)
                preds = [e.from_node for e in pipeline.edges if e.to_node == node_id]

                self._log_node_started(pipeline, run_id, node.id, node.plugin_id, node.tool_id, step_index, preds)
                node_started_at = time.time()

                # Merge predecessor outputs
                payload = self._merge_predecessor_outputs(node_id, pipeline, context, initial_payload)

                # Execute tool
                plugin = self._plugin_manager.get_plugin(node.plugin_id)
                try:
                    output = plugin.run_tool(node.tool_id, payload)
                except Exception as exc:
                    duration_ms = (time.time() - node_started_at) * 1000
                    self._log_node_failed(
                        pipeline, run_id, node.id, node.plugin_id, node.tool_id, step_index, duration_ms,
                        type(exc).__name__, str(exc)
                    )
                    raise

                duration_ms = (time.time() - node_started_at) * 1000
                context[node_id] = output or {}
                self._log_node_completed(
                    pipeline, run_id, node.id, node.plugin_id, node.tool_id, step_index, duration_ms, list((output or {}).keys())
                )

            # Merge all node outputs into final result
            # Start with initial payload, then add all node outputs in execution order
            final: Dict[str, Any] = dict(initial_payload)
            for node_id in order:
                final.update(context.get(node_id, {}))

            duration_ms = (time.time() - started_at) * 1000
            self._log_pipeline_completed(pipeline, run_id, duration_ms)
            
            return final

        except Exception as exc:
            duration_ms = (time.time() - started_at) * 1000
            self._log_pipeline_failed(
                pipeline, run_id, duration_ms,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
            raise

    def validate(self, pipeline: Pipeline) -> PipelineValidationResult:
        """
        Validate a pipeline structure.
        
        Args:
            pipeline: Pipeline to validate
            
        Returns:
            PipelineValidationResult with validation status and errors
        """
        errors = []

        # Check for cycles
        if self._has_cycle(pipeline):
            errors.append("Pipeline contains a cycle")

        # Check all entry nodes exist
        for entry in pipeline.entry_nodes:
            if not any(n.id == entry for n in pipeline.nodes):
                errors.append(f"Entry node not found: {entry}")

        # Check all output nodes exist
        for output in pipeline.output_nodes:
            if not any(n.id == output for n in pipeline.nodes):
                errors.append(f"Output node not found: {output}")

        # Check all nodes are reachable from entry nodes
        reachable = self._get_reachable_nodes(pipeline)
        for node in pipeline.nodes:
            if node.id not in reachable:
                errors.append(f"Node is unreachable: {node.id}")

        return PipelineValidationResult(valid=len(errors) == 0, errors=errors)

    def _topological_order(self, pipeline: Pipeline) -> List[str]:
        """
        Get nodes in topological order using Kahn's algorithm.
        
        Args:
            pipeline: Pipeline to sort
            
        Returns:
            List of node IDs in topological order
        """
        # Calculate in-degree for each node
        in_degree = {node.id: 0 for node in pipeline.nodes}
        for edge in pipeline.edges:
            in_degree[edge.to_node] += 1

        # Start with nodes that have no incoming edges (entry nodes)
        queue = [node_id for node_id in in_degree if in_degree[node_id] == 0]
        result = []

        while queue:
            node_id = queue.pop(0)
            result.append(node_id)

            # Reduce in-degree for neighbors
            for edge in pipeline.edges:
                if edge.from_node == node_id:
                    in_degree[edge.to_node] -= 1
                    if in_degree[edge.to_node] == 0:
                        queue.append(edge.to_node)

        return result

    def _merge_predecessor_outputs(
        self,
        node_id: str,
        pipeline: Pipeline,
        context: Dict[str, Dict[str, Any]],
        initial_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Merge initial payload with outputs of all predecessor nodes.
        
        Uses last-wins rule for key conflicts.
        
        Args:
            node_id: Current node ID
            pipeline: Pipeline definition
            context: Context with outputs from executed nodes
            initial_payload: Initial input payload
            
        Returns:
            Merged payload dictionary
        """
        merged: Dict[str, Any] = dict(initial_payload)

        # Get predecessors in edge order (topological order guarantees determinism)
        predecessors: List[str] = [
            e.from_node for e in pipeline.edges if e.to_node == node_id
        ]

        for pred_id in predecessors:
            pred_output = context.get(pred_id, {})
            if pred_output:
                merged.update(pred_output)

        return merged

    def _has_cycle(self, pipeline: Pipeline) -> bool:
        """
        Check if pipeline contains a cycle using DFS.
        
        Args:
            pipeline: Pipeline to check
            
        Returns:
            True if cycle detected, False otherwise
        """
        visited = set()
        recursion_stack = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            recursion_stack.add(node_id)

            # Visit all neighbors
            for edge in pipeline.edges:
                if edge.from_node == node_id:
                    if edge.to_node not in visited:
                        if dfs(edge.to_node):
                            return True
                    elif edge.to_node in recursion_stack:
                        return True

            recursion_stack.remove(node_id)
            return False

        # Check all nodes
        for node in pipeline.nodes:
            if node.id not in visited:
                if dfs(node.id):
                    return True

        return False

    def _get_reachable_nodes(self, pipeline: Pipeline) -> set:
        """
        Get all nodes reachable from entry nodes.
        
        Args:
            pipeline: Pipeline to analyze
            
        Returns:
            Set of reachable node IDs
        """
        reachable = set()
        to_visit = list(pipeline.entry_nodes)

        while to_visit:
            node_id = to_visit.pop()
            if node_id in reachable:
                continue

            reachable.add(node_id)

            # Add neighbors to visit
            for edge in pipeline.edges:
                if edge.from_node == node_id:
                    to_visit.append(edge.to_node)

        return reachable

    # Observability logging methods

    def _log_pipeline_started(self, pipeline: Pipeline, run_id: str) -> None:
        """Log pipeline started event."""
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

    def _log_pipeline_completed(self, pipeline: Pipeline, run_id: str, duration_ms: float) -> None:
        """Log pipeline completed event."""
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
        pipeline: Pipeline,
        run_id: str,
        duration_ms: float,
        error_type: str,
        error_message: str,
        failed_node_id: str | None = None,
    ) -> None:
        """Log pipeline failed event."""
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
        pipeline: Pipeline,
        run_id: str,
        node_id: str,
        plugin_id: str,
        tool_id: str,
        step_index: int,
        predecessor_node_ids: list[str],
    ) -> None:
        """Log node started event."""
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
        pipeline: Pipeline,
        run_id: str,
        node_id: str,
        plugin_id: str,
        tool_id: str,
        step_index: int,
        duration_ms: float,
        output_keys: list[str],
    ) -> None:
        """Log node completed event."""
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
        pipeline: Pipeline,
        run_id: str,
        node_id: str,
        plugin_id: str,
        tool_id: str,
        step_index: int,
        duration_ms: float,
        error_type: str,
        error_message: str,
    ) -> None:
        """Log node failed event."""
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