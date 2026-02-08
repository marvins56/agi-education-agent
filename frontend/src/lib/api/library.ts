import { apiClient, getAccessToken, type SSEProgress } from "./client";
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

/**
 * Upload a file with SSE progress tracking.
 * Uses XMLHttpRequest for upload transfer progress + SSE parsing for processing progress.
 */
export function uploadFileSSE(
  file: File,
  options: { title?: string; subject?: string; grade_level?: string },
  onProgress: (event: SSEProgress) => void
): Promise<void> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append("file", file);

    const params = new URLSearchParams();
    params.set("stream", "true");
    if (options.title) params.set("title", options.title);
    if (options.subject) params.set("subject", options.subject);
    if (options.grade_level) params.set("grade_level", options.grade_level);

    const url = `${API_URL}/api/v1/content/upload?${params}`;

    // Track upload transfer progress (0-48%)
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        const pct = Math.round((e.loaded / e.total) * 48);
        const mb = (e.loaded / (1024 * 1024)).toFixed(1);
        const totalMb = (e.total / (1024 * 1024)).toFixed(1);
        onProgress({
          step: "uploading",
          progress: pct,
          message: `Uploading file... ${mb}MB / ${totalMb}MB`,
        });
      }
    };

    // Track processing progress via SSE events in response body
    let lastParsed = 0;
    xhr.onprogress = () => {
      const text = xhr.responseText.substring(lastParsed);
      lastParsed = xhr.responseText.length;
      const lines = text.split("\n");
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            onProgress(JSON.parse(line.slice(6)) as SSEProgress);
          } catch {
            // skip malformed SSE lines
          }
        }
      }
    };

    xhr.onload = () => {
      // Parse any remaining SSE events
      const remaining = xhr.responseText.substring(lastParsed);
      const lines = remaining.split("\n");
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            onProgress(JSON.parse(line.slice(6)) as SSEProgress);
          } catch {
            // skip
          }
        }
      }

      if (xhr.status >= 200 && xhr.status < 300) {
        resolve();
      } else {
        let detail = `Upload failed with status ${xhr.status}`;
        try {
          const err = JSON.parse(xhr.responseText);
          if (err.detail) detail = err.detail;
        } catch {
          // use default
        }
        reject(new Error(detail));
      }
    };

    xhr.onerror = () => reject(new Error("Upload failed — network error"));

    xhr.open("POST", url);
    const token = getAccessToken();
    if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    // Do NOT set Content-Type — browser sets multipart/form-data with boundary
    xhr.send(formData);
  });
}
