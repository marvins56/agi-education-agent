import { apiClient } from './client'

export interface VoiceMessage {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: string
  audioUrl?: string
  transcription?: string
}

export interface VoiceSession {
  id: string
  studentId: string
  messages: VoiceMessage[]
  createdAt: string
  updatedAt: string
  subject?: string
  status: 'active' | 'completed'
}

export interface TranscriptionRequest {
  audioData: Blob
  language?: string
}

export interface TranscriptionResponse {
  text: string
  confidence: number
  alternatives?: string[]
}

export interface TTSRequest {
  text: string
  voice?: string
  speed?: number
  pitch?: number
}

export interface TTSResponse {
  audioUrl: string
  duration: number
}

export interface VoiceSettings {
  ttsVoice: string
  ttsSpeed: number
  ttsPitch: number
  ttsVolume: number
  autoPlay: boolean
  language: string
  noiseSupression: boolean
  echoCancellation: boolean
  autoGainControl: boolean
  showTranscript: boolean
  showAudioVisualizer: boolean
}

export class VoiceAPI {
  /**
   * Start a new voice chat session
   */
  static async startSession(subject?: string): Promise<VoiceSession> {
    return apiClient<VoiceSession>('/api/v1/voice/sessions', {
      method: 'POST',
      body: JSON.stringify({ subject })
    })
  }

  /**
   * Get voice session by ID
   */
  static async getSession(sessionId: string): Promise<VoiceSession> {
    return apiClient<VoiceSession>(`/api/v1/voice/sessions/${sessionId}`)
  }

  /**
   * Get all voice sessions for current user
   */
  static async getSessions(): Promise<VoiceSession[]> {
    return apiClient<VoiceSession[]>('/api/v1/voice/sessions')
  }

  /**
   * Transcribe audio to text
   */
  static async transcribeAudio(request: TranscriptionRequest): Promise<TranscriptionResponse> {
    const formData = new FormData()
    formData.append('audio', request.audioData, 'recording.webm')
    if (request.language) {
      formData.append('language', request.language)
    }

    return apiClient<TranscriptionResponse>('/api/v1/voice/transcribe', {
      method: 'POST',
      body: formData,
      headers: {} // Let browser set content-type for FormData
    })
  }

  /**
   * Convert text to speech
   */
  static async textToSpeech(request: TTSRequest): Promise<TTSResponse> {
    return apiClient<TTSResponse>('/api/v1/voice/tts', {
      method: 'POST',
      body: JSON.stringify(request)
    })
  }

  /**
   * Process voice message in session
   */
  static async processVoiceMessage(
    sessionId: string,
    audioData: Blob,
    transcription?: string
  ): Promise<VoiceMessage> {
    const formData = new FormData()
    formData.append('audio', audioData, 'message.webm')
    if (transcription) {
      formData.append('transcription', transcription)
    }

    return apiClient<VoiceMessage>(`/api/v1/voice/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: formData,
      headers: {} // Let browser set content-type for FormData
    })
  }

  /**
   * Get voice settings for current user
   */
  static async getSettings(): Promise<VoiceSettings> {
    return apiClient<VoiceSettings>('/api/v1/voice/settings')
  }

  /**
   * Update voice settings for current user
   */
  static async updateSettings(settings: Partial<VoiceSettings>): Promise<VoiceSettings> {
    return apiClient<VoiceSettings>('/api/v1/voice/settings', {
      method: 'PATCH',
      body: JSON.stringify(settings)
    })
  }

  /**
   * End voice session
   */
  static async endSession(sessionId: string): Promise<void> {
    return apiClient<void>(`/api/v1/voice/sessions/${sessionId}/end`, {
      method: 'POST'
    })
  }

  /**
   * Get available TTS voices
   */
  static async getAvailableVoices(): Promise<Array<{
    id: string
    name: string
    language: string
    gender: 'male' | 'female' | 'neutral'
  }>> {
    return apiClient<Array<{
      id: string
      name: string
      language: string
      gender: 'male' | 'female' | 'neutral'
    }>>('/api/v1/voice/voices')
  }

  /**
   * Test voice settings
   */
  static async testVoice(settings: TTSRequest): Promise<TTSResponse> {
    return apiClient<TTSResponse>('/api/v1/voice/test', {
      method: 'POST',
      body: JSON.stringify(settings)
    })
  }
}