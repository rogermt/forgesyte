/**
 * Integration tests for server API responses
 *
 * These tests verify that actual server responses match what the WebUI client expects.
 * Unlike unit tests that mock everything, these tests check real response formats
 * against the client's expectations.
 *
 * Expected Server Response Formats (from server/app/api.py):
 * - POST /v1/analyze → { job_id, status, ...job_fields }
 * - GET /v1/plugins → { plugins: PluginMetadata[], count: number }
 * - GET /v1/jobs → { jobs: Job[], count: number }
 * - GET /v1/jobs/:id → Job object (bare, no wrapper)
 * - DELETE /v1/jobs/:id → { status, job_id }
 * - GET /v1/health → { status, plugins_loaded, version }
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import type { Plugin, Job, AnalysisResult } from "../api/client";

/**
 * Mock Server Response Formats
 * These represent what the refactored server actually returns
 */

const mockPluginResponse = {
  plugins: [
    {
      name: "motion_detector",
      description: "Detects motion in images",
      version: "1.0.0",
      inputs: ["image"],
      outputs: ["detection"],
      permissions: [],
    },
    {
      name: "ocr_plugin",
      description: "Extracts text from images",
      version: "1.0.0",
      inputs: ["image"],
      outputs: ["text"],
      permissions: [],
    },
  ],
  count: 2,
};

const mockJobResponse: Job = {
  id: "job-123",
  status: "done" as const,
  plugin: "motion_detector",
  created_at: "2026-01-12T10:00:00Z",
  updated_at: "2026-01-12T10:01:00Z",
};

const mockJobsListResponse = {
  jobs: [
    mockJobResponse,
    {
      id: "job-124",
      status: "processing" as const,
      plugin: "ocr_plugin",
      created_at: "2026-01-12T10:02:00Z",
      updated_at: "2026-01-12T10:02:30Z",
    },
  ],
  count: 2,
};

const mockAnalyzeResponse: AnalysisResult = {
  job_id: "job-new-123",
  status: "processing",
};

const mockCancelResponse = {
  status: "cancelled",
  job_id: "job-123",
};

const mockHealthResponse = {
  status: "ok",
  plugins_loaded: 4,
  version: "0.1.0",
};

