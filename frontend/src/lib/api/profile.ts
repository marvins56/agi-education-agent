import { apiClient } from "./client";
import type { Profile, ProfileUpdateRequest, TopicMastery, MasteryBySubject } from "../types/api";

export async function getProfile(): Promise<Profile> {
  return apiClient<Profile>("/api/v1/profile");
}

export async function updateProfile(
  data: ProfileUpdateRequest
): Promise<Profile> {
  return apiClient<Profile>("/api/v1/profile", {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function getMastery(): Promise<TopicMastery[]> {
  return apiClient<TopicMastery[]>("/api/v1/profile/mastery");
}

export async function getMasteryBySubject(
  subject: string
): Promise<MasteryBySubject> {
  return apiClient<MasteryBySubject>(
    `/api/v1/profile/mastery/${encodeURIComponent(subject)}`
  );
}

export async function getHistory(limit = 20): Promise<unknown[]> {
  return apiClient<unknown[]>(`/api/v1/profile/history?limit=${limit}`);
}

export async function getStreaks(): Promise<Record<string, unknown>> {
  return apiClient<Record<string, unknown>>("/api/v1/profile/streaks");
}
