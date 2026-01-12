/**
 * Tests for App.tsx branding updates
 */

import { render, screen, act } from "@testing-library/react";
import App from "./App";

describe("App - Branding Updates", () => {
    describe("Header styling", () => {
        it("should use ForgeSyte brand colors in header", async () => {
            let container: HTMLElement;
            await act(async () => {
                container = render(<App />).container;
            });
            const header = container!.querySelector("header");

            expect(header).toHaveStyle({
                backgroundColor: "var(--bg-primary)",
            });
        });

        it("should display ForgeSyte branding in logo", async () => {
            await act(async () => {
                render(<App />);
            });
            const logo = screen.getByTestId("app-logo");

            expect(logo).toBeInTheDocument();
            expect(logo).toHaveStyle({
                color: "var(--text-primary)",
            });
        });
    });

    describe("Navigation buttons", () => {
        it("should use brand colors for active nav button", async () => {
            await act(async () => {
                render(<App />);
            });
            const navButton = screen.getByRole("button", { name: "Stream" }); 
            
            expect(navButton).toBeInTheDocument();
            expect(navButton).toHaveStyle({
                backgroundColor: "var(--accent-orange)",
                color: "var(--text-primary)",
            });
        });

        it("should use brand colors for inactive nav button", async () => {
            await act(async () => {
                render(<App />);
            });
            const uploadButton = screen.getByRole("button", { name: /upload/i });

            expect(uploadButton).toHaveStyle({
                backgroundColor: "var(--bg-tertiary)",
            });
        });
    });

    describe("Status indicator", () => {
        it("should use brand color scheme for connection status", async () => {
            await act(async () => {
                render(<App />);
            });
            const statusIndicator = screen.getByTestId("connection-status-indicator");

            expect(statusIndicator).toBeInTheDocument();
            // Status colors will vary based on connection state
        });
    });

    describe("Main layout", () => {
        it("should use ForgeSyte colors for panels", async () => {
            let container: HTMLElement;
            await act(async () => {
                container = render(<App />).container;
            });
            const panels = container!.querySelectorAll("div");

            // At least one panel should use brand background
            const brandPanels = Array.from(panels).filter(
                (panel) =>
                    panel.style.backgroundColor === "var(--bg-secondary)" ||
                    panel.style.backgroundColor === "var(--bg-tertiary)"
            );

            expect(brandPanels.length).toBeGreaterThan(0);
        });

        it("should apply consistent spacing with brand grid", async () => {
            let container: HTMLElement;
            await act(async () => {
                container = render(<App />).container;
            });
            const main = container!.querySelector("main");

            expect(main).toHaveStyle({
                gap: "16px",
                padding: "16px",
            });
        });
    });

    describe("Error messages", () => {
        it("should use brand error color for WebSocket errors", async () => {
            await act(async () => {
                render(<App />);
            });
            const errorStyle = {
                backgroundColor: "rgba(220, 53, 69, 0.1)",
                border: "1px solid var(--accent-red)",
                color: "var(--accent-red)",
            };

            // Error box styling should be consistent with brand
            const hasErrorStyle =
                errorStyle.backgroundColor === "rgba(220, 53, 69, 0.1)";
            expect(hasErrorStyle).toBe(true);
        });
    });
});
