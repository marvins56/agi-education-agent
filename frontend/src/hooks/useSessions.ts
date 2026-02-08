"use client";

import { useCallback, useEffect, useState } from "react";
import * as sessionsApi from "@/lib/api/sessions";
import * as chatApi from "@/lib/api/chat";
import type { ChatSession } from "@/lib/types/api";

export function useSessions() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const loadSessions = useCallback(async () => {
    setLoading(true);
    try {
      const data = await sessionsApi.listSessions();
      setSessions(data.sessions);
    } catch {
      // silently fail — sessions may not be available yet
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const createSession = useCallback(
    async (options?: { subject?: string; topic?: string; mode?: string }) => {
      const session = await chatApi.createSession(options || {});
      setSessions((prev) => [session, ...prev]);
      setActiveSessionId(session.session_id);
      return session;
    },
    []
  );

  const selectSession = useCallback((sessionId: string) => {
    setActiveSessionId(sessionId);
  }, []);

  return {
    sessions,
    activeSessionId,
    loading,
    loadSessions,
    createSession,
    selectSession,
  };
}
