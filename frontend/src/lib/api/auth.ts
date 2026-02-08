import { apiClient, setTokens, clearTokens } from "./client";
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  User,
} from "../types/api";

export async function login(data: LoginRequest): Promise<TokenResponse> {
  const res = await apiClient<TokenResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
    skipAuth: true,
  });
  setTokens(res.access_token, res.refresh_token);
  return res;
}

export async function register(data: RegisterRequest): Promise<User> {
  return apiClient<User>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
    skipAuth: true,
  });
}

export async function refresh(refreshToken: string): Promise<TokenResponse> {
  const res = await apiClient<TokenResponse>("/api/v1/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
    skipAuth: true,
  });
  setTokens(res.access_token, res.refresh_token);
  return res;
}

export async function logout(): Promise<void> {
  try {
    await apiClient<void>("/api/v1/auth/logout", { method: "POST" });
  } finally {
    clearTokens();
  }
}

export async function getMe(): Promise<User> {
  return apiClient<User>("/api/v1/auth/me");
}
