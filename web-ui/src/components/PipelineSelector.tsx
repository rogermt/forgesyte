/**
 * Pipeline Selector component for Phase 14
 */

import { useState, useEffect } from "react";
import type { PipelineAPIClient } from "../api/pipelines";

interface PipelineSelectorProps {
  client: PipelineAPIClient;
  onPipelineSelect: (pipelineId: string) => void;
  disabled?: boolean;
  selectedPipelineId?: string;
}

export function PipelineSelector({
  client,
  onPipelineSelect,
  disabled = false,
  selectedPipelineId,
}: PipelineSelectorProps) {
  const [pipelines, setPipelines] = useState<
    Array<{ id: string; name: string }>
  >([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadPipelines() {
      if (disabled) return;
      
      setLoading(true);
      setError(null);
      try {
        const result = await client.listPipelines();
        setPipelines(result.pipelines);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load pipelines");
      } finally {
        setLoading(false);
      }
    }

    loadPipelines();
  }, [client, disabled]);

  if (disabled) {
    return (
      <select
        disabled
        className="form-select"
        style={{ opacity: 0.6 }}
        value=""
      >
        <option value="">Select a pipeline...</option>
      </select>
    );
  }

  if (loading) {
    return (
      <select disabled className="form-select">
        <option>Loading pipelines...</option>
      </select>
    );
  }

  if (error) {
    return (
      <select disabled className="form-select is-invalid">
        <option>Error: {error}</option>
      </select>
    );
  }

  if (pipelines.length === 0) {
    return (
      <select disabled className="form-select">
        <option>No pipelines available</option>
      </select>
    );
  }

  return (
    <select
      className="form-select"
      value={selectedPipelineId || ""}
      onChange={(e) => {
        const pipelineId = e.target.value;
        if (pipelineId) {
          onPipelineSelect(pipelineId);
        }
      }}
      disabled={disabled}
    >
      <option value="">Select a pipeline...</option>
      {pipelines.map((pipeline) => (
        <option key={pipeline.id} value={pipeline.id}>
          {pipeline.name}
        </option>
      ))}
    </select>
  );
}