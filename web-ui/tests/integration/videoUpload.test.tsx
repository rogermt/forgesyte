/**
 * Integration test for video upload flow
 * v0.13.11: Redesigned UX - action buttons appear immediately after file selection
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent, act } from "@testing-library/react";
import { VideoUpload } from "../../src/components/VideoUpload";

// Mock API client
vi.mock("../../src/api/client", () => ({
    apiClient: {
        submitVideo: vi.fn(),
        submitVideoUpload: vi.fn(),
        getJob: vi.fn(),
    },
}));

import { apiClient } from "../../src/api/client";

// Default manifest with video tool
const videoManifest = {
    id: "yolo",
    name: "yolo",
    version: "1.0.0",
    tools: {
        video_player_detection: {
            title: "Video Player Detection",
            description: "Run player detection on video",
            input_types: ["video"],
            output_types: ["video_detections"],
            capabilities: ["player_detection"],
        },
    },
};

describe("VideoUpload Integration", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    // v0.13.11: New UX - action buttons appear immediately
    it("should show action buttons after file selection", async () => {
        const onStartStreaming = vi.fn();
        const onRunJob = vi.fn();

        await act(async () => {
            render(
                <VideoUpload
                    pluginId="yolo"
                    manifest={videoManifest}
                    onStartStreaming={onStartStreaming}
                    onRunJob={onRunJob}
                />
            );
        });

        // No buttons before file selection
        expect(screen.queryByText("Start Streaming")).not.toBeInTheDocument();
        expect(screen.queryByText("Run Job")).not.toBeInTheDocument();

        // Select file
        const fileInput = screen.getByLabelText(/select/i) as HTMLInputElement;
        const file = new File([""], "test.mp4", { type: "video/mp4" });
        fireEvent.change(fileInput, { target: { files: [file] } });

        // Buttons appear after selection
        expect(screen.getByText("Start Streaming")).toBeInTheDocument();
        expect(screen.getByText("Run Job")).toBeInTheDocument();
    });

    it("should reject non-MP4 files", async () => {
        await act(async () => {
            render(<VideoUpload pluginId="yolo" manifest={videoManifest} />);
        });

        const fileInput = screen.getByLabelText(/select/i) as HTMLInputElement;
        const file = new File([""], "test.jpg", { type: "image/jpeg" });
        fireEvent.change(fileInput, { target: { files: [file] } });

        expect(screen.getByText(/Only MP4 videos are supported/i)).toBeInTheDocument();
    });

    // v0.13.11: Upload triggered by Start Streaming
    it("should upload video when Start Streaming is clicked", async () => {
        (apiClient.submitVideoUpload as ReturnType<typeof vi.fn>).mockResolvedValue({
            video_path: "video/input/test-123.mp4",
        });

        const onVideoUploaded = vi.fn();
        const onStartStreaming = vi.fn();

        await act(async () => {
            render(
                <VideoUpload
                    pluginId="yolo"
                    manifest={videoManifest}
                    onVideoUploaded={onVideoUploaded}
                    onStartStreaming={onStartStreaming}
                />
            );
        });

        // Select file
        const fileInput = screen.getByLabelText(/select/i) as HTMLInputElement;
        const file = new File(["video data"], "test.mp4", { type: "video/mp4" });
        fireEvent.change(fileInput, { target: { files: [file] } });

        // Click Start Streaming
        const startButton = screen.getByText("Start Streaming");
        await act(async () => {
            fireEvent.click(startButton);
        });

        // Verify upload was called
        await waitFor(() => {
            expect(apiClient.submitVideoUpload).toHaveBeenCalledWith(
                file,
                "yolo",
                expect.any(Function)
            );
        });

        // Verify callbacks were called
        await waitFor(() => {
            expect(onVideoUploaded).toHaveBeenCalledWith("video/input/test-123.mp4", file);
            expect(onStartStreaming).toHaveBeenCalled();
        });
    });

    // v0.13.11: Upload triggered by Run Job
    it("should upload video when Run Job is clicked", async () => {
        (apiClient.submitVideoUpload as ReturnType<typeof vi.fn>).mockResolvedValue({
            video_path: "video/input/test-456.mp4",
        });

        const onVideoUploaded = vi.fn();
        const onRunJob = vi.fn();

        await act(async () => {
            render(
                <VideoUpload
                    pluginId="yolo"
                    manifest={videoManifest}
                    onVideoUploaded={onVideoUploaded}
                    onRunJob={onRunJob}
                />
            );
        });

        // Select file
        const fileInput = screen.getByLabelText(/select/i) as HTMLInputElement;
        const file = new File(["video data"], "test.mp4", { type: "video/mp4" });
        fireEvent.change(fileInput, { target: { files: [file] } });

        // Click Run Job
        const runButton = screen.getByText("Run Job");
        await act(async () => {
            fireEvent.click(runButton);
        });

        // Verify upload was called
        await waitFor(() => {
            expect(apiClient.submitVideoUpload).toHaveBeenCalledWith(
                file,
                "yolo",
                expect.any(Function)
            );
        });

        // Verify callbacks were called
        await waitFor(() => {
            expect(onVideoUploaded).toHaveBeenCalledWith("video/input/test-456.mp4", file);
            expect(onRunJob).toHaveBeenCalled();
        });
    });

    it("should display upload progress during upload", async () => {
        let progressCallback: ((percent: number) => void) | null = null;

        (apiClient.submitVideoUpload as ReturnType<typeof vi.fn>).mockImplementation(
            (_file: File, _pluginId: string, onProgress?: (percent: number) => void) => {
                progressCallback = onProgress || null;
                return new Promise((resolve) => {
                    setTimeout(() => resolve({ video_path: "video/input/test.mp4" }), 100);
                });
            }
        );

        const onStartStreaming = vi.fn();

        await act(async () => {
            render(
                <VideoUpload
                    pluginId="yolo"
                    manifest={videoManifest}
                    onStartStreaming={onStartStreaming}
                />
            );
        });

        // Select file
        const fileInput = screen.getByLabelText(/select/i) as HTMLInputElement;
        const file = new File([""], "test.mp4", { type: "video/mp4" });
        fireEvent.change(fileInput, { target: { files: [file] } });

        // Click Start Streaming
        const startButton = screen.getByText("Start Streaming");
        await act(async () => {
            fireEvent.click(startButton);
        });

        // Simulate progress
        if (progressCallback) {
            progressCallback(50);
        }

        await waitFor(() => {
            expect(screen.getByText(/Uploading… 50%/i)).toBeInTheDocument();
        });
    });

    it("should handle upload failure gracefully", async () => {
        (apiClient.submitVideoUpload as ReturnType<typeof vi.fn>).mockRejectedValue(
            new Error("Upload failed: server error")
        );

        const onVideoUploaded = vi.fn();
        const onStartStreaming = vi.fn();

        await act(async () => {
            render(
                <VideoUpload
                    pluginId="yolo"
                    manifest={videoManifest}
                    onVideoUploaded={onVideoUploaded}
                    onStartStreaming={onStartStreaming}
                />
            );
        });

        // Select file
        const fileInput = screen.getByLabelText(/select/i) as HTMLInputElement;
        const file = new File([""], "test.mp4", { type: "video/mp4" });
        fireEvent.change(fileInput, { target: { files: [file] } });

        // Click Start Streaming
        const startButton = screen.getByText("Start Streaming");
        await act(async () => {
            fireEvent.click(startButton);
        });

        // v0.13.11: Increased timeout for retry logic (Issue #320)
        // withRetry does 3 retries with ~1400ms total delay
        // Verify error is shown
        await waitFor(() => {
            expect(screen.getByText(/Upload failed: server error/i)).toBeInTheDocument();
        }, { timeout: 3000 });

        // Verify callbacks were NOT called on failure
        expect(onVideoUploaded).not.toHaveBeenCalled();
        expect(onStartStreaming).not.toHaveBeenCalled();
    });

    it("should disable action buttons when no plugin selected", async () => {
        const onStartStreaming = vi.fn();
        const onRunJob = vi.fn();

        await act(async () => {
            render(
                <VideoUpload
                    pluginId={null}
                    manifest={videoManifest}
                    onStartStreaming={onStartStreaming}
                    onRunJob={onRunJob}
                />
            );
        });

        // Select file
        const fileInput = screen.getByLabelText(/select/i) as HTMLInputElement;
        const file = new File([""], "test.mp4", { type: "video/mp4" });
        fireEvent.change(fileInput, { target: { files: [file] } });

        // Buttons should be disabled
        expect(screen.getByText("Start Streaming")).toBeDisabled();
        expect(screen.getByText("Run Job")).toBeDisabled();
    });
});
