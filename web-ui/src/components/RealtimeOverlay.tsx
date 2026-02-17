/**
 * Phase 10: Real-Time Overlay Component (LEGACY)
 *
 * Container component for displaying real-time updates during job execution.
 * Integrates ProgressBar and PluginInspector components.
 *
 * LEGACY: This component is from Phase 10 and is maintained for backward compatibility.
 * Phase 17 streaming uses RealtimeStreamingOverlay instead.
 *
 * Author: Roger
 * Phase: 10
 */

import { useRealtimeContext } from '../realtime/RealtimeContext';
import { ProgressBar } from '@/components/ProgressBar';
import { PluginInspector } from '@/components/PluginInspector';

export interface RealtimeOverlayProps {
  jobId: string;
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
   const { state } = useRealtimeContext();

   return (
     <div className="realtime-overlay" data-testid="realtime-overlay" data-job-id={jobId}>
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
          {state.warnings.map((warning: string, index: number) => (
            <div key={index} className="warning-message">
              ⚠️ {warning}
            </div>
          ))}
        </div>
      )}

      {/* Errors */}
      {showErrors && state.errors.length > 0 && (
        <div className="realtime-errors">
          {state.errors.map((error: string, index: number) => (
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
