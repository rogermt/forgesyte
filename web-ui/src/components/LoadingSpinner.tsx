/**
 * Loading Spinner Component
 * 
 * Displays a loading indicator with optional message.
 * Uses the status role for accessibility.
 * 
 * Phase 9: UI Controls
 */



// ============================================================================
// Types
// ============================================================================

export interface LoadingSpinnerProps {
  /** Optional message to display below the spinner */
  message?: string;
  /** Size of the spinner */
  size?: 'small' | 'medium' | 'large';
}

// ============================================================================
// Component
// ============================================================================

export function LoadingSpinner({ message = 'Loading...', size = 'medium' }: LoadingSpinnerProps) {
  const spinnerSize = SIZE_MAP[size];

  return (
    <div 
      style={styles.container} 
      role="status" 
      aria-live="polite"
      aria-busy="true"
    >
      <svg
        style={styles.spinner}
        width={spinnerSize}
        height={spinnerSize}
        viewBox="0 0 50 50"
        aria-hidden="true"
      >
        <circle
          style={styles.circle}
          cx="25"
          cy="25"
          r="20"
          fill="none"
          strokeWidth="4"
        />
      </svg>
      {message && (
        <p style={styles.message}>{message}</p>
      )}
    </div>
  );
}

// ============================================================================
// Constants & Styles
// ============================================================================

const SIZE_MAP = {
  small: 20,
  medium: 40,
  large: 60,
};

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px',
    padding: '16px',
  },
  spinner: {
    animation: 'spin 1s linear infinite',
  },
  circle: {
    stroke: 'var(--accent-cyan)',
    strokeLinecap: 'round',
    strokeDasharray: '30, 200',
    strokeDashoffset: '0',
  },
  message: {
    margin: 0,
    fontSize: '14px',
    color: 'var(--text-secondary)',
  },
} as const;

// Add keyframe animation via style tag
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;
if (typeof document !== 'undefined') {
  document.head.appendChild(styleSheet);
}

export default LoadingSpinner;

