/**
 * Tests for PluginHost - dynamic plugin loader
 *
 * Mocks UIPluginManager to test loading, error handling, and prop passing.
 */

import { render, screen, waitFor } from "@testing-library/react";
import type { ComponentType } from "react";
import { PluginHost } from "./PluginHost";
import { UIPluginManager } from "./uiPluginManager";

// Mock the UIPluginManager
vi.mock("./uiPluginManager", () => {
    const mockManager = {
        loadUIComponent: vi.fn(),
    };
    return {
        UIPluginManager: mockManager,
    };
});

describe("PluginHost", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("should load and render a plugin component", async () => {
        const TestComponent: ComponentType = () => <div>Test Plugin</div>;
        (UIPluginManager.loadUIComponent as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(TestComponent);

        render(<PluginHost plugin="test_plugin" />);

        await waitFor(() => {
            expect(screen.getByText("Test Plugin")).toBeInTheDocument();
        });
        expect(UIPluginManager.loadUIComponent).toHaveBeenCalledWith("test_plugin");
    });

    it("should pass props to loaded plugin", async () => {
        const TestComponent: ComponentType<{ message: string }> = ({ message }) => <div>{message}</div>;
        (UIPluginManager.loadUIComponent as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(TestComponent);

        render(
            <PluginHost plugin="test_plugin" props={{ message: "Hello Plugin" }} />
        );

        await waitFor(() => {
            expect(screen.getByText("Hello Plugin")).toBeInTheDocument();
        });
    });

    it("should show loading state while loading plugin", () => {
        (UIPluginManager.loadUIComponent as unknown as ReturnType<typeof vi.fn>).mockImplementation(
            () => new Promise(() => {})
        );

        render(<PluginHost plugin="test_plugin" />);
        expect(screen.getByText("Loading plugin UI…")).toBeInTheDocument();
    });

    it("should handle plugin load error", async () => {
        const error = new Error("Plugin not found");
        (UIPluginManager.loadUIComponent as unknown as ReturnType<typeof vi.fn>).mockRejectedValue(error);

        render(<PluginHost plugin="missing_plugin" />);

        await waitFor(() => {
            expect(
                screen.getByText(/Failed to load plugin "missing_plugin": Plugin not found/)
            ).toBeInTheDocument();
        });
    });

    it("should reload when plugin name changes", async () => {
        const Plugin1: ComponentType = () => <div>Plugin 1</div>;
        const Plugin2: ComponentType = () => <div>Plugin 2</div>;

        (UIPluginManager.loadUIComponent as unknown as ReturnType<typeof vi.fn>)
            .mockResolvedValueOnce(Plugin1)
            .mockResolvedValueOnce(Plugin2);

        const { rerender } = render(<PluginHost plugin="plugin_1" />);

        await waitFor(() => {
            expect(screen.getByText("Plugin 1")).toBeInTheDocument();
        });

        rerender(<PluginHost plugin="plugin_2" />);

        await waitFor(() => {
            expect(screen.getByText("Plugin 2")).toBeInTheDocument();
        });

        expect(UIPluginManager.loadUIComponent).toHaveBeenCalledTimes(2);
    });

    it("should cleanup on unmount", async () => {
        const TestComponent: ComponentType = () => <div>Plugin</div>;
        (UIPluginManager.loadUIComponent as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(TestComponent);

        const { unmount } = render(<PluginHost plugin="test_plugin" />);

        await waitFor(() => {
            expect(screen.getByText("Plugin")).toBeInTheDocument();
        });

        unmount();
        // Should not throw or cause memory leaks
    });
});
