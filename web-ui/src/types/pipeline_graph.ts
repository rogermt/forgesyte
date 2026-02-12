/**
 * Pipeline graph types for Phase 14
 */

export interface PipelineNode {
  id: string;
  plugin_id: string;
  tool_id: string;
}

export interface PipelineEdge {
  from_node: string;
  to_node: string;
}

export interface Pipeline {
  id: string;
  name: string;
  nodes: PipelineNode[];
  edges: PipelineEdge[];
  entry_nodes: string[];
  output_nodes: string[];
}

export interface PipelineInfo {
  id: string;
  name: string;
  node_count: number;
  edge_count: number;
  entry_nodes: string[];
  output_nodes: string[];
}

export interface PipelineValidationResult {
  valid: boolean;
  errors: string[];
}

export interface PipelineExecutionResult {
  status: "success" | "error";
  output: Record<string, unknown>;
  error?: string;
}