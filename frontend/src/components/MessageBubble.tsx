import { useState } from "react";
import { ChevronDown } from "lucide-react";
import ReactMarkdown from "react-markdown";
import type { Message } from "@/types";

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const [open, setOpen] = useState(false);

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[78%] rounded-2xl rounded-br-md bg-foreground px-4 py-2.5 text-[13px] text-background">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-[82%] space-y-2.5">
        <div className="surface rounded-2xl rounded-bl-md px-4 py-3 text-[13px] leading-relaxed text-foreground/95 markdown-body">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>

        <div className="flex items-center gap-2 px-1">
          {message.sources && message.sources.length > 0 && (
            <button
              onClick={() => setOpen((v) => !v)}
              className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[10px] font-medium uppercase tracking-wider text-white/55 transition-colors hover:text-foreground"
            >
              {message.sources.length} source
              {message.sources.length === 1 ? "" : "s"}
              <ChevronDown
                className={`h-3 w-3 transition-transform ${
                  open ? "rotate-180" : ""
                }`}
              />
            </button>
          )}
          {typeof message.latency_ms === "number" && (
            <span className="rounded-full border border-white/10 bg-white/[0.02] px-2.5 py-1 font-mono text-[10px] tabular-nums text-white/45">
              {(message.latency_ms / 1000).toFixed(2)}s
            </span>
          )}
        </div>

        {open && message.sources && (
          <div className="space-y-2">
            {message.sources.map((s, i) => (
              <div
                key={i}
                className="surface-inset rounded-xl px-3 py-2.5 text-[12px] text-foreground/80"
              >
                <div className="mb-1 flex items-center justify-between text-[10px] uppercase tracking-wider text-white/40">
                  <span>Page {s.page}</span>
                  <span className="font-mono">doc #{s.doc_id}</span>
                </div>
                <p className="leading-relaxed text-foreground/85">
                  {s.excerpt}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
