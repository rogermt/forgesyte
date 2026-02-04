/**
 * Phase 10: Real-Time Overlay Component.
 *
 * Container component for displaying real-time updates during job execution.
 * Integrates ProgressBar and PluginInspector components.
 *
 * TODO: Implement the following:
 * - Real-time progress display
 * - Plugin timing visualization
 * - Warning/error notifications
 * - Connection status indicator
 *
 * Author: Roger
 * Phase: 10
 */

import React from 'react';
import { useRealtime } from '@/realtime/RealtimeContext';
import { ProgressBar } from '@/components/ProgressBar';
import { PluginInspector } from '@/components/PluginInspector';

interface RealtimeOverlayProps {
  jobId?: string;
  showProgressBar?: boolean;
  showPluginInspector?: boolean;
  showWarnings?: boolean;
  showErrors?: boolean;
}

export function RealtimeOverlay({
  jobId,
  showProgressBar = true,
  showPluginInspector = true,
  showWarnings = true,
  showErrors = true,
}: RealtimeOverlayProps) {
  const { state, connect, disconnect } = useRealtime();

  return (
    <div className="realtime-overlay" data-testid="realtime-overlay">
      {/* Connection Status */}
      <div className="realtime-status">
        <span className={`connection-status ${state.isConnected ? 'connected' : 'disconnected'}`}>
          {state.isConnected ? '● Connected' : '○ Disconnected'}
        </span>
      </div>

      {/* Progress Bar */}
      {showProgressBar && state.progress !== null && (
        <ProgressBar progress={state.progress} />
      )}

      {/* Plugin Inspector */}
      {showPluginInspector && (
        <PluginInspector
          pluginTimings={state.pluginTimings}
          currentPlugin={state.currentPlugin}
        />
      )}

      {/* Warnings */}
      {showWarnings && state.warnings.length > 0 && (
        <div className="realtime-warnings">
          {state.warnings.map((warning, index) => (
            <div key={index} className="warning-message">
              ⚠️ {warning}
            </div>
          ))}
        </div>
      )}

      {/* Errors */}
      {showErrors && state.errors.length > 0 && (
        <div className="realtime-errors">
          {state.errors.map((error, index) => (
            <div key={index} className="error-message">
              ❌ {error}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default RealtimeOverlay;

