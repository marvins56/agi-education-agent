"use client";

import { useCallback, useState } from "react";
import * as chatApi from "@/lib/api/chat";
import type { ChatMessage, MessageResponse } from "@/lib/types/api";

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadHistory = useCallback(async (sessionId: string) => {
    try {
      const data = await chatApi.getHistory(sessionId);
      setMessages(data.messages);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load history");
    }
  }, []);

  const sendMessage = useCallback(
    async (
      content: string,
      sessionId: string,
      options?: { provider?: string; model?: string }
    ): Promise<MessageResponse | null> => {
      setError(null);
      setLoading(true);

      const userMsg: ChatMessage = {
        role: "user",
        content,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);

      try {
        const response = await chatApi.sendMessage({
          content,
          session_id: sessionId,
          provider: options?.provider,
          model: options?.model,
        });

        const assistantMsg: ChatMessage = {
          role: "assistant",
          content: response.text,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
        return response;
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to send message"
        );
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return { messages, loading, error, sendMessage, loadHistory, clearMessages };
}
