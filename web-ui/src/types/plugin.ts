export interface ToolParameter {
  type: string;
  default?: any;
  description?: string;
}

export interface Tool {
  description?: string;
  inputs: Record<string, ToolParameter>;
  outputs: Record<string, ToolParameter>;
}

export interface PluginManifest {
  id: string;
  name: string;
  version: string;
  entrypoint: string;
  tools: Record<string, Tool>;
}

export interface Detection {
  x: number;
  y: number;
  width: number;
  height: number;
  confidence: number;
  class: string;
  track_id?: number;
}

export interface ToolExecutionResponse {
  success: boolean;
  result: any;
  error?: string;
}