interface ErrorBannerProps {
  title: string;
  message: string;
  showDismiss?: boolean;
  onDismiss?: () => void;
}

export function ErrorBanner({
  title,
  message,
  showDismiss = false,
  onDismiss,
}: ErrorBannerProps) {
  return (
    <div
      style={{
        padding: "12px",
        backgroundColor: "rgba(220, 53, 69, 0.1)",
        border: "1px solid var(--accent-red)",
        borderRadius: "4px",
        color: "var(--accent-red)",
        marginBottom: "12px",
      }}
    >
      <div style={{ fontWeight: 600, marginBottom: "4px" }}>{title}</div>
      <div style={{ fontSize: "13px" }}>{message}</div>
      {showDismiss && onDismiss && (
        <button
          onClick={onDismiss}
          style={{
            marginTop: "8px",
            padding: "4px 8px",
            borderRadius: "4px",
            border: "1px solid var(--accent-red)",
            backgroundColor: "transparent",
            color: "var(--accent-red)",
            cursor: "pointer",
            fontSize: "12px",
          }}
        >
          Dismiss
        </button>
      )}
    </div>
  );
}