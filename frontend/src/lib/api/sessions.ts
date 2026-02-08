import { apiClient } from "./client";
import type { ChatSession, SessionListResponse } from "../types/api";

interface RawSession {
  id?: string;
  session_id?: string;
  student_id?: string;
  mode?: string;
  subject?: string;
  topic?: string;
  started_at?: string;
  ended_at?: string | null;
  [key: string]: unknown;
}

function normalizeSession(raw: RawSession): ChatSession {
  return {
    session_id: raw.session_id || raw.id || "",
    created_at: (raw.started_at as string) || "",
    mode: raw.mode || "tutoring",
    subject: raw.subject as string | undefined,
    topic: raw.topic as string | undefined,
  };
}

export async function listSessions(): Promise<SessionListResponse> {
  const data = await apiClient<{ sessions: RawSession[]; total: number }>("/api/v1/sessions");
  return {
    sessions: data.sessions.map(normalizeSession),
    total: data.total,
  };
}

export async function endSession(sessionId: string): Promise<void> {
  return apiClient<void>(`/api/v1/sessions/${sessionId}/end`, {
    method: "POST",
  });
}

export async function resumeSession(sessionId: string): Promise<void> {
  return apiClient<void>(`/api/v1/sessions/${sessionId}/resume`, {
    method: "POST",
  });
}
