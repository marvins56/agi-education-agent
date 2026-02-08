"use client";

import { Plus, MessageSquare } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import type { ChatSession } from "@/lib/types/api";

interface SessionSidebarProps {
  sessions: ChatSession[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
}

export function SessionSidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
}: SessionSidebarProps) {
  return (
    <div className="flex h-full w-64 flex-col border-r border-gray-800 bg-gray-950">
      <div className="p-3">
        <button
          onClick={onNewSession}
          className="flex w-full items-center justify-center gap-2 rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm font-medium text-gray-200 transition-colors hover:bg-gray-700"
        >
          <Plus className="h-4 w-4" />
          New Session
        </button>
      </div>

      <div className="flex-1 space-y-0.5 overflow-y-auto px-3 pb-3">
        {sessions.length === 0 ? (
          <p className="px-3 py-4 text-center text-sm text-gray-500">
            No sessions yet
          </p>
        ) : (
          sessions.map((session) => (
            <button
              key={session.session_id}
              onClick={() => onSelectSession(session.session_id)}
              className={cn(
                "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors",
                activeSessionId === session.session_id
                  ? "bg-gray-800 text-blue-400"
                  : "text-gray-400 hover:bg-gray-900 hover:text-gray-200"
              )}
            >
              <MessageSquare className="h-4 w-4 shrink-0" />
              <span className="truncate">
                {session.subject || session.topic || session.mode || "Chat"}
              </span>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
