import { apiClient } from "./client";
import type {
  CreateSessionRequest,
  ChatSession,
  MessageRequest,
  MessageResponse,
  ChatHistory,
} from "../types/api";

export async function createSession(
  data: CreateSessionRequest = {}
): Promise<ChatSession> {
  return apiClient<ChatSession>("/api/v1/chat/sessions", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function sendMessage(
  data: MessageRequest
): Promise<MessageResponse> {
  return apiClient<MessageResponse>("/api/v1/chat/message", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getHistory(
  sessionId: string,
  limit = 50
): Promise<ChatHistory> {
  return apiClient<ChatHistory>(
    `/api/v1/chat/history/${sessionId}?limit=${limit}`
  );
}
