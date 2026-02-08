import { apiClient } from "./client";
import type { RecommendedTopic, ReviewDue } from "../types/api";

interface ApiResponse<T> {
  success: boolean;
  data: T;
}

export async function getRecommended(): Promise<RecommendedTopic[]> {
  const res = await apiClient<ApiResponse<RecommendedTopic[]>>(
    "/api/v1/learning-path/recommended"
  );
  return res.data;
}

export async function getGraph(
  subject: string
): Promise<{ nodes: unknown[]; edges: unknown[] }> {
  const res = await apiClient<
    ApiResponse<{ nodes: unknown[]; edges: unknown[] }>
  >(`/api/v1/learning-path/graph/${encodeURIComponent(subject)}`);
  return res.data;
}

export async function getReviewsDue(): Promise<ReviewDue[]> {
  const res = await apiClient<ApiResponse<ReviewDue[]>>(
    "/api/v1/learning-path/reviews-due"
  );
  return res.data;
}

export async function completeReview(
  topic_id: string,
  quality: number
): Promise<void> {
  await apiClient("/api/v1/learning-path/review-completed", {
    method: "POST",
    body: JSON.stringify({ topic_id, quality }),
  });
}
