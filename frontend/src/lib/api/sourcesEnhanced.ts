import { apiClient } from './client'

export interface PrimarySource {
  id: string
  title: string
  author?: string
  date: string
  year: number
  location?: string
  type: 'document' | 'letter' | 'diary' | 'speech' | 'newspaper' | 'photograph' | 'artifact' | 'audio' | 'video'
  content: string
  description: string
  historicalContext: string
  perspective: string
  purpose: string
  audience: string
  reliability: 'high' | 'medium' | 'low'
  bias?: string[]
  significance: string
  relatedEvents?: string[]
  tags: string[]
  sourceUrl?: string
  imageUrl?: string
  subject: string
  timelineIds?: string[]
  createdAt: string
  updatedAt: string
}

export interface SourceAnalysis {
  sourceId: string
  studentId: string
  pointOfView: string
  purpose: string
  audience: string
  situation: string
  credibility: {
    score: number
    factors: string[]
  }
  biases: string[]
  limitations: string[]
  strengths: string[]
  historicalValue: string
  questions: string[]
  createdAt: string
  isPublic?: boolean
}

export interface SourceCollection {
  id: string
  title: string
  description: string
  sources: string[] // source IDs
  subject: string
  topic: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  estimatedTime: number
  createdBy: string
  createdAt: string
  isPublic: boolean
  tags: string[]
}

export interface DocumentBasedQuestion {
  id: string
  title: string
  prompt: string
  historicalContext: string
  sources: string[] // source IDs
  rubric: {
    thesis: { weight: number; description: string }
    evidenceFromDocuments: { weight: number; description: string }
    documentAnalysis: { weight: number; description: string }
    outsideEvidence: { weight: number; description: string }
    contextualization: { weight: number; description: string }
    complexity: { weight: number; description: string }
  }
  timeLimit?: number
  subject: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  tags: string[]
  createdBy: string
  createdAt: string
}

export interface SourceFilters {
  subject?: string
  type?: string[]
  year?: { min?: number; max?: number }
  reliability?: string[]
  tags?: string[]
  search?: string
  hasImages?: boolean
  difficulty?: string[]
}

export interface AnalyzeSourceRequest {
  sourceId: string
  analysisType: 'guided' | 'free_form'
  focusAreas?: ('point_of_view' | 'purpose' | 'audience' | 'situation' | 'credibility' | 'bias')[]
}

export interface CreateSourceRequest {
  title: string
  author?: string
  date: string
  type: PrimarySource['type']
  content: string
  description: string
  historicalContext: string
  perspective: string
  purpose: string
  audience: string
  reliability: PrimarySource['reliability']
  bias?: string[]
  significance: string
  subject: string
  tags: string[]
  sourceUrl?: string
  imageUrl?: string
  location?: string
}

export class SourcesEnhancedAPI {
  /**
   * Get all primary sources with advanced filtering
   */
  static async getSources(filters?: SourceFilters): Promise<PrimarySource[]> {
    const params = new URLSearchParams()
    
    if (filters?.subject) params.append('subject', filters.subject)
    if (filters?.search) params.append('search', filters.search)
    if (filters?.hasImages !== undefined) params.append('has_images', filters.hasImages.toString())
    
    if (filters?.type?.length) {
      filters.type.forEach(type => params.append('type', type))
    }
    if (filters?.reliability?.length) {
      filters.reliability.forEach(rel => params.append('reliability', rel))
    }
    if (filters?.tags?.length) {
      filters.tags.forEach(tag => params.append('tags', tag))
    }
    if (filters?.difficulty?.length) {
      filters.difficulty.forEach(diff => params.append('difficulty', diff))
    }
    
    if (filters?.year?.min) params.append('year_min', filters.year.min.toString())
    if (filters?.year?.max) params.append('year_max', filters.year.max.toString())

    const query = params.toString()
    const url = query ? `/api/v1/sources/enhanced?${query}` : '/api/v1/sources/enhanced'
    
    return apiClient<PrimarySource[]>(url)
  }

  /**
   * Get source by ID with full details
   */
  static async getSource(sourceId: string): Promise<PrimarySource> {
    return apiClient<PrimarySource>(`/api/v1/sources/enhanced/${sourceId}`)
  }

