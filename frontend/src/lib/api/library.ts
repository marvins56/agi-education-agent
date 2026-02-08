import { apiClient } from "./client";
import type {
  DocumentItem,
  DocumentListResponse,
  SearchResponse,
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
