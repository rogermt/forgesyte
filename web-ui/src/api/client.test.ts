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
                    job_id: "job-1",
                    status: "completed" as const,
                    plugin_id: "ocr",
                    tool: "analyze",
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

            await client.listJobs(10, 0, "completed");

            const callUrl = (fetchMock.mock.calls[0][0] as string);
            expect(callUrl).toContain("status=completed");
        });
    });

    describe("getJob", () => {
        it("should fetch a specific job", async () => {
            const mockJob = {
                job_id: "job-123",
                status: "completed" as const,
                plugin_id: "ocr",
                tool: "analyze",
                results: { text: "Hello" },
                created_at: "2026-01-09T21:00:00Z",
                updated_at: "2026-01-09T21:00:30Z",
            };

            fetchMock.mockResolvedValueOnce(
                createMockResponse(mockJob)
            );

            const job = await client.getJob("job-123");

            expect(job.job_id).toBe("job-123");
            expect(job.status).toBe("completed");
            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining("/jobs/job-123"),
                expect.any(Object)
            );
        });

        it("should handle job response without wrapper", async () => {
            const mockJob = {
                job_id: "job-123",
                status: "pending" as const,
                plugin_id: "ocr",
                tool: "analyze",
                created_at: "2026-01-09T21:00:00Z",
                updated_at: "2026-01-09T21:00:30Z",
            };

            fetchMock.mockResolvedValueOnce(
                createMockResponse(mockJob)
            );

            const job = await client.getJob("job-123");

            expect(job.job_id).toBe("job-123");
            expect(job.status).toBe("pending");
        });

        // Issue #231: Cache-busting tests
        it("should include cache-busting timestamp query param", async () => {
            const mockJob = {
                job_id: "job-456",
                status: "completed" as const,
                created_at: "2026-01-09T21:00:00Z",
            };

            fetchMock.mockResolvedValueOnce(createMockResponse(mockJob));

            await client.getJob("job-456");

            const callUrl = fetchMock.mock.calls[0][0] as string;
            // Should contain ?_t= followed by a timestamp
            expect(callUrl).toMatch(/\/jobs\/job-456\?_t=\d+$/);
        });

        it("should use cache: no-store option to bypass browser cache", async () => {
            const mockJob = {
                job_id: "job-789",
                status: "running" as const,
                created_at: "2026-01-09T21:00:00Z",
            };

            fetchMock.mockResolvedValueOnce(createMockResponse(mockJob));

            await client.getJob("job-789");

            const callOptions = fetchMock.mock.calls[0][1] as RequestInit;
            // Should include cache: "no-store" to prevent browser caching
            expect(callOptions.cache).toBe("no-store");
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
            const runningJob = {
                job_id: "job-1",
                status: "running" as const,
                plugin_id: "ocr",
                tool: "analyze",
                created_at: "2026-01-09T21:00:00Z",
                updated_at: "2026-01-09T21:00:10Z",
            };

            const completedJob = {
                job_id: "job-1",
                status: "completed" as const,
                plugin_id: "ocr",
                tool: "analyze",
                results: { text: "Done" },
                created_at: "2026-01-09T21:00:00Z",
                updated_at: "2026-01-09T21:00:30Z",
            };

            fetchMock
                .mockResolvedValueOnce(createMockResponse(runningJob))
                .mockResolvedValueOnce(createMockResponse(completedJob));

            const result = await client.pollJob("job-1", 10, 5000);

            expect(result.status).toBe("completed");
            expect(fetchMock).toHaveBeenCalledTimes(2);
        });

        it("should timeout if job not completed", async () => {
            const pendingJob = {
                job_id: "job-1",
                status: "pending" as const,
                plugin_id: "ocr",
                tool: "analyze",
                created_at: "2026-01-09T21:00:00Z",
                updated_at: "2026-01-09T21:00:10Z",
            };

            fetchMock.mockResolvedValue(
                createMockResponse(pendingJob)
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
            it("should submit video with plugin_id and tool", async () => {
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

                const result = await client.submitVideo(mockFile, "ocr", "analyze");

                expect(result).toEqual(mockResult);
                expect(mockXHRInstances[0]?.open).toHaveBeenCalledWith(
                    "POST",
                    expect.stringContaining("/video/submit?plugin_id=ocr&tool=analyze")
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

                await client.submitVideo(mockFile, "ocr", "analyze", progressCallback);

                expect(progressCallback).toHaveBeenCalledWith(50);
                expect(progressCallback).toHaveBeenCalledWith(100);
            });

            // Phase 5: Multi-tool video submission tests
            it("should submit video with multiple logical_tool_id params", async () => {
                const mockFile = new File(["test"], "test.mp4", { type: "video/mp4" });
                const mockResult = { job_id: "video-multi-123", tools: [{ logical: "player_detection", resolved: "video_player_tracking" }] };

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
                        setTimeout(() => { if (this.onload) this.onload(); }, 0);
                    }
                }

                (global as unknown as { XMLHttpRequest: typeof MockXMLHttpRequest }).XMLHttpRequest = MockXMLHttpRequest;

                // Submit with array of logical IDs and useLogicalId=true
                const result = await client.submitVideo(
                    mockFile,
                    "yolo-tracker",
                    ["player_detection", "ball_detection"],
                    undefined,
                    true
                );

                expect(result).toEqual(mockResult);
                const calledUrl = mockXHRInstances[0]?.open.mock.calls[0][1] as string;
                // Should have repeated logical_tool_id params
                expect(calledUrl).toContain("logical_tool_id=player_detection");
                expect(calledUrl).toContain("logical_tool_id=ball_detection");
            });

            it("should submit video with single logical_tool_id when useLogicalId=true", async () => {
                const mockFile = new File(["test"], "test.mp4", { type: "video/mp4" });
                const mockResult = { job_id: "video-single-123" };

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
                        setTimeout(() => { if (this.onload) this.onload(); }, 0);
                    }
                }

                (global as unknown as { XMLHttpRequest: typeof MockXMLHttpRequest }).XMLHttpRequest = MockXMLHttpRequest;

                const result = await client.submitVideo(
                    mockFile,
                    "yolo-tracker",
                    "player_detection",
                    undefined,
                    true
                );

                expect(result).toEqual(mockResult);
                const calledUrl = mockXHRInstances[0]?.open.mock.calls[0][1] as string;
                expect(calledUrl).toContain("logical_tool_id=player_detection");
                expect(calledUrl).not.toContain("tool=");
            });
        });

        // v0.10.1: Video upload-only endpoint tests
        describe("submitVideo (v0.10.1 upload-only)", () => {
            it("should upload video and return video_path", async () => {
                const mockFile = new File(["test"], "test.mp4", { type: "video/mp4" });
                const mockResult = { video_path: "video/input/abc-123.mp4" };

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
                        setTimeout(() => { if (this.onload) this.onload(); }, 0);
                    }
                }

                (global as unknown as { XMLHttpRequest: typeof MockXMLHttpRequest }).XMLHttpRequest = MockXMLHttpRequest;

                // v0.10.1: New signature - upload only, returns video_path
                const result = await (client as unknown as { submitVideoUpload: (file: File, pluginId: string, onProgress?: (p: number) => void) => Promise<{ video_path: string }> }).submitVideoUpload(
                    mockFile,
                    "yolo-tracker"
                );

                expect(result).toEqual(mockResult);
                expect(mockXHRInstances[0]?.open).toHaveBeenCalledWith(
                    "POST",
                    expect.stringContaining("/video/upload?plugin_id=yolo-tracker")
                );
            });

            it("should NOT return job_id from upload-only endpoint", async () => {
                const mockFile = new File(["test"], "test.mp4", { type: "video/mp4" });
                const mockResult = { video_path: "video/input/abc-123.mp4" };

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
                        setTimeout(() => { if (this.onload) this.onload(); }, 0);
                    }
                }

                (global as unknown as { XMLHttpRequest: typeof MockXMLHttpRequest }).XMLHttpRequest = MockXMLHttpRequest;

                const result = await (client as unknown as { submitVideoUpload: (file: File, pluginId: string, onProgress?: (p: number) => void) => Promise<{ video_path: string }> }).submitVideoUpload(
                    mockFile,
                    "yolo-tracker"
                );

                expect(result).toHaveProperty("video_path");
                expect(result).not.toHaveProperty("job_id");
            });
        });

        // v0.10.1: Video job submission with video_path and lockedTools
        describe("submitVideoJob (v0.10.1 JSON body)", () => {
            it("should submit job with video_path and lockedTools", async () => {
                const mockResult = { job_id: "video-job-456" };

                fetchMock.mockResolvedValueOnce(createMockResponse(mockResult));

                const result = await (client as unknown as { submitVideoJob: (pluginId: string, videoPath: string, lockedTools: string[]) => Promise<{ job_id: string }> }).submitVideoJob(
                    "yolo-tracker",
                    "video/input/abc-123.mp4",
                    ["video_player_tracking"]
                );

                expect(result).toEqual(mockResult);
                expect(fetchMock).toHaveBeenCalledWith(
                    expect.stringContaining("/video/job"),
                    expect.objectContaining({
                        method: "POST",
                        body: expect.stringContaining("video/input/abc-123.mp4"),
                    })
                );
            });

            it("should send lockedTools as JSON array", async () => {
                const mockResult = { job_id: "video-job-789" };

                fetchMock.mockResolvedValueOnce(createMockResponse(mockResult));

                await (client as unknown as { submitVideoJob: (pluginId: string, videoPath: string, lockedTools: string[]) => Promise<{ job_id: string }> }).submitVideoJob(
                    "yolo-tracker",
                    "video/input/test.mp4",
                    ["video_player_tracking", "video_ball_detection"]
                );

                const callArgs = fetchMock.mock.calls[0][1] as RequestInit;
                const body = JSON.parse(callArgs.body as string);

                expect(body.lockedTools).toEqual(["video_player_tracking", "video_ball_detection"]);
            });
        });
    });

    // Phase 5: Image submission with useLogicalId flag
    describe("submitImage with logical_tool_id", () => {
        it("should submit image with useLogicalId=true using logical_tool_id param", async () => {
            const mockFile = new File(["test"], "test.png", { type: "image/png" });
            const mockResult = { job_id: "image-logical-123" };

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
                    setTimeout(() => { if (this.onload) this.onload(); }, 0);
                }
            }

            (global as unknown as { XMLHttpRequest: typeof MockXMLHttpRequest }).XMLHttpRequest = MockXMLHttpRequest;

            // Need to call with useLogicalId - currently not implemented, test will fail
            const result = await (client as unknown as { submitImage: (file: File, pluginId: string, tools: string | string[], onProgress?: (p: number) => void, useLogicalId?: boolean) => Promise<{ job_id: string }> }).submitImage(
                mockFile,
                "ocr",
                "text_extraction",
                undefined,
                true
            );

            expect(result).toEqual(mockResult);
            const calledUrl = mockXHRInstances[0]?.open.mock.calls[0][1] as string;
            expect(calledUrl).toContain("logical_tool_id=text_extraction");
            expect(calledUrl).not.toContain("tool=");
        });

        it("should submit image with multiple logical_tool_id params", async () => {
            const mockFile = new File(["test"], "test.png", { type: "image/png" });
            const mockResult = { job_id: "image-multi-123", tools: [{ logical: "text_extraction", resolved: "ocr" }] };

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
                    setTimeout(() => { if (this.onload) this.onload(); }, 0);
                }
            }

            (global as unknown as { XMLHttpRequest: typeof MockXMLHttpRequest }).XMLHttpRequest = MockXMLHttpRequest;

            const result = await (client as unknown as { submitImage: (file: File, pluginId: string, tools: string | string[], onProgress?: (p: number) => void, useLogicalId?: boolean) => Promise<{ job_id: string }> }).submitImage(
                mockFile,
                "ocr",
                ["text_extraction", "layout_analysis"],
                undefined,
                true
            );

            expect(result).toEqual(mockResult);
            const calledUrl = mockXHRInstances[0]?.open.mock.calls[0][1] as string;
            expect(calledUrl).toContain("logical_tool_id=text_extraction");
            expect(calledUrl).toContain("logical_tool_id=layout_analysis");
        });
    });
});