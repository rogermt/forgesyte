/**
 * Error Banner Component
 * 
 * Displays error messages in a prominent banner.
 * 
 * Phase 9: UI Controls
 */

import { useCallback } from 'react';

// ============================================================================
// Types
// ============================================================================

export interface ErrorBannerProps {
  /** Error message to display */
  message: string;
  /** Optional title for the error */
  title?: string;
  /** Callback when dismiss button is clicked */
  onDismiss?: () => void;
  /** Whether to show the dismiss button */
  showDismiss?: boolean;
}

// ============================================================================
// Component
// ============================================================================

export function ErrorBanner({
  message,
  title = 'Error',
  onDismiss,
  showDismiss = true,
}: ErrorBannerProps) {
  const handleDismiss = useCallback(() => {
    if (onDismiss) {
      onDismiss();
    }
  }, [onDismiss]);

  return (
    <div style={styles.container} role="alert" aria-live="assertive">
      <div style={styles.header}>
        <span style={styles.icon} aria-hidden="true">
          ⚠
        </span>
        <strong style={styles.title}>{title}</strong>
        {showDismiss && (
          <button
            style={styles.dismissButton}
            onClick={handleDismiss}
            aria-label="Dismiss error"
          >
            ×
          </button>
        )}
      </div>
      <p style={styles.message}>{message}</p>
    </div>
  );
}

// ============================================================================
// Styles
// ============================================================================

const styles = {
  container: {
    padding: '12px 16px',
    backgroundColor: 'rgba(220, 53, 69, 0.1)',
    border: '1px solid var(--accent-red)',
    borderRadius: '6px',
    margin: '8px 0',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '6px',
  },
  icon: {
    fontSize: '16px',
    color: 'var(--accent-red)',
  },
  title: {
    fontSize: '14px',
    fontWeight: 600,
    color: 'var(--accent-red)',
    flex: 1,
  },
  dismissButton: {
    background: 'transparent',
    border: 'none',
    color: 'var(--accent-red)',
    fontSize: '20px',
    cursor: 'pointer',
    padding: '0 4px',
    lineHeight: 1,
    opacity: 0.7,
    transition: 'opacity 0.2s',
  },
  message: {
    margin: 0,
    fontSize: '13px',
    color: 'var(--text-primary)',
    lineHeight: 1.5,
  },
} as const;

export default ErrorBanner;

