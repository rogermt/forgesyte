/**
 * Tests for ConfigPanel
 */

import { render, screen } from "@testing-library/react";
import { ConfigPanel } from "./ConfigPanel";

describe("ConfigPanel", () => {
    it("should render fallback message", () => {
        render(
            <ConfigPanel
                pluginName="motion_detector"
            />
        );

        expect(screen.getByText(/No configuration available for plugin: motion_detector/)).toBeInTheDocument();
    });

    it("should display plugin name in message", () => {
        render(
            <ConfigPanel
                pluginName="ocr"
            />
        );

        expect(screen.getByText(/No configuration available for plugin: ocr/)).toBeInTheDocument();
    });

    // TODO: Add tests for dynamic plugin config loading when UIPluginManager is implemented
});