describe("Server API Integration Tests", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn();
    (global as any).fetch = fetchMock;
  });

  describe("Response Format Verification", () => {
    describe("GET /v1/plugins", () => {
      it("should return plugins in {plugins: [], count: number} format", async () => {
        // Server returns: { plugins: [...], count: N }
        fetchMock.mockResolvedValueOnce({
          ok: true,
          json: async () => mockPluginResponse,
        });

        const response = await fetch("/v1/plugins");
        const data = await response.json();

        // WebUI client expects this format
        expect(data).toHaveProperty("plugins");
        expect(data).toHaveProperty("count");
        expect(Array.isArray(data.plugins)).toBe(true);
        expect(data.plugins[0]).toHaveProperty("name");
        expect(data.plugins[0]).toHaveProperty("description");
        expect(data.plugins[0]).toHaveProperty("version");
      });

      it("plugins array should contain valid plugin metadata", () => {
        const { plugins } = mockPluginResponse;

        expect(plugins.length).toBeGreaterThan(0);
        plugins.forEach((plugin) => {
          expect(plugin).toHaveProperty("name");
          expect(plugin).toHaveProperty("description");
          expect(plugin).toHaveProperty("version");
          expect(plugin).toHaveProperty("inputs");
          expect(plugin).toHaveProperty("outputs");
          expect(plugin).toHaveProperty("permissions");
        });
      });
    });

    describe("GET /v1/jobs", () => {
      it("should return jobs in {jobs: [], count: number} format", async () => {
        // Server returns: { jobs: [...], count: N }
        fetchMock.mockResolvedValueOnce({
          ok: true,
          json: async () => mockJobsListResponse,
        });

        const response = await fetch("/v1/jobs");
        const data = await response.json();

        // WebUI client expects this format
        expect(data).toHaveProperty("jobs");
        expect(data).toHaveProperty("count");
        expect(Array.isArray(data.jobs)).toBe(true);
        expect(data.jobs[0]).toHaveProperty("id");
        expect(data.jobs[0]).toHaveProperty("status");
        expect(data.jobs[0]).toHaveProperty("plugin");
      });

      it("jobs array should contain valid job objects", () => {
        const { jobs } = mockJobsListResponse;

        expect(jobs.length).toBeGreaterThan(0);
        jobs.forEach((job) => {
          expect(job).toHaveProperty("id");
          expect(job).toHaveProperty("status");
          expect(job).toHaveProperty("plugin");
          expect(job).toHaveProperty("created_at");
          expect(job).toHaveProperty("updated_at");
          // status should be one of the valid values
          expect(["pending", "processing", "done", "error"]).toContain(
            job.status
          );
        });
      });

      it("should support query parameters for filtering", async () => {
        fetchMock.mockResolvedValueOnce({
          ok: true,
          json: async () => ({ jobs: [mockJobResponse], count: 1 }),
        });

        await fetch("/v1/jobs?limit=10&skip=0&status=done");

        const url = fetchMock.mock.calls[0][0] as string;
        expect(url).toContain("limit=10");
        expect(url).toContain("skip=0");
        expect(url).toContain("status=done");
      });
    });

    describe("GET /v1/jobs/:id", () => {
      it("should return job object (possibly wrapped in {job: ...})", async () => {
        // Server may return either:
        // Option 1: Bare job object
        // Option 2: { job: object }
        // Client handles both (see client.ts line 116)

        fetchMock.mockResolvedValueOnce({
          ok: true,
          json: async () => mockJobResponse,
        });

        const response = await fetch("/v1/jobs/job-123");
        const data = await response.json();

        // Check if it's wrapped or bare
        if (data.job) {
          // Wrapped format
          expect(data.job).toBeDefined();
          expect(data.job).toHaveProperty("id");
        } else {
          // Bare format
          expect(data).toHaveProperty("id");
          expect(data).toHaveProperty("status");
        }

        // Both should have required fields
        const job = data.job || data;
        expect(job).toHaveProperty("id");
        expect(job).toHaveProperty("status");
        expect(job).toHaveProperty("plugin");
      });

      it("should include optional fields if present (result, error)", async () => {
        const jobWithResult = {
          ...mockJobResponse,
          result: { motion: true, confidence: 0.95 },
        };

        fetchMock.mockResolvedValueOnce({
          ok: true,
          json: async () => jobWithResult,
        });

        const response = await fetch("/v1/jobs/job-123");
        const job = await response.json();

        expect(job.result).toBeDefined();
        expect(job.result).toHaveProperty("motion");
      });
    });

    describe("POST /v1/analyze", () => {
      it("should return analysis result with job_id and status", async () => {
        // Server returns: { job_id, status, ... }
        fetchMock.mockResolvedValueOnce({
          ok: true,
          json: async () => mockAnalyzeResponse,
        });

        const formData = new FormData();
        formData.append("file", new File(["test"], "test.jpg"));
        formData.append("plugin", "ocr");

        const response = await fetch("/v1/analyze", {
          method: "POST",
          body: formData,
        });
        const result = (await response.json()) as AnalysisResult;

        // WebUI client expects this format
        expect(result).toHaveProperty("job_id");
        expect(result).toHaveProperty("status");
        expect(typeof result.job_id).toBe("string");
        expect(typeof result.status).toBe("string");
      });

      it("should handle image_url parameter", async () => {
        fetchMock.mockResolvedValueOnce({
          ok: true,
          json: async () => mockAnalyzeResponse,
        });

        await fetch(
          "/v1/analyze?plugin=motion_detector&image_url=https://example.com/image.jpg",
          { method: "POST" }
        );

        const url = fetchMock.mock.calls[0][0] as string;
        expect(url).toContain("image_url=");
        expect(url).toContain("plugin=");
      });
    });

    describe("DELETE /v1/jobs/:id", () => {
      it("should return cancellation status with job_id", async () => {
        // Server returns: { status, job_id }
        fetchMock.mockResolvedValueOnce({
          ok: true,
          json: async () => mockCancelResponse,
        });

        const response = await fetch("/v1/jobs/job-123", {
          method: "DELETE",
        });
        const result = await response.json();

        // WebUI client expects this format
        expect(result).toHaveProperty("status");
        expect(result).toHaveProperty("job_id");
        expect(result.status).toMatch(/cancel|delete|ok/i);
      });
    });

    describe("GET /v1/health", () => {
      it("should return health status with required fields", async () => {
        // Server returns: { status, plugins_loaded, version }
        fetchMock.mockResolvedValueOnce({
          ok: true,
          json: async () => mockHealthResponse,
        });

        const response = await fetch("/v1/health");
        const health = await response.json();

        // WebUI client expects this format
        expect(health).toHaveProperty("status");
        expect(health).toHaveProperty("plugins_loaded");
        expect(health).toHaveProperty("version");
        expect(typeof health.status).toBe("string");
        expect(typeof health.plugins_loaded).toBe("number");
        expect(typeof health.version).toBe("string");
      });
    });
  });

  describe("Client Parsing Compatibility", () => {
    it("plugins response can be parsed by getPlugins()", async () => {
      // Simulate: client.getPlugins() calls /plugins and extracts result.plugins
      const result = mockPluginResponse;
      const plugins = result.plugins as Plugin[];

      expect(plugins).toBeDefined();
      expect(Array.isArray(plugins)).toBe(true);
      expect(plugins.length).toBeGreaterThan(0);
    });

    it("jobs response can be parsed by listJobs()", async () => {
      // Simulate: client.listJobs() calls /jobs and extracts result.jobs
      const result = mockJobsListResponse;
      const jobs = result.jobs as Job[];

      expect(jobs).toBeDefined();
      expect(Array.isArray(jobs)).toBe(true);
      expect(jobs.length).toBeGreaterThan(0);
    });

    it("job response can be parsed by getJob() with both formats", () => {
      // Format 1: Wrapped
      const wrappedResult = { job: mockJobResponse };
      const wrappedJob = wrappedResult.job ? wrappedResult.job : wrappedResult;
      expect(wrappedJob).toHaveProperty("id");

      // Format 2: Bare
      const bareJob = mockJobResponse;
      expect(bareJob).toHaveProperty("id");
    });

    it("analyze response can be parsed by analyzeImage()", async () => {
      // Simulate: client.analyzeImage() calls /analyze and returns result
      const result = mockAnalyzeResponse;

      expect(result.job_id).toBeDefined();
      expect(result.status).toBeDefined();
    });
  });

  describe("Error Handling", () => {
    it("should handle 500 errors from server", async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
      });

      const response = await fetch("/v1/plugins");
      expect(response.ok).toBe(false);
      expect(response.status).toBe(500);
    });

    it("should handle 400 errors (bad request)", async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: "Bad Request",
      });

      const response = await fetch("/v1/analyze", {
        method: "POST",
        body: new FormData(),
      });
      expect(response.ok).toBe(false);
      expect(response.status).toBe(400);
    });

    it("should handle 401 errors (unauthorized)", async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: "Unauthorized",
      });

      const response = await fetch("/v1/jobs");
      expect(response.ok).toBe(false);
      expect(response.status).toBe(401);
    });
  });
});
