/**
 * Tests for ConfigPanel with dynamic plugin config UIs
 */

import { render, screen, waitFor } from "@testing-library/react";
import { ConfigPanel } from "./ConfigPanel";
import { UIPluginManager } from "../plugin-system/uiPluginManager";

vi.mock("../plugin-system/uiPluginManager", () => ({
    UIPluginManager: {
        loadConfigComponent: vi.fn(),
    },
}));

describe("ConfigPanel", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("should render custom config component when available", async () => {
        const CustomConfig = ({ options }: any) => (
            <div>Custom Config: {options.mode}</div>
        );
        (UIPluginManager.loadConfigComponent as any).mockResolvedValue(
            CustomConfig
        );

        render(
            <ConfigPanel
                pluginName="motion_detector"
                options={{ mode: "fast" }}
                onChange={vi.fn()}
            />
        );

        await waitFor(() => {
            expect(screen.getByText("Custom Config: fast")).toBeInTheDocument();
        });
    });

    it("should show fallback when no custom config", async () => {
        (UIPluginManager.loadConfigComponent as any).mockResolvedValue(null);

        render(
            <ConfigPanel
                pluginName="motion_detector"
                options={{}}
                onChange={vi.fn()}
            />
        );

        await waitFor(() => {
            expect(
                screen.getByText(/No configuration available/)
            ).toBeInTheDocument();
        });
    });

    it("should call onChange when config updates", async () => {
        const handleChange = vi.fn();
        const CustomConfig = ({ onChange }: any) => (
            <button onClick={() => onChange({ setting: true })}>Update</button>
        );
        (UIPluginManager.loadConfigComponent as any).mockResolvedValue(
            CustomConfig
        );

        render(
            <ConfigPanel
                pluginName="test"
                options={{}}
                onChange={handleChange}
            />
        );

        await waitFor(() => {
            expect(screen.getByText("Update")).toBeInTheDocument();
        });

        screen.getByText("Update").click();

        await waitFor(() => {
            expect(handleChange).toHaveBeenCalledWith({ setting: true });
        });
    });

    it("should load config for new plugin", async () => {
        const Config1 = () => <div>Config 1</div>;
        const Config2 = () => <div>Config 2</div>;

        (UIPluginManager.loadConfigComponent as any)
            .mockResolvedValueOnce(Config1)
            .mockResolvedValueOnce(Config2);

        const { rerender } = render(
            <ConfigPanel
                pluginName="plugin_1"
                options={{}}
                onChange={vi.fn()}
            />
        );

        await waitFor(() => {
            expect(screen.getByText("Config 1")).toBeInTheDocument();
        });

        rerender(
            <ConfigPanel
                pluginName="plugin_2"
                options={{}}
                onChange={vi.fn()}
            />
        );

        await waitFor(() => {
            expect(screen.getByText("Config 2")).toBeInTheDocument();
        });
    });
});
