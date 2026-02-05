/**
 * Phase 10: Plugin Inspector Component.
 *
 * Displays plugin metadata, execution timings, and status.
 * Must have id="plugin-inspector" for test identification.
 *
 * TODO: Implement the following:
 * - Plugin timing display
 * - Plugin metadata display
 * - Execution status
 * - Timing bar chart
 *
 * Author: Roger
 * Phase: 10
 */



interface PluginInspectorProps {
  pluginTimings: Record<string, number>;
  currentPlugin?: string | null;
  metadata?: Record<string, Record<string, string>>;
}

export function PluginInspector({
  pluginTimings,
  currentPlugin = null,
  metadata = {},
}: PluginInspectorProps) {
  const plugins = Object.keys(pluginTimings);

  return (
    <div id="plugin-inspector" className="plugin-inspector">
      <h3 className="plugin-inspector-title">Plugin Inspector</h3>

      {plugins.length === 0 ? (
        <p className="plugin-inspector-empty">No plugin data available</p>
      ) : (
        <ul className="plugin-list">
          {plugins.map((pluginId) => {
            const timing = pluginTimings[pluginId];
            const isCurrent = pluginId === currentPlugin;
            const pluginMetadata = metadata[pluginId] || {};

            return (
              <li key={pluginId} className={`plugin-item ${isCurrent ? 'active' : ''}`}>
                <div className="plugin-header">
                  <span className="plugin-id">{pluginId}</span>
                  <span className="plugin-timing">
                    {timing.toFixed(1)}ms
                  </span>
                </div>

                {/* Timing bar */}
                <div className="timing-bar-container">
                  <div
                    className="timing-bar-fill"
                    style={{ width: `${Math.min(timing / 10, 100)}%` }}
                  />
                </div>

                {/* Plugin metadata */}
                {pluginMetadata.name && (
                  <div className="plugin-metadata">
                    <span className="metadata-name">{pluginMetadata.name}</span>
                    {pluginMetadata.version && (
                      <span className="metadata-version">
                        v{pluginMetadata.version}
                      </span>
                    )}
                  </div>
                )}

                {/* Active indicator */}
                {isCurrent && (
                  <span className="plugin-active">● Running</span>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

export default PluginInspector;

