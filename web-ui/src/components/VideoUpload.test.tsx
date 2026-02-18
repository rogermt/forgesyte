/**
 * Tests for VideoUpload component
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { VideoUpload } from "./VideoUpload";

// Mock the API client
vi.mock("../api/client", () => ({
    apiClient: {
        submitVideo: vi.fn(),
        getVideoJobStatus: vi.fn(),
        getVideoJobResults: vi.fn(),
    },
}));

import { apiClient } from "../api/client";

describe("VideoUpload", () => {
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

    it("renders without errors", () => {
        render(<VideoUpload />);
        expect(screen.getByText("Video Upload")).toBeInTheDocument();
    });

    it("accepts MP4 files", () => {
        render(<VideoUpload />);

        const fileInput = screen.getByLabelText(/upload/i) as HTMLInputElement;
        const file = new File(["test"], "test.mp4", { type: "video/mp4" });

        fireEvent.change(fileInput, { target: { files: [file] } });

        expect(fileInput.files).toHaveLength(1);
        expect(fileInput.files?.[0]).toBe(file);
    });

    it("rejects non-MP4 files", () => {
        render(<VideoUpload />);

        const fileInput = screen.getByLabelText(/upload/i) as HTMLInputElement;
        const file = new File(["test"], "test.jpg", { type: "image/jpeg" });

        fireEvent.change(fileInput, { target: { files: [file] } });

        expect(screen.getByText(/Only MP4 videos are supported/i)).toBeInTheDocument();
    });

    it("disables upload button when no file selected", () => {
        render(<VideoUpload />);

        const uploadButton = screen.getByText("Upload");
        expect(uploadButton).toBeDisabled();
    });

    it("disables upload button during upload", async () => {
        (apiClient.submitVideo as ReturnType<typeof vi.fn>).mockImplementation(
            () => new Promise(() => {}) // Never resolves
        );

        render(<VideoUpload />);

        const fileInput = screen.getByLabelText(/upload/i) as HTMLInputElement;
        const file = new File(["test"], "test.mp4", { type: "video/mp4" });

        fireEvent.change(fileInput, { target: { files: [file] } });

        const uploadButton = screen.getByText("Upload");
        fireEvent.click(uploadButton);

        await waitFor(() => {
            expect(uploadButton).toBeDisabled();
        });
    });

    it("displays upload progress", async () => {
        let progressCallback: ((percent: number) => void) | null = null;
        let resolveUpload: ((value: { job_id: string }) => void) | null = null;

        (apiClient.submitVideo as ReturnType<typeof vi.fn>).mockImplementation(
            (_file: File, _pipelineId: string, onProgress?: (percent: number) => void) => {
                progressCallback = onProgress || null;
                return new Promise((resolve) => {
                    resolveUpload = resolve;
                });
            }
        );

        render(<VideoUpload />);

        const fileInput = screen.getByLabelText(/upload/i) as HTMLInputElement;
        const file = new File(["test"], "test.mp4", { type: "video/mp4" });

        fireEvent.change(fileInput, { target: { files: [file] } });

        const uploadButton = screen.getByText("Upload");
        fireEvent.click(uploadButton);

        // Simulate progress updates before upload completes
        if (progressCallback) {
            progressCallback(50);
        }

        await waitFor(() => {
            expect(screen.getByText(/Uploading… 50%/i)).toBeInTheDocument();
        });

        // Complete the upload
        if (resolveUpload) {
            resolveUpload({ job_id: "test-job-123" });
        }
    });

    it("displays job ID after successful upload", async () => {
        (apiClient.submitVideo as ReturnType<typeof vi.fn>).mockResolvedValue({
            job_id: "test-job-123",
        });

        render(<VideoUpload />);

        const fileInput = screen.getByLabelText(/upload/i) as HTMLInputElement;
        const file = new File(["test"], "test.mp4", { type: "video/mp4" });

        fireEvent.change(fileInput, { target: { files: [file] } });

        const uploadButton = screen.getByText("Upload");
        fireEvent.click(uploadButton);

        await waitFor(() => {
            expect(screen.getByText(/Job ID: test-job-123/i)).toBeInTheDocument();
        });
    });

    it("displays error message on upload failure", async () => {
        (apiClient.submitVideo as ReturnType<typeof vi.fn>).mockRejectedValue(
            new Error("Upload failed")
        );

        render(<VideoUpload />);

        const fileInput = screen.getByLabelText(/upload/i) as HTMLInputElement;
        const file = new File(["test"], "test.mp4", { type: "video/mp4" });

        fireEvent.change(fileInput, { target: { files: [file] } });

        const uploadButton = screen.getByText("Upload");
        fireEvent.click(uploadButton);

        await waitFor(() => {
            expect(screen.getByText(/Upload failed/i)).toBeInTheDocument();
        });
    });

    it("clears error when new file is selected", async () => {
        (apiClient.submitVideo as ReturnType<typeof vi.fn>).mockRejectedValue(
            new Error("Upload failed")
        );

        render(<VideoUpload />);

        const fileInput = screen.getByLabelText(/upload/i) as HTMLInputElement;
        const file1 = new File(["test1"], "test1.mp4", { type: "video/mp4" });

        fireEvent.change(fileInput, { target: { files: [file1] } });

        const uploadButton = screen.getByText("Upload");
        fireEvent.click(uploadButton);

        await waitFor(() => {
            expect(screen.getByText(/Upload failed/i)).toBeInTheDocument();
        });

        // Select a new file
        const file2 = new File(["test2"], "test2.mp4", { type: "video/mp4" });
        fireEvent.change(fileInput, { target: { files: [file2] } });

        expect(screen.queryByText(/Upload failed/i)).not.toBeInTheDocument();
    });

    it("clears job ID when new file is selected", async () => {
        (apiClient.submitVideo as ReturnType<typeof vi.fn>).mockResolvedValue({
            job_id: "test-job-123",
        });

        render(<VideoUpload />);

        const fileInput = screen.getByLabelText(/upload/i) as HTMLInputElement;
        const file1 = new File(["test1"], "test1.mp4", { type: "video/mp4" });

        fireEvent.change(fileInput, { target: { files: [file1] } });

        const uploadButton = screen.getByText("Upload");
        fireEvent.click(uploadButton);

        await waitFor(() => {
            expect(screen.getByText(/Job ID: test-job-123/i)).toBeInTheDocument();
        });

        // Select a new file
        const file2 = new File(["test2"], "test2.mp4", { type: "video/mp4" });
        fireEvent.change(fileInput, { target: { files: [file2] } });

        expect(screen.queryByText(/Job ID: test-job-123/i)).not.toBeInTheDocument();
    });
});