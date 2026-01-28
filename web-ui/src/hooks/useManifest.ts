/**
 * useManifest Hook
 * Fetches and caches plugin manifests with TTL-based expiration
 */

import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import type { PluginManifest } from "../types/plugin";

const MANIFEST_CACHE_TTL = 5 * 60 * 1000; // 5 minutes

interface CacheEntry {
    manifest: PluginManifest;
    timestamp: number;
}

const manifestCache = new Map<string, CacheEntry>();

/**
 * Clear the manifest cache (exported for testing purposes)
 */
export function clearManifestCache(): void {
    manifestCache.clear();
}

export function useManifest(pluginId: string | null) {
    const [manifest, setManifest] = useState<PluginManifest | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!pluginId) {
            setManifest(null);
            return;
        }

        const fetchManifest = async () => {
            setLoading(true);
            setError(null);

            try {
                // Check cache first
                const cached = manifestCache.get(pluginId);
                const now = Date.now();

                if (cached && now - cached.timestamp < MANIFEST_CACHE_TTL) {
                    setManifest(cached.manifest);
                    setLoading(false);
                    return;
                }

                // Fetch from API
                const fetchedManifest = await apiClient.getPluginManifest(
                    pluginId
                );

                // Update cache
                manifestCache.set(pluginId, {
                    manifest: fetchedManifest,
                    timestamp: now,
                });

                setManifest(fetchedManifest);
            } catch (err) {
                const message =
                    err instanceof Error ? err.message : "Failed to load manifest";
                setError(message);
                setManifest(null);
            } finally {
                setLoading(false);
            }
        };

        fetchManifest();
    }, [pluginId]);

    const clearCache = (id: string = pluginId!) => {
        manifestCache.delete(id);
    };

    return { manifest, loading, error, clearCache };
}
