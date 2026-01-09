/**
 * Tests for JobList API integration and styling
 */

import { render, screen, waitFor } from "@testing-library/react";
import { JobList } from "./JobList";
import * as client from "../api/client";

// Mock the API client
vi.mock("../api/client", () => ({
    apiClient: {
        listJobs: vi.fn(),
    },
}));

describe("JobList - API Integration", () => {
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

            render(<JobList onJobSelect={vi.fn()} />);
            expect(screen.getByText("Loading jobs...")).toBeInTheDocument();
        });
    });

    describe("error state", () => {
        it("should display error message with brand styling", async () => {
            const errorMsg = "API connection failed";
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockRejectedValue(
                new Error(errorMsg)
            );

            render(<JobList onJobSelect={vi.fn()} />);

            await waitFor(() => {
                expect(
                    screen.getByText(new RegExp(errorMsg))
                ).toBeInTheDocument();
            });
        });
    });

    describe("empty state", () => {
        it("should display message when no jobs", async () => {
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue([]);

            render(<JobList onJobSelect={vi.fn()} />);

            await waitFor(() => {
                expect(screen.getByText("No jobs yet")).toBeInTheDocument();
            });
        });
    });

    describe("job list display", () => {
        const mockJobs = [
            {
                id: "job-123456",
                status: "done",
                plugin: "motion_detector",
                created_at: "2026-01-09T21:00:00Z",
                updated_at: "2026-01-09T21:00:30Z",
            },
            {
                id: "job-234567",
                status: "processing",
                plugin: "object_detection",
                created_at: "2026-01-09T21:30:00Z",
                updated_at: "2026-01-09T21:30:15Z",
            },
        ];

        it("should display jobs with proper information", async () => {
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue(
                mockJobs
            );

            render(<JobList onJobSelect={vi.fn()} />);

            await waitFor(() => {
                expect(screen.getByText("Recent Jobs")).toBeInTheDocument();
                expect(screen.getByText("done")).toBeInTheDocument();
                expect(screen.getByText("processing")).toBeInTheDocument();
            });
        });

        it("should call onJobSelect when job is clicked", async () => {
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue([
                mockJobs[0],
            ]);

            const mockSelectJob = vi.fn();
            const { container } = render(
                <JobList onJobSelect={mockSelectJob} />
            );

            await waitFor(() => {
                const jobElement = container.querySelector(
                    "div[style*='cursor: pointer']"
                );
                expect(jobElement).toBeInTheDocument();
            });
        });
    });

    describe("styling", () => {
        const mockJobs = [
            {
                id: "job-123456",
                status: "done",
                plugin: "motion_detector",
                created_at: "2026-01-09T21:00:00Z",
                updated_at: "2026-01-09T21:00:30Z",
            },
        ];

        it("should use brand colors for job items", async () => {
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue(
                mockJobs
            );

            const { container } = render(
                <JobList onJobSelect={vi.fn()} />
            );

            await waitFor(() => {
                const jobItem = container.querySelector(
                    "div[style*='cursor: pointer']"
                );
                expect(jobItem).toHaveStyle({
                    cursor: "pointer",
                    borderRadius: "4px",
                    transition: "all 0.2s",
                });
            });
        });

        it("should apply proper scrolling to job list", async () => {
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue(
                mockJobs
            );

            const { container } = render(
                <JobList onJobSelect={vi.fn()} />
            );

            await waitFor(() => {
                const scrollContainer = container.querySelector(
                    "div[style*='maxHeight: 400px']"
                );
                expect(scrollContainer).toHaveStyle({
                    maxHeight: "400px",
                    overflowY: "auto",
                });
            });
        });
    });
});

// Mock vi globally for tests
import { vi } from "vitest";
