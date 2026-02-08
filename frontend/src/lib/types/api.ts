// Auth types
export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Chat types
export interface CreateSessionRequest {
  subject?: string;
  topic?: string;
  mode?: string;
}

export interface ChatSession {
  session_id: string;
  created_at: string;
  mode: string;
  subject?: string;
  topic?: string;
}

export interface MessageRequest {
  content: string;
  session_id: string;
  subject?: string;
  topic?: string;
  provider?: string;
  model?: string;
}

export interface MessageResponse {
  text: string;
  session_id: string;
  sources: string[];
  suggested_actions: string[];
  metadata: Record<string, unknown>;
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
}

export interface ChatHistory {
  messages: ChatMessage[];
}

// Session types
export interface SessionListResponse {
  sessions: ChatSession[];
  total: number;
}

// Model types
export interface ModelProvider {
  provider: string;
  available: boolean;
  models: string[];
  base_url?: string;
}

export interface CurrentModel {
  provider: string;
  model: string;
}

// Generic API error
export interface ApiError {
  detail: string;
}
