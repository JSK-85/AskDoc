import { CheckCircle2, FileText, Loader2, MessageCircle, XCircle } from "lucide-react";
import type { DocStatus } from "@/types";

type State = "idle" | "uploading" | DocStatus;

interface Props {
  status: State;
  filename: string | null;
  chunkCount: number;
  error: string | null;
  onReset: () => void;
  onChat?: () => void;
}

const stages: { key: State; label: string }[] = [
  { key: "uploading", label: "Uploading" },
  { key: "pending", label: "Queued" },
  { key: "ingesting", label: "Indexing" },
  { key: "done", label: "Ready" },
];

function stageIndex(s: State) {
  return stages.findIndex((x) => x.key === s);
}

export function UploadProgress({
  status,
  filename,
  chunkCount,
  error,
  onReset,
  onChat,
}: Props) {
  const idx = stageIndex(status);
  const failed = status === "failed";

  return (
    <div className="flex h-full w-full items-center justify-center p-10">
      <div className="w-full max-w-md rounded-2xl border border-white/[0.08] bg-white/[0.02] p-7">
        <div className="flex items-start gap-4">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-white/[0.08] bg-white/[0.03]">
            {failed ? (
              <XCircle className="h-5 w-5 text-[color:var(--status-failed)]" />
            ) : status === "done" ? (
              <CheckCircle2 className="h-5 w-5 text-[color:var(--status-done)]" />
            ) : (
              <FileText className="h-5 w-5 opacity-80" />
            )}
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-foreground">
              {filename ?? "Document"}
            </p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              {failed
                ? "Something went wrong"
                : status === "done"
                  ? "Indexed · Ready to chat"
                  : status === "ingesting"
                    ? "Indexing document…"
                    : status === "pending"
                      ? "Waiting for the indexer"
                      : "Uploading to server"}
            </p>
          </div>
          {!failed && status !== "done" && (
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          )}
        </div>

        <div className="mt-7">
          <div className="relative h-1 w-full overflow-hidden rounded-full bg-white/[0.06]">
            <div
              className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-white/70 to-white/30 transition-all duration-500"
              style={{
                width: failed
                  ? "100%"
                  : `${Math.max(8, ((idx + 1) / stages.length) * 100)}%`,
                background: failed
                  ? "color-mix(in oklab, var(--status-failed) 70%, transparent)"
                  : undefined,
              }}
            />
          </div>
          <div className="mt-3 grid grid-cols-4 gap-2 text-[10px] uppercase tracking-wider text-muted-foreground">
            {stages.map((s, i) => (
              <span
                key={s.key}
                className={
                  i <= idx && !failed
                    ? "text-foreground/90"
                    : "text-muted-foreground/60"
                }
              >
                {s.label}
              </span>
            ))}
          </div>
        </div>

        {error && (
          <div className="mt-6 rounded-xl border border-[color:var(--status-failed)]/30 bg-[color:var(--status-failed)]/10 px-4 py-3 text-xs text-[color:var(--status-failed)]">
            {error}
          </div>
        )}

        {(failed || status === "done") && (
          <div className="mt-6 flex justify-end gap-3">
            <button
              onClick={onReset}
              className="rounded-full border border-white/[0.12] bg-black px-4 py-2 text-[12px] font-semibold text-white/80 transition-colors hover:border-white/20 hover:text-white"
            >
              Upload another
            </button>
            {status === "done" && onChat && (
              <button
                onClick={onChat}
                className="flex items-center gap-1.5 rounded-full bg-foreground px-4 py-2 text-[12px] font-semibold text-background transition-colors hover:bg-white/90"
              >
                <MessageCircle className="h-3.5 w-3.5" />
                Chat
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
