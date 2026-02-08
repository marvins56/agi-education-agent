"use client";

import { useEffect, useRef } from "react";
import { MessageSquarePlus } from "lucide-react";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { Spinner } from "@/components/ui/Spinner";
import type { ChatMessage as ChatMessageType } from "@/lib/types/api";

interface ChatAreaProps {
  messages: ChatMessageType[];
  loading: boolean;
  error: string | null;
  onSend: (message: string) => void;
  hasSession: boolean;
  onNewSession: () => void;
}

export function ChatArea({
  messages,
  loading,
  error,
  onSend,
  hasSession,
  onNewSession,
}: ChatAreaProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  if (!hasSession) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 bg-gray-950 p-8">
        <MessageSquarePlus className="h-12 w-12 text-gray-600" />
        <h2 className="text-xl font-semibold text-gray-300">
          Start a conversation
        </h2>
        <p className="max-w-md text-center text-sm text-gray-500">
          Create a new session to begin chatting with your AI tutor. Ask
          questions about any subject and get personalized help.
        </p>
        <button
          onClick={onNewSession}
          className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-500"
        >
          New Session
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col bg-gray-950">
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl">
          {messages.length === 0 && !loading ? (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <p className="text-sm text-gray-500">
                Send a message to start the conversation.
              </p>
            </div>
          ) : (
            messages.map((msg, i) => <ChatMessage key={i} message={msg} />)
          )}

          {loading && (
            <div className="flex items-center gap-3 px-4 py-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gray-700">
                <Spinner size="sm" />
              </div>
              <span className="text-sm text-gray-400">Thinking...</span>
            </div>
          )}

          {error && (
            <div className="mx-4 my-2 rounded-lg border border-red-800 bg-red-900/30 p-3 text-sm text-red-300">
              {error}
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      <ChatInput onSend={onSend} disabled={loading} />
    </div>
  );
}
