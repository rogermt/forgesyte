/**
 * Tests for ForgeSyteAPIClient
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { ForgeSyteAPIClient } from "./client";

// Helper function to create mock fetch responses with proper headers
const createMockResponse = (
    data: unknown,
    ok = true,
    status = 200
) => ({
    ok,
    status,
    statusText: ok ? "OK" : "Error",
    headers: {
        get: (name: string) =>
            name === "content-type" ? "application/json" : null,
    },
    json: async () => data,
});

describe("ForgeSyteAPIClient", () => {
    let client: ForgeSyteAPIClient;
    let fetchMock: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        fetchMock = vi.fn();
        (window as unknown as { fetch: ReturnType<typeof vi.fn> }).fetch = fetchMock;
        client = new ForgeSyteAPIClient("http://localhost:3000/v1");
    });

    describe("getPlugins", () => {
        it("should fetch and return plugins list", async () => {
            const mockPlugins = [
                {
                    name: "motion_detector",
                    description: "Detects motion",
                    version: "1.0.0",
                    inputs: ["image"],
                    outputs: ["detection"],
                    permissions: [],
                },
            ];

            fetchMock.mockResolvedValueOnce(
                createMockResponse({ plugins: mockPlugins })
            );

            const plugins = await client.getPlugins();

            expect(plugins).toEqual(mockPlugins);
            expect(fetchMock).toHaveBeenCalledWith(
                "http://localhost:3000/v1/plugins",
                expect.any(Object)
            );
        });

        it("should handle API errors", async () => {
            fetchMock.mockResolvedValueOnce(
                createMockResponse({ detail: "Internal Server Error" }, false, 500)
            );

            await expect(client.getPlugins()).rejects.toThrow(
                "Internal Server Error"
            );
        });
    });

    describe("listJobs", () => {
        it("should fetch jobs with default parameters", async () => {
            const mockJobs = [
                {
                    id: "job-1",
                    status: "done" as const,
                    plugin: "motion_detector",
                    created_at: "2026-01-09T21:00:00Z",
                    updated_at: "2026-01-09T21:00:30Z",
                },
            ];

            fetchMock.mockResolvedValueOnce(
                createMockResponse({ jobs: mockJobs })
            );

            const jobs = await client.listJobs();

            expect(jobs).toEqual(mockJobs);
            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining("/v1/jobs"),
                expect.any(Object)
            );
        });

        it("should include pagination parameters", async () => {
            fetchMock.mockResolvedValueOnce(
                createMockResponse({ jobs: [] })
            );

            await client.listJobs(20, 10);

            const callUrl = (fetchMock.mock.calls[0][0] as string);
            expect(callUrl).toContain("limit=20");
            expect(callUrl).toContain("skip=10");
        });

        it("should include status filter when provided", async () => {
            fetchMock.mockResolvedValueOnce(
                createMockResponse({ jobs: [] })
            );

            await client.listJobs(10, 0, "done");

            const callUrl = (fetchMock.mock.calls[0][0] as string);
            expect(callUrl).toContain("status=done");
        });
    });

    describe("getJob", () => {
        it("should fetch a specific job", async () => {
            const mockJob = {
                id: "job-123",
                status: "done" as const,
                plugin: "motion_detector",
                result: { motion: true },
                created_at: "2026-01-09T21:00:00Z",
                updated_at: "2026-01-09T21:00:30Z",
            };

            fetchMock.mockResolvedValueOnce(
                createMockResponse({ job: mockJob })
            );

            const job = await client.getJob("job-123");

            expect(job).toEqual(mockJob);
            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining("/jobs/job-123"),
                expect.any(Object)
            );
        });

        it("should handle job response without wrapper", async () => {
            const mockJob = {
                id: "job-123",
                status: "done" as const,
                plugin: "motion_detector",
                created_at: "2026-01-09T21:00:00Z",
                updated_at: "2026-01-09T21:00:30Z",
            };

            fetchMock.mockResolvedValueOnce(
                createMockResponse(mockJob)
            );

            const job = await client.getJob("job-123");

            expect(job).toEqual(mockJob);
        });
    });

    describe("analyzeImage", () => {
        it("should upload file and return analysis result", async () => {
            const mockFile = new File(["test"], "test.jpg", {
                type: "image/jpeg",
            });
            const mockResult = { job_id: "job-123", status: "processing" };

            fetchMock.mockResolvedValueOnce({
                ok: true,
                json: async () => mockResult,
            });

            const result = await client.analyzeImage(mockFile, "motion_detector");

            expect(result).toEqual(mockResult);
            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining("/analyze"),
                expect.objectContaining({
                    method: "POST",
                })
            );
        });

        it("should pass plugin as query parameter, not form field", async () => {
            const mockFile = new File(["test"], "test.jpg", {
                type: "image/jpeg",
            });
            const mockResult = { job_id: "job-123", status: "processing" };

            fetchMock.mockResolvedValueOnce({
                ok: true,
                json: async () => mockResult,
            });

            await client.analyzeImage(mockFile, "moderation");

            const callUrl = fetchMock.mock.calls[0][0] as string;
            expect(callUrl).toContain("plugin=moderation");
        });

        it("should include API key in headers", async () => {
            const clientWithKey = new ForgeSyteAPIClient(
                "http://localhost:3000/v1",
                "test-api-key"
            );

            const mockFile = new File(["test"], "test.jpg");

            fetchMock.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ job_id: "job-1" }),
            });

            await clientWithKey.analyzeImage(mockFile, "plugin");

            const callArgs = fetchMock.mock.calls[0][1] as RequestInit;
            expect(callArgs.headers).toBeDefined();
        });
    });

    describe("cancelJob", () => {
        it("should send DELETE request to cancel job", async () => {
            fetchMock.mockResolvedValueOnce(
                createMockResponse({ status: "cancelled", job_id: "job-123" })
            );

            const result = await client.cancelJob("job-123");

            expect(result).toEqual({ status: "cancelled", job_id: "job-123" });
            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining("/jobs/job-123"),
                expect.objectContaining({
                    method: "DELETE",
                })
            );
        });
    });

    describe("getHealth", () => {
        it("should fetch health status", async () => {
            const mockHealth = {
                status: "ok",
                plugins_loaded: 5,
                version: "0.1.0",
            };

            fetchMock.mockResolvedValueOnce(
                createMockResponse(mockHealth)
            );

            const health = await client.getHealth();

            expect(health).toEqual(mockHealth);
            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining("/health"),
                expect.any(Object)
            );
        });
    });

    describe("pollJob", () => {
        it("should poll until job is complete", async () => {
            const pendingJob = {
                id: "job-1",
                status: "processing" as const,
                plugin: "motion_detector",
                created_at: "2026-01-09T21:00:00Z",
                updated_at: "2026-01-09T21:00:10Z",
            };

            const completeJob = {
                ...pendingJob,
                status: "done" as const,
                updated_at: "2026-01-09T21:00:30Z",
            };

            fetchMock
                .mockResolvedValueOnce(
                    createMockResponse({ job: pendingJob })
                )
                .mockResolvedValueOnce(
                    createMockResponse({ job: completeJob })
                );

            const result = await client.pollJob("job-1", 10, 5000);

            expect(result).toEqual(completeJob);
            expect(fetchMock).toHaveBeenCalledTimes(2);
        });

        it("should timeout if job not completed", async () => {
            const pendingJob = {
                id: "job-1",
                status: "processing" as const,
                plugin: "motion_detector",
                created_at: "2026-01-09T21:00:00Z",
                updated_at: "2026-01-09T21:00:10Z",
            };

            fetchMock.mockResolvedValue(
                createMockResponse({ job: pendingJob })
            );

            await expect(
                client.pollJob("job-1", 10, 100)
            ).rejects.toThrow(/polling timed out/);
        });
    });

    describe("API key handling", () => {
        it("should include X-API-Key header when provided", async () => {
            const clientWithKey = new ForgeSyteAPIClient(
                "http://localhost:3000/v1",
                "secret-key"
            );

            fetchMock.mockResolvedValueOnce(
                createMockResponse({ plugins: [] })
            );

            await clientWithKey.getPlugins();

            const callArgs = fetchMock.mock.calls[0][1] as RequestInit;
            const headers = callArgs.headers as Record<string, string>;
            expect(headers["X-API-Key"]).toBe("secret-key");
        });

        it("should not include X-API-Key header when not provided", async () => {
            fetchMock.mockResolvedValueOnce(
                createMockResponse({ plugins: [] })
            );

            await client.getPlugins();

            const callArgs = fetchMock.mock.calls[0][1] as RequestInit;
            const headers = callArgs.headers as Record<string, string>;
            expect(headers["X-API-Key"]).toBeUndefined();
        });
    });

    describe("Video API methods", () => {
        describe("submitVideo", () => {
            it("should submit video with default pipeline", async () => {
                const mockFile = new File(["test"], "test.mp4", {
                    type: "video/mp4",
                });
                const mockResult = { job_id: "video-job-123" };

                // Mock XMLHttpRequest class
                const mockXHRInstances: MockXMLHttpRequest[] = [];

                class MockXMLHttpRequest {
                    open = vi.fn();
                    send = vi.fn();
                    setRequestHeader = vi.fn();
                    upload = { onprogress: null as null };
                    onload: (() => void) | null = null;
                    onerror: (() => void) | null = null;
                    status = 200;
                    responseText = JSON.stringify(mockResult);

                    constructor() {
                        mockXHRInstances.push(this);
                        // Simulate successful upload
                        setTimeout(() => {
                            if (this.onload) this.onload();
                        }, 0);
                    }
                }

                (global as unknown as { XMLHttpRequest: typeof MockXMLHttpRequest }).XMLHttpRequest = MockXMLHttpRequest;

                const result = await (client as unknown as ForgeSyteAPIClient & { submitVideo: (file: File, pipelineId?: string, onProgress?: (percent: number) => void) => Promise<{ job_id: string }> }).submitVideo(mockFile);

                expect(result).toEqual(mockResult);
                expect(mockXHRInstances[0]?.open).toHaveBeenCalledWith(
                    "POST",
                    expect.stringContaining("/video/submit?pipeline_id=ocr_only")
                );
            });

            it("should submit video with explicit pipeline", async () => {
                const mockFile = new File(["test"], "test.mp4", {
                    type: "video/mp4",
                });
                const mockResult = { job_id: "video-job-456" };

                const mockXHRInstances: MockXMLHttpRequest[] = [];

                class MockXMLHttpRequest {
                    open = vi.fn();
                    send = vi.fn();
                    setRequestHeader = vi.fn();
                    upload = { onprogress: null as null };
                    onload: (() => void) | null = null;
                    onerror: (() => void) | null = null;
                    status = 200;
                    responseText = JSON.stringify(mockResult);

                    constructor() {
                        mockXHRInstances.push(this);
                        setTimeout(() => {
                            if (this.onload) this.onload();
                        }, 0);
                    }
                }

                (global as unknown as { XMLHttpRequest: typeof MockXMLHttpRequest }).XMLHttpRequest = MockXMLHttpRequest;

                const result = await (client as unknown as ForgeSyteAPIClient & { submitVideo: (file: File, pipelineId?: string, onProgress?: (percent: number) => void) => Promise<{ job_id: string }> }).submitVideo(mockFile, "yolo_ocr");

                expect(result).toEqual(mockResult);
                expect(mockXHRInstances[0]?.open).toHaveBeenCalledWith(
                    "POST",
                    expect.stringContaining("/video/submit?pipeline_id=yolo_ocr")
                );
            });

            it("should call progress callback during upload", async () => {
                const mockFile = new File(["test"], "test.mp4", {
                    type: "video/mp4",
                });
                const mockResult = { job_id: "video-job-789" };
                const progressCallback = vi.fn();

                class MockXMLHttpRequest {
                    open = vi.fn();
                    send = vi.fn();
                    setRequestHeader = vi.fn();
                    upload = { onprogress: null as null };
                    onload: (() => void) | null = null;
                    onerror: (() => void) | null = null;
                    status = 200;
                    responseText = JSON.stringify(mockResult);

                    constructor() {
                        // Simulate upload progress
                        setTimeout(() => {
                            if (this.upload.onprogress) {
                                this.upload.onprogress({ lengthComputable: true, loaded: 50, total: 100 } as ProgressEvent);
                                this.upload.onprogress({ lengthComputable: true, loaded: 100, total: 100 } as ProgressEvent);
                            }
                            if (this.onload) this.onload();
                        }, 0);
                    }
                }

                (global as unknown as { XMLHttpRequest: typeof MockXMLHttpRequest }).XMLHttpRequest = MockXMLHttpRequest;

                await (client as unknown as ForgeSyteAPIClient & { submitVideo: (file: File, pipelineId?: string, onProgress?: (percent: number) => void) => Promise<{ job_id: string }> }).submitVideo(mockFile, "ocr_only", progressCallback);

                expect(progressCallback).toHaveBeenCalledWith(50);
                expect(progressCallback).toHaveBeenCalledWith(100);
            });
        });

        describe("getVideoJobStatus", () => {
            it("should fetch video job status", async () => {
                const mockStatus = {
                    job_id: "video-job-123",
                    status: "completed",
                    progress: 100,
                    created_at: "2026-02-18T10:00:00Z",
                    updated_at: "2026-02-18T10:01:00Z",
                };

                fetchMock.mockResolvedValueOnce(
                    createMockResponse(mockStatus)
                );

                const status = await (client as unknown as ForgeSyteAPIClient & { getVideoJobStatus: (jobId: string) => Promise<Record<string, unknown>> }).getVideoJobStatus("video-job-123");

                expect(status).toEqual(mockStatus);
                expect(fetchMock).toHaveBeenCalledWith(
                    expect.stringContaining("/video/status/video-job-123"),
                    expect.any(Object)
                );
            });

            it("should handle pending status", async () => {
                const mockStatus = {
                    job_id: "video-job-456",
                    status: "pending",
                    progress: 0,
                    created_at: "2026-02-18T10:00:00Z",
                    updated_at: "2026-02-18T10:00:00Z",
                };

                fetchMock.mockResolvedValueOnce(
                    createMockResponse(mockStatus)
                );

                const status = await (client as unknown as ForgeSyteAPIClient & { getVideoJobStatus: (jobId: string) => Promise<Record<string, unknown>> }).getVideoJobStatus("video-job-456");

                expect(status.status).toBe("pending");
            });
        });

        describe("getVideoJobResults", () => {
            it("should fetch video job results", async () => {
                const mockResults = {
                    job_id: "video-job-123",
                    results: {
                        text: "Sample OCR text",
                        detections: [],
                    },
                    created_at: "2026-02-18T10:00:00Z",
                    updated_at: "2026-02-18T10:01:00Z",
                };

                fetchMock.mockResolvedValueOnce(
                    createMockResponse(mockResults)
                );

                const results = await (client as unknown as ForgeSyteAPIClient & { getVideoJobResults: (jobId: string) => Promise<Record<string, unknown>> }).getVideoJobResults("video-job-123");

                expect(results).toEqual(mockResults);
                expect(fetchMock).toHaveBeenCalledWith(
                    expect.stringContaining("/video/results/video-job-123"),
                    expect.any(Object)
                );
            });

            it("should handle results with detections", async () => {
                const mockResults = {
                    job_id: "video-job-789",
                    results: {
                        text: "Sample text",
                        detections: [
                            {
                                label: "person",
                                confidence: 0.95,
                                bbox: [100, 100, 50, 100],
                            },
                        ],
                    },
                    created_at: "2026-02-18T10:00:00Z",
                    updated_at: "2026-02-18T10:01:00Z",
                };

                fetchMock.mockResolvedValueOnce(
                    createMockResponse(mockResults)
                );

                const results = await (client as unknown as ForgeSyteAPIClient & { getVideoJobResults: (jobId: string) => Promise<Record<string, unknown>> }).getVideoJobResults("video-job-789");

                expect(results.results.detections).toHaveLength(1);
            });
        });
    });

    describe("analyzeMulti", () => {
        it("should analyze image with multiple tools", async () => {
            const mockFile = new File(["test"], "test.jpg", {
                type: "image/jpeg",
            });
            const mockResult = {
                tools: {
                    ocr: { text: "Sample text", confidence: 0.95 },
                    "yolo-tracker": {
                        detections: [
                            {
                                label: "person",
                                confidence: 0.92,
                                bbox: [100, 100, 50, 100],
                            },
                        ],
                    },
                },
            };

            fetchMock.mockResolvedValueOnce({
                ok: true,
                json: async () => mockResult,
            });

            const result = await (client as unknown as ForgeSyteAPIClient & { analyzeMulti: (file: File, tools: string[]) => Promise<Record<string, unknown>> }).analyzeMulti(mockFile, ["ocr", "yolo-tracker"]);

            expect(result).toEqual(mockResult);
            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining("/image/analyze-multi"),
                expect.objectContaining({
                    method: "POST",
                })
            );
        });

        it("should analyze image with single tool", async () => {
            const mockFile = new File(["test"], "test.jpg", {
                type: "image/jpeg",
            });
            const mockResult = {
                tools: {
                    ocr: { text: "Sample text", confidence: 0.95 },
                },
            };

            fetchMock.mockResolvedValueOnce({
                ok: true,
                json: async () => mockResult,
            });

            const result = await (client as unknown as ForgeSyteAPIClient & { analyzeMulti: (file: File, tools: string[]) => Promise<Record<string, unknown>> }).analyzeMulti(mockFile, ["ocr"]);

            expect(result).toEqual(mockResult);
            expect(result.tools).toHaveProperty("ocr");
        });

        it("should handle tool execution errors", async () => {
            const mockFile = new File(["test"], "test.jpg", {
                type: "image/jpeg",
            });
            const mockResult = {
                tools: {
                    ocr: { text: "Sample text", confidence: 0.95 },
                    "yolo-tracker": { error: "Tool execution failed" },
                },
            };

            fetchMock.mockResolvedValueOnce({
                ok: true,
                json: async () => mockResult,
            });

            const result = await (client as unknown as ForgeSyteAPIClient & { analyzeMulti: (file: File, tools: string[]) => Promise<Record<string, unknown>> }).analyzeMulti(mockFile, ["ocr", "yolo-tracker"]);

            expect(result.tools["yolo-tracker"]).toHaveProperty("error");
        });

        it("should include API key in headers", async () => {
            const clientWithKey = new ForgeSyteAPIClient(
                "http://localhost:3000/v1",
                "test-api-key"
            );

            const mockFile = new File(["test"], "test.jpg", {
                type: "image/jpeg",
            });

            fetchMock.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ tools: {} }),
            });

            await (clientWithKey as unknown as ForgeSyteAPIClient & { analyzeMulti: (file: File, tools: string[]) => Promise<Record<string, unknown>> }).analyzeMulti(mockFile, ["ocr"]);

            const callArgs = fetchMock.mock.calls[0][1] as RequestInit;
            expect(callArgs.headers).toBeDefined();
        });
    });
});

