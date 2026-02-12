"""
Phase 14: Type Validator

Validates type compatibility between pipeline nodes using intersection-based matching.
"""
from typing import Dict, List

from app.pipeline_models.pipeline_graph_models import (
    Pipeline,
    ToolMetadata,
)


class TypeValidator:
    """
    Validates type compatibility between connected pipeline nodes.
    
    Uses intersection-based matching: an edge is valid if the output types
    of the source node intersect with the input types of the destination node.
    """

    def validate_types(
        self, pipeline: Pipeline, tools: Dict[str, ToolMetadata]
    ) -> List[str]:
        """
        Validate type compatibility for all edges in a pipeline.
        
        Args:
            pipeline: Pipeline to validate
            tools: Dictionary mapping node IDs to ToolMetadata
            
        Returns:
            List of error messages (empty if all edges are compatible)
        """
        errors = []

        for edge in pipeline.edges:
            from_node = next((n for n in pipeline.nodes if n.id == edge.from_node), None)
            to_node = next((n for n in pipeline.nodes if n.id == edge.to_node), None)

            if from_node is None or to_node is None:
                continue

            from_metadata = tools.get(edge.from_node)
            to_metadata = tools.get(edge.to_node)

            if from_metadata is None or to_metadata is None:
                continue

            # Check type compatibility using intersection
            if not self._types_compatible(from_metadata, to_metadata):
                errors.append(
                    f"Type mismatch: {edge.from_node} (outputs: {from_metadata.output_types}) "
                    f"→ {edge.to_node} (inputs: {to_metadata.input_types})"
                )

        return errors

    def _types_compatible(
        self, from_metadata: ToolMetadata, to_metadata: ToolMetadata
    ) -> bool:
        """
        Check if two tools have compatible types.
        
        Args:
            from_metadata: Tool metadata for source node
            to_metadata: Tool metadata for destination node
            
        Returns:
            True if types are compatible (intersection non-empty), False otherwise
        """
        # If either has empty types, no validation (backward compatibility)
        if not from_metadata.output_types or not to_metadata.input_types:
            return True

        # Check intersection
        intersection = set(from_metadata.output_types) & set(to_metadata.input_types)
        return len(intersection) > 0