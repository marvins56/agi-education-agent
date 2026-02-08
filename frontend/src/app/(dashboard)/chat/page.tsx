"use client";

import { useCallback, useEffect } from "react";
import { SessionSidebar } from "@/components/chat/SessionSidebar";
import { ChatArea } from "@/components/chat/ChatArea";
import { useSessions } from "@/hooks/useSessions";
import { useChat } from "@/hooks/useChat";
import { useModels } from "@/hooks/useModels";

export default function ChatPage() {
  const {
    sessions,
    activeSessionId,
    createSession,
    selectSession,
  } = useSessions();

  const { messages, loading, error, sendMessage, loadHistory, clearMessages } =
    useChat();

  const { selectedProvider, selectedModel } = useModels();

  useEffect(() => {
    if (activeSessionId) {
      loadHistory(activeSessionId);
    } else {
      clearMessages();
    }
  }, [activeSessionId, loadHistory, clearMessages]);

  const handleNewSession = useCallback(async () => {
    await createSession();
    clearMessages();
  }, [createSession, clearMessages]);

  const handleSend = useCallback(
    (content: string) => {
      if (!activeSessionId) return;
      sendMessage(content, activeSessionId, {
        provider: selectedProvider || undefined,
        model: selectedModel || undefined,
      });
    },
    [activeSessionId, sendMessage, selectedProvider, selectedModel]
  );

  return (
    <div className="flex h-full">
      <SessionSidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={selectSession}
        onNewSession={handleNewSession}
      />
      <ChatArea
        messages={messages}
        loading={loading}
        error={error}
        onSend={handleSend}
        hasSession={!!activeSessionId}
        onNewSession={handleNewSession}
      />
    </div>
  );
}
