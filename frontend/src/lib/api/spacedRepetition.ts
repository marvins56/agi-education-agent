import { apiClient } from './client'

export interface SpacedRepetitionCard {
  id: string
  studentId: string
  contentId: string
  contentType: 'fact' | 'concept' | 'date' | 'cause_effect' | 'timeline' | 'source_analysis'
  concept: string
  subject: string
  
  // Spaced repetition parameters
  easeFactor: number
  interval: number
  repetition: number
  
  // Performance tracking
  correctStreak: number
  totalReviews: number
  successRate: number
  lastPerformance: number
  
  // Scheduling
  nextReviewDate: string
  lastReviewed?: string
  createdAt: string
  
  // Metadata
  difficultyRating: number
  importanceWeight: number
  learningState: 'new' | 'learning' | 'review' | 'mastered'
  reviewHistory: ReviewRecord[]
  tags: string[]
}

export interface ReviewRecord {
  reviewDate: string
  performanceScore: number
  responseTime?: number
  interval: number
  easeFactor: number
  performanceCategory: 'fail' | 'poor' | 'fair' | 'good' | 'excellent'
}

export interface ReviewSession {
  id: string
  studentId: string
  subject?: string
  cards: SpacedRepetitionCard[]
  estimatedDurationMinutes: number
  createdAt: string
  status: 'active' | 'completed' | 'abandoned'
  completedCards?: number
  totalCards?: number
}

export interface ReviewResult {
  cardId: string
  nextReviewDate: string
  intervalDays: number
  learningState: string
  performanceCategory: string
  successRate: number
  correctStreak: number
}

export interface StudyProgress {
  studentId: string
  subject?: string
  analysisPeriodDays: number
  totalCards: number
  progressMetrics: {
    learningStateDistribution: Record<string, number>
    masteryPercentage: number
    averageSuccessRate: number
    recentReviewCount: number
    reviewsPerDay: number
    difficultyDistribution: Record<string, number>
    averageCorrectStreak: number
    longestCorrectStreak: number
    totalReviewSessions: number
  }
  upcomingReviews: Record<string, number>
  generatedAt: string
}

export interface CreateCardRequest {
  contentId: string
  contentType: SpacedRepetitionCard['contentType']
  concept: string
  subject: string
  difficulty?: number
  importance?: number
  tags?: string[]
}

export interface ReviewSessionRequest {
  subject?: string
  maxCards?: number
  sessionDurationMinutes?: number
}

export interface ProcessReviewRequest {
  cardId: string
  performanceScore: number
  responseTimeSeconds?: number
  difficultyRating?: number
}

export class SpacedRepetitionAPI {
  /**
   * Get all spaced repetition cards for current user
   */
  static async getCards(subject?: string): Promise<SpacedRepetitionCard[]> {
    const params = subject ? `?subject=${encodeURIComponent(subject)}` : ''
    return apiClient<SpacedRepetitionCard[]>(`/api/v1/spaced-repetition/cards${params}`)
  }

  /**
   * Get a specific card by ID
   */
  static async getCard(cardId: string): Promise<SpacedRepetitionCard> {
    return apiClient<SpacedRepetitionCard>(`/api/v1/spaced-repetition/cards/${cardId}`)
  }

  /**
   * Create a new spaced repetition card
   */
  static async createCard(request: CreateCardRequest): Promise<SpacedRepetitionCard> {
    return apiClient<SpacedRepetitionCard>('/api/v1/spaced-repetition/cards', {
      method: 'POST',
      body: JSON.stringify(request)
    })
  }

