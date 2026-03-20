/**
 * Integration test for "Run Job" flow - Issues #347 & #348
 *
 * This test guards against UI freeze caused by infinite render loops:
 * - Issue #347: selectedTools in useEffect deps causes infinite loop
 * - Issue #348: tools array reference instability causes interval recreation
 *
 * Focus: Verify setInterval is bounded during Run Job flow
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent, act } from "@testing-library/react";
import App from "./App";

// Mock WebSocket with contract matching UseWebSocketReturn interface
vi.mock("./hooks/useWebSocket", () => ({
  useWebSocket: vi.fn(() => ({
    // Connection state
    isConnected: true,
    isConnecting: false,
    connectionStatus: "connected" as const,
    attempt: 0,
    // Error state
    error: null,
    errorInfo: null,
    // Methods
    sendFrame: vi.fn(),
    switchPlugin: vi.fn(),
    disconnect: vi.fn(),
    reconnect: vi.fn(),
    // Results
    latestResult: null,
    stats: { framesProcessed: 0, avgProcessingTime: 0 },
  })),
}));

// Mock API client
const mockGetPlugins = vi.fn();
const mockGetPluginManifest = vi.fn();
const mockSubmitVideoUpload = vi.fn();
const mockSubmitVideoJob = vi.fn();
const mockGetJob = vi.fn();
const mockListJobs = vi.fn();

vi.mock("./api/client", () => ({
  apiClient: {
    getPlugins: () => mockGetPlugins(),
    getPluginManifest: (id: string) => mockGetPluginManifest(id),
    submitVideoUpload: (...args: unknown[]) => mockSubmitVideoUpload(...args),
    submitVideoJob: (...args: unknown[]) => mockSubmitVideoJob(...args),
    getJob: (id: string) => mockGetJob(id),
    listJobs: () => mockListJobs(),
  },
}));

// Mock JobList to expose onJobSelect callback for testing
vi.mock("./components/JobList", () => ({
  JobList: ({ onJobSelect }: { onJobSelect: (job: unknown) => void }) => (
    <div data-testid="job-list">
      <button
        data-testid="select-test-job"
        onClick={() => onJobSelect({
          job_id: "job-video-multi-123",
          status: "completed",
          job_type: "video_multi",
          results: { frames: new Array(1000).fill({ detections: [] }) },
          created_at: new Date().toISOString(),
        })}
      >
        Select Test Job
      </button>
    </div>
  ),
}));

describe("App - Run Job Flow (Issues #347, #348)", () => {
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
        description: "Detect objects in images",
        input_types: ["image", "video"],
        output_types: ["detections"],
        capabilities: ["object_detection"],
      },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();

    // Spy on setInterval to detect infinite loop
    setIntervalSpy = vi.spyOn(window, "setInterval");

    // Default mock implementations
    mockGetPlugins.mockResolvedValue([mockPlugin]);
    mockGetPluginManifest.mockResolvedValue(mockManifest);
    mockSubmitVideoUpload.mockResolvedValue({
      video_path: "video/input/test-123.mp4",
    });
    mockSubmitVideoJob.mockResolvedValue({
      job_id: "job-test-123",
    });
    // Job is already completed
    mockGetJob.mockResolvedValue({
      job_id: "job-test-123",
      status: "completed",
      results: { detections: [{ label: "person", confidence: 0.95 }] },
      created_at: new Date().toISOString(),
    });
    mockListJobs.mockResolvedValue([]);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should NOT create runaway intervals - Issue #348 guard", async () => {
    await act(async () => {
      render(<App />);
    });

    // Wait for plugins to load
    await waitFor(
      () => {
        expect(mockGetPlugins).toHaveBeenCalled();
      },
      { timeout: 3000 }
    );

    // Select a plugin to load manifest (required - fail if missing)
    const pluginSelect = screen.getByRole("combobox");
    await act(async () => {
      fireEvent.change(pluginSelect, { target: { value: "test-plugin" } });
    });

    // Wait for manifest to load
    await waitFor(
      () => {
        expect(mockGetPluginManifest).toHaveBeenCalledWith("test-plugin");
      },
      { timeout: 3000 }
    );

    // Record interval count after initial mount
    const initialCount = setIntervalSpy.mock.calls.length;
    console.log(`Intervals after mount: ${initialCount}`);

    // Navigate to video-upload view (required - fail if missing)
    // Use more specific selector to avoid matching multiple buttons
    const uploadTab = screen.getByRole("button", { name: /upload.*video|video.*upload/i });
    await act(async () => {
      fireEvent.click(uploadTab);
    });

    // Find file input (required - fail if missing)
    const fileInput = screen.getByLabelText(/select.*video|choose.*file|upload/i);
    const videoFile = new File(["test"], "test.mp4", { type: "video/mp4" });

    await act(async () => {
      fireEvent.change(fileInput, { target: { files: [videoFile] } });
    });

    // Wait for Run Job button to appear and be enabled
    await waitFor(
      () => {
        const btn = screen.getByRole("button", { name: /run job/i });
        expect(btn).not.toHaveAttribute("disabled");
      },
      { timeout: 2000 }
    );

    const runJobButton = screen.getByRole("button", { name: /run job/i });

    await act(async () => {
      fireEvent.click(runJobButton);
    });

    // Wait for async operations
    await waitFor(
      () => {
        expect(mockSubmitVideoUpload).toHaveBeenCalled();
      },
      { timeout: 3000 }
    );

    await waitFor(
      () => {
        expect(mockSubmitVideoJob).toHaveBeenCalled();
      },
      { timeout: 3000 }
    );

    // Give time for any polling to start
    await new Promise((resolve) => setTimeout(resolve, 500));

    // Count total intervals created
    const finalCount = setIntervalSpy.mock.calls.length;
    const newIntervals = finalCount - initialCount;

    console.log(`New intervals during test: ${newIntervals}`);

    // CRITICAL: Issue #348 bug would create 50+ intervals due to infinite loop
    // Fixed code should create a small number (polling intervals, etc.)
    expect(newIntervals).toBeLessThan(20);
  });

  it("UI should remain responsive after re-renders - Issue #347 guard", async () => {
    await act(async () => {
      render(<App />);
    });

    await waitFor(
      () => {
        expect(mockGetPlugins).toHaveBeenCalled();
      },
      { timeout: 3000 }
    );

    // Select plugin (required - fail if missing)
    const pluginSelect = screen.getByRole("combobox");
    await act(async () => {
      fireEvent.change(pluginSelect, { target: { value: "test-plugin" } });
    });

    await waitFor(
      () => {
        expect(mockGetPluginManifest).toHaveBeenCalled();
      },
      { timeout: 2000 }
    );

    // Click different tabs to verify UI responds (required - fail if missing)
    const tabs = ["Stream", "Upload", "Jobs"];
    for (const tabName of tabs) {
      const tab = screen.getByRole("button", { name: new RegExp(`^${tabName}$`, "i") });
      // Should not throw or timeout
      await act(async () => {
        fireEvent.click(tab);
      });

      // Small delay to allow React to process
      await new Promise((resolve) => setTimeout(resolve, 50));
    }

    // If we got here without timeout/freeze, the UI is responsive
    // (The real assertion is that we didn't timeout above)
  });

  it("interval count should stay bounded during re-renders", async () => {
    // Increase timeout due to multiple tab clicks and re-renders
    vi.setConfig({ testTimeout: 15000 });
    await act(async () => {
      render(<App />);
    });

    await waitFor(
      () => {
        expect(mockGetPlugins).toHaveBeenCalled();
      },
      { timeout: 3000 }
    );

    // Select plugin (required - fail if missing)
    const pluginSelect = screen.getByRole("combobox");
    await act(async () => {
      fireEvent.change(pluginSelect, { target: { value: "test-plugin" } });
    });

    await waitFor(
      () => {
        expect(mockGetPluginManifest).toHaveBeenCalled();
      },
      { timeout: 2000 }
    );

    // Clear count after initial mount
    setIntervalSpy.mockClear();

    // Trigger multiple re-renders by clicking around (required - fail if missing)
    const tabs = ["Stream", "Upload", "Jobs"];
    for (let i = 0; i < 3; i++) {
      for (const tabName of tabs) {
        const tab = screen.getByRole("button", { name: new RegExp(`^${tabName}$`, "i") });
        await act(async () => {
          fireEvent.click(tab);
        });
        await new Promise((resolve) => setTimeout(resolve, 50));
      }
    }

    // Check interval creation after re-renders
    const rerenderIntervals = setIntervalSpy.mock.calls.length;

    console.log(`Intervals after re-renders: ${rerenderIntervals}`);

    // Issue #347/348 bug would cause massive interval growth on re-renders
    // Fixed code should have very few new intervals
    expect(rerenderIntervals).toBeLessThan(15);
  });
});

describe("App - State smear fix (Discussion #349)", () => {
  // These tests guard against UI freeze when switching from Jobs to Video Upload
  // with a huge video_multi job still selected

  beforeEach(() => {
    vi.clearAllMocks();
    mockGetPlugins.mockResolvedValue([{
      name: "test-plugin",
      description: "Test Plugin",
      version: "1.0.0",
    }]);
    mockGetPluginManifest.mockResolvedValue({
      id: "test-plugin",
      name: "Test Plugin",
      version: "1.0.0",
      tools: [{
        id: "detect_objects",
        title: "Detect Objects",
        capabilities: ["object_detection"],
      }],
    });
    mockListJobs.mockResolvedValue([]);
    mockGetJob.mockResolvedValue({
      job_id: "job-video-multi-123",
      status: "completed",
      created_at: new Date().toISOString(),
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should clear selectedJob when switching to video-upload mode", async () => {
    // TDD: This test proves the bug - selectedJob persists when entering video-upload
    // causing ResultsPanel to render huge JSON and freeze UI

    await act(async () => {
      render(<App />);
    });

    // 1. Go to Jobs view
    const jobsTab = screen.getByRole("button", { name: /^Jobs$/i });
    await act(async () => {
      fireEvent.click(jobsTab);
    });

    // 2. Select a job (this sets selectedJob state)
    const selectJobButton = screen.getByTestId("select-test-job");
    await act(async () => {
      fireEvent.click(selectJobButton);
    });

    // 3. Verify job is shown (job_id visible in ResultsPanel)
    expect(screen.getByText(/job-video-multi-123/i)).toBeInTheDocument();

    // 4. Switch to video-upload
    const uploadVideoTab = screen.getByRole("button", { name: /upload.*video|video.*upload/i });
    await act(async () => {
      fireEvent.click(uploadVideoTab);
    });

    // 5. CRITICAL: selectedJob should be cleared
    // The job_id should NOT be visible anymore
    // FAILS before fix - job_id still shown because selectedJob not cleared
    expect(screen.queryByText(/job-video-multi-123/i)).not.toBeInTheDocument();
  });

  it("should NOT render ResultsPanel in video-upload mode", async () => {
    // TDD: ResultsPanel should be hidden in video-upload/video-stream modes
    // to prevent rendering huge JSON from old selectedJob

    await act(async () => {
      render(<App />);
    });

    // 1. Go to video-upload directly
    const uploadVideoTab = screen.getByRole("button", { name: /upload.*video|video.*upload/i });
    await act(async () => {
      fireEvent.click(uploadVideoTab);
    });

    // 2. ResultsPanel should NOT be in the DOM
    // The fix: resultsMode === "none" so ResultsPanel is not rendered at all
    const resultsPanel = screen.queryByTestId("results-panel");
    expect(resultsPanel).toBeNull();
  });
});
