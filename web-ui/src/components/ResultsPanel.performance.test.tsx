/**
 * Performance tests for ResultsPanel component
 *
 * These tests ensure the UI doesn't freeze when handling large results
 * (e.g., video_multi jobs with ~1.7MB JSON results).
 *
 * See: https://github.com/rogermt/forgesyte/discussions/349
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { ResultsPanel } from "./ResultsPanel";
import { createMockJob } from "../test-utils/factories";

describe("ResultsPanel performance guards", () => {
  let stringifySpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    stringifySpy = vi.spyOn(JSON, "stringify");
  });

  afterEach(() => {
    stringifySpy.mockRestore();
  });

  describe("video_multi job type", () => {
    it("should NOT stringify huge video_multi results", () => {
      // Simulate a 1MB+ result from video_multi job
      const bigResult = { data: "x".repeat(1_000_000) };

      const job = createMockJob({
        status: "completed",
        job_type: "video_multi",
        results: bigResult,
      });

      render(<ResultsPanel mode="job" job={job} />);

      // For video_multi we should NOT call JSON.stringify on the huge result
      expect(stringifySpy).not.toHaveBeenCalledWith(
        bigResult,
        expect.anything(),
        expect.anything()
      );
    });

    it("should display message for video_multi instead of rendering JSON", () => {
      const bigResult = { data: "x".repeat(1_000_000) };

      const job = createMockJob({
        status: "completed",
        job_type: "video_multi",
        results: bigResult,
      });

      render(<ResultsPanel mode="job" job={job} />);

      // Should show job type in meta info
      const videoMultiElements = screen.getAllByText(/video_multi/);
      expect(videoMultiElements.length).toBeGreaterThanOrEqual(1);

      // Should show message about large result in the pre block
      expect(
        screen.getByText(/too large to render/i)
      ).toBeInTheDocument();
    });
  });

  describe("normal job results", () => {
    it("should stringify normal job results", () => {
      const result = { foo: "bar" };

      const job = createMockJob({
        status: "completed",
        job_type: "image",
        results: result,
      });

      render(<ResultsPanel mode="job" job={job} />);

      // Normal jobs should stringify the result
      expect(stringifySpy).toHaveBeenCalledWith(
        result,
        null,
        2
      );
    });

    it("should use memoization for repeated renders", () => {
      const result = { foo: "bar" };

      const job = createMockJob({
        status: "completed",
        job_type: "image",
        results: result,
      });

      const { rerender } = render(<ResultsPanel mode="job" job={job} />);

      // Clear the spy after initial render
      const initialCallCount = stringifySpy.mock.calls.length;

      // Re-render with same job (result reference unchanged)
      rerender(<ResultsPanel mode="job" job={job} />);

      // Stringify should not be called again for the same result
      // (memoization should prevent re-stringifying)
      expect(stringifySpy.mock.calls.length).toBe(initialCallCount);
    });
  });
});
