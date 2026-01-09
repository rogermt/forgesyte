/**
 * Plugin selector component
 */

import React, { useEffect, useState } from "react";
import { apiClient, Plugin } from "../api/client";

export interface PluginSelectorProps {
    selectedPlugin: string;
    onPluginChange: (pluginName: string) => void;
    disabled?: boolean;
}

export function PluginSelector({
    selectedPlugin,
    onPluginChange,
    disabled = false,
}: PluginSelectorProps) {
    const [plugins, setPlugins] = useState<Plugin[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadPlugins = async () => {
            try {
                const data = await apiClient.getPlugins();
                setPlugins(data);
                setError(null);
            } catch (err) {
                setError(
                    err instanceof Error ? err.message : "Failed to load plugins"
                );
                setPlugins([]);
            } finally {
                setLoading(false);
            }
        };

        loadPlugins();
    }, []);

    if (loading) return <p>Loading plugins...</p>;
    if (error) return <p style={{ color: "#dc3545" }}>Error: {error}</p>;

    return (
        <div>
            <h3>Select Plugin</h3>
            <select
                value={selectedPlugin}
                onChange={(e) => onPluginChange(e.target.value)}
                disabled={disabled}
                style={{
                    width: "100%",
                    padding: "8px",
                    borderRadius: "4px",
                    backgroundColor: disabled ? "#666" : "#2a2a3e",
                    color: "#fff",
                    border: "1px solid #444",
                    cursor: disabled ? "not-allowed" : "pointer",
                }}
            >
                {plugins.map((plugin) => (
                    <option key={plugin.name} value={plugin.name}>
                        {plugin.name} (v{plugin.version})
                    </option>
                ))}
            </select>
            {plugins.find((p) => p.name === selectedPlugin) && (
                <div style={{ marginTop: "12px", fontSize: "13px", color: "#aaa" }}>
                    <p>
                        {
                            plugins.find((p) => p.name === selectedPlugin)
                                ?.description
                        }
                    </p>
                </div>
            )}
        </div>
    );
}
