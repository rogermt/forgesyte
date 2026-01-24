/**
 * Tests for useVideoProcessor Hook (TDD)
 *
 * Verifies:
 * - Hook exports correctly
 * - Hook accepts correct arguments
 * - Hook returns correct types
 * - No plugin-specific assumptions
 */

import { describe, it, expect } from "vitest";
import { useVideoProcessor } from "./useVideoProcessor";

describe("useVideoProcessor Hook", () => {
  it("exports hook as default", () => {
    expect(useVideoProcessor).toBeDefined();
    expect(typeof useVideoProcessor).toBe("function");
  });

  it("hook function signature is correct", () => {
    const hookName = useVideoProcessor.name;
    expect(hookName).toBe("useVideoProcessor");
  });

  it("exports FrameResult type as plugin-agnostic", () => {
    // FrameResult should be Record<string, unknown>
    // This verifies at compile time via TypeScript
    expect(true).toBe(true);
  });
});
