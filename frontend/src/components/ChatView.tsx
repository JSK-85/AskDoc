import { useEffect, useRef, useState } from "react";
import { ArrowUp } from "lucide-react";
import type { Document } from "@/types";
import { useChat } from "@/hooks/useChat";
import { MessageBubble } from "./MessageBubble";
import { TypingIndicator } from "./TypingIndicator";

interface Props {
  activeDoc: Document | null;
  totalDocs: number;
}

export function ChatView({ activeDoc, totalDocs }: Props) {
  const { messages, loading, error, sendMessage, clearMessages } = useChat(
    activeDoc?.doc_id ?? null,
  );
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    clearMessages();
    setInput("");
  }, [activeDoc?.doc_id, clearMessages]);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, loading]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const q = input.trim();
    if (!q || loading) return;
    sendMessage(q);
    setInput("");
  };

  const title = activeDoc ? activeDoc.filename : "All documents";
  const subtitle = activeDoc
    ? "Ready"
    : `Searching across ${totalDocs} document${totalDocs === 1 ? "" : "s"}`;

  return (
    <div className="flex h-full min-w-0 flex-1 flex-col">
      {/* Header */}
      <div className="px-8 pt-7 pb-5">
        <span className="mb-1 block text-[10px] font-semibold uppercase tracking-[0.18em] text-white/30">
          {activeDoc ? "Asking" : "Current scope"}
        </span>
        <h1 className="truncate text-[19px] font-medium tracking-tight text-foreground">
          {title}
        </h1>
        <p className="mt-1 text-[12px] text-white/40">{subtitle}</p>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-8">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl border border-white/[0.08] bg-white/[0.02]">
              <svg
                className="h-5 w-5 text-white/25"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="1.2"
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
            </div>
            <p className="text-[14px] font-medium tracking-tight text-white/80">
              Ask anything about your document
            </p>
            <p className="mt-1 text-[12px] text-white/40">
              Answers are grounded with precise citations.
            </p>
          </div>
        ) : (
          <div className="mx-auto flex max-w-3xl flex-col gap-5 pb-2">
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}
            {loading && <TypingIndicator />}
            {error && (
              <div className="rounded-xl border border-[color:var(--status-failed)]/30 bg-[color:var(--status-failed)]/10 px-4 py-3 text-xs text-[color:var(--status-failed)]">
                {error}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Composer */}
      <div className="px-8 pb-7 pt-5">
        <form
          onSubmit={submit}
          className="relative mx-auto max-w-3xl"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            placeholder={
              activeDoc
                ? `Ask about ${activeDoc.filename}…`
                : "Ask across all documents…"
            }
            className="h-12 w-full rounded-full border border-white/[0.1] bg-white/[0.03] px-5 pr-14 text-[14px] text-foreground placeholder:text-white/25 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.04)] focus:border-white/20 focus:outline-none focus:ring-1 focus:ring-white/15"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            aria-label="Send"
            className="absolute right-1.5 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full bg-foreground text-background transition-all hover:bg-white/90 disabled:bg-white/10 disabled:text-white/40"
          >
            <ArrowUp className="h-4 w-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