  /**
   * Update card parameters
   */
  static async updateCard(
    cardId: string, 
    updates: Partial<Pick<SpacedRepetitionCard, 'difficultyRating' | 'importanceWeight' | 'tags'>>
  ): Promise<SpacedRepetitionCard> {
    return apiClient<SpacedRepetitionCard>(`/api/v1/spaced-repetition/cards/${cardId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates)
    })
  }

  /**
   * Delete a spaced repetition card
   */
  static async deleteCard(cardId: string): Promise<void> {
    return apiClient<void>(`/api/v1/spaced-repetition/cards/${cardId}`, {
      method: 'DELETE'
    })
  }

  /**
   * Get cards due for review
   */
  static async getDueReviews(subject?: string, limit?: number): Promise<SpacedRepetitionCard[]> {
    const params = new URLSearchParams()
    if (subject) params.append('subject', subject)
    if (limit) params.append('limit', limit.toString())
    
    const query = params.toString()
    const url = query ? `/api/v1/spaced-repetition/due?${query}` : '/api/v1/spaced-repetition/due'
    
    return apiClient<SpacedRepetitionCard[]>(url)
  }

  /**
   * Create a new review session
   */
  static async createReviewSession(request: ReviewSessionRequest = {}): Promise<ReviewSession> {
    return apiClient<ReviewSession>('/api/v1/spaced-repetition/sessions', {
      method: 'POST',
      body: JSON.stringify(request)
    })
  }

  /**
   * Get review session by ID
   */
  static async getReviewSession(sessionId: string): Promise<ReviewSession> {
    return apiClient<ReviewSession>(`/api/v1/spaced-repetition/sessions/${sessionId}`)
  }

  /**
   * Get all review sessions for current user
   */
  static async getReviewSessions(): Promise<ReviewSession[]> {
    return apiClient<ReviewSession[]>('/api/v1/spaced-repetition/sessions')
  }

  /**
   * Process review result for a card
   */
  static async processReview(request: ProcessReviewRequest): Promise<ReviewResult> {
    return apiClient<ReviewResult>('/api/v1/spaced-repetition/review', {
      method: 'POST',
      body: JSON.stringify(request)
    })
  }

  /**
   * Complete review session
   */
  static async completeSession(sessionId: string): Promise<ReviewSession> {
    return apiClient<ReviewSession>(`/api/v1/spaced-repetition/sessions/${sessionId}/complete`, {
      method: 'POST'
    })
  }

  /**
   * Abandon review session
   */
  static async abandonSession(sessionId: string): Promise<void> {
    return apiClient<void>(`/api/v1/spaced-repetition/sessions/${sessionId}/abandon`, {
      method: 'POST'
    })
  }

  /**
   * Get student progress report
   */
  static async getProgress(subject?: string, daysBack?: number): Promise<StudyProgress> {
    const params = new URLSearchParams()
    if (subject) params.append('subject', subject)
    if (daysBack) params.append('days_back', daysBack.toString())
    
    const query = params.toString()
    const url = query ? `/api/v1/spaced-repetition/progress?${query}` : '/api/v1/spaced-repetition/progress'
    
    return apiClient<StudyProgress>(url)
  }

  /**
   * Get upcoming reviews for the next N days
   */
  static async getUpcomingReviews(days: number = 7): Promise<Record<string, number>> {
    return apiClient<Record<string, number>>(`/api/v1/spaced-repetition/upcoming?days=${days}`)
  }

  /**
   * Bulk create cards from content
   */
  static async createCardsFromContent(
    contentItems: Array<{
      contentId: string
      type: SpacedRepetitionCard['contentType']
      concept: string
      difficulty?: number
      importance?: number
    }>,
    subject: string
  ): Promise<SpacedRepetitionCard[]> {
    return apiClient<SpacedRepetitionCard[]>('/api/v1/spaced-repetition/cards/bulk', {
      method: 'POST',
      body: JSON.stringify({
        content_items: contentItems,
        subject
      })
    })
  }

  /**
   * Get learning statistics
   */
  static async getStatistics(timeRange: 'week' | 'month' | 'year' = 'month'): Promise<{
    totalCards: number
    totalReviews: number
    averageSuccessRate: number
    masteredCards: number
    streak: {
      current: number
      longest: number
    }
    reviewsByDay: Array<{
      date: string
      reviews: number
      success_rate: number
    }>
    performanceBySubject: Array<{
      subject: string
      cards: number
      success_rate: number
      mastery_percentage: number
    }>
  }> {
    return apiClient(`/api/v1/spaced-repetition/statistics?time_range=${timeRange}`)
  }

  /**
   * Get card review history
   */
  static async getCardHistory(cardId: string): Promise<ReviewRecord[]> {
    return apiClient<ReviewRecord[]>(`/api/v1/spaced-repetition/cards/${cardId}/history`)
  }

  /**
   * Reset card progress (start over)
   */
  static async resetCard(cardId: string): Promise<SpacedRepetitionCard> {
    return apiClient<SpacedRepetitionCard>(`/api/v1/spaced-repetition/cards/${cardId}/reset`, {
      method: 'POST'
    })
  }

  /**
   * Suspend card (pause reviews)
   */
  static async suspendCard(cardId: string): Promise<SpacedRepetitionCard> {
    return apiClient<SpacedRepetitionCard>(`/api/v1/spaced-repetition/cards/${cardId}/suspend`, {
      method: 'POST'
    })
  }

  /**
   * Resume suspended card
   */
  static async resumeCard(cardId: string): Promise<SpacedRepetitionCard> {
    return apiClient<SpacedRepetitionCard>(`/api/v1/spaced-repetition/cards/${cardId}/resume`, {
      method: 'POST'
    })
  }

  /**
   * Get optimal study schedule for student
   */
  static async getOptimalSchedule(): Promise<{
    todayReviews: number
    thisWeekReviews: Array<{
      date: string
      reviews: number
      estimated_minutes: number
    }>
    recommendations: {
      dailyGoal: number
      bestStudyTimes: string[]
      weeklySchedule: Record<string, number>
    }
  }> {
    return apiClient('/api/v1/spaced-repetition/schedule')
  }

  /**
   * Export spaced repetition data
   */
  static async exportData(format: 'json' | 'csv'): Promise<Blob> {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/api/v1/spaced-repetition/export?format=${format}`,
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
}