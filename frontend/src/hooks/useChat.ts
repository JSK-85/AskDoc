import { useCallback, useState } from "react";
import { queryDocument } from "../lib/api";
import type { Message } from "../types";

let _msgCounter = 0;
function nextId(): string {
  return `msg-${Date.now()}-${++_msgCounter}`;
}

export function useChat(activeDocId: number | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (question: string) => {
      setMessages((prev) => [
        ...prev,
        { id: nextId(), role: "user", content: question },
      ]);
      setLoading(true);
      setError(null);
      try {
        const res = await queryDocument(question, activeDocId ?? undefined);
        setMessages((prev) => [
          ...prev,
          {
            id: nextId(),
            role: "assistant",
            content: res.answer,
            sources: res.sources,
            latency_ms: res.latency_ms,
          },
        ]);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Query failed");
      } finally {
        setLoading(false);
      }
    },
    [activeDocId],
  );

  const clearMessages = useCallback(() => setMessages([]), []);

  return { messages, loading, error, sendMessage, clearMessages };
}
