/**
 * Integration test for video upload flow
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { VideoUpload } from "../../src/components/VideoUpload";

// Mock API client
vi.mock("../../src/api/client", () => ({
    apiClient: {
        submitVideo: vi.fn(),
        getVideoJobStatus: vi.fn(),
        getVideoJobResults: vi.fn(),
    },
}));

import { apiClient } from "../../src/api/client";

describe("VideoUpload Integration", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        // Mock getVideoJobStatus to return pending status by default
        (apiClient.getVideoJobStatus as ReturnType<typeof vi.fn>).mockResolvedValue({
            job_id: "test-job-123",
            status: "pending",
            progress: 0,
            created_at: "2026-02-18T10:00:00Z",
            updated_at: "2026-02-18T10:00:00Z",
        });
        // Mock getVideoJobResults to return empty results by default
        (apiClient.getVideoJobResults as ReturnType<typeof vi.fn>).mockResolvedValue({
            job_id: "test-job-123",
            results: { text: "", detections: [] },
            created_at: "2026-02-18T10:00:00Z",
            updated_at: "2026-02-18T10:01:00Z",
        });
    });

    it("should submit video and display job ID", async () => {
        // Mock successful upload
        (apiClient.submitVideo as ReturnType<typeof vi.fn>).mockResolvedValue({
            job_id: "test-job-123",
        });

        render(<VideoUpload pluginId="yolo" selectedTools={["video_track"]} />);

        // Simulate file selection
        const fileInput = screen.getByLabelText(/upload/i) as HTMLInputElement;
        const file = new File([""], "test.mp4", { type: "video/mp4" });
        Object.defineProperty(fileInput, "files", { value: [file] });
        fileInput.dispatchEvent(new Event("change", { bubbles: true }));

        // Click upload button
        const uploadButton = screen.getByText("Upload");
        uploadButton.click();

        // Wait for job ID to appear
        await waitFor(() => {
            expect(screen.getByText(/Job ID: test-job-123/i)).toBeInTheDocument();
        });
    });

    it("should reject non-MP4 files", () => {
        render(<VideoUpload pluginId="yolo" selectedTools={["video_track"]} />);

        const fileInput = screen.getByLabelText(/upload/i) as HTMLInputElement;
        const file = new File([""], "test.jpg", { type: "image/jpeg" });
        Object.defineProperty(fileInput, "files", { value: [file] });
        fileInput.dispatchEvent(new Event("change", { bubbles: true }));

        expect(screen.getByText(/Only MP4 videos are supported/i)).toBeInTheDocument();
    });

    it("should poll job status and display results when complete", async () => {
        // Mock successful upload
        (apiClient.submitVideo as ReturnType<typeof vi.fn>).mockResolvedValue({
            job_id: "test-job-456",
        });

        // Mock job status progression
        (apiClient.getVideoJobStatus as ReturnType<typeof vi.fn>)
            .mockResolvedValueOnce({
                job_id: "test-job-456",
                status: "pending",
                progress: 0,
                created_at: "2026-02-18T10:00:00Z",
                updated_at: "2026-02-18T10:00:00Z",
            })
            .mockResolvedValueOnce({
                job_id: "test-job-456",
                status: "completed",
                progress: 100,
                created_at: "2026-02-18T10:00:00Z",
                updated_at: "2026-02-18T10:01:00Z",
            });

        // Mock job results
        (apiClient.getVideoJobResults as ReturnType<typeof vi.fn>).mockResolvedValue({
            job_id: "test-job-456",
            results: {
                text: "Test OCR text",
                detections: [],
            },
            created_at: "2026-02-18T10:00:00Z",
            updated_at: "2026-02-18T10:01:00Z",
        });

        render(<VideoUpload pluginId="yolo" selectedTools={["video_track"]} />);

        // Simulate file selection
        const fileInput = screen.getByLabelText(/upload/i) as HTMLInputElement;
        const file = new File([""], "test.mp4", { type: "video/mp4" });
        Object.defineProperty(fileInput, "files", { value: [file] });
        fileInput.dispatchEvent(new Event("change", { bubbles: true }));

        // Click upload button
        const uploadButton = screen.getByText("Upload");
        uploadButton.click();

        // Wait for job ID to appear
        await waitFor(() => {
            expect(screen.getByText(/Job ID: test-job-456/i)).toBeInTheDocument();
        });

        // Wait for status to update to completed
        await waitFor(() => {
            expect(screen.getByText(/Status: completed/i)).toBeInTheDocument();
        }, { timeout: 3000 });

        // Wait for results to appear
        await waitFor(() => {
            expect(screen.getByText(/Test OCR text/i)).toBeInTheDocument();
        }, { timeout: 3000 });
    });

    it("should handle job failure gracefully", async () => {
        // Mock successful upload
        (apiClient.submitVideo as ReturnType<typeof vi.fn>).mockResolvedValue({
            job_id: "test-job-789",
        });

        // Mock job status progression to failed
        (apiClient.getVideoJobStatus as ReturnType<typeof vi.fn>).mockResolvedValue({
            job_id: "test-job-789",
            status: "failed",
            progress: 50,
            created_at: "2026-02-18T10:00:00Z",
            updated_at: "2026-02-18T10:00:30Z",
        });

        render(<VideoUpload pluginId="yolo" selectedTools={["video_track"]} />);

        // Simulate file selection
        const fileInput = screen.getByLabelText(/upload/i) as HTMLInputElement;
        const file = new File([""], "test.mp4", { type: "video/mp4" });
        Object.defineProperty(fileInput, "files", { value: [file] });
        fileInput.dispatchEvent(new Event("change", { bubbles: true }));

        // Click upload button
        const uploadButton = screen.getByText("Upload");
        uploadButton.click();

        // Wait for job ID to appear
        await waitFor(() => {
            expect(screen.getByText(/Job ID: test-job-789/i)).toBeInTheDocument();
        });

        // Wait for error message to appear
        await waitFor(() => {
            expect(screen.getByText(/Job failed/i)).toBeInTheDocument();
        }, { timeout: 3000 });
    });

    it("should display upload progress", async () => {
        let progressCallback: ((percent: number) => void) | null = null;
        let resolveUpload: ((value: { job_id: string }) => void) | null = null;

        (apiClient.submitVideo as ReturnType<typeof vi.fn>).mockImplementation(
            (_file: File, _pluginId: string, _tool: string, onProgress?: (percent: number) => void) => {
                progressCallback = onProgress || null;
                return new Promise((resolve) => {
                    resolveUpload = resolve;
                });
            }
        );

        render(<VideoUpload pluginId="yolo" selectedTools={["video_track"]} />);

        // Simulate file selection
        const fileInput = screen.getByLabelText(/upload/i) as HTMLInputElement;
        const file = new File([""], "test.mp4", { type: "video/mp4" });
        Object.defineProperty(fileInput, "files", { value: [file] });
        fileInput.dispatchEvent(new Event("change", { bubbles: true }));

        // Click upload button
        const uploadButton = screen.getByText("Upload");
        uploadButton.click();

        // Simulate progress updates
        if (progressCallback) {
            progressCallback(25);
            progressCallback(50);
            progressCallback(75);
        }

        // Wait for progress to be displayed
        await waitFor(() => {
            expect(screen.getByText(/Uploading… 75%/i)).toBeInTheDocument();
        });

        // Complete the upload
        if (resolveUpload) {
            resolveUpload({ job_id: "test-job-999" });
        }
    });
});