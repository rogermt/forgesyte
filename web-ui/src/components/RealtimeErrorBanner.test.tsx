import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { RealtimeErrorBanner } from "./RealtimeErrorBanner";

vi.mock("../realtime/RealtimeContext", () => {
  return {
    __esModule: true,
    useRealtimeContext: vi.fn(),
  };
});

import { useRealtimeContext } from "../realtime/RealtimeContext";

describe("RealtimeErrorBanner (Phase-17)", () => {
  it("renders nothing when there is no error", () => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      state: { lastError: null },
    });

    const { container } = render(<RealtimeErrorBanner />);
    expect(container.firstChild).toBeNull();
  });

  it("renders mapped error message", () => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      state: {
        lastError: { error: "invalid_pipeline", detail: "bad id" },
      },
      clearError: vi.fn(),
      connect: vi.fn(),
      currentPipelineId: "p1",
    });

    render(<RealtimeErrorBanner />);
    expect(
      screen.getByText("The selected pipeline is not available.")
    ).toBeInTheDocument();
  });

  it("calls clearError() and connect() on Retry", () => {
    const clearError = vi.fn();
    const connect = vi.fn();

    (useRealtimeContext as vi.Mock).mockReturnValue({
      state: {
        lastError: { error: "invalid_frame", detail: "bad jpeg" },
      },
      clearError,
      connect,
      currentPipelineId: "p1",
    });

    render(<RealtimeErrorBanner />);

    fireEvent.click(screen.getByRole("button")); // ErrorBanner dismiss button

    expect(clearError).toHaveBeenCalledTimes(1);
    expect(connect).toHaveBeenCalledWith("p1");
  });
});
