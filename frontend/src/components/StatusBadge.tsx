import type { DocStatus } from "@/types";

const map: Record<DocStatus, { label: string; color: string; pulse?: boolean }> = {
  pending: { label: "Pending", color: "var(--status-pending)" },
  ingesting: { label: "Indexing", color: "var(--status-ingesting)", pulse: true },
  done: { label: "Ready", color: "var(--status-done)" },
  failed: { label: "Failed", color: "var(--status-failed)" },
};

export function StatusBadge({ status }: { status: DocStatus }) {
  const s = map[status];
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-medium tracking-wide uppercase"
      style={{
        color: s.color,
        background: `color-mix(in oklab, ${s.color} 14%, transparent)`,
        border: `1px solid color-mix(in oklab, ${s.color} 24%, transparent)`,
      }}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${s.pulse ? "animate-pulse" : ""}`}
        style={{ background: s.color, boxShadow: `0 0 8px ${s.color}` }}
      />
      {s.label}
    </span>
  );
}
