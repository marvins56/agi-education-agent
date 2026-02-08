import { apiClient, getAccessToken } from "./client";
import type {
  DocumentItem,
  DocumentListResponse,
  SearchResponse,
  UploadFileResponse,
  UploadUrlRequest,
  UploadUrlResponse,
} from "../types/api";

export async function listDocuments(
  page = 1,
  pageSize = 20
): Promise<DocumentListResponse> {
  return apiClient<DocumentListResponse>(
    `/api/v1/content/documents?page=${page}&page_size=${pageSize}`
  );
}

export async function getDocument(id: string): Promise<DocumentItem> {
  return apiClient<DocumentItem>(`/api/v1/content/documents/${id}`);
}

export async function searchContent(
  query: string,
  subject?: string,
  limit = 5
): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  if (subject) params.set("subject", subject);
  return apiClient<SearchResponse>(`/api/v1/content/search?${params}`);
}

export async function deleteDocument(id: string): Promise<void> {
  await apiClient(`/api/v1/content/documents/${id}`, { method: "DELETE" });
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function uploadFile(
  file: File,
  options?: { title?: string; subject?: string; grade_level?: string }
): Promise<UploadFileResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const params = new URLSearchParams();
  if (options?.title) params.set("title", options.title);
  if (options?.subject) params.set("subject", options.subject);
  if (options?.grade_level) params.set("grade_level", options.grade_level);

  const token = getAccessToken();
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_URL}/api/v1/content/upload?${params}`, {
    method: "POST",
    headers,
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function uploadUrl(
  data: UploadUrlRequest
): Promise<UploadUrlResponse> {
  return apiClient<UploadUrlResponse>("/api/v1/content/upload-url", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
