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

    const selectedPluginData = plugins.find((p) => p.name === selectedPlugin);

    if (loading)
        return (
            <p style={{ color: "var(--text-muted)", margin: 0 }}>
                Loading plugins...
            </p>
        );
    if (error)
        return (
            <p
                style={{
                    color: "var(--accent-red)",
                    backgroundColor: "rgba(220, 53, 69, 0.1)",
                    padding: "8px",
                    borderRadius: "4px",
                    border: "1px solid var(--accent-red)",
                    margin: 0,
                }}
            >
                Error: {error}
            </p>
        );

    return (
        <div>
            <h3>Select Plugin</h3>
            <select
                value={selectedPlugin}
                onChange={(e) => onPluginChange(e.target.value)}
                disabled={disabled}
                style={{
                    width: "100%",
                    padding: "10px 12px",
                    borderRadius: "4px",
                    backgroundColor: disabled
                        ? "var(--bg-hover)"
                        : "var(--bg-tertiary)",
                    color: disabled ? "var(--text-muted)" : "var(--text-secondary)",
                    border: `1px solid ${
                        disabled ? "var(--border-color)" : "var(--border-light)"
                    }`,
                    cursor: disabled ? "not-allowed" : "pointer",
                    fontSize: "13px",
                    fontWeight: 500,
                    transition: "all 0.2s",
                }}
            >
                {plugins.map((plugin) => (
                    <option key={plugin.name} value={plugin.name}>
                        {plugin.name} (v{plugin.version})
                    </option>
                ))}
            </select>
            {selectedPluginData && (
                <div
                    style={{
                        marginTop: "12px",
                        padding: "10px",
                        backgroundColor: "rgba(0, 229, 255, 0.05)",
                        border: "1px solid var(--border-light)",
                        borderRadius: "4px",
                        fontSize: "12px",
                        color: "var(--text-secondary)",
                        lineHeight: 1.6,
                    }}
                >
                    <div
                        style={{
                            marginBottom: "8px",
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                        }}
                    >
                        <div style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                            {selectedPluginData.name}
                        </div>
                        <div
                            style={{
                                fontSize: "11px",
                                color: "var(--text-muted)",
                                fontFamily: "monospace",
                            }}
                        >
                            v{selectedPluginData.version}
                        </div>
                    </div>
                    <p style={{ margin: "0 0 8px 0" }}>
                        {selectedPluginData.description}
                    </p>
                    {selectedPluginData.inputs.length > 0 && (
                        <div style={{ marginBottom: "6px" }}>
                            <div style={{ fontSize: "11px", color: "var(--accent-cyan)" }}>
                                Inputs:
                            </div>
                            <div style={{ fontSize: "11px", marginTop: "2px" }}>
                                {selectedPluginData.inputs.join(", ")}
                            </div>
                        </div>
                    )}
                    {selectedPluginData.outputs.length > 0 && (
                        <div>
                            <div style={{ fontSize: "11px", color: "var(--accent-orange)" }}>
                                Outputs:
                            </div>
                            <div style={{ fontSize: "11px", marginTop: "2px" }}>
                                {selectedPluginData.outputs.join(", ")}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
