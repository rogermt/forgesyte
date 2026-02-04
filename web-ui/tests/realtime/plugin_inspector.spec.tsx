/**
 * Phase 10: PluginInspector component test.
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { PluginInspector } from "@/components/PluginInspector";

describe("PluginInspector", () => {
    it("should render with id plugin-inspector", async () => {
        const { PluginInspector } = await import("@/components/PluginInspector");
        render(<PluginInspector pluginTimings={{}} />);
        const element = document.getElementById("plugin-inspector");
        expect(element).toBeInTheDocument();
    });

    it("should show empty state when no plugins", async () => {
        const { PluginInspector } = await import("@/components/PluginInspector");
        render(<PluginInspector pluginTimings={{}} />);
        expect(screen.getByText("No plugin data available")).toBeInTheDocument();
    });

    it("should display plugin timings", async () => {
        const { PluginInspector } = await import("@/components/PluginInspector");
        const timings = { "test-plugin": 45.5 };
        render(<PluginInspector pluginTimings={timings} />);
        expect(screen.getByText("test-plugin")).toBeInTheDocument();
        expect(screen.getByText("45.5ms")).toBeInTheDocument();
    });

    it("should display multiple plugins", async () => {
        const { PluginInspector } = await import("@/components/PluginInspector");
        const timings = {
            "plugin-1": 100.0,
            "plugin-2": 50.5,
            "plugin-3": 75.25,
        };
        render(<PluginInspector pluginTimings={timings} />);
        expect(screen.getByText("plugin-1")).toBeInTheDocument();
        expect(screen.getByText("plugin-2")).toBeInTheDocument();
        expect(screen.getByText("plugin-3")).toBeInTheDocument();
    });

    it("should indicate current plugin as active", async () => {
        const { PluginInspector } = await import("@/components/PluginInspector");
        const timings = { "test-plugin": 45.5 };
        render(
            <PluginInspector
                pluginTimings={timings}
                currentPlugin="test-plugin"
            />
        );
        // Look for the bullet character with Running text
        expect(screen.getByText(/● Running/)).toBeInTheDocument();
    });

    it("should not show running indicator for non-current plugin", async () => {
        const { PluginInspector } = await import("@/components/PluginInspector");
        const timings = { "plugin-1": 100.0, "plugin-2": 50.5 };
        render(
            <PluginInspector
                pluginTimings={timings}
                currentPlugin="plugin-1"
            />
        );
        // Only plugin-1 should show running, plugin-2 should not
        const plugin2Element = screen.getByText("plugin-2");
        expect(plugin2Element.parentElement).not.toHaveTextContent(/● Running/);
    });

    it("should display plugin metadata", async () => {
        const { PluginInspector } = await import("@/components/PluginInspector");
        const timings = { "test-plugin": 45.5 };
        const metadata = {
            "test-plugin": {
                name: "Test Plugin",
                version: "1.0.0",
            },
        };
        render(
            <PluginInspector
                pluginTimings={timings}
                metadata={metadata}
            />
        );
        expect(screen.getByText("Test Plugin")).toBeInTheDocument();
        expect(screen.getByText("v1.0.0")).toBeInTheDocument();
    });
});

