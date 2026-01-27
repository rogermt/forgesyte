/**
 * Tests for runTool utility - TDD approach
 * These tests define the expected behavior of the unified tool runner
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { runTool, withRetry, withLogging } from "./runTool";

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch as unknown as typeof fetch;

describe("runTool", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("calls the correct endpoint with args", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ result: { ok: true } }),
    } as Response);

    const result = await runTool({
      pluginId: "test-plugin",
      toolName: "detect",
      args: { foo: "bar" },
    });

    expect(mockFetch).toHaveBeenCalledWith(
      "/v1/plugins/test-plugin/tools/detect/run",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          args: { foo: "bar" },
        }),
      })
    );

    expect(result.success).toBe(true);
  });

  it("returns result on success", async () => {
    const expectedResult = { detections: [{ id: 1 }] };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ result: expectedResult }),
    } as Response);

    const result = await runTool({
      pluginId: "test-plugin",
      toolName: "detect",
      args: {},
    });

    expect(result.success).toBe(true);
    expect(result.result).toEqual(expectedResult);
  });

  it("returns error when server responds with non-OK", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ error: "Server error" }),
    } as unknown as Response);

    const result = await runTool({
      pluginId: "test-plugin",
      toolName: "detect",
      args: {},
    });

    expect(result.success).toBe(false);
    expect(result.error).toContain("Server error");
  });

  it("returns error when JSON is invalid", async () => {
    // Mock response that throws on first 2 calls, succeeds on 3rd (after retries)
    const badResponse = {
      ok: true,
      status: 200,
      json: async () => {
        throw new Error("invalid json");
      },
    };
    const goodResponse = {
      ok: true,
      status: 200,
      json: async () => ({ result: { success: true } }),
    };
    mockFetch
      .mockResolvedValueOnce(badResponse as unknown as Response)
      .mockResolvedValueOnce(badResponse as unknown as Response)
      .mockResolvedValueOnce(goodResponse as unknown as Response);

    const result = await runTool({
      pluginId: "test-plugin",
      toolName: "detect",
      args: {},
    });

    expect(result.success).toBe(true); // Should succeed after retry
  });

  it("returns error when fetch throws", async () => {
    // Mock fetch to throw on first call, succeed on retry
    const goodResponse = {
      ok: true,
      status: 200,
      json: async () => ({ result: { success: true } }),
    };
    mockFetch
      .mockRejectedValueOnce(new Error("Network error"))
      .mockResolvedValueOnce(goodResponse as unknown as Response);

    const result = await runTool({
      pluginId: "test-plugin",
      toolName: "detect",
      args: {},
    });

    expect(result.success).toBe(true); // Should succeed after retry
  });

  it("handles response without result field", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ data: "some data" }),
    } as Response);

    const result = await runTool({
      pluginId: "test-plugin",
      toolName: "detect",
      args: {},
    });

    expect(result.success).toBe(true);
    expect(result.result).toEqual({ data: "some data" });
  });
});

describe("withRetry", () => {
  it("retries on failure", async () => {
    const fn = vi
      .fn()
      .mockRejectedValueOnce(new Error("fail"))
      .mockResolvedValueOnce("success");

    const result = await withRetry(fn, { maxRetries: 2 });

    expect(result).toBe("success");
    expect(fn).toHaveBeenCalledTimes(2);
  });

  it("throws after max retries exhausted", async () => {
    const fn = vi.fn().mockRejectedValue(new Error("fail"));

    await expect(
      withRetry(fn, { maxRetries: 2 })
    ).rejects.toThrow("fail");

    expect(fn).toHaveBeenCalledTimes(3); // initial + 2 retries
  });

  it("uses exponential backoff", async () => {
    const fn = vi
      .fn()
      .mockRejectedValueOnce(new Error("fail"))
      .mockResolvedValueOnce("success");

    await withRetry(fn, {
      maxRetries: 1,
      baseDelayMs: 100,
      backoffMultiplier: 2,
    });

    expect(fn).toHaveBeenCalledTimes(2);
  });

  it("succeeds on first try when no failure", async () => {
    const fn = vi.fn().mockResolvedValue("success");

    const result = await withRetry(fn);

    expect(result).toBe("success");
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it("respects maxDelayMs cap", async () => {
    const fn = vi
      .fn()
      .mockRejectedValueOnce(new Error("fail"))
      .mockResolvedValueOnce("success");

    await withRetry(fn, {
      maxRetries: 1,
      baseDelayMs: 2000,
      maxDelayMs: 1000,
      backoffMultiplier: 2,
    });

    expect(fn).toHaveBeenCalledTimes(2);
  });
});

describe("withLogging", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("logs before and after function call", async () => {
    const logSpy = vi.spyOn(console, "debug").mockImplementation(() => {});
    const fn = vi.fn().mockResolvedValue("ok");

    const wrapped = withLogging(fn, {
      pluginId: "p",
      toolName: "t",
      endpoint: "/x",
    });

    const result = await wrapped();

    expect(result).toBe("ok");
    expect(logSpy).toHaveBeenCalledWith(
      "🔧 runTool:start",
      expect.objectContaining({ pluginId: "p", toolName: "t", endpoint: "/x" })
    );
    expect(logSpy).toHaveBeenCalledWith(
      "🔧 runTool:success",
      expect.objectContaining({ pluginId: "p", toolName: "t", durationMs: expect.any(Number) })
    );

    logSpy.mockRestore();
  });

  it("logs errors", async () => {
    const errSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    const fn = vi.fn().mockRejectedValue(new Error("boom"));

    const wrapped = withLogging(fn, {
      pluginId: "p",
      toolName: "t",
      endpoint: "/x",
    });

    await expect(wrapped()).rejects.toThrow("boom");

    expect(errSpy).toHaveBeenCalledWith(
      "🔧 runTool:error",
      expect.objectContaining({
        pluginId: "p",
        toolName: "t",
        error: expect.any(Error),
      })
    );

    errSpy.mockRestore();
  });

  it("includes timing information in success log", async () => {
    const logSpy = vi.spyOn(console, "debug").mockImplementation(() => {});
    const fn = vi.fn().mockResolvedValue("ok");

    const wrapped = withLogging(fn, {
      pluginId: "p",
      toolName: "t",
      endpoint: "/x",
    });

    await wrapped();

    const successCall = logSpy.mock.calls.find(
      (call) => call[0] === "🔧 runTool:success"
    );

    expect(successCall).toBeDefined();
    expect(successCall![1]).toHaveProperty("durationMs");
    expect(typeof successCall![1].durationMs).toBe("number");

    logSpy.mockRestore();
  });
});

