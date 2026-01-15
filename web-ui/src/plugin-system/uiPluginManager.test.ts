import { describe, it, expect, vi, beforeEach } from "vitest";
import { UIPluginManager } from "./uiPluginManager";

describe("UIPluginManager", () => {
    beforeEach(() => {
        // Reset caches before each test
        // @ts-expect-error - Accessing internal method for testing
        UIPluginManager.clearCache();
    });

    // ---------------------------------------------------------
    // 1. Manifest Loading
    // ---------------------------------------------------------
    it("loads plugin manifest from correct path", async () => {
        const mockManifest = {
            name: "ocr",
            version: "1.0.0",
            ui: { entry: "ResultRenderer.tsx" },
        };

        // Mock the dynamicImport method
        // @ts-expect-error - Mocking internal method for testing
        UIPluginManager.dynamicImport = vi.fn().mockResolvedValue({
            default: mockManifest,
        });

        const manifest = await UIPluginManager.loadManifest("ocr");

        expect(manifest.name).toBe("ocr");
        expect(manifest.ui.entry).toBe("ResultRenderer.tsx");
    });

    it("caches manifest after first load", async () => {
        const mockManifest = {
            name: "ocr",
            version: "1.0.0",
            ui: { entry: "ResultRenderer.tsx" },
        };

        const mockImport = vi.fn().mockResolvedValue({ default: mockManifest });

        // @ts-expect-error - Mocking internal method for testing
        UIPluginManager.dynamicImport = mockImport;

        await UIPluginManager.loadManifest("ocr");
        await UIPluginManager.loadManifest("ocr");

        // Should only call import once due to caching
        expect(mockImport).toHaveBeenCalledTimes(1);
    });

    // ---------------------------------------------------------
    // 2. UI Component Loading
    // ---------------------------------------------------------
    it("loads main UI component from manifest entry", async () => {
        const mockManifest = {
            name: "ocr",
            version: "1.0.0",
            ui: { entry: "ResultRenderer.tsx" },
        };

        const mockComponent = (): string => "OCR Renderer";

        const dynamicImportMock = vi.fn((pluginPath: string) => {
            if (pluginPath.includes("plugin.json")) {
                return Promise.resolve({ default: mockManifest });
            }
            return Promise.resolve({ default: mockComponent });
        });

        // @ts-expect-error - Mocking internal method for testing
        UIPluginManager.dynamicImport = dynamicImportMock;

        const component = await UIPluginManager.loadUIComponent("ocr");

        expect(component).toBe(mockComponent);
    });

    it("caches UI component after first load", async () => {
        const mockManifest = {
            name: "ocr",
            version: "1.0.0",
            ui: { entry: "ResultRenderer.tsx" },
        };

        const mockComponent = (): string => "OCR Renderer";

        let callCount = 0;
        const dynamicImportMock = vi.fn((pluginPath: string) => {
            if (pluginPath.includes("plugin.json")) {
                return Promise.resolve({ default: mockManifest });
            }
            callCount++;
            return Promise.resolve({ default: mockComponent });
        });

        // @ts-expect-error - Mocking internal method for testing
        UIPluginManager.dynamicImport = dynamicImportMock;

        await UIPluginManager.loadUIComponent("ocr");
        await UIPluginManager.loadUIComponent("ocr");

        // Component should only be imported once due to caching
        expect(callCount).toBe(1);
    });

    // ---------------------------------------------------------
    // 3. Config Component Loading
    // ---------------------------------------------------------
    it("loads config component when defined", async () => {
        const mockManifest = {
            name: "ocr",
            version: "1.0.0",
            ui: {
                entry: "ResultRenderer.tsx",
                configComponent: "ConfigForm.tsx",
            },
        };

        const mockConfig = (): string => "Config UI";

        const dynamicImportMock = vi.fn((pluginPath: string) => {
            if (pluginPath.includes("plugin.json")) {
                return Promise.resolve({ default: mockManifest });
            }
            return Promise.resolve({ default: mockConfig });
        });

        // @ts-expect-error - Mocking internal method for testing
        UIPluginManager.dynamicImport = dynamicImportMock;

        const config = await UIPluginManager.loadConfigComponent("ocr");

        expect(config).toBe(mockConfig);
    });

    it("returns null when config component is not defined", async () => {
        const mockManifest = {
            name: "motion_detector",
            version: "1.0.0",
            ui: { entry: "ResultRenderer.tsx" },
        };

        const dynamicImportMock = vi.fn(() => {
            return Promise.resolve({ default: mockManifest });
        });

        // @ts-expect-error - Mocking internal method for testing
        UIPluginManager.dynamicImport = dynamicImportMock;

        const config = await UIPluginManager.loadConfigComponent(
            "motion_detector"
        );

        expect(config).toBeNull();
    });

    // ---------------------------------------------------------
    // 4. Result Component Loading
    // ---------------------------------------------------------
    it("loads result renderer when defined", async () => {
        const mockManifest = {
            name: "motion_detector",
            version: "1.0.0",
            ui: {
                entry: "ResultRenderer.tsx",
                resultComponent: "ResultRenderer.tsx",
            },
        };

        const mockRenderer = (): string => "Motion Renderer";

        const dynamicImportMock = vi.fn((pluginPath: string) => {
            if (pluginPath.includes("plugin.json")) {
                return Promise.resolve({ default: mockManifest });
            }
            return Promise.resolve({ default: mockRenderer });
        });

        // @ts-expect-error - Mocking internal method for testing
        UIPluginManager.dynamicImport = dynamicImportMock;

        const renderer = await UIPluginManager.loadResultComponent(
            "motion_detector"
        );

        expect(renderer).toBe(mockRenderer);
    });

    it("returns null when result renderer is not defined", async () => {
        const mockManifest = {
            name: "plugin_selector",
            version: "1.0.0",
            ui: { entry: "PluginSelector.tsx" },
        };

        const dynamicImportMock = vi.fn(() => {
            return Promise.resolve({ default: mockManifest });
        });

        // @ts-expect-error - Mocking internal method for testing
        UIPluginManager.dynamicImport = dynamicImportMock;

        const renderer = await UIPluginManager.loadResultComponent(
            "plugin_selector"
        );

        expect(renderer).toBeNull();
    });
});
