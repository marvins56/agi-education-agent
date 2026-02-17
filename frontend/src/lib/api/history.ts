import { apiClient } from "./client";

export interface HistoricalEvent {
  id: string;
  title: string;
  date: string;
  description: string;
  importance: number;
  category: string;
  connections: string[];
  primarySources: string[];
  location?: {
    name: string;
    coordinates?: [number, number];
  };
  tags: string[];
  verified: boolean;
}

export interface Timeline {
  id: string;
  title: string;
  description: string;
  topic: string;
  events: HistoricalEvent[];
  timeRange: {
    start: string;
    end: string;
  };
  createdAt: string;
  updatedAt: string;
}

export interface TimelineFilters {
  startDate?: string;
  endDate?: string;
  categories?: string[];
  minImportance?: number;
  tags?: string[];
  verified?: boolean;
}

interface ApiResponse<T> {
  success: boolean;
  data: T;
}

export async function getTimelines(topic?: string): Promise<Timeline[]> {
  const queryParams = topic ? `?topic=${encodeURIComponent(topic)}` : '';
  const res = await apiClient<ApiResponse<Timeline[]>>(
    `/api/v1/history/timelines${queryParams}`
  );
  return res.data;
}

export async function getTimeline(timelineId: string): Promise<Timeline> {
  const res = await apiClient<ApiResponse<Timeline>>(
    `/api/v1/history/timelines/${timelineId}`
  );
  return res.data;
}

export async function getEvents(filters?: TimelineFilters): Promise<HistoricalEvent[]> {
  const queryParams = new URLSearchParams();
  
  if (filters) {
    if (filters.startDate) queryParams.set('startDate', filters.startDate);
    if (filters.endDate) queryParams.set('endDate', filters.endDate);
    if (filters.categories) queryParams.set('categories', filters.categories.join(','));
    if (filters.minImportance) queryParams.set('minImportance', filters.minImportance.toString());
    if (filters.tags) queryParams.set('tags', filters.tags.join(','));
    if (filters.verified !== undefined) queryParams.set('verified', filters.verified.toString());
  }

  const res = await apiClient<ApiResponse<HistoricalEvent[]>>(
    `/api/v1/history/events?${queryParams.toString()}`
  );
  return res.data;
}

export async function getEvent(eventId: string): Promise<HistoricalEvent> {
  const res = await apiClient<ApiResponse<HistoricalEvent>>(
    `/api/v1/history/events/${eventId}`
  );
  return res.data;
}

export async function getEventConnections(eventId: string): Promise<HistoricalEvent[]> {
  const res = await apiClient<ApiResponse<HistoricalEvent[]>>(
    `/api/v1/history/events/${eventId}/connections`
  );
  return res.data;
}

export async function getCategories(): Promise<string[]> {
  const res = await apiClient<ApiResponse<string[]>>(
    `/api/v1/history/categories`
  );
  return res.data;
}

export async function generateTimeline(topic: string, timeRange?: { start: string; end: string }): Promise<Timeline> {
  const res = await apiClient<ApiResponse<Timeline>>(
    `/api/v1/history/timelines/generate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        topic,
        timeRange,
      }),
    }
  );
  return res.data;
}