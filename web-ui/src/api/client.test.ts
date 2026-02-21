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
                    tool: "extract_text",
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
                tool: "extract_text",
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
                tool: "extract_text",
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
                tool: "extract_text",
                created_at: "2026-01-09T21:00:00Z",
                updated_at: "2026-01-09T21:00:10Z",
            };

            const completedJob = {
                job_id: "job-1",
                status: "completed" as const,
                plugin_id: "ocr",
                tool: "extract_text",
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
                tool: "extract_text",
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

                const result = await client.submitVideo(mockFile, "ocr", "extract_text");

                expect(result).toEqual(mockResult);
                expect(mockXHRInstances[0]?.open).toHaveBeenCalledWith(
                    "POST",
                    expect.stringContaining("/video/submit?plugin_id=ocr&tool=extract_text")
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

                await client.submitVideo(mockFile, "ocr", "extract_text", progressCallback);

                expect(progressCallback).toHaveBeenCalledWith(50);
                expect(progressCallback).toHaveBeenCalledWith(100);
            });
        });
    });
});