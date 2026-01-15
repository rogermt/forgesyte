/**
 * Tests for ResultsPanel with dynamic plugin result renderers
 */

import { render, screen, waitFor } from "@testing-library/react";
import { ResultsPanel } from "./ResultsPanel";
import { UIPluginManager } from "../plugin-system/uiPluginManager";
import { createMockFrameResult } from "../test-utils/factories";

vi.mock("../plugin-system/uiPluginManager", () => ({
    UIPluginManager: {
        loadResultComponent: vi.fn(),
    },
}));

describe("ResultsPanel - Plugin Renderers", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("should render custom result component when available", async () => {
        const CustomRenderer = ({ result }: any) => (
            <div>Custom: {result.frame_id}</div>
        );
        (UIPluginManager.loadResultComponent as any).mockResolvedValue(
            CustomRenderer
        );

        const result = createMockFrameResult();
        render(
            <ResultsPanel pluginName="motion_detector" result={result} />
        );

        await waitFor(() => {
            expect(screen.getByText(/Custom:/)).toBeInTheDocument();
        });
    });

    it("should show fallback JSON when no custom renderer", async () => {
        (UIPluginManager.loadResultComponent as any).mockResolvedValue(null);

        const result = createMockFrameResult();
        const { container } = render(
            <ResultsPanel pluginName="motion_detector" result={result} />
        );

        await waitFor(() => {
            const pre = container.querySelector("pre");
            expect(pre).toBeInTheDocument();
        });
    });

    it("should show no results message when result is null", async () => {
        (UIPluginManager.loadResultComponent as any).mockResolvedValue(null);

        render(<ResultsPanel pluginName="motion_detector" result={null} />);

        expect(screen.getByText("No results yet.")).toBeInTheDocument();
    });

    it("should load renderer for new plugin", async () => {
        const Renderer1 = () => <div>Renderer 1</div>;
        const Renderer2 = () => <div>Renderer 2</div>;

        (UIPluginManager.loadResultComponent as any)
            .mockResolvedValueOnce(Renderer1)
            .mockResolvedValueOnce(Renderer2);

        const result = createMockFrameResult();
        const { rerender } = render(
            <ResultsPanel pluginName="plugin_1" result={result} />
        );

        await waitFor(() => {
            expect(screen.getByText("Renderer 1")).toBeInTheDocument();
        });

        rerender(
            <ResultsPanel pluginName="plugin_2" result={result} />
        );

        await waitFor(() => {
            expect(screen.getByText("Renderer 2")).toBeInTheDocument();
        });
    });
});
