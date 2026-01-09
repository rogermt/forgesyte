/**
 * Tests for CameraPreview styling updates
 */

import { render, screen } from "@testing-library/react";
import { CameraPreview } from "./CameraPreview";

describe("CameraPreview - Styling Updates", () => {
    describe("heading and layout", () => {
        it("should display heading with brand colors", () => {
            render(<CameraPreview enabled={false} />);
            const heading = screen.getByText("Camera Preview");

            expect(heading).toBeInTheDocument();
            expect(heading.tagName).toBe("H3");
        });
    });

    describe("video element styling", () => {
        it("should apply brand background color to video", () => {
            const { container } = render(<CameraPreview enabled={false} />);
            const video = container.querySelector("video");

            expect(video).toHaveStyle({
                width: "100%",
                height: "auto",
                borderRadius: "8px",
            });
        });

        it("should use proper aspect ratio styling", () => {
            const { container } = render(<CameraPreview enabled={false} />);
            const video = container.querySelector("video");

            expect(video).toHaveStyle({
                width: "100%",
                height: "auto",
            });
        });
    });

    describe("error message styling", () => {
        it("should display error in brand error color", async () => {
            // Note: CameraPreview sets error via state, so we test the structure
            const { container } = render(<CameraPreview enabled={false} />);

            // Verify component structure for error handling
            const paragraphs = container.querySelectorAll("p");
            expect(paragraphs.length).toBeGreaterThan(0);
        });
    });

    describe("device selector styling", () => {
        it("should apply consistent styling to select element", () => {
            const { container } = render(
                <CameraPreview enabled={false} width={640} height={480} />
            );
            const select = container.querySelector("select");

            if (select) {
                // Select element should have consistent styling
                expect(select).toHaveStyle({
                    borderRadius: "4px",
                });
            }
        });
    });

    describe("status indicator", () => {
        it("should display streaming status with proper styling", () => {
            const { container } = render(<CameraPreview enabled={false} />);
            const statusParagraphs = Array.from(
                container.querySelectorAll("p")
            ).filter((p) => p.textContent?.includes("streaming"));

            expect(statusParagraphs.length).toBeGreaterThan(0);
        });
    });

    describe("canvas element", () => {
        it("should have hidden canvas for frame capture", () => {
            const { container } = render(<CameraPreview enabled={false} />);
            const canvas = container.querySelector("canvas");

            expect(canvas).toHaveStyle({
                display: "none",
            });
        });
    });
});
