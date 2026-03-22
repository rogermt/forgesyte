/**
 * Performance tests for ResultsPanel component
 *
 * v0.16.1: Removed JSON frame results - only summary is displayed.
 * Download button uses result_url for full JSON download.
 *
 * These tests ensure the UI doesn't freeze when handling large results
 * (e.g., video jobs with ~1.7MB JSON results).
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

    describe("Summary display", () => {
        it("should NOT have inline results field in job", () => {
            // v0.16.1: Jobs show summary only, download button for full JSON
            const job = createMockJob({
                status: "completed",
                job_type: "video",
                result_url: "/v1/jobs/test-job/result",
                summary: { frame_count: 1000, detection_count: 5000 },
            });

            render(<ResultsPanel mode="job" job={job} />);

            // Should display summary (small JSON)
            expect(screen.getByText(/Summary/)).toBeInTheDocument();

            // Should have download button
            expect(screen.getByText(/Download Full JSON/)).toBeInTheDocument();
        });

        it("should NOT stringify large results - uses download button instead", () => {
            // Large video job - results downloaded via button, not loaded into memory
            const summary = {
                frame_count: 10000,
                detection_count: 50000,
                classes: ["player", "ball", "referee"],
            };

            const job = createMockJob({
                status: "completed",
                job_type: "video",
                result_url: "/v1/jobs/test-job/result",
                summary,
            });

            render(<ResultsPanel mode="job" job={job} />);

            // Should only stringify the small summary, not large results
            expect(stringifySpy).toHaveBeenCalledWith(summary, null, 2);

            // Verify no calls with objects larger than the summary
            const calls = stringifySpy.mock.calls;
            calls.forEach(([arg]) => {
                if (typeof arg === "object" && arg !== null) {
                    const size = JSON.stringify(arg).length;
                    expect(size).toBeLessThan(1000); // Summary should be small
                }
            });
        });

        it("should display summary without loading full results", () => {
            const job = createMockJob({
                status: "completed",
                job_type: "video_multi",
                result_url: "/v1/jobs/test-job/result",
                summary: {
                    frame_count: 5000,
                    detection_count: 25000,
                    classes: ["person", "car", "bicycle"],
                },
            });

            render(<ResultsPanel mode="job" job={job} />);

            // Summary should be visible immediately
            expect(screen.getByText(/frame_count/)).toBeInTheDocument();
            expect(screen.getByText(/5000/)).toBeInTheDocument();
            expect(screen.getByText(/detection_count/)).toBeInTheDocument();
            expect(screen.getByText(/25000/)).toBeInTheDocument();
        });

        it("should show download button for result_url", () => {
            const job = createMockJob({
                job_id: "video-123",
                status: "completed",
                job_type: "video",
                result_url: "/v1/jobs/video-123/result",
                summary: { frame_count: 100 },
            });

            render(<ResultsPanel mode="job" job={job} />);

            // Download button should be rendered
            expect(screen.getByText(/Download Full JSON/)).toBeInTheDocument();
        });

        it("should show 'No result available' when no result_url or summary", () => {
            const job = createMockJob({
                status: "completed",
                result_url: undefined,
                summary: undefined,
            });

            render(<ResultsPanel mode="job" job={job} />);

            expect(screen.getByText(/No result available/)).toBeInTheDocument();
        });
    });

    describe("Summary rendering", () => {
        it("should stringify summary for display", () => {
            const summary = {
                frame_count: 100,
                detection_count: 200,
                classes: ["a", "b"],
            };

            const job = createMockJob({
                status: "completed",
                job_type: "video",
                result_url: "/v1/jobs/test-job/result",
                summary,
            });

            render(<ResultsPanel mode="job" job={job} />);

            // Summary is a small object, safe to stringify
            expect(stringifySpy).toHaveBeenCalledWith(summary, null, 2);
        });

        it("should handle missing summary gracefully", () => {
            const job = createMockJob({
                status: "completed",
                job_type: "video",
                result_url: "/v1/jobs/test-job/result",
                summary: undefined,
            });

            render(<ResultsPanel mode="job" job={job} />);

            // Should still show download button
            expect(screen.getByText(/Download Full JSON/)).toBeInTheDocument();
        });
    });
});
