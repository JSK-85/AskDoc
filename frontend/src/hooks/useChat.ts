import { useCallback, useState } from "react";
import { queryDocumentStream } from "../lib/api";
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
      const userMsgId = nextId();
      const assistantMsgId = nextId();
      const startTime = Date.now();

      setMessages((prev) => [
        ...prev,
        { id: userMsgId, role: "user", content: question },
        { id: assistantMsgId, role: "assistant", content: "", latency_ms: 0 },
      ]);
      setLoading(true);
      setError(null);
      
      try {
        await queryDocumentStream(
          question,
          activeDocId ?? undefined,
          (sources) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId ? { ...m, sources } : m
              )
            );
          },
          (textDelta) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId
                  ? { ...m, content: m.content + textDelta, latency_ms: Date.now() - startTime }
                  : m
              )
            );
          }
        );
      } catch (e) {
        setError(e instanceof Error ? e.message : "Query failed");
        setMessages((prev) => prev.filter((m) => m.id !== assistantMsgId));
      } finally {
        setLoading(false);
      }
    },
    [activeDocId],
  );

  const clearMessages = useCallback(() => setMessages([]), []);

  return { messages, loading, error, sendMessage, clearMessages };
}
