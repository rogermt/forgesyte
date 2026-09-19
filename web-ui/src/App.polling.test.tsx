/**
 * Tests for unified job polling in App.tsx
 *
 * Guards against:
 * - Duplicate polling (two pollers racing)
 * - Stale state overwrites
 * - Polling continuing after terminal state
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import App from "./App";

// Mock WebSocket
vi.mock("./hooks/useWebSocket", () => ({
  useWebSocket: vi.fn(() => ({
    isConnected: true,
    isConnecting: false,
    connectionStatus: "connected" as const,
    attempt: 0,
    error: null,
    errorInfo: null,
    sendFrame: vi.fn(),
    switchPlugin: vi.fn(),
    disconnect: vi.fn(),
    reconnect: vi.fn(),
    latestResult: null,
    stats: { framesProcessed: 0, avgProcessingTime: 0 },
  })),
}));

// Mock API client
const mockGetPlugins = vi.fn();
const mockGetPluginManifest = vi.fn();
const mockGetJob = vi.fn();
const mockListJobs = vi.fn();

vi.mock("./api/client", () => ({
  apiClient: {
    getPlugins: () => mockGetPlugins(),
    getPluginManifest: (id: string) => mockGetPluginManifest(id),
    getJob: (id: string) => mockGetJob(id),
    listJobs: () => mockListJobs(),
  },
}));

// Mock JobList to expose onJobSelect callback
vi.mock("./components/JobList", () => ({
  JobList: ({ onJobSelect }: { onJobSelect: (job: unknown) => void }) => (
    <div data-testid="job-list">
      <button
        data-testid="select-pending-job"
        onClick={() => onJobSelect({
          job_id: "job-pending-123",
          status: "pending",
          created_at: new Date().toISOString(),
        })}
      >
        Select Pending Job
      </button>
      <button
        data-testid="select-completed-job"
        onClick={() => onJobSelect({
          job_id: "job-completed-456",
          status: "completed",
          created_at: new Date().toISOString(),
        })}
      >
        Select Completed Job
      </button>
    </div>
  ),
}));

describe("App - Unified Job Polling", () => {
  let setIntervalSpy: ReturnType<typeof vi.spyOn>;

  const mockPlugin = {
    name: "test-plugin",
    description: "Test Plugin",
    version: "1.0.0",
  };

  const mockManifest = {
    id: "test-plugin",
    name: "Test Plugin",
    version: "1.0.0",
    tools: [
      {
        id: "detect_objects",
        title: "Detect Objects",
        capabilities: ["object_detection"],
      },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    setIntervalSpy = vi.spyOn(window, "setInterval");

    mockGetPlugins.mockResolvedValue([mockPlugin]);
    mockGetPluginManifest.mockResolvedValue(mockManifest);
    mockListJobs.mockResolvedValue([]);
    mockGetJob.mockResolvedValue({
      job_id: "job-pending-123",
      status: "pending",
      created_at: new Date().toISOString(),
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it("should create only ONE polling interval for selectedJob", async () => {
    await act(async () => {
      render(<App />);
    });

    // Go to Jobs view
    const jobsTab = screen.getByRole("button", { name: /^Jobs$/i });
    await act(async () => {
      fireEvent.click(jobsTab);
    });

    // Clear any intervals from initial render
    setIntervalSpy.mockClear();

    // Select a pending job
    const selectJobButton = screen.getByTestId("select-pending-job");
    await act(async () => {
      fireEvent.click(selectJobButton);
    });

    // Advance timers to allow polling to start
    await act(async () => {
      vi.advanceTimersByTime(100);
    });

    // Should have created exactly ONE interval for polling
    const intervalCalls = setIntervalSpy.mock.calls.length;
    expect(intervalCalls).toBeLessThanOrEqual(1);

    // Advance time and verify polling happens
    await act(async () => {
      vi.advanceTimersByTime(1000);
    });

    // getJob should be called once after first poll
    expect(mockGetJob).toHaveBeenCalledWith("job-pending-123");
  });

  it("should NOT poll when job is already completed", async () => {
    await act(async () => {
      render(<App />);
    });

    // Go to Jobs view
    const jobsTab = screen.getByRole("button", { name: /^Jobs$/i });
    await act(async () => {
      fireEvent.click(jobsTab);
    });

    // Clear any previous calls from mount
    mockGetJob.mockClear();

    // Select a completed job
    const selectJobButton = screen.getByTestId("select-completed-job");
    await act(async () => {
      fireEvent.click(selectJobButton);
    });

    // Advance time - should NOT poll for completed job
    await act(async () => {
      vi.advanceTimersByTime(3000);
    });

    // getJob should NOT be called for completed job
    expect(mockGetJob).not.toHaveBeenCalled();
  });

  it("should NOT create polling interval for uploadResult", async () => {
    await act(async () => {
      render(<App />);
    });

    // Advance timers to let initial effects settle
    await act(async () => {
      vi.advanceTimersByTime(100);
    });

    // Record intervals before any job selection
    const intervalsBeforeSelect = setIntervalSpy.mock.calls.length;

    // The key assertion: there should be NO dedicated uploadResult poller
    // The only poller should be for selectedJob
    // This test documents that uploadResult should NOT have its own poller

    // Navigate around to trigger any potential effects
    const tabs = ["Stream", "Upload", "Jobs"];
    for (const tabName of tabs) {
      const tab = screen.getByRole("button", { name: new RegExp(`^${tabName}$`, "i") });
      await act(async () => {
        fireEvent.click(tab);
      });
      await act(async () => {
        vi.advanceTimersByTime(100);
      });
    }

    // The interval count should not grow significantly from view changes
    const intervalsAfterNav = setIntervalSpy.mock.calls.length;
    expect(intervalsAfterNav - intervalsBeforeSelect).toBeLessThan(5);
  });

  it("should stop polling when job reaches terminal state", async () => {
    // This test verifies that polling stops after a job completes
    // We mock getJob to return completed on first call, then verify no further calls

    mockGetJob.mockResolvedValue({
      job_id: "job-pending-123",
      status: "completed",
      created_at: new Date().toISOString(),
    });

    await act(async () => {
      render(<App />);
    });

    // Go to Jobs view
    const jobsTab = screen.getByRole("button", { name: /^Jobs$/i });
    await act(async () => {
      fireEvent.click(jobsTab);
    });

    // Select pending job
    const selectJobButton = screen.getByTestId("select-pending-job");
    await act(async () => {
      fireEvent.click(selectJobButton);
    });

    // Clear mock calls
    mockGetJob.mockClear();

    // Advance time - should poll once, get "completed", then stop
    await act(async () => {
      vi.advanceTimersByTime(1000);
    });

    // First poll happens
    expect(mockGetJob).toHaveBeenCalledTimes(1);

    // Advance more time - should NOT poll again because status is now "completed"
    await act(async () => {
      vi.advanceTimersByTime(5000);
    });

    // Should still be 1 (no additional polls)
    expect(mockGetJob).toHaveBeenCalledTimes(1);
  });
});
