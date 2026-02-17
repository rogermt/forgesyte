import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, fireEvent } from "@testing-library/react";
import { PipelineSelector } from "./PipelineSelector";
import type { PipelineAPIClient } from "../api/pipelines";

// Mock RealtimeContext
vi.mock("../realtime/RealtimeContext", () => ({
  __esModule: true,
  useRealtimeContext: vi.fn(),
}));

import { useRealtimeContext } from "../realtime/RealtimeContext";

describe("PipelineSelector (Phase-17)", () => {
  let mockClient: PipelineAPIClient;
  let mockConnect: ReturnType<typeof vi.fn>;
  let mockDisconnect: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock connect and disconnect functions
    mockConnect = vi.fn();
    mockDisconnect = vi.fn();

    // Mock useRealtimeContext
    (useRealtimeContext as vi.Mock).mockReturnValue({
      connect: mockConnect,
      disconnect: mockDisconnect,
      sendFrame: vi.fn(),
      state: {
        isConnected: false,
        lastResult: null,
        droppedFrames: 0,
        slowDownWarnings: 0,
        lastError: null,
      },
    });

    // Mock PipelineAPIClient
    mockClient = {
      listPipelines: vi.fn().mockResolvedValue({
        pipelines: [
          { id: "pipeline_1", name: "Pipeline 1" },
          { id: "pipeline_2", name: "Pipeline 2" },
        ],
      }),
    } as unknown as PipelineAPIClient;
  });

  it("calls disconnect then connect with selected pipeline", async () => {
    const { findByRole } = render(
      <PipelineSelector
        client={mockClient}
        onPipelineSelect={vi.fn()}
        selectedPipelineId="pipeline_1"
      />
    );

    // Wait for pipelines to load
    const select = await findByRole("combobox");

    // Change selection to pipeline_2
    fireEvent.change(select, { target: { value: "pipeline_2" } });

    // Verify disconnect was called first
    expect(mockDisconnect).toHaveBeenCalledTimes(1);
    
    // Verify connect was called with new pipeline
    expect(mockConnect).toHaveBeenCalledTimes(1);
    expect(mockConnect).toHaveBeenCalledWith("pipeline_2");
  });

  it("loads and displays pipeline options", async () => {
    const { findByRole, getByText } = render(
      <PipelineSelector
        client={mockClient}
        onPipelineSelect={vi.fn()}
        selectedPipelineId=""
      />
    );

    // Wait for pipelines to load
    await findByRole("combobox");

    // Verify pipelines are displayed
    expect(getByText("Pipeline 1")).toBeInTheDocument();
    expect(getByText("Pipeline 2")).toBeInTheDocument();
  });

  it("handles empty selection gracefully", async () => {
    const { findByRole } = render(
      <PipelineSelector
        client={mockClient}
        onPipelineSelect={vi.fn()}
        selectedPipelineId=""
      />
    );

    const select = await findByRole("combobox");

    // Select empty option
    fireEvent.change(select, { target: { value: "" } });

    // Should not call connect or disconnect for empty selection
    expect(mockDisconnect).not.toHaveBeenCalled();
    expect(mockConnect).not.toHaveBeenCalled();
  });
});
