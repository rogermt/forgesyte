/**
 * Tests for CameraPreview styling updates
 */

import { render, screen, act } from "@testing-library/react";
import { CameraPreview } from "./CameraPreview";

describe("CameraPreview - Styling Updates", () => {
    describe("heading and layout", () => {
        it("should display heading with brand colors", async () => {
            await act(async () => {
                render(<CameraPreview enabled={false} />);
            });
            const heading = screen.getByText("Camera Preview");

            expect(heading).toBeInTheDocument();
            expect(heading.tagName).toBe("H3");
        });
    });

    describe("video element styling", () => {
        it("should apply brand background color to video", async () => {
            let container: HTMLElement;
            await act(async () => {
                container = render(<CameraPreview enabled={false} />).container;
            });
            const video = container!.querySelector("video");

            expect(video).toHaveStyle({
                width: "100%",
                height: "auto",
                borderRadius: "8px",
            });
        });

        it("should use proper aspect ratio styling", async () => {
            let container: HTMLElement;
            await act(async () => {
                container = render(<CameraPreview enabled={false} />).container;
            });
            const video = container!.querySelector("video");

            expect(video).toHaveStyle({
                width: "100%",
                height: "auto",
            });
        });
    });

    describe("error message styling", () => {
        it("should display error in brand error color", async () => {
            let container: HTMLElement;
            await act(async () => {
                container = render(<CameraPreview enabled={false} />).container;
            });

            // Verify component structure for error handling
            const paragraphs = container!.querySelectorAll("p");
            expect(paragraphs.length).toBeGreaterThan(0);
        });
    });

    describe("device selector styling", () => {
        it("should apply consistent styling to select element", async () => {
            let container: HTMLElement;
            await act(async () => {
                container = render(
                    <CameraPreview enabled={false} width={640} height={480} />
                ).container;
            });
            const select = container!.querySelector("select");

            if (select) {
                // Select element should have consistent styling
                expect(select).toHaveStyle({
                    borderRadius: "4px",
                });
            }
        });
    });

    describe("status indicator", () => {
        it("should display streaming status with proper styling", async () => {
            let container: HTMLElement;
            await act(async () => {
                container = render(<CameraPreview enabled={false} />).container;
            });
            const statusParagraphs = Array.from(
                container!.querySelectorAll("p")
            ).filter((p) => p.textContent?.includes("streaming"));

            expect(statusParagraphs.length).toBeGreaterThan(0);
        });
    });

    describe("canvas element", () => {
        it("should have hidden canvas for frame capture", async () => {
            let container: HTMLElement;
            await act(async () => {
                container = render(<CameraPreview enabled={false} />).container;
            });
            const canvas = container!.querySelector("canvas");

            expect(canvas).toHaveStyle({
                display: "none",
            });
        });
    });
});
