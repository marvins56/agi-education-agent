import { apiClient } from "./client";
import type { AnalyticsSummary, TopicMastery, ActivityHeatmap, Alert } from "../types/api";

interface ApiResponse<T> {
  success: boolean;
  data: T;
}

export async function getSummary(): Promise<AnalyticsSummary> {
  const res = await apiClient<ApiResponse<AnalyticsSummary>>(
    "/api/v1/analytics/student/summary"
  );
  return res.data;
}

export async function getMastery(): Promise<TopicMastery[]> {
  const res = await apiClient<ApiResponse<TopicMastery[]>>(
    "/api/v1/analytics/student/mastery"
  );
  return res.data;
}

export async function getActivity(days = 30): Promise<ActivityHeatmap[]> {
  const res = await apiClient<ApiResponse<ActivityHeatmap[]>>(
    `/api/v1/analytics/student/activity?days=${days}`
  );
  return res.data;
}

export async function getStreaks(): Promise<Record<string, unknown>> {
  const res = await apiClient<ApiResponse<Record<string, unknown>>>(
    "/api/v1/analytics/student/streaks"
  );
  return res.data;
}

export async function getAlerts(): Promise<Alert[]> {
  const res = await apiClient<ApiResponse<Alert[]>>(
    "/api/v1/analytics/student/alerts"
  );
  return res.data;
}
