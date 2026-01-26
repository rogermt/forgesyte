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
});

