/**
 * Pipeline API client for Phase 14
 */

import type {
  Pipeline,
  PipelineInfo,
  PipelineValidationResult,
  PipelineExecutionResult,
} from "../types/pipeline_graph";

const API_BASE = import.meta.env.VITE_API_URL || "/v1";

export class PipelineAPIClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  /**
   * List all registered pipelines
   */
  async listPipelines(): Promise<{ pipelines: Array<{ id: string; name: string }> }> {
    const response = await fetch(`${this.baseUrl}/pipelines/list`);
    if (!response.ok) {
      throw new Error(`Failed to list pipelines: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Get pipeline metadata
   */
  async getPipelineInfo(pipelineId: string): Promise<PipelineInfo> {
    const response = await fetch(`${this.baseUrl}/pipelines/${pipelineId}/info`);
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Pipeline not found: ${pipelineId}`);
      }
      throw new Error(`Failed to get pipeline info: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Validate a pipeline structure
   */
  async validatePipeline(pipeline: Pipeline): Promise<PipelineValidationResult> {
    const response = await fetch(`${this.baseUrl}/pipelines/validate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(pipeline),
    });
    if (!response.ok) {
      throw new Error(`Failed to validate pipeline: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Execute a pipeline
   */
  async runPipeline(
    pipelineId: string,
    payload: Record<string, unknown>
  ): Promise<PipelineExecutionResult> {
    const response = await fetch(`${this.baseUrl}/pipelines/${pipelineId}/run`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Pipeline not found: ${pipelineId}`);
      }
      throw new Error(`Failed to run pipeline: ${response.statusText}`);
    }
    return response.json();
  }
}