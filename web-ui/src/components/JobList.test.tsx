/**
 * Tests for JobList component (Phase 17)
 *
 * Phase 17: JobList is a simple read-only display component
 * Shows job history with status, progress, and metadata
 */

import { render, screen, waitFor } from "@testing-library/react";
import { JobList } from "./JobList";
import * as client from "../api/client";
import { createMockJob } from "../test-utils/factories";
import { vi } from "vitest";

// Mock the API client
vi.mock("../api/client", () => ({
    apiClient: {
        listJobs: vi.fn(),
    },
}));

describe("JobList (Phase 17)", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe("loading state", () => {
        it("should display loading message initially", () => {
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockImplementation(
                () => new Promise(() => {
                    /* never resolves */
                })
            );

            render(<JobList />);
            expect(screen.getByText("Loading jobs...")).toBeInTheDocument();
        });
    });

    describe("error state", () => {
        it("should display error message with brand styling", async () => {
            const errorMsg = "API connection failed";
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockRejectedValue(
                new Error(errorMsg)
            );

            render(<JobList />);

            await waitFor(() => {
                const errorElement = screen.getByText(/Error:/);
                expect(errorElement).toBeInTheDocument();
                expect(errorElement).toHaveStyle({
                    color: "var(--accent-red)",
                });
            });
        });
    });

    describe("empty state", () => {
        it("should display message when no jobs exist", async () => {
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue([]);

            render(<JobList />);

            await waitFor(() => {
                expect(screen.getByText("No jobs yet")).toBeInTheDocument();
            });
        });
    });

    describe("job list display", () => {
        it("should display list of jobs", async () => {
            const mockJobs = [
                createMockJob({ job_id: "job-1", plugin: "plugin-1" }),
                createMockJob({ job_id: "job-2", plugin: "plugin-2" }),
                createMockJob({ job_id: "job-3", plugin: "plugin-3" }),
            ];
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue(mockJobs);

            render(<JobList />);

            await waitFor(() => {
                expect(screen.getByText("Recent Jobs")).toBeInTheDocument();
                expect(screen.getByTestId("job-list-container")).toBeInTheDocument();
                mockJobs.forEach((job) => {
                    expect(screen.getByTestId(`job-item-${job.job_id}`)).toBeInTheDocument();
                    expect(screen.getByText(job.plugin)).toBeInTheDocument();
                });
            });
        });

        it("should display job status with correct styling", async () => {
            const mockJobs = [
                createMockJob({ job_id: "job-1", status: "done" }),
                createMockJob({ job_id: "job-2", status: "error" }),
                createMockJob({ job_id: "job-3", status: "running" }),
            ];
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue(mockJobs);

            render(<JobList />);

            await waitFor(() => {
                expect(screen.getByText("done")).toBeInTheDocument();
                expect(screen.getByText("error")).toBeInTheDocument();
                expect(screen.getByText("running")).toBeInTheDocument();
            });
        });
    });
});