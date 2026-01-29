/**
 * Plugin selector component
 *
 * Best Practices Applied:
 * - [BP-1] Controlled component that syncs with parent state
 * - [BP-2] useMemo for expensive computations
 * - [BP-3] useCallback for stable event handlers
 * - [BP-4] Proper loading/error/empty states
 * - [BP-5] Accessible form controls with labels
 *
 * @see https://react.dev/reference/react/useMemo
 * @see https://react.dev/learn/sharing-state-between-components#controlled-and-uncontrolled-components
 */

import { useEffect, useState, useMemo, useCallback, useId } from "react";
import { apiClient, Plugin } from "../api/client";

// ============================================================================
// Types
// ============================================================================

export interface PluginSelectorProps {
  /** Currently selected plugin name */
  selectedPlugin: string;
  /** Callback when plugin selection changes */
  onPluginChange: (pluginName: string) => void;
  /** Whether the selector is disabled (e.g., during streaming) */
  disabled?: boolean;
  /** Optional: Show compact version without description */
  compact?: boolean;
}

// ============================================================================
// Styles (memoized outside component to avoid recreation)
// ============================================================================

const styles = {
  container: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "12px",
  },
  heading: {
    margin: 0,
    fontSize: "14px",
    fontWeight: 600,
    color: "var(--text-primary)",
  },
  label: {
    display: "block",
    marginBottom: "6px",
    fontSize: "12px",
    fontWeight: 500,
    color: "var(--text-secondary)",
  },
  selectBase: {
    width: "100%",
    padding: "10px 12px",
    borderRadius: "4px",
    fontSize: "13px",
    fontWeight: 500,
    transition: "all 0.2s",
    outline: "none",
  },
  loading: {
    color: "var(--text-muted)",
    margin: 0,
    padding: "10px 0",
    fontSize: "13px",
  },
  error: {
    color: "var(--accent-red)",
    backgroundColor: "rgba(220, 53, 69, 0.1)",
    padding: "10px 12px",
    borderRadius: "4px",
    border: "1px solid var(--accent-red)",
    margin: 0,
    fontSize: "13px",
  },
  empty: {
    color: "var(--text-muted)",
    margin: 0,
    padding: "10px 0",
    fontSize: "13px",
  },
  infoBox: {
    padding: "12px",
    backgroundColor: "rgba(0, 229, 255, 0.05)",
    border: "1px solid var(--border-light)",
    borderRadius: "4px",
    fontSize: "12px",
    color: "var(--text-secondary)",
    lineHeight: 1.6,
  },
  infoHeader: {
    marginBottom: "8px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  infoName: {
    fontWeight: 600,
    color: "var(--text-primary)",
  },
  infoVersion: {
    fontSize: "11px",
    color: "var(--text-muted)",
    fontFamily: "monospace",
  },
  infoDescription: {
    margin: "0 0 8px 0",
  },
  infoSection: {
    marginTop: "6px",
  },
  infoLabel: {
    fontSize: "11px",
    marginBottom: "2px",
  },
  infoValue: {
    fontSize: "11px",
    marginTop: "2px",
  },
} as const;

// ============================================================================
// Component
// ============================================================================

