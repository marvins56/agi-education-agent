import { apiClient } from "./client";
import type {
  Assessment,
  QuickQuizRequest,
  QuickQuizResponse,
  SubmissionResponse,
} from "../types/api";

export async function listAssessments(): Promise<Assessment[]> {
  return apiClient<Assessment[]>("/api/v1/assessments");
}

export async function getAssessment(id: string): Promise<Assessment> {
  return apiClient<Assessment>(`/api/v1/assessments/${id}`);
}

export async function quickQuiz(
  data: QuickQuizRequest
): Promise<QuickQuizResponse> {
  return apiClient<QuickQuizResponse>("/api/v1/assessments/quick-quiz", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function submitAssessment(
  id: string,
  answers: Record<string, string>
): Promise<SubmissionResponse> {
  return apiClient<SubmissionResponse>(`/api/v1/assessments/${id}/submit`, {
    method: "POST",
    body: JSON.stringify({ answers }),
  });
}

export async function getResults(id: string): Promise<SubmissionResponse> {
  return apiClient<SubmissionResponse>(`/api/v1/assessments/${id}/results`);
}
