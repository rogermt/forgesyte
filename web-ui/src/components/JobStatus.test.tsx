/**
 * Tests for JobStatus component with WebSocket progress streaming
 *
 * Tests WebSocket integration with HTTP polling fallback.
 */

import { vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
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
    it("shows error state from WebSocket", () => {
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

      render(<JobStatus jobId="job-123" />);
      
      expect(screen.getByText(/Processing failed/)).toBeInTheDocument();
    });
  });

  describe("video results display", () => {
    it("handles flattened video results (total_frames at top level)", async () => {
      // v0.10.0: Backend now returns {total_frames, frames} at top level
      // not wrapped in {results: {total_frames, frames}}
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
      
      // Should not throw "Cannot read properties of undefined (reading 'total_frames')"
      // VideoResultsViewer should render for video results
      await waitFor(() => {
        // Video elements don't have an implicit role, query by tag name
        const video = document.querySelector('video');
        expect(video).toBeInTheDocument();
      });
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

      // This should NOT throw
      expect(() => {
        render(<JobStatus jobId="job-123" />);
      }).not.toThrow();
    });
  });
});
