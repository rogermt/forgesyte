/**
 * Tests for VideoUpload component
 *
 * Issue #366: Video Upload Re-use feature
 */

import { vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { VideoUpload } from "./VideoUpload";
import * as client from "../api/client";
import type { PluginManifest } from "../types/plugin";

// Mock the API client
vi.mock("../api/client", () => ({
    apiClient: {
        submitVideoUpload: vi.fn(),
    },
}));

// Mock resolveVideoTools
vi.mock("../utils/resolveVideoTools", () => ({
    resolveVideoTools: vi.fn((tools: string[]) => tools),
}));

// Create a mock MP4 file
function createMockFile(name: string = "test.mp4", size: number = 1024 * 1024): File {
    const file = new File(["x".repeat(size)], name, { type: "video/mp4" });
    return file;
}

// Create mock manifest with video tools
function createMockManifest(): PluginManifest {
    return {
        id: "test-plugin",
        name: "Test Plugin",
        version: "1.0.0",
        tools: [
            {
                id: "video-tool",
                title: "Video Tool",
                input_types: ["video"],
                input_schema: {},
                output_schema: {},
            },
        ],
    };
}

describe("VideoUpload", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe("basic rendering", () => {
        it("should render file input", () => {
            render(
                <VideoUpload
                    pluginId="test-plugin"
                    manifest={createMockManifest()}
                />
            );
            expect(screen.getByLabelText(/select video/i)).toBeInTheDocument();
        });

        it("should show no video tools message when manifest has no video tools", () => {
            const manifest: PluginManifest = {
                id: "test-plugin",
                name: "Test Plugin",
                version: "1.0.0",
                tools: [
                    {
                        id: "image-tool",
                        title: "Image Tool",
                        input_types: ["image"],
                        input_schema: {},
                        output_schema: {},
                    },
                ],
            };
            render(
                <VideoUpload
                    pluginId="test-plugin"
                    manifest={manifest}
                />
            );
            expect(screen.getByText(/no video-compatible tools/i)).toBeInTheDocument();
        });
    });

    describe("file selection", () => {
        it("should show file info when MP4 is selected", async () => {
            render(
                <VideoUpload
                    pluginId="test-plugin"
                    manifest={createMockManifest()}
                />
            );

            const input = screen.getByLabelText(/select video/i) as HTMLInputElement;
            const file = createMockFile("video.mp4", 5 * 1024 * 1024); // 5 MB

            fireEvent.change(input, { target: { files: [file] } });

            await waitFor(() => {
                expect(screen.getByText(/video.mp4/)).toBeInTheDocument();
                expect(screen.getByText(/5.00 MB/)).toBeInTheDocument();
            });
        });

        it("should show error for non-MP4 files", async () => {
            render(
                <VideoUpload
                    pluginId="test-plugin"
                    manifest={createMockManifest()}
                />
            );

            const input = screen.getByLabelText(/select video/i) as HTMLInputElement;
            const file = new File(["x"], "video.avi", { type: "video/avi" });

            fireEvent.change(input, { target: { files: [file] } });

            await waitFor(() => {
                expect(screen.getByText(/only mp4 videos are supported/i)).toBeInTheDocument();
            });
        });
    });

    describe("Issue #366: Video Upload Re-use", () => {
        it("should upload video on first Run Job click", async () => {
            const mockOnRunJob = vi.fn();
            (client.apiClient.submitVideoUpload as ReturnType<typeof vi.fn>).mockResolvedValue({
                video_path: "video/input/test-123.mp4",
            });

            render(
                <VideoUpload
                    pluginId="test-plugin"
                    manifest={createMockManifest()}
                    selectedTools={["video-tool"]}
                    onRunJob={mockOnRunJob}
                />
            );

            // Select file
            const input = screen.getByLabelText(/select video/i) as HTMLInputElement;
            const file = createMockFile("video.mp4");
            fireEvent.change(input, { target: { files: [file] } });

            // Click Run Job
            await waitFor(() => {
                expect(screen.getByText("Run Job")).toBeInTheDocument();
            });
            fireEvent.click(screen.getByText("Run Job"));

            await waitFor(() => {
                // Should have called upload
                expect(client.apiClient.submitVideoUpload).toHaveBeenCalledTimes(1);
                // Should call onRunJob with video_path
                expect(mockOnRunJob).toHaveBeenCalledWith(
                    "video/input/test-123.mp4",
                    file,
                    ["video-tool"]
                );
            });
        });

        it("should SKIP upload on second Run Job click (re-use videoPath)", async () => {
            const mockOnRunJob = vi.fn();
            (client.apiClient.submitVideoUpload as ReturnType<typeof vi.fn>).mockResolvedValue({
                video_path: "video/input/test-123.mp4",
            });

            render(
                <VideoUpload
                    pluginId="test-plugin"
                    manifest={createMockManifest()}
                    selectedTools={["video-tool"]}
                    onRunJob={mockOnRunJob}
                />
            );

            // Select file
            const input = screen.getByLabelText(/select video/i) as HTMLInputElement;
            const file = createMockFile("video.mp4");
            fireEvent.change(input, { target: { files: [file] } });

            // First Run Job - should upload
            await waitFor(() => {
                expect(screen.getByText("Run Job")).toBeInTheDocument();
            });
            fireEvent.click(screen.getByText("Run Job"));

            await waitFor(() => {
                expect(client.apiClient.submitVideoUpload).toHaveBeenCalledTimes(1);
                expect(mockOnRunJob).toHaveBeenCalledTimes(1);
            });

            // Clear mock for second call check
            (client.apiClient.submitVideoUpload as ReturnType<typeof vi.fn>).mockClear();
            mockOnRunJob.mockClear();

            // Second Run Job - should SKIP upload
            fireEvent.click(screen.getByText("Run Job"));

            await waitFor(() => {
                // Should NOT upload again
                expect(client.apiClient.submitVideoUpload).not.toHaveBeenCalled();
                // Should still call onRunJob with same video_path
                expect(mockOnRunJob).toHaveBeenCalledWith(
                    "video/input/test-123.mp4",
                    file,
                    ["video-tool"]
                );
            });
        });

        it("should clear videoPath when different file is selected", async () => {
            const mockOnRunJob = vi.fn();
            (client.apiClient.submitVideoUpload as ReturnType<typeof vi.fn>)
                .mockResolvedValueOnce({ video_path: "video/input/first.mp4" })
                .mockResolvedValueOnce({ video_path: "video/input/second.mp4" });

            render(
                <VideoUpload
                    pluginId="test-plugin"
                    manifest={createMockManifest()}
                    selectedTools={["video-tool"]}
                    onRunJob={mockOnRunJob}
                />
            );

            // Select first file
            const input = screen.getByLabelText(/select video/i) as HTMLInputElement;
            const file1 = createMockFile("first.mp4");
            fireEvent.change(input, { target: { files: [file1] } });

            // Run Job for first file
            await waitFor(() => {
                expect(screen.getByText("Run Job")).toBeInTheDocument();
            });
            fireEvent.click(screen.getByText("Run Job"));

            await waitFor(() => {
                expect(client.apiClient.submitVideoUpload).toHaveBeenCalledTimes(1);
            });

            // Select different file
            const file2 = createMockFile("second.mp4");
            fireEvent.change(input, { target: { files: [file2] } });

            // Run Job for second file - should upload again
            await waitFor(() => {
                expect(screen.getByText(/second.mp4/)).toBeInTheDocument();
            });
            fireEvent.click(screen.getByText("Run Job"));

            await waitFor(() => {
                // Should upload again because file changed
                expect(client.apiClient.submitVideoUpload).toHaveBeenCalledTimes(2);
                expect(mockOnRunJob).toHaveBeenLastCalledWith(
                    "video/input/second.mp4",
                    file2,
                    ["video-tool"]
                );
            });
        });

        it("should show 'Video uploaded' status after successful upload", async () => {
            const mockOnRunJob = vi.fn();
            (client.apiClient.submitVideoUpload as ReturnType<typeof vi.fn>).mockResolvedValue({
                video_path: "video/input/test-123.mp4",
            });

            render(
                <VideoUpload
                    pluginId="test-plugin"
                    manifest={createMockManifest()}
                    selectedTools={["video-tool"]}
                    onRunJob={mockOnRunJob}
                />
            );

            // Select file and run job
            const input = screen.getByLabelText(/select video/i) as HTMLInputElement;
            const file = createMockFile("video.mp4");
            fireEvent.change(input, { target: { files: [file] } });

            await waitFor(() => {
                expect(screen.getByText("Run Job")).toBeInTheDocument();
            });
            fireEvent.click(screen.getByText("Run Job"));

            await waitFor(() => {
                expect(screen.getByText(/video uploaded/i)).toBeInTheDocument();
            });
        });
    });
});