  /**
   * Create a new primary source
   */
  static async createSource(request: CreateSourceRequest): Promise<PrimarySource> {
    return apiClient<PrimarySource>('/api/v1/sources/enhanced', {
      method: 'POST',
      body: JSON.stringify(request)
    })
  }

  /**
   * Update primary source
   */
  static async updateSource(sourceId: string, updates: Partial<CreateSourceRequest>): Promise<PrimarySource> {
    return apiClient<PrimarySource>(`/api/v1/sources/enhanced/${sourceId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates)
    })
  }

  /**
   * Delete primary source
   */
  static async deleteSource(sourceId: string): Promise<void> {
    return apiClient<void>(`/api/v1/sources/enhanced/${sourceId}`, {
      method: 'DELETE'
    })
  }

  /**
   * Analyze a primary source
   */
  static async analyzeSource(request: AnalyzeSourceRequest): Promise<SourceAnalysis> {
    return apiClient<SourceAnalysis>('/api/v1/sources/enhanced/analyze', {
      method: 'POST',
      body: JSON.stringify(request)
    })
  }

  /**
   * Get source analysis by ID
   */
  static async getAnalysis(analysisId: string): Promise<SourceAnalysis> {
    return apiClient<SourceAnalysis>(`/api/v1/sources/enhanced/analyses/${analysisId}`)
  }

  /**
   * Get all analyses for a source
   */
  static async getSourceAnalyses(sourceId: string): Promise<SourceAnalysis[]> {
    return apiClient<SourceAnalysis[]>(`/api/v1/sources/enhanced/${sourceId}/analyses`)
  }

  /**
   * Update source analysis
   */
  static async updateAnalysis(
    analysisId: string, 
    updates: Partial<Omit<SourceAnalysis, 'sourceId' | 'studentId' | 'createdAt'>>
  ): Promise<SourceAnalysis> {
    return apiClient<SourceAnalysis>(`/api/v1/sources/enhanced/analyses/${analysisId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates)
    })
  }

  /**
   * Delete source analysis
   */
  static async deleteAnalysis(analysisId: string): Promise<void> {
    return apiClient<void>(`/api/v1/sources/enhanced/analyses/${analysisId}`, {
      method: 'DELETE'
    })
  }

  /**
   * Get source collections
   */
  static async getCollections(subject?: string): Promise<SourceCollection[]> {
    const params = subject ? `?subject=${encodeURIComponent(subject)}` : ''
    return apiClient<SourceCollection[]>(`/api/v1/sources/enhanced/collections${params}`)
  }

  /**
   * Get collection by ID
   */
  static async getCollection(collectionId: string): Promise<SourceCollection> {
    return apiClient<SourceCollection>(`/api/v1/sources/enhanced/collections/${collectionId}`)
  }

  /**
   * Create source collection
   */
  static async createCollection(
    collection: Omit<SourceCollection, 'id' | 'createdBy' | 'createdAt'>
  ): Promise<SourceCollection> {
    return apiClient<SourceCollection>('/api/v1/sources/enhanced/collections', {
      method: 'POST',
      body: JSON.stringify(collection)
    })
  }

  /**
   * Update source collection
   */
  static async updateCollection(
    collectionId: string, 
    updates: Partial<SourceCollection>
  ): Promise<SourceCollection> {
    return apiClient<SourceCollection>(`/api/v1/sources/enhanced/collections/${collectionId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates)
    })
  }

  /**
   * Delete source collection
   */
  static async deleteCollection(collectionId: string): Promise<void> {
    return apiClient<void>(`/api/v1/sources/enhanced/collections/${collectionId}`, {
      method: 'DELETE'
    })
  }

  /**
   * Get Document-Based Questions
   */
  static async getDBQs(subject?: string, difficulty?: string): Promise<DocumentBasedQuestion[]> {
    const params = new URLSearchParams()
    if (subject) params.append('subject', subject)
    if (difficulty) params.append('difficulty', difficulty)
    
    const query = params.toString()
    const url = query ? `/api/v1/sources/enhanced/dbq?${query}` : '/api/v1/sources/enhanced/dbq'
    
    return apiClient<DocumentBasedQuestion[]>(url)
  }

  /**
   * Get DBQ by ID
   */
  static async getDBQ(dbqId: string): Promise<DocumentBasedQuestion> {
    return apiClient<DocumentBasedQuestion>(`/api/v1/sources/enhanced/dbq/${dbqId}`)
  }

  /**
   * Generate DBQ from sources
   */
  static async generateDBQ(request: {
    topic: string
    sources: string[]
    difficulty: 'beginner' | 'intermediate' | 'advanced'
    subject: string
    focusArea?: string
  }): Promise<DocumentBasedQuestion> {
    return apiClient<DocumentBasedQuestion>('/api/v1/sources/enhanced/dbq/generate', {
      method: 'POST',
      body: JSON.stringify(request)
    })
  }

  /**
   * Search for related sources
   */
  static async findRelatedSources(
    sourceId: string, 
    limit: number = 10
  ): Promise<Array<PrimarySource & { similarity: number; relationshipType: string }>> {
    return apiClient(`/api/v1/sources/enhanced/${sourceId}/related?limit=${limit}`)
  }

  /**
   * Get sources by time period
   */
  static async getSourcesByTimePeriod(
    startYear: number, 
    endYear: number, 
    subject?: string
  ): Promise<PrimarySource[]> {
    const params = new URLSearchParams({
      start_year: startYear.toString(),
      end_year: endYear.toString()
    })
    if (subject) params.append('subject', subject)
    
    return apiClient<PrimarySource[]>(`/api/v1/sources/enhanced/time-period?${params.toString()}`)
  }

  /**
   * Get source statistics
   */
  static async getSourceStatistics(): Promise<{
    totalSources: number
    sourcesByType: Record<string, number>
    sourcesByReliability: Record<string, number>
    sourcesBySubject: Record<string, number>
    sourcesByDecade: Record<string, number>
    averageAnalyses: number
  }> {
    return apiClient('/api/v1/sources/enhanced/statistics')
  }

  /**
   * Generate analysis questions for a source
   */
  static async generateAnalysisQuestions(
    sourceId: string,
    questionTypes: ('understanding' | 'perspective' | 'reliability' | 'significance')[] = [
      'understanding', 'perspective', 'reliability', 'significance'
    ]
  ): Promise<{
    questions: Array<{
      type: string
      question: string
      guidingPoints: string[]
    }>
  }> {
    return apiClient(`/api/v1/sources/enhanced/${sourceId}/questions`, {
      method: 'POST',
      body: JSON.stringify({ question_types: questionTypes })
    })
  }

  /**
   * Compare multiple sources
   */
  static async compareSources(sourceIds: string[]): Promise<{
    comparison: {
      perspectives: Array<{
        sourceId: string
        perspective: string
        biases: string[]
      }>
      agreements: string[]
      contradictions: string[]
      complementaryInformation: string[]
      credibilityRanking: Array<{
        sourceId: string
        score: number
        reasoning: string
      }>
    }
    analysisQuestions: string[]
  }> {
    return apiClient('/api/v1/sources/enhanced/compare', {
      method: 'POST',
      body: JSON.stringify({ source_ids: sourceIds })
    })
  }

  /**
   * Upload source image
   */
  static async uploadSourceImage(sourceId: string, imageFile: File): Promise<{ imageUrl: string }> {
    const formData = new FormData()
    formData.append('image', imageFile)
    
    return apiClient<{ imageUrl: string }>(`/api/v1/sources/enhanced/${sourceId}/image`, {
      method: 'POST',
      body: formData,
      headers: {} // Let browser set content-type for FormData
    })
  }

  /**
   * Get featured sources
   */
  static async getFeaturedSources(): Promise<PrimarySource[]> {
    return apiClient<PrimarySource[]>('/api/v1/sources/enhanced/featured')
  }

  /**
   * Get recently added sources
   */
  static async getRecentSources(limit: number = 20): Promise<PrimarySource[]> {
    return apiClient<PrimarySource[]>(`/api/v1/sources/enhanced/recent?limit=${limit}`)
  }

  /**
   * Export sources data
   */
  static async exportSources(
    sourceIds: string[], 
    format: 'json' | 'csv' | 'pdf'
  ): Promise<Blob> {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/api/v1/sources/enhanced/export?format=${format}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({ source_ids: sourceIds })
      }
    )
    
    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`)
    }
    
    return response.blob()
  }
}