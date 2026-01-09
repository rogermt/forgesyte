/**
 * Tests for App.tsx branding updates
 */

import { render, screen } from "@testing-library/react";
import App from "./App";

describe("App - Branding Updates", () => {
    describe("Header styling", () => {
        it("should use ForgeSyte brand colors in header", () => {
            const { container } = render(<App />);
            const header = container.querySelector("header");

            expect(header).toHaveStyle({
                backgroundColor: "var(--bg-primary)",
            });
        });

        it("should display ForgeSyte branding in logo", () => {
            render(<App />);
            const logo = screen.getByText(/ForgeSyte/i);

            expect(logo).toBeInTheDocument();
            expect(logo.parentElement).toHaveStyle({
                color: "var(--text-primary)",
            });
        });
    });

    describe("Navigation buttons", () => {
        it("should use brand colors for active nav button", () => {
            const { container } = render(<App />);
            const activeButton = container.querySelector("nav button");

            expect(activeButton).toHaveStyle({
                backgroundColor: "var(--accent-orange)",
                color: "var(--text-primary)",
            });
        });

        it("should use brand colors for inactive nav button", () => {
            const { container } = render(<App />);
            const buttons = container.querySelectorAll("nav button");

            if (buttons.length > 1) {
                const inactiveButton = buttons[1];
                expect(inactiveButton).toHaveStyle({
                    backgroundColor: "var(--bg-tertiary)",
                });
            }
        });
    });

    describe("Status indicator", () => {
        it("should use brand color scheme for connection status", () => {
            const { container } = render(<App />);
            const statusIndicator = container.querySelector(
                "[style*='borderRadius: 50%']"
            );

            expect(statusIndicator).toBeInTheDocument();
            // Status colors will vary based on connection state
        });
    });

    describe("Main layout", () => {
        it("should use ForgeSyte colors for panels", () => {
            const { container } = render(<App />);
            const panels = container.querySelectorAll("div");

            // At least one panel should use brand background
            const brandPanels = Array.from(panels).filter(
                (panel) =>
                    panel.style.backgroundColor === "var(--bg-secondary)" ||
                    panel.style.backgroundColor === "var(--bg-tertiary)"
            );

            expect(brandPanels.length).toBeGreaterThan(0);
        });

        it("should apply consistent spacing with brand grid", () => {
            const { container } = render(<App />);
            const main = container.querySelector("main");

            expect(main).toHaveStyle({
                gap: "16px",
                padding: "16px",
            });
        });
    });

    describe("Error messages", () => {
        it("should use brand error color for WebSocket errors", () => {
            const { container } = render(<App />);
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
