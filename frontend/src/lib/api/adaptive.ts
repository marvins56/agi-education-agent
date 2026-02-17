import { apiClient } from "./client";

export interface LearningProgress {
  topicId: string;
  topicName: string;
  mastery: number;
  timeSpent: number;
  lastStudied: string;
  strengthAreas: string[];
  weaknessAreas: string[];
  nextRecommendation: string;
}

export interface AdaptiveRecommendation {
  id: string;
  type: 'content' | 'assessment' | 'review' | 'practice';
  title: string;
  description: string;
  difficulty: number;
  estimatedTime: number;
  priority: 'high' | 'medium' | 'low';
  reason: string;
}

export interface LearningGoal {
  id: string;
  title: string;
  description: string;
  targetDate: string;
  progress: number;
  milestones: Milestone[];
  status: 'active' | 'completed' | 'paused';
  createdAt: string;
}

export interface Milestone {
  id: string;
  title: string;
  description: string;
  completed: boolean;
  completedAt?: string;
  dueDate?: string;
}

export interface SkillAssessment {
  skill: string;
  level: number;
  confidence: number;
  assessmentDate: string;
  evidence: string[];
}

interface ApiResponse<T> {
  success: boolean;
  data: T;
}

export async function getAdaptiveRecommendations(limit = 10): Promise<AdaptiveRecommendation[]> {
  const res = await apiClient<ApiResponse<AdaptiveRecommendation[]>>(
    `/api/v1/adaptive/recommendations?limit=${limit}`
  );
  return res.data;
}

export async function getLearningProgress(): Promise<LearningProgress[]> {
  const res = await apiClient<ApiResponse<LearningProgress[]>>(
    `/api/v1/adaptive/progress`
  );
  return res.data;
}

export async function updateLearningProgress(
  topicId: string,
  progress: Partial<LearningProgress>
): Promise<LearningProgress> {
  const res = await apiClient<ApiResponse<LearningProgress>>(
    `/api/v1/adaptive/progress/${topicId}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(progress),
    }
  );
  return res.data;
}

export async function createLearningGoal(goal: Omit<LearningGoal, 'id' | 'createdAt' | 'progress'>): Promise<LearningGoal> {
  const res = await apiClient<ApiResponse<LearningGoal>>(
    `/api/v1/adaptive/goals`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(goal),
    }
  );
  return res.data;
}

export async function getLearningGoals(): Promise<LearningGoal[]> {
  const res = await apiClient<ApiResponse<LearningGoal[]>>(
    `/api/v1/adaptive/goals`
  );
  return res.data;
}

export async function updateLearningGoal(goalId: string, updates: Partial<LearningGoal>): Promise<LearningGoal> {
  const res = await apiClient<ApiResponse<LearningGoal>>(
    `/api/v1/adaptive/goals/${goalId}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(updates),
    }
  );
  return res.data;
}

export async function getSkillAssessments(): Promise<SkillAssessment[]> {
  const res = await apiClient<ApiResponse<SkillAssessment[]>>(
    `/api/v1/adaptive/skills`
  );
  return res.data;
}

export async function recordLearningActivity(activity: {
  type: string;
  content: string;
  duration: number;
  performance?: number;
  metadata?: Record<string, any>;
}): Promise<void> {
  await apiClient<ApiResponse<void>>(
    `/api/v1/adaptive/activity`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ...activity,
        timestamp: new Date().toISOString(),
      }),
    }
  );
}

export async function getDifficultyRecommendation(topicId: string): Promise<{ difficulty: number; reason: string }> {
  const res = await apiClient<ApiResponse<{ difficulty: number; reason: string }>>(
    `/api/v1/adaptive/difficulty/${topicId}`
  );
  return res.data;
}