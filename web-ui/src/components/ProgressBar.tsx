/**
 * Phase 10: Progress Bar Component.
 *
 * Displays job progress as a percentage (0-100).
 * Must have id="progress-bar" for test identification.
 *
 * TODO: Implement the following:
 * - Progress display (0-100%)
 * - Animation transitions
 * - Optional label
 * - Accessibility support
 *
 * Author: Roger
 * Phase: 10
 */



interface ProgressBarProps {
  progress: number;
  max?: number;
  label?: string;
  showPercentage?: boolean;
  size?: 'small' | 'medium' | 'large';
  variant?: 'default' | 'success' | 'warning' | 'error';
}

export function ProgressBar({
  progress,
  max = 100,
  label,
  showPercentage = true,
  size = 'medium',
  variant = 'default',
}: ProgressBarProps) {
  const percentage = Math.min(Math.max((progress / max) * 100, 0), 100);

  const sizeClasses = {
    small: 'progress-bar-small',
    medium: 'progress-bar-medium',
    large: 'progress-bar-large',
  };

  const variantClasses = {
    default: 'progress-bar-default',
    success: 'progress-bar-success',
    warning: 'progress-bar-warning',
    error: 'progress-bar-error',
  };

  return (
    <div
      id="progress-bar"
      className={`progress-bar ${sizeClasses[size]} ${variantClasses[variant]}`}
      role="progressbar"
      aria-valuenow={progress}
      aria-valuemin={0}
      aria-valuemax={max}
      aria-label={label || 'Job progress'}
    >
      <div
        className="progress-bar-fill"
        style={{ width: `${percentage}%` }}
      >
        {showPercentage && (
          <span className="progress-bar-label">
            {Math.round(percentage)}%
          </span>
        )}
      </div>
      {label && !showPercentage && (
        <span className="progress-bar-text">{label}</span>
      )}
    </div>
  );
}

export default ProgressBar;

