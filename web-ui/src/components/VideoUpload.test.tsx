/**
 * Tests for VideoUpload component
 * v0.13.11: Redesigned UX - action buttons appear immediately after file selection
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { VideoUpload } from "./VideoUpload";

// Mock the API client
vi.mock("../api/client", () => ({
    apiClient: {
        submitVideo: vi.fn(),
        submitVideoUpload: vi.fn(),
        getVideoJobStatus: vi.fn(),
        getVideoJobResults: vi.fn(),
    },
}));

import { apiClient } from "../api/client";

// Default manifest with video tool
const defaultManifest = {
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

describe("VideoUpload", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("renders without errors when video tools available", () => {
        render(<VideoUpload pluginId="yolo" manifest={defaultManifest} />);
        expect(screen.getByText("Video Upload")).toBeInTheDocument();
    });

    it("accepts MP4 files", () => {
        render(<VideoUpload pluginId="yolo" manifest={defaultManifest} />);

        const fileInput = screen.getByLabelText(/select/i) as HTMLInputElement;
        const file = new File(["test"], "test.mp4", { type: "video/mp4" });

        fireEvent.change(fileInput, { target: { files: [file] } });

        expect(fileInput.files).toHaveLength(1);
        expect(fileInput.files?.[0]).toBe(file);
    });

    it("rejects non-MP4 files", () => {
        render(<VideoUpload pluginId="yolo" manifest={defaultManifest} />);

        const fileInput = screen.getByLabelText(/select/i) as HTMLInputElement;
        const file = new File(["test"], "test.jpg", { type: "image/jpeg" });

        fireEvent.change(fileInput, { target: { files: [file] } });

        expect(screen.getByText(/Only MP4 videos are supported/i)).toBeInTheDocument();
    });

    // v0.13.11: New UX - action buttons appear immediately after file selection
    describe("action buttons", () => {
        it("shows Start Streaming and Run Job buttons after file selection", () => {
            render(
                <VideoUpload
                    pluginId="yolo"
                    manifest={defaultManifest}
                    onStartStreaming={vi.fn()}
                    onRunJob={vi.fn()}
                />
            );

            const fileInput = screen.getByLabelText(/select/i) as HTMLInputElement;
            const file = new File(["test"], "test.mp4", { type: "video/mp4" });

            fireEvent.change(fileInput, { target: { files: [file] } });

            expect(screen.getByText("Start Streaming")).toBeInTheDocument();
            expect(screen.getByText("Run Job")).toBeInTheDocument();
        });

        it("does not show action buttons before file selection", () => {
            render(
                <VideoUpload
                    pluginId="yolo"
                    manifest={defaultManifest}
                    onStartStreaming={vi.fn()}
                    onRunJob={vi.fn()}
                />
            );

            expect(screen.queryByText("Start Streaming")).not.toBeInTheDocument();
            expect(screen.queryByText("Run Job")).not.toBeInTheDocument();
        });

        it("disables action buttons when no plugin selected", () => {
            render(
                <VideoUpload
                    pluginId={null}
                    manifest={defaultManifest}
                    onStartStreaming={vi.fn()}
                    onRunJob={vi.fn()}
                />
            );

            const fileInput = screen.getByLabelText(/select/i) as HTMLInputElement;
            const file = new File(["test"], "test.mp4", { type: "video/mp4" });

            fireEvent.change(fileInput, { target: { files: [file] } });

            expect(screen.getByText("Start Streaming")).toBeDisabled();
            expect(screen.getByText("Run Job")).toBeDisabled();
        });

        it("disables action buttons when callback not provided", () => {
            render(<VideoUpload pluginId="yolo" manifest={defaultManifest} />);

            const fileInput = screen.getByLabelText(/select/i) as HTMLInputElement;
            const file = new File(["test"], "test.mp4", { type: "video/mp4" });

            fireEvent.change(fileInput, { target: { files: [file] } });

            expect(screen.getByText("Start Streaming")).toBeDisabled();
            expect(screen.getByText("Run Job")).toBeDisabled();
        });
    });

    // v0.13.11: Upload triggered by action buttons
    describe("upload on action", () => {
        it("uploads video when Start Streaming is clicked", async () => {
            (apiClient.submitVideoUpload as ReturnType<typeof vi.fn>).mockResolvedValue({
                video_path: "video/input/test-123.mp4",
            });

            const onVideoUploaded = vi.fn();
            const onStartStreaming = vi.fn();

            render(
                <VideoUpload
                    pluginId="yolo"
                    manifest={defaultManifest}
                    onVideoUploaded={onVideoUploaded}
                    onStartStreaming={onStartStreaming}
                />
            );

            const fileInput = screen.getByLabelText(/select/i) as HTMLInputElement;
            const file = new File(["test"], "test.mp4", { type: "video/mp4" });

            fireEvent.change(fileInput, { target: { files: [file] } });

            const startButton = screen.getByText("Start Streaming");
            fireEvent.click(startButton);

            await waitFor(() => {
                expect(apiClient.submitVideoUpload).toHaveBeenCalledWith(
                    file,
                    "yolo",
                    expect.any(Function)
                );
            });

            await waitFor(() => {
                expect(onVideoUploaded).toHaveBeenCalledWith("video/input/test-123.mp4", file);
                expect(onStartStreaming).toHaveBeenCalled();
            });
        });

        it("uploads video when Run Job is clicked", async () => {
            (apiClient.submitVideoUpload as ReturnType<typeof vi.fn>).mockResolvedValue({
                video_path: "video/input/test-123.mp4",
            });

            const onVideoUploaded = vi.fn();
            const onRunJob = vi.fn();

            render(
                <VideoUpload
                    pluginId="yolo"
                    manifest={defaultManifest}
                    onVideoUploaded={onVideoUploaded}
                    onRunJob={onRunJob}
                />
            );

            const fileInput = screen.getByLabelText(/select/i) as HTMLInputElement;
            const file = new File(["test"], "test.mp4", { type: "video/mp4" });

            fireEvent.change(fileInput, { target: { files: [file] } });

            const runButton = screen.getByText("Run Job");
            fireEvent.click(runButton);

            await waitFor(() => {
                expect(apiClient.submitVideoUpload).toHaveBeenCalledWith(
                    file,
                    "yolo",
                    expect.any(Function)
                );
            });

            await waitFor(() => {
                expect(onVideoUploaded).toHaveBeenCalledWith("video/input/test-123.mp4", file);
                expect(onRunJob).toHaveBeenCalled();
            });
        });

        it("shows upload progress during upload", async () => {
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

            render(
                <VideoUpload
                    pluginId="yolo"
                    manifest={defaultManifest}
                    onStartStreaming={onStartStreaming}
                />
            );

            const fileInput = screen.getByLabelText(/select/i) as HTMLInputElement;
            const file = new File(["test"], "test.mp4", { type: "video/mp4" });

            fireEvent.change(fileInput, { target: { files: [file] } });

            const startButton = screen.getByText("Start Streaming");
            fireEvent.click(startButton);

            // Simulate progress
            if (progressCallback) {
                progressCallback(50);
            }

            await waitFor(() => {
                expect(screen.getByText(/Uploading… 50%/i)).toBeInTheDocument();
            });
        });

        it("disables buttons during upload", async () => {
            // Create a promise that we can control
            let resolveUpload: ((value: { video_path: string }) => void) | null = null;
            (apiClient.submitVideoUpload as ReturnType<typeof vi.fn>).mockImplementation(
                () => new Promise((resolve) => {
                    resolveUpload = resolve;
                })
            );

            const onStartStreaming = vi.fn();
            const onRunJob = vi.fn();

            render(
                <VideoUpload
                    pluginId="yolo"
                    manifest={defaultManifest}
                    onStartStreaming={onStartStreaming}
                    onRunJob={onRunJob}
                />
            );

            const fileInput = screen.getByLabelText(/select/i) as HTMLInputElement;
            const file = new File(["test"], "test.mp4", { type: "video/mp4" });

            fireEvent.change(fileInput, { target: { files: [file] } });

            const startButton = screen.getByText("Start Streaming");

            // Click starts the upload
            fireEvent.click(startButton);

            // Wait for uploading state to appear (buttons are hidden during upload)
            await waitFor(() => {
                expect(screen.getByText(/Uploading/i)).toBeInTheDocument();
            });

            // Verify callbacks haven't been called yet (upload still in progress)
            expect(onStartStreaming).not.toHaveBeenCalled();

            // Resolve the upload
            if (resolveUpload) {
                resolveUpload({ video_path: "video/input/test.mp4" });
            }

            // Now callbacks should be called
            await waitFor(() => {
                expect(onStartStreaming).toHaveBeenCalled();
            });
        });

        it("displays error message on upload failure", async () => {
            (apiClient.submitVideoUpload as ReturnType<typeof vi.fn>).mockRejectedValue(
                new Error("Upload failed")
            );

            const onStartStreaming = vi.fn();

            render(
                <VideoUpload
                    pluginId="yolo"
                    manifest={defaultManifest}
                    onStartStreaming={onStartStreaming}
                />
            );

            const fileInput = screen.getByLabelText(/select/i) as HTMLInputElement;
            const file = new File(["test"], "test.mp4", { type: "video/mp4" });

            fireEvent.change(fileInput, { target: { files: [file] } });

            const startButton = screen.getByText("Start Streaming");
            fireEvent.click(startButton);

            // v0.13.11: Increased timeout for retry logic (Issue #320)
            // withRetry does 3 retries with ~1400ms total delay
            await waitFor(() => {
                expect(screen.getByText(/Upload failed/i)).toBeInTheDocument();
            }, { timeout: 3000 });

            // Should NOT call callbacks on failure
            expect(onStartStreaming).not.toHaveBeenCalled();
        });

        it("clears error when new file is selected", async () => {
            // v0.13.11: Use mockRejectedValue (not mockRejectedValueOnce) because withRetry retries
            (apiClient.submitVideoUpload as ReturnType<typeof vi.fn>).mockRejectedValue(
                new Error("Upload failed")
            );

            const onStartStreaming = vi.fn();

            render(
                <VideoUpload
                    pluginId="yolo"
                    manifest={defaultManifest}
                    onStartStreaming={onStartStreaming}
                />
            );

            const fileInput = screen.getByLabelText(/select/i) as HTMLInputElement;
            const file1 = new File(["test1"], "test1.mp4", { type: "video/mp4" });

            fireEvent.change(fileInput, { target: { files: [file1] } });

            const startButton = screen.getByText("Start Streaming");
            fireEvent.click(startButton);

            // v0.13.11: Increased timeout for retry logic (Issue #320)
            await waitFor(() => {
                expect(screen.getByText(/Upload failed/i)).toBeInTheDocument();
            }, { timeout: 3000 });

            // Select a new file
            const file2 = new File(["test2"], "test2.mp4", { type: "video/mp4" });
            fireEvent.change(fileInput, { target: { files: [file2] } });

            expect(screen.queryByText(/Upload failed/i)).not.toBeInTheDocument();
        });
    });

    // v0.9.5: Video tool filtering tests
    describe("video tool filtering", () => {
        it("shows fallback message when no video tools available", () => {
            const manifestWithoutVideoTools = {
                id: "ocr",
                name: "ocr",
                version: "1.0.0",
                tools: {
                    analyze: {
                        description: "Extract text from images",
                        input_types: ["image_bytes"],
                        output_types: ["text"],
                    },
                },
            };

            render(
                <VideoUpload
                    pluginId="ocr"
                    manifest={manifestWithoutVideoTools}
                />
            );

            expect(
                screen.getByText(/No video-compatible tools available/i)
            ).toBeInTheDocument();
        });

        it("filters tools by input_types containing 'video'", () => {
            const manifest = {
                id: "test-plugin",
                name: "test-plugin",
                version: "1.0.0",
                tools: {
                    image_tool: {
                        input_types: ["image_bytes"],
                    },
                    video_tool_1: {
                        input_types: ["video"],
                        capabilities: ["player_detection"],
                    },
                    video_tool_2: {
                        input_types: ["video", "video_frame"],
                        capabilities: ["ball_detection"],
                    },
                },
            };

            render(
                <VideoUpload
                    pluginId="test-plugin"
                    manifest={manifest}
                />
            );

            // Should NOT show fallback because video tools exist
            expect(
                screen.queryByText(/No video-compatible tools available/i)
            ).not.toBeInTheDocument();

            // Should show upload UI
            expect(screen.getByLabelText(/select/i)).toBeInTheDocument();
        });
    });

    // v0.13.11: File info display
    describe("file info display", () => {
        it("shows selected file name and size after selection", () => {
            render(<VideoUpload pluginId="yolo" manifest={defaultManifest} />);

            const fileInput = screen.getByLabelText(/select/i) as HTMLInputElement;
            const file = new File(["x".repeat(1024 * 1024)], "my-video.mp4", { type: "video/mp4" });

            fireEvent.change(fileInput, { target: { files: [file] } });

            expect(screen.getByText(/my-video.mp4/)).toBeInTheDocument();
            expect(screen.getByText(/1.00 MB/)).toBeInTheDocument();
        });
    });
});