export function PluginSelector({
  selectedPlugin,
  onPluginChange,
  disabled = false,
  compact = false,
}: PluginSelectorProps) {
  // Generate unique ID for accessibility
  const selectId = useId();

  // -------------------------------------------------------------------------
  // State
  // -------------------------------------------------------------------------
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // -------------------------------------------------------------------------
  // Load plugins on mount
  // -------------------------------------------------------------------------
  useEffect(() => {
    let cancelled = false;

    const loadPlugins = async () => {
      try {
        setLoading(true);
        setError(null);

        const data = await apiClient.getPlugins();

        if (!cancelled) {
          setPlugins(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load plugins"
          );
          setPlugins([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadPlugins();

    return () => {
      cancelled = true;
    };
  }, []);

  // -------------------------------------------------------------------------
  // [BP-1] CRITICAL FIX: Sync parent state with loaded plugins
  //
  // When plugins load, if the parent's selectedPlugin doesn't match any
  // available plugin, we need to update the parent to match the first
  // available plugin. This prevents the visual/state mismatch bug.
  // -------------------------------------------------------------------------
  useEffect(() => {
    if (loading || plugins.length === 0) {
      return;
    }

    const pluginExists = plugins.some((p) => p.name === selectedPlugin);

    if (!selectedPlugin || !pluginExists) {
      // No plugin selected or selected plugin doesn't exist
      // Auto-select the first available plugin
      console.warn(
        `[PluginSelector] Selected plugin "${selectedPlugin}" not found. ` +
          `Defaulting to "${plugins[0].name}".`
      );
      onPluginChange(plugins[0].name);
    }
  }, [loading, plugins, selectedPlugin, onPluginChange]);

  // -------------------------------------------------------------------------
  // [BP-2] Memoized computed values
  // -------------------------------------------------------------------------
  const selectedPluginData = useMemo(() => {
    return plugins.find((p) => p.name === selectedPlugin) ?? null;
  }, [plugins, selectedPlugin]);

  // [BP-2] Memoized select styles based on disabled state
  const selectStyles = useMemo(
    () => ({
      ...styles.selectBase,
      backgroundColor: disabled ? "var(--bg-hover)" : "var(--bg-tertiary)",
      color: disabled ? "var(--text-muted)" : "var(--text-primary)",
      border: `1px solid ${
        disabled ? "var(--border-color)" : "var(--border-light)"
      }`,
      cursor: disabled ? "not-allowed" : "pointer",
    }),
    [disabled]
  );

  // -------------------------------------------------------------------------
  // [BP-3] Stable event handler
  // -------------------------------------------------------------------------
  const handleChange = useCallback(
    (event: React.ChangeEvent<HTMLSelectElement>) => {
      const newPlugin = event.target.value;
      console.log("[PluginSelector] Selection changed to:", newPlugin);
      onPluginChange(newPlugin);
    },
    [onPluginChange]
  );

  // -------------------------------------------------------------------------
  // Render: Loading State
  // -------------------------------------------------------------------------
  if (loading) {
    return (
      <div style={styles.container}>
        <h3 style={styles.heading}>Select Plugin</h3>
        <p style={styles.loading}>Loading plugins...</p>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Render: Error State
  // -------------------------------------------------------------------------
  if (error) {
    const displayError = error.includes("non-JSON") 
      ? "Server unavailable. Please ensure the server is running and try again."
      : error;
    
    return (
      <div style={styles.container}>
        <h3 style={styles.heading}>Select Plugin</h3>
        <p style={styles.error}>
          <strong>Unable to load plugins:</strong> {displayError}
        </p>
        <button
          onClick={() => window.location.reload()}
          style={{
            padding: "8px 12px",
            backgroundColor: "var(--bg-tertiary)",
            color: "var(--text-primary)",
            border: "1px solid var(--border-light)",
            borderRadius: "4px",
            cursor: "pointer",
            fontSize: "12px",
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Render: Empty State (no plugins available)
  // -------------------------------------------------------------------------
  if (plugins.length === 0) {
    return (
      <div style={styles.container}>
        <h3 style={styles.heading}>Select Plugin</h3>
        <p style={styles.empty}>No plugins available</p>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Render: Main Component
  // -------------------------------------------------------------------------
  return (
    <div style={styles.container}>
      <div>
        <label htmlFor={selectId} style={styles.label}>
          Analysis Plugin
        </label>
        <select
          id={selectId}
          value={selectedPlugin}
          onChange={handleChange}
          disabled={disabled}
          style={selectStyles}
          aria-describedby={selectedPluginData ? `${selectId}-desc` : undefined}
        >
          {plugins.map((plugin) => (
            <option key={plugin.name} value={plugin.name}>
              {plugin.name} (v{plugin.version})
            </option>
          ))}
        </select>
      </div>

      {/* Plugin Info Box - only show if not compact and plugin data exists */}
      {!compact && selectedPluginData && (
        <div
          style={styles.infoBox}
          id={`${selectId}-desc`}
          role="region"
          aria-label={`${selectedPluginData.name} plugin details`}
        >
          <div style={styles.infoHeader}>
            <span style={styles.infoName}>{selectedPluginData.name}</span>
            <span style={styles.infoVersion}>v{selectedPluginData.version}</span>
          </div>

          <p style={styles.infoDescription}>{selectedPluginData.description}</p>

          {selectedPluginData.inputs.length > 0 && (
            <div style={styles.infoSection}>
              <div style={{ ...styles.infoLabel, color: "var(--accent-cyan)" }}>
                Inputs:
              </div>
              <div style={styles.infoValue}>
                {selectedPluginData.inputs.join(", ")}
              </div>
            </div>
          )}

          {selectedPluginData.outputs.length > 0 && (
            <div style={styles.infoSection}>
              <div style={{ ...styles.infoLabel, color: "var(--accent-orange)" }}>
                Outputs:
              </div>
              <div style={styles.infoValue}>
                {selectedPluginData.outputs.join(", ")}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Show warning if streaming is active */}
      {disabled && (
        <p
          style={{
            margin: 0,
            fontSize: "11px",
            color: "var(--text-muted)",
            fontStyle: "italic",
          }}
        >
          Stop streaming to change plugin
        </p>
      )}
    </div>
  );
}

export default PluginSelector;