import { apiClient } from "./client";
import type { ModelProvider, CurrentModel } from "../types/api";

export async function listModels(): Promise<ModelProvider[]> {
  return apiClient<ModelProvider[]>("/api/v1/models");
}

export async function getCurrentModel(): Promise<CurrentModel> {
  return apiClient<CurrentModel>("/api/v1/models/current");
}
