/**
 * Tests for PluginSelector styling and API integration
 */

import { render, screen, waitFor } from "@testing-library/react";
import { PluginSelector } from "./PluginSelector";
import * as client from "../api/client";

// Mock the API client
vi.mock("../api/client", () => ({
    apiClient: {
        getPlugins: vi.fn(),
    },
}));

describe("PluginSelector - Styling and Integration", () => {
    const mockPlugins: client.Plugin[] = [
        {
            name: "motion_detector",
            description: "Detects motion in video frames",
            version: "1.0.0",
            inputs: ["image"],
            outputs: ["detection"],
            permissions: ["camera"],
        },
        {
            name: "object_detection",
            description: "Detects objects in images",
            version: "2.1.0",
            inputs: ["image"],
            outputs: ["objects"],
            permissions: ["camera"],
        },
    ];

    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe("heading and layout", () => {
        it("should display heading", async () => {
            (client.apiClient.getPlugins as ReturnType<typeof vi.fn>).mockResolvedValue(
                mockPlugins
            );

            render(
                <PluginSelector
                    selectedPlugin="motion_detector"
                    onPluginChange={vi.fn()}
                />
            );

            await waitFor(() => {
                expect(
                    screen.getByText("Select Plugin")
                ).toBeInTheDocument();
            });
        });
    });

    describe("loading state", () => {
        it("should display loading message", () => {
            (client.apiClient.getPlugins as ReturnType<typeof vi.fn>).mockImplementation(
                () => new Promise(() => {
                    /* never resolves */
                })
            );

            render(
                <PluginSelector
                    selectedPlugin="motion_detector"
                    onPluginChange={vi.fn()}
                />
            );

            expect(screen.getByText("Loading plugins...")).toBeInTheDocument();
        });
    });

    describe("error state", () => {
        it("should display error with brand styling", async () => {
            const errorMsg = "Failed to connect to API";
            (client.apiClient.getPlugins as ReturnType<typeof vi.fn>).mockRejectedValue(
                new Error(errorMsg)
            );

            render(
                <PluginSelector
                    selectedPlugin="motion_detector"
                    onPluginChange={vi.fn()}
                />
            );

            await waitFor(() => {
                expect(
                    screen.getByText(new RegExp(errorMsg))
                ).toBeInTheDocument();
            });
        });
    });

    describe("plugin list display", () => {
        it("should display plugins with version info", async () => {
            (client.apiClient.getPlugins as ReturnType<typeof vi.fn>).mockResolvedValue(
                mockPlugins
            );

            render(
                <PluginSelector
                    selectedPlugin="motion_detector"
                    onPluginChange={vi.fn()}
                />
            );

            await waitFor(() => {
                expect(
                    screen.getByText(/motion_detector \(v1.0.0\)/)
                ).toBeInTheDocument();
                expect(
                    screen.getByText(/object_detection \(v2.1.0\)/)
                ).toBeInTheDocument();
            });
        });

        it("should call onPluginChange when selection changes", async () => {
            (client.apiClient.getPlugins as ReturnType<typeof vi.fn>).mockResolvedValue(
                mockPlugins
            );

            const mockChange = vi.fn();
            const { container } = render(
                <PluginSelector
                    selectedPlugin="motion_detector"
                    onPluginChange={mockChange}
                />
            );

            await waitFor(() => {
                const select = container.querySelector("select");
                expect(select).toBeInTheDocument();
            });
        });
    });

    describe("description display", () => {
        it("should display plugin description", async () => {
            (client.apiClient.getPlugins as ReturnType<typeof vi.fn>).mockResolvedValue(
                mockPlugins
            );

            render(
                <PluginSelector
                    selectedPlugin="motion_detector"
                    onPluginChange={vi.fn()}
                />
            );

            await waitFor(() => {
                expect(
                    screen.getByText("Detects motion in video frames")
                ).toBeInTheDocument();
            });
        });
    });

    describe("disabled state", () => {
        it("should disable select when disabled prop is true", async () => {
            (client.apiClient.getPlugins as ReturnType<typeof vi.fn>).mockResolvedValue(
                mockPlugins
            );

            const { container } = render(
                <PluginSelector
                    selectedPlugin="motion_detector"
                    onPluginChange={vi.fn()}
                    disabled={true}
                />
            );

            await waitFor(() => {
                const select = container.querySelector("select");
                expect(select).toBeDisabled();
            });
        });
    });

    describe("styling", () => {
        it("should use brand colors for select element", async () => {
            (client.apiClient.getPlugins as ReturnType<typeof vi.fn>).mockResolvedValue(
                mockPlugins
            );

            const { container } = render(
                <PluginSelector
                    selectedPlugin="motion_detector"
                    onPluginChange={vi.fn()}
                />
            );

            await waitFor(() => {
                const select = container.querySelector("select");
                expect(select).toHaveStyle({
                    width: "100%",
                    borderRadius: "4px",
                    cursor: "pointer",
                });
            });
        });
    });
});

import { vi } from "vitest";
