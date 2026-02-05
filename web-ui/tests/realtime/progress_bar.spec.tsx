/**
 * Phase 10: ProgressBar component test.
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProgressBar } from "@/components/ProgressBar";

describe("ProgressBar", () => {
    it("should render with progress value", async () => {
        const { ProgressBar } = await import("@/components/ProgressBar");
        render(<ProgressBar progress={50} />);
        const progressElement = screen.getByRole("progressbar");
        expect(progressElement).toBeInTheDocument();
    });

    it("should have id progress-bar", async () => {
        const { ProgressBar } = await import("@/components/ProgressBar");
        render(<ProgressBar progress={50} />);
        const element = document.getElementById("progress-bar");
        expect(element).toBeInTheDocument();
    });

    it("should display correct percentage", async () => {
        const { ProgressBar } = await import("@/components/ProgressBar");
        render(<ProgressBar progress={75} showPercentage={true} />);
        expect(screen.getByText("75%")).toBeInTheDocument();
    });

    it("should handle 0% progress", async () => {
        const { ProgressBar } = await import("@/components/ProgressBar");
        render(<ProgressBar progress={0} />);
        expect(screen.getByRole("progressbar")).toBeInTheDocument();
    });

    it("should handle 100% progress", async () => {
        const { ProgressBar } = await import("@/components/ProgressBar");
        render(<ProgressBar progress={100} />);
        expect(screen.getByRole("progressbar")).toBeInTheDocument();
    });

    it("should have different size variants", async () => {
        const smallContainer = render(<ProgressBar progress={50} size="small" />);
        expect(smallContainer.container.querySelector(".progress-bar-small")).toBeInTheDocument();

        const largeContainer = render(<ProgressBar progress={50} size="large" />);
        expect(largeContainer.container.querySelector(".progress-bar-large")).toBeInTheDocument();
    });

    it("should have different variant classes", async () => {
        const defaultContainer = render(<ProgressBar progress={50} variant="default" />);
        expect(defaultContainer.container.querySelector(".progress-bar-default")).toBeInTheDocument();

        const successContainer = render(<ProgressBar progress={50} variant="success" />);
        expect(successContainer.container.querySelector(".progress-bar-success")).toBeInTheDocument();
    });

    it("should accept custom label", async () => {
        const { ProgressBar } = await import("@/components/ProgressBar");
        render(<ProgressBar progress={50} label="Processing" showPercentage={false} />);
        expect(screen.getByText("Processing")).toBeInTheDocument();
    });
});

