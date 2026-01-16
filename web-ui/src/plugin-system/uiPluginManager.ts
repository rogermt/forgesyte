/**
 * UI Plugin Manager
 *
 * Dynamically loads UI plugins from the forgesyte-plugins repo.
 * Each plugin must contain a plugin.json manifest describing its UI components.
 */

import React from "react";

export interface UIPluginManifest {
    name: string;
    version: string;
    description?: string;
    ui: {
        entry: string;              // main UI component
        configComponent?: string;   // optional config UI
        resultComponent?: string;   // optional result renderer
    };
}

type ComponentModule = {
    default: React.ComponentType<Record<string, unknown>> | (() => React.ReactNode);
};

class UIPluginManagerClass {
    private componentCache: Map<string, ComponentModule['default']> = new Map();
    private manifestCache: Map<string, UIPluginManifest> = new Map();

    /**
     * Load plugin manifest from forgesyte-plugins repo
     */
    async loadManifest(pluginName: string): Promise<UIPluginManifest> {
        if (this.manifestCache.has(pluginName)) {
            return this.manifestCache.get(pluginName)!;
        }

        const module = await this.dynamicImport(`${pluginName}/plugin.json`);
        const manifest = (module.default || module) as unknown as UIPluginManifest;
        this.manifestCache.set(pluginName, manifest);
        return manifest;
    }

    /**
     * Load the main UI component for a plugin
     */
    async loadUIComponent(pluginName: string): Promise<ComponentModule['default']> {
        const cacheKey = `ui-component:${pluginName}`;
        if (this.componentCache.has(cacheKey)) {
            return this.componentCache.get(cacheKey)!;
        }

        const manifest = await this.loadManifest(pluginName);
        const module = await this.dynamicImport(
            `${pluginName}/${manifest.ui.entry}`
        );

        const result = (module.default || module) as unknown as ComponentModule['default'];
        this.componentCache.set(cacheKey, result);
        return result;
    }

    /**
     * Load optional config component
     */
    async loadConfigComponent(pluginName: string): Promise<ComponentModule['default'] | null> {
        const cacheKey = `config-component:${pluginName}`;
        if (this.componentCache.has(cacheKey)) {
            const cached = this.componentCache.get(cacheKey);
            return cached || null;
        }

        const manifest = await this.loadManifest(pluginName);

        if (!manifest.ui.configComponent) {
            this.componentCache.set(cacheKey, null as unknown as ComponentModule['default']);
            return null;
        }

        const module = await this.dynamicImport(
            `${pluginName}/${manifest.ui.configComponent}`
        );

        const result = (module.default || module) as unknown as ComponentModule['default'];
        this.componentCache.set(cacheKey, result);
        return result;
    }

    /**
     * Load optional result renderer
     */
    async loadResultComponent(pluginName: string): Promise<ComponentModule['default'] | null> {
        const cacheKey = `result-component:${pluginName}`;
        if (this.componentCache.has(cacheKey)) {
            const cached = this.componentCache.get(cacheKey);
            return cached || null;
        }

        const manifest = await this.loadManifest(pluginName);

        if (!manifest.ui.resultComponent) {
            this.componentCache.set(cacheKey, null as unknown as ComponentModule['default']);
            return null;
        }

        const module = await this.dynamicImport(
            `${pluginName}/${manifest.ui.resultComponent}`
        );

        const result = (module.default || module) as unknown as ComponentModule['default'];
        this.componentCache.set(cacheKey, result);
        return result;
    }

    /**
     * Dynamic import with proper path resolution
     * This is extracted to a separate method to allow easy mocking in tests
     */
    async dynamicImport(pluginPath: string): Promise<Record<string, unknown>> {
        return import(/* @vite-ignore */ `../../../forgesyte-plugins/${pluginPath}`);
    }

    /**
     * Clear all caches (used for testing)
     */
    clearCache(): void {
        this.componentCache.clear();
        this.manifestCache.clear();
    }

    /**
     * Get manifest cache (used for testing)
     */
    getManifestCache(): Map<string, UIPluginManifest> {
        return this.manifestCache;
    }

    /**
     * Get component cache (used for testing)
     */
    getComponentCache(): Map<string, ComponentModule['default']> {
        return this.componentCache;
    }
}

// Export singleton instance
export const UIPluginManager = new UIPluginManagerClass();
