import { useState } from "react";
import { validateApiKey, setApiKey } from "@/lib/api";

interface Props {
  onAuthenticated: () => void;
}

export function AuthGate({ onAuthenticated }: Props) {
  const [key, setKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = key.trim();
    if (!trimmed) return;

    setLoading(true);
    setError(null);

    const valid = await validateApiKey(trimmed);
    if (valid) {
      setApiKey(trimmed);
      onAuthenticated();
    } else {
      setError("Invalid Unique Identifier. Check the identifier and try again.");
    }
    setLoading(false);
  };

  return (
    <div className="flex h-screen w-screen items-center justify-center bg-[color:var(--shell)]">
      <div className="w-full max-w-sm px-6">
        {/* Logo */}
        <div className="mb-8 flex flex-col items-center gap-3">
          <div className="relative h-8 w-8">
            <div className="absolute inset-0 rounded-lg bg-foreground" />
            <div className="absolute inset-[7px] rounded-[3px] bg-[color:var(--shell)]" />
          </div>
          <div className="text-center">
            <h1 className="text-[15px] font-semibold tracking-tight text-foreground">
              AskDoc
            </h1>
            <p className="mt-1 text-[11px] text-white/40">
              Enter your Unique Identifier to continue
            </p>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="password"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            disabled={loading}
            placeholder="Paste your Unique Identifier…"
            autoFocus
            className="h-11 w-full rounded-xl border border-white/[0.1] bg-white/[0.03] px-4 text-[13px] text-foreground placeholder:text-white/25 focus:border-white/20 focus:outline-none focus:ring-1 focus:ring-white/15"
          />

          {error && (
            <p className="rounded-lg bg-[color:var(--status-failed)]/10 px-3 py-2 text-[12px] text-[color:var(--status-failed)]">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading || !key.trim()}
            className="w-full rounded-full bg-foreground py-2.5 text-[13px] font-semibold text-background transition-colors hover:bg-white/90 active:bg-white/80 disabled:bg-white/10 disabled:text-white/40"
          >
            {loading ? "Verifying…" : "Continue"}
          </button>
        </form>

        <p className="mt-6 text-center text-[10px] leading-relaxed text-white/25">
          Your identifier is stored in session memory only and cleared when you close
          the tab.
        </p>
      </div>
    </div>
  );
}
