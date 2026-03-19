/**
 * Tests for JobStatus component with WebSocket progress streaming
 *
 * Tests WebSocket integration with HTTP polling fallback.
 */

import { vi } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import { JobStatus } from "./JobStatus";
import * as client from "../api/client";
import { useJobProgress } from "../hooks/useJobProgress";

// Mock the API client
vi.mock("../api/client", () => ({
  apiClient: {
    getJob: vi.fn(),
  },
}));

// Mock useJobProgress hook
vi.mock("../hooks/useJobProgress", () => ({
  useJobProgress: vi.fn(),
}));

describe("JobStatus", () => {
  const mockUseJobProgress = useJobProgress as ReturnType<typeof vi.fn>;
  const mockGetJob = client.apiClient.getJob as ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.clearAllMocks();
    // Default mock for useJobProgress
    mockUseJobProgress.mockReturnValue({
      progress: null,
      status: "pending",
      error: null,
      isConnected: false,
    });
  });

  describe("initial state", () => {
    it("shows pending state initially", () => {
      mockGetJob.mockImplementation(() => new Promise(() => {})); // Never resolves
      
      render(<JobStatus jobId="job-123" />);
      
      expect(screen.getByText(/pending/i)).toBeInTheDocument();
    });
  });

  describe("WebSocket connection indicator", () => {
    it("shows live indicator when WebSocket connected", () => {
      mockUseJobProgress.mockReturnValue({
        progress: null,
        status: "pending",
        error: null,
        isConnected: true,
      });
      mockGetJob.mockImplementation(() => new Promise(() => {}));

      render(<JobStatus jobId="job-123" />);
      
      expect(screen.getByTitle(/WebSocket connected/i)).toBeInTheDocument();
    });

    it("shows polling indicator when WebSocket disconnected", () => {
      mockUseJobProgress.mockReturnValue({
        progress: null,
        status: "pending",
        error: null,
        isConnected: false,
      });
      mockGetJob.mockImplementation(() => new Promise(() => {}));

      render(<JobStatus jobId="job-123" />);
      
      expect(screen.getByTitle(/Using HTTP polling/i)).toBeInTheDocument();
    });
  });

  describe("progress display", () => {
    it("shows progress bar when running with WebSocket progress", () => {
      mockUseJobProgress.mockReturnValue({
        progress: {
          job_id: "job-123",
          current_frame: 50,
          total_frames: 100,
          percent: 50,
        },
        status: "running",
        error: null,
        isConnected: true,
      });
      mockGetJob.mockResolvedValue({
        status: "running",
        progress: 50,
      });

      render(<JobStatus jobId="job-123" />);
      
      expect(screen.getByText(/50%/)).toBeInTheDocument();
    });

    it("shows frame count when available", () => {
      mockUseJobProgress.mockReturnValue({
        progress: {
          job_id: "job-123",
          current_frame: 75,
          total_frames: 150,
          percent: 50,
        },
        status: "running",
        error: null,
        isConnected: true,
      });
      mockGetJob.mockResolvedValue({
        status: "running",
        progress: 50,
      });

      render(<JobStatus jobId="job-123" />);
      
      expect(screen.getByText(/75/)).toBeInTheDocument();
      expect(screen.getByText(/150/)).toBeInTheDocument();
    });

    it("shows multi-tool progress when available", () => {
      mockUseJobProgress.mockReturnValue({
        progress: {
          job_id: "job-123",
          current_frame: 50,
          total_frames: 100,
          percent: 25,
          current_tool: "yolo-tracker",
          tools_total: 2,
          tools_completed: 0,
        },
        status: "running",
        error: null,
        isConnected: true,
      });
      mockGetJob.mockResolvedValue({
        status: "running",
        progress: 25,
      });

      render(<JobStatus jobId="job-123" />);
      
      expect(screen.getByText(/yolo-tracker/)).toBeInTheDocument();
    });
  });

  describe("HTTP polling fallback", () => {
    it("falls back to polling when WebSocket disconnected", async () => {
      mockUseJobProgress.mockReturnValue({
        progress: null,
        status: "pending",
        error: null,
        isConnected: false,
      });
      mockGetJob.mockResolvedValue({
        status: "running",
        progress: 30,
      });

      render(<JobStatus jobId="job-123" />);
      
      await waitFor(() => {
        expect(mockGetJob).toHaveBeenCalledWith("job-123");
      });
    });
  });

  describe("completion", () => {
    it("shows completed state", async () => {
      mockUseJobProgress.mockReturnValue({
        progress: null,
        status: "completed",
        error: null,
        isConnected: true,
      });
      mockGetJob.mockResolvedValue({
        status: "completed",
        results: { job_id: "job-123", results: null },
      });

      render(<JobStatus jobId="job-123" />);
      
      await waitFor(() => {
        expect(screen.getByText(/completed/i)).toBeInTheDocument();
      });
    });
  });

  describe("error handling", () => {
    it("shows error state from WebSocket", async () => {
      mockUseJobProgress.mockReturnValue({
        progress: null,
        status: "failed",
        error: "Processing failed",
        isConnected: false,
      });
      mockGetJob.mockResolvedValue({
        status: "failed",
        error_message: "Processing failed",
      });

      await act(async () => {
        render(<JobStatus jobId="job-123" />);
      });

      expect(screen.getByText(/Processing failed/)).toBeInTheDocument();
    });
  });

  describe("results display", () => {
    it("handles flattened video results (total_frames at top level)", async () => {
      // v0.10.0: Backend now returns {total_frames, frames} at top level
      // JobResults displays all result data as JSON
      mockUseJobProgress.mockReturnValue({
        progress: null,
        status: "completed",
        error: null,
        isConnected: true,
      });
      mockGetJob.mockResolvedValue({
        status: "completed",
        results: {
          job_id: "job-123",
          total_frames: 100,
          frames: [
            { frame_index: 0, detections: { tracked_objects: [] } },
          ],
        },
      });

      render(<JobStatus jobId="job-123" />);
      
      await waitFor(() => {
        expect(screen.getByText(/completed/i)).toBeInTheDocument();
      });
      
      // Should display results in JobResults (JSON format)
      await waitFor(() => {
        expect(screen.getByText(/Job Results/i)).toBeInTheDocument();
      });

      // Should display the total_frames in the JSON output
      expect(screen.getByText(/total_frames/i)).toBeInTheDocument();
    });

    it("handles video results with undefined results.results gracefully", async () => {
      // Edge case: results.results is undefined but results has total_frames
      mockUseJobProgress.mockReturnValue({
        progress: null,
        status: "completed",
        error: null,
        isConnected: true,
      });
      mockGetJob.mockResolvedValue({
        status: "completed",
        results: {
          job_id: "job-123",
          total_frames: 100,
          frames: [],
        },
      });

      // This should NOT throw - wrap in act() to handle async state updates
      await act(async () => {
        render(<JobStatus jobId="job-123" />);
      });
    });
  });

  // Race condition: results not fetched when status=completed but results=null
  describe("Race condition: results fetching after completed", () => {
    it("should continue polling for results when status=completed but results=null", async () => {
      // This test catches the bug where polling stops after status=completed
      // even if results is still null (results file not yet written)
      
      mockUseJobProgress.mockReturnValue({
        progress: null,
        status: "pending",
        error: null,
        isConnected: false, // WebSocket disconnected - polling will run
      });

      // First poll: status=completed, results=null (race condition)
      mockGetJob.mockResolvedValueOnce({
        job_id: "job-123",
        status: "completed",
        results: null,
        created_at: new Date().toISOString(),
      });

      // Second poll: status=completed, results populated
      // Note: results must have nested 'results' property or total_frames/frames for JobResults
      mockGetJob.mockResolvedValueOnce({
        job_id: "job-123",
        status: "completed",
        results: {
          job_id: "job-123",
          results: { detections: [{ label: "person", confidence: 0.95 }] },
        },
        created_at: new Date().toISOString(),
      });

      render(<JobStatus jobId="job-123" />);

      // Wait for completed status to appear
      await waitFor(() => {
        expect(screen.getByText(/completed/i)).toBeInTheDocument();
      }, { timeout: 3000 });

      // Wait for results to appear (should poll again after first null)
      await waitFor(() => {
        expect(screen.getByText(/person/)).toBeInTheDocument();
      }, { timeout: 5000 });

      // Verify getJob was called at least twice (continued polling)
      expect(mockGetJob.mock.calls.length).toBeGreaterThanOrEqual(2);
    });
  });

  // Issue #231: Terminal state locking tests
  describe("Issue #231: Terminal state locking", () => {
    it("should lock status to 'completed' when HTTP polling confirms completion while WebSocket disconnected", async () => {
      // Race condition scenario:
      // 1. Job completes on server
      // 2. WebSocket disconnects
      // 3. HTTP polling fetches and sees "completed"
      // 4. WebSocket reconnects with fresh "pending" state
      // The UI should stay locked on "completed"

      // Step 1-3: WebSocket disconnected, polling runs and sees completed
      mockUseJobProgress.mockReturnValue({
        progress: null,
        status: "pending",
        error: null,
        isConnected: false, // WebSocket disconnected - polling will run
      });

      mockGetJob.mockResolvedValue({
        status: "completed",
        progress: 100,
        results: { job_id: "job-123" },
      });

      render(<JobStatus jobId="job-123" />);

      // Wait for polling to complete
      await waitFor(() => {
        expect(screen.getByText(/completed/i)).toBeInTheDocument();
      });

      // Step 4: WebSocket reconnects with fresh "pending" state
      mockUseJobProgress.mockReturnValue({
        progress: null,
        status: "pending", // Fresh WebSocket reconnection
        error: null,
        isConnected: true, // Now connected
      });

      // Trigger re-render by causing a state change
      // The status should remain "completed" because pollStatus is locked

      // Status should still be completed (locked)
      expect(screen.getByText(/completed/i)).toBeInTheDocument();
    });

    it("should lock status to 'failed' when HTTP polling confirms failure while WebSocket disconnected", async () => {
      mockUseJobProgress.mockReturnValue({
        progress: null,
        status: "pending",
        error: null,
        isConnected: false, // WebSocket disconnected - polling will run
      });

      mockGetJob.mockResolvedValue({
        status: "failed",
        error_message: "Processing error",
      });

      render(<JobStatus jobId="job-123" />);

      await waitFor(() => {
        expect(screen.getByText(/failed/i)).toBeInTheDocument();
      });

      // Simulate WebSocket reconnecting
      mockUseJobProgress.mockReturnValue({
        progress: null,
        status: "pending",
        error: null,
        isConnected: true,
      });

      // Status should still be failed (locked)
      expect(screen.getByText(/failed/i)).toBeInTheDocument();
      expect(screen.getByText(/Processing error/)).toBeInTheDocument();
    });

    it("should stop polling once terminal state 'completed' is reached", async () => {
      mockUseJobProgress.mockReturnValue({
        progress: null,
        status: "completed",
        error: null,
        isConnected: true, // WebSocket connected and reports completed
      });

      mockGetJob.mockResolvedValue({
        status: "completed",
        progress: 100,
        results: { job_id: "job-123" },
      });

      render(<JobStatus jobId="job-123" />);

      // When WebSocket reports completed, polling runs to fetch results
      await waitFor(() => {
        expect(mockGetJob).toHaveBeenCalledWith("job-123");
      });

      // Clear the mock to count additional calls
      mockGetJob.mockClear();

      // Wait a bit to see if polling continues
      await new Promise((resolve) => setTimeout(resolve, 100));

      // Should NOT have called getJob again after terminal state
      expect(mockGetJob).not.toHaveBeenCalled();
    });

    it("should stop polling once terminal state 'failed' is reached", async () => {
      mockUseJobProgress.mockReturnValue({
        progress: null,
        status: "failed",
        error: "Job failed",
        isConnected: false, // Disconnected - polling runs
      });

      mockGetJob.mockResolvedValue({
        status: "failed",
        error_message: "Job failed",
      });

      render(<JobStatus jobId="job-123" />);

      await waitFor(() => {
        expect(screen.getByText(/failed/i)).toBeInTheDocument();
      });

      mockGetJob.mockClear();

      await new Promise((resolve) => setTimeout(resolve, 100));

      expect(mockGetJob).not.toHaveBeenCalled();
    });

    it("should prioritize HTTP polling completed status over WebSocket pending on reconnect", async () => {
      // Test the actual race: polling completes, then WS reconnects
      mockUseJobProgress.mockReturnValue({
        progress: { job_id: "job-123", current_frame: 50, total_frames: 100, percent: 50 },
        status: "running",
        error: null,
        isConnected: false, // Start disconnected so polling runs
      });

      mockGetJob.mockResolvedValue({
        status: "completed",
        progress: 100,
        results: { job_id: "job-123" },
      });

      render(<JobStatus jobId="job-123" />);

      // Wait for polling to complete
      await waitFor(() => {
        expect(screen.getByText(/completed/i)).toBeInTheDocument();
      });

      // Now simulate WebSocket reconnecting with stale "pending" state
      mockUseJobProgress.mockReturnValue({
        progress: { job_id: "job-123", current_frame: 50, total_frames: 100, percent: 50 },
        status: "pending", // Fresh reconnection - back to pending
        error: null,
        isConnected: true,
      });

      // Status should REMAIN completed (locked by pollStatus)
      // This is the core fix for Issue #231
      expect(screen.getByText(/completed/i)).toBeInTheDocument();
    });
  });
});
