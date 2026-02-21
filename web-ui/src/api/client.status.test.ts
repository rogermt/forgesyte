/**
 * Tests for Job status enum alignment (Issue #212).
 *
 * The web-UI Job interface should use the same status values as the server:
 * - "pending" (not "queued")
 * - "running"
 * - "completed" (not "done")
 * - "failed" (not "error")
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

describe("Job status enum alignment (Issue #212)", () => {
    let client: ForgeSyteAPIClient;
    let fetchMock: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        fetchMock = vi.fn();
        (window as unknown as { fetch: ReturnType<typeof vi.fn> }).fetch = fetchMock;
        client = new ForgeSyteAPIClient("http://localhost:3000/v1");
    });

    describe("Job status types", () => {
        it("should accept 'pending' status from server", async () => {
            const mockJob = {
                job_id: "job-123",
                status: "pending",
                plugin_id: "ocr",
                tool: "extract_text",
                created_at: "2026-01-09T21:00:00Z",
                updated_at: "2026-01-09T21:00:30Z",
            };

            fetchMock.mockResolvedValueOnce(createMockResponse(mockJob));

            const job = await client.getJob("job-123");

            expect(job.status).toBe("pending");
        });

        it("should accept 'running' status from server", async () => {
            const mockJob = {
                job_id: "job-456",
                status: "running",
                plugin_id: "ocr",
                tool: "extract_text",
                created_at: "2026-01-09T21:00:00Z",
                updated_at: "2026-01-09T21:00:30Z",
            };

            fetchMock.mockResolvedValueOnce(createMockResponse(mockJob));

            const job = await client.getJob("job-456");

            expect(job.status).toBe("running");
        });

        it("should accept 'completed' status from server", async () => {
            const mockJob = {
                job_id: "job-789",
                status: "completed",
                plugin_id: "ocr",
                tool: "extract_text",
                results: { text: "Hello" },
                created_at: "2026-01-09T21:00:00Z",
                updated_at: "2026-01-09T21:00:30Z",
            };

            fetchMock.mockResolvedValueOnce(createMockResponse(mockJob));

            const job = await client.getJob("job-789");

            expect(job.status).toBe("completed");
        });

        it("should accept 'failed' status from server", async () => {
            const mockJob = {
                job_id: "job-abc",
                status: "failed",
                plugin_id: "ocr",
                tool: "extract_text",
                error_message: "Processing failed",
                created_at: "2026-01-09T21:00:00Z",
                updated_at: "2026-01-09T21:00:30Z",
            };

            fetchMock.mockResolvedValueOnce(createMockResponse(mockJob));

            const job = await client.getJob("job-abc");

            expect(job.status).toBe("failed");
        });
    });

    describe("pollJob terminal states", () => {
        it("should stop polling on 'completed' status", async () => {
            const runningJob = {
                job_id: "job-1",
                status: "running",
                plugin_id: "ocr",
                tool: "extract_text",
                created_at: "2026-01-09T21:00:00Z",
                updated_at: "2026-01-09T21:00:10Z",
            };

            const completedJob = {
                job_id: "job-1",
                status: "completed",
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

        it("should stop polling on 'failed' status", async () => {
            const pendingJob = {
                job_id: "job-2",
                status: "pending",
                plugin_id: "ocr",
                tool: "extract_text",
                created_at: "2026-01-09T21:00:00Z",
                updated_at: "2026-01-09T21:00:10Z",
            };

            const failedJob = {
                job_id: "job-2",
                status: "failed",
                plugin_id: "ocr",
                tool: "extract_text",
                error_message: "Processing error",
                created_at: "2026-01-09T21:00:00Z",
                updated_at: "2026-01-09T21:00:30Z",
            };

            fetchMock
                .mockResolvedValueOnce(createMockResponse(pendingJob))
                .mockResolvedValueOnce(createMockResponse(failedJob));

            const result = await client.pollJob("job-2", 10, 5000);

            expect(result.status).toBe("failed");
            expect(fetchMock).toHaveBeenCalledTimes(2);
        });
    });
});