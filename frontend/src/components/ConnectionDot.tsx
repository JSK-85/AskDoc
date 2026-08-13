interface Props {
  online: boolean | null;
}

export function ConnectionDot({ online }: Props) {
  const color =
    online === null
      ? "var(--status-pending)"
      : online
        ? "var(--status-done)"
        : "var(--status-failed)";
  const label =
    online === null ? "Connecting" : online ? "Connected" : "Offline";

  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <span
        className="relative flex h-2 w-2"
        aria-label={label}
        title={label}
      >
        <span
          className="absolute inset-0 rounded-full opacity-50"
          style={{
            background: color,
            filter: `blur(4px)`,
          }}
        />
        <span
          className="relative inline-flex h-2 w-2 rounded-full"
          style={{ background: color }}
        />
      </span>
      <span className="hidden sm:inline">{label}</span>
    </div>
  );
}
