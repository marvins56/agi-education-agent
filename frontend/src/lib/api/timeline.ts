import { apiClient } from './client'

export interface TimelineEvent {
  id: string
  title: string
  date: string
  year: number
  description: string
  category: 'political' | 'military' | 'social' | 'economic' | 'cultural' | 'religious'
  significance: 'low' | 'medium' | 'high' | 'critical'
  location?: string
  relatedEvents?: string[]
  sources?: string[]
  imageUrl?: string
  tags: string[]
}

export interface Timeline {
  id: string
  title: string
  description: string
  subject: string
  timeRange: {
    start: number
    end: number
  }
  events: TimelineEvent[]
  createdBy: string
  createdAt: string
  updatedAt: string
  isPublic: boolean
  tags: string[]
}

export interface TimelineFilters {
  subject?: string
  category?: string[]
  yearStart?: number
  yearEnd?: number
  significance?: string[]
  search?: string
  tags?: string[]
}

export interface GenerateTimelineRequest {
  topic: string
  timeRange?: {
    start?: number
    end?: number
  }
  categories?: string[]
  maxEvents?: number
  detailLevel: 'brief' | 'detailed' | 'comprehensive'
  includeImages?: boolean
}

export class TimelineAPI {
  /**
   * Get all available timelines
   */
  static async getTimelines(filters?: TimelineFilters): Promise<Timeline[]> {
    const params = new URLSearchParams()
    
    if (filters?.subject) params.append('subject', filters.subject)
    if (filters?.search) params.append('search', filters.search)
    if (filters?.yearStart) params.append('year_start', filters.yearStart.toString())
    if (filters?.yearEnd) params.append('year_end', filters.yearEnd.toString())
    if (filters?.category?.length) {
      filters.category.forEach(cat => params.append('category', cat))
    }
    if (filters?.significance?.length) {
      filters.significance.forEach(sig => params.append('significance', sig))
    }
    if (filters?.tags?.length) {
      filters.tags.forEach(tag => params.append('tags', tag))
    }

    const query = params.toString()
    const url = query ? `/api/v1/timelines?${query}` : '/api/v1/timelines'
    
    return apiClient<Timeline[]>(url)
  }

  /**
   * Get timeline by ID
   */
  static async getTimeline(timelineId: string): Promise<Timeline> {
    return apiClient<Timeline>(`/api/v1/timelines/${timelineId}`)
  }

  /**
   * Generate a new timeline based on topic
   */
  static async generateTimeline(request: GenerateTimelineRequest): Promise<Timeline> {
    return apiClient<Timeline>('/api/v1/timelines/generate', {
      method: 'POST',
      body: JSON.stringify(request)
    })
  }

  /**
   * Create a custom timeline
   */
  static async createTimeline(timeline: Omit<Timeline, 'id' | 'createdBy' | 'createdAt' | 'updatedAt'>): Promise<Timeline> {
    return apiClient<Timeline>('/api/v1/timelines', {
      method: 'POST',
      body: JSON.stringify(timeline)
    })
  }

  /**
   * Update timeline
   */
  static async updateTimeline(timelineId: string, updates: Partial<Timeline>): Promise<Timeline> {
    return apiClient<Timeline>(`/api/v1/timelines/${timelineId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates)
    })
  }

  /**
   * Delete timeline
   */
  static async deleteTimeline(timelineId: string): Promise<void> {
    return apiClient<void>(`/api/v1/timelines/${timelineId}`, {
      method: 'DELETE'
    })
  }

  /**
   * Add event to timeline
   */
  static async addEventToTimeline(timelineId: string, event: Omit<TimelineEvent, 'id'>): Promise<TimelineEvent> {
    return apiClient<TimelineEvent>(`/api/v1/timelines/${timelineId}/events`, {
      method: 'POST',
      body: JSON.stringify(event)
    })
  }

  /**
   * Update timeline event
   */
  static async updateTimelineEvent(
    timelineId: string, 
    eventId: string, 
    updates: Partial<TimelineEvent>
  ): Promise<TimelineEvent> {
    return apiClient<TimelineEvent>(`/api/v1/timelines/${timelineId}/events/${eventId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates)
    })
  }

  /**
   * Remove event from timeline
   */
  static async removeEventFromTimeline(timelineId: string, eventId: string): Promise<void> {
    return apiClient<void>(`/api/v1/timelines/${timelineId}/events/${eventId}`, {
      method: 'DELETE'
    })
  }

  /**
   * Get timeline events with filters
   */
  static async getTimelineEvents(
    timelineId: string, 
    filters?: Omit<TimelineFilters, 'subject'>
  ): Promise<TimelineEvent[]> {
    const params = new URLSearchParams()
    
    if (filters?.search) params.append('search', filters.search)
    if (filters?.yearStart) params.append('year_start', filters.yearStart.toString())
    if (filters?.yearEnd) params.append('year_end', filters.yearEnd.toString())
    if (filters?.category?.length) {
      filters.category.forEach(cat => params.append('category', cat))
    }
    if (filters?.significance?.length) {
      filters.significance.forEach(sig => params.append('significance', sig))
    }
    if (filters?.tags?.length) {
      filters.tags.forEach(tag => params.append('tags', tag))
    }

    const query = params.toString()
    const url = query 
      ? `/api/v1/timelines/${timelineId}/events?${query}` 
      : `/api/v1/timelines/${timelineId}/events`
    
    return apiClient<TimelineEvent[]>(url)
  }

  /**
   * Search for related events across all timelines
   */
  static async searchRelatedEvents(eventId: string, timelineId?: string): Promise<TimelineEvent[]> {
    const params = new URLSearchParams({ event_id: eventId })
    if (timelineId) params.append('timeline_id', timelineId)
    
    return apiClient<TimelineEvent[]>(`/api/v1/timelines/events/related?${params.toString()}`)
  }

  /**
   * Get timeline statistics
   */
  static async getTimelineStatistics(timelineId: string): Promise<{
    totalEvents: number
    eventsByCategory: Record<string, number>
    eventsBySignificance: Record<string, number>
    eventsByDecade: Record<string, number>
    timeSpan: number
  }> {
    return apiClient(`/api/v1/timelines/${timelineId}/statistics`)
  }

  /**
   * Export timeline data
   */
  static async exportTimeline(
    timelineId: string, 
    format: 'json' | 'csv' | 'pdf'
  ): Promise<Blob> {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/api/v1/timelines/${timelineId}/export?format=${format}`,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      }
    )
    
    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`)
    }
    
    return response.blob()
  }

  /**
   * Get available timeline templates
   */
  static async getTemplates(): Promise<Array<{
    id: string
    name: string
    description: string
    subject: string
    previewEvents: TimelineEvent[]
  }>> {
    return apiClient('/api/v1/timelines/templates')
  }

  /**
   * Create timeline from template
   */
  static async createFromTemplate(
    templateId: string, 
    customization?: {
      title?: string
      description?: string
      timeRange?: { start?: number; end?: number }
    }
  ): Promise<Timeline> {
    return apiClient<Timeline>(`/api/v1/timelines/templates/${templateId}/create`, {
      method: 'POST',
      body: JSON.stringify(customization || {})
    })
  }

  /**
   * Get popular timelines
   */
  static async getPopularTimelines(): Promise<Timeline[]> {
    return apiClient<Timeline[]>('/api/v1/timelines/popular')
  }

  /**
   * Get user's recent timelines
   */
  static async getRecentTimelines(): Promise<Timeline[]> {
    return apiClient<Timeline[]>('/api/v1/timelines/recent')
  }
}