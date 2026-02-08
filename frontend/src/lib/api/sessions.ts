import { apiClient } from "./client";
import type { SessionListResponse } from "../types/api";

export async function listSessions(): Promise<SessionListResponse> {
  return apiClient<SessionListResponse>("/api/v1/sessions");
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
