// Auth types
export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Chat types
export interface CreateSessionRequest {
  subject?: string;
  topic?: string;
  mode?: string;
}

export interface ChatSession {
  session_id: string;
  created_at: string;
  mode: string;
  subject?: string;
  topic?: string;
}

export interface MessageRequest {
  content: string;
  session_id: string;
  subject?: string;
  topic?: string;
  provider?: string;
  model?: string;
}

export interface MessageResponse {
  text: string;
  session_id: string;
  sources: string[];
  suggested_actions: string[];
  metadata: Record<string, unknown>;
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
}

export interface ChatHistory {
  messages: ChatMessage[];
}

// Session types
export interface SessionListResponse {
  sessions: ChatSession[];
  total: number;
}

// Model types
export interface ModelProvider {
  provider: string;
  available: boolean;
  models: string[];
  base_url?: string;
}

export interface CurrentModel {
  provider: string;
  model: string;
}

// Generic API error
export interface ApiError {
  detail: string;
}

// Profile types
export interface Profile {
  name: string;
  email: string;
  learning_style: string;
  pace: string;
  grade_level: string | null;
  strengths: string[];
  weaknesses: string[];
  preferences: Record<string, unknown>;
}

export interface ProfileUpdateRequest {
  learning_style?: string;
  pace?: string;
  grade_level?: string;
}

export interface TopicMastery {
  subject: string;
  topic: string;
  mastery_score: number;
  confidence: number;
  attempts: number;
  last_assessed: string | null;
}

export interface MasteryBySubject {
  subject: string;
  topics: TopicMastery[];
  average_mastery: number;
}

// Analytics types
export interface AnalyticsSummary {
  total_events: number;
  active_days: number;
  streak: number;
  engagement_rate: number;
  quiz_score_trend: { scores: number[] };
}

export interface ActivityHeatmap {
  date: string;
  count: number;
}

export interface Alert {
  type: string;
  severity: string;
  message: string;
}

// Learning Path types
export interface RecommendedTopic {
  topic_id: string;
  subject: string;
  topic: string;
  display_name: string;
  difficulty: string;
  estimated_minutes: number;
  reason: string;
}

export interface ReviewDue {
  id: string;
  topic_id: string;
  next_review_date: string;
  interval_days: number;
  easiness_factor: number;
  review_count: number;
}

// Library/Content types
export interface DocumentItem {
  id: string;
  title: string;
  subject: string | null;
  file_type: string;
  status: string;
  chunk_count: number;
  created_at: string | null;
}

export interface DocumentListResponse {
  items: DocumentItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface SearchResultItem {
  content_preview: string;
  metadata: Record<string, unknown>;
  distance: number;
  citation: Record<string, unknown>;
}

export interface SearchResponse {
  query: string;
  results: SearchResultItem[];
  total: number;
}

// Assessment types
export interface Assessment {
  id: string;
  title: string;
  subject: string;
  type: string;
  question_count: number;
  total_points: number;
  created_at: string;
  due_at: string | null;
}

export interface QuestionResponse {
  id: string;
  type: string;
  content: string;
  options: string[] | null;
  points: number;
  difficulty: string;
}

export interface QuickQuizRequest {
  subject: string;
  topic: string;
  question_count: number;
  difficulty: string;
}

export interface QuickQuizResponse {
  subject: string;
  topic: string;
  questions: QuizQuestion[];
  question_count: number;
}

export interface QuizQuestion {
  type: string;
  content: string;
  options: string[] | null;
  points: number;
  difficulty: string;
  correct_answer: string;
}

export interface SubmissionResponse {
  id: string;
  assessment_id: string;
  total_score: number;
  max_score: number;
  percentage: number;
  grades: GradeResult[];
  submitted_at: string;
  graded_at: string;
}

export interface GradeResult {
  question_id: string;
  score: number;
  max_score: number;
  feedback: string;
  correct: boolean;
}

// Upload types
export interface UploadFileResponse {
  document_id: string;
  status: string;
  chunk_count: number;
  filename: string;
}

export interface UploadUrlRequest {
  url: string;
  title?: string;
  subject?: string;
  grade_level?: string;
}

export interface UploadUrlResponse {
  document_id: string;
  status: string;
  chunk_count: number;
}
