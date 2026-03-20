/**
 * Performance tests for ResultsPanel component
 *
 * Clean Break (Issue #350): No more inline results.
 * All results are loaded via ArtifactViewer with pagination.
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

// Mock ArtifactViewer component
// Discussion #352: ArtifactViewer now receives jobId (required) and resultUrl (optional)
vi.mock("./ArtifactViewer", () => ({
    ArtifactViewer: ({ jobId, resultUrl }: { jobId: string; resultUrl?: string }) => (
        <div
            data-testid="artifact-viewer"
            data-job-id={jobId}
            data-result-url={resultUrl || ""}
        >
            ArtifactViewer: jobId={jobId}
        </div>
    ),
}));

describe("ResultsPanel performance guards", () => {
    let stringifySpy: ReturnType<typeof vi.spyOn>;

    beforeEach(() => {
        stringifySpy = vi.spyOn(JSON, "stringify");
    });

    afterEach(() => {
        stringifySpy.mockRestore();
    });

    describe("Clean Break - Artifact Pattern", () => {
        it("should NOT have inline results field in job", () => {
            // Clean Break: Jobs no longer have inline results
            const job = createMockJob({
                status: "completed",
                job_type: "video",
                result_url: "/v1/jobs/test-job/result",
                summary: { frame_count: 1000, detection_count: 5000 },
            });

            render(<ResultsPanel mode="job" job={job} />);

            // Should display summary (small JSON)
            expect(screen.getByText(/Summary/)).toBeInTheDocument();

            // Should use ArtifactViewer for results
            expect(screen.getByTestId("artifact-viewer")).toBeInTheDocument();
        });

        it("should NOT stringify large results - uses pagination instead", () => {
            // Large video job - results are paginated, not loaded into memory
            const job = createMockJob({
                status: "completed",
                job_type: "video",
                result_url: "/v1/jobs/test-job/result",
                summary: {
                    frame_count: 10000,
                    detection_count: 50000,
                    classes: ["player", "ball", "referee"],
                },
            });

            render(<ResultsPanel mode="job" job={job} />);

            // Should only stringify the small summary
            // NOT a huge result object
            const bigResult = { data: "x".repeat(1_000_000) };
            expect(stringifySpy).not.toHaveBeenCalledWith(
                bigResult,
                expect.anything(),
                expect.anything()
            );
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

        it("should use ArtifactViewer for result_url", () => {
            const job = createMockJob({
                job_id: "video-123",
                status: "completed",
                job_type: "video",
                result_url: "/v1/jobs/video-123/result",
                summary: { frame_count: 100 },
            });

            render(<ResultsPanel mode="job" job={job} />);

            // ArtifactViewer should be rendered
            const artifactViewer = screen.getByTestId("artifact-viewer");
            expect(artifactViewer).toBeInTheDocument();
            // Discussion #352: Should pass jobId and resultUrl
            expect(artifactViewer).toHaveAttribute(
                "data-job-id",
                "video-123"
            );
            expect(artifactViewer).toHaveAttribute(
                "data-result-url",
                "/v1/jobs/video-123/result"
            );
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

            // Should still render ArtifactViewer
            expect(screen.getByTestId("artifact-viewer")).toBeInTheDocument();
        });
    });
});