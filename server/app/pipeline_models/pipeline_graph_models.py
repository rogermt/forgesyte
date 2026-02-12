"""
Phase 14: Pipeline Graph Models

Defines core data structures for DAG-based cross-plugin pipelines:
- PipelineNode: A single tool invocation
- PipelineEdge: Data flow between nodes
- Pipeline: Complete DAG definition
- ToolMetadata: Tool capability metadata
- PipelineValidationResult: Validation output
"""
from typing import List
from pydantic import BaseModel, Field


class PipelineNode(BaseModel):
    """Represents a single tool invocation in a pipeline."""

    id: str = Field(..., description="Unique identifier for this node")
    plugin_id: str = Field(..., description="Plugin that provides the tool")
    tool_id: str = Field(..., description="Tool to execute within the plugin")


class PipelineEdge(BaseModel):
    """Represents data flow between two nodes."""

    from_node: str = Field(..., description="Source node ID")
    to_node: str = Field(..., description="Destination node ID")


class Pipeline(BaseModel):
    """Complete DAG pipeline definition."""

    id: str = Field(..., description="Unique pipeline identifier")
    name: str = Field(..., description="Human-readable pipeline name")
    nodes: List[PipelineNode] = Field(..., description="All nodes in the pipeline")
    edges: List[PipelineEdge] = Field(..., description="Data flow edges")
    entry_nodes: List[str] = Field(
        ..., description="Nodes with no predecessors (receive initial input)"
    )
    output_nodes: List[str] = Field(
        ..., description="Nodes whose output is returned to the caller"
    )


class ToolMetadata(BaseModel):
    """Metadata about a tool's capabilities and contracts."""

    plugin_id: str = Field(..., description="Plugin that provides this tool")
    tool_id: str = Field(..., description="Tool identifier")
    input_types: List[str] = Field(
        default_factory=list,
        description="Data types this tool accepts as input",
    )
    output_types: List[str] = Field(
        default_factory=list,
        description="Data types this tool produces as output",
    )
    capabilities: List[str] = Field(
        default_factory=list,
        description="High-level capabilities this tool provides",
    )


class PipelineValidationResult(BaseModel):
    """Result of pipeline validation."""

    valid: bool = Field(..., description="Whether the pipeline is valid")
    errors: List[str] = Field(
        default_factory=list,
        description="List of validation error messages",
    )