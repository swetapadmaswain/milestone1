import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios';
import { 
  RecommendationRequest, 
  RecommendationResponse, 
  FeedbackRequest, 
  FeedbackResponse, 
  UserProfile,
  HealthResponse,
  MetricsResponse,
  ApiError 
} from '../types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiService {
  private client: AxiosInstance;
  private sessionId: string;

  constructor() {
    this.sessionId = this.getOrCreateSessionId();
    
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/api/v1`,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': this.sessionId,
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('api_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        // Add user ID if available
        const userId = localStorage.getItem('user_id');
        if (userId) {
          config.headers['X-User-ID'] = userId;
        }

        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        const status = error.response?.status;
        if (status === 429) {
          console.warn('Rate limit exceeded. Please try again later.');
        } else if (status && status >= 500) {
          console.error('Server error:', error.response?.data);
        }
        return Promise.reject(error);
      }
    );
  }

  private getOrCreateSessionId(): string {
    if (typeof window !== 'undefined') {
      let sessionId = localStorage.getItem('session_id');
      if (!sessionId) {
        sessionId = `sess_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        localStorage.setItem('session_id', sessionId);
      }
      return sessionId;
    }
    return '';
  }

  // Recommendations
  async getRecommendations(request: Omit<RecommendationRequest, 'session_id'>): Promise<RecommendationResponse> {
    const response = await this.client.post<RecommendationResponse>('/recommend', {
      ...request,
      session_id: this.sessionId,
    });
    return response.data;
  }

  // Feedback
  async submitFeedback(feedback: Omit<FeedbackRequest, 'session_id'>): Promise<FeedbackResponse> {
    const response = await this.client.post<FeedbackResponse>('/feedback', {
      ...feedback,
      session_id: this.sessionId,
    });
    return response.data;
  }

  // User Profile
  async getUserProfile(userId?: string): Promise<UserProfile> {
    const params = userId ? { user_id: userId } : {};
    const response = await this.client.get<UserProfile>(`/profile/${this.sessionId}`, { params });
    return response.data;
  }

  // Health Check
  async checkHealth(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health');
    return response.data;
  }

  // Metrics
  async getMetrics(): Promise<MetricsResponse> {
    const response = await this.client.get<MetricsResponse>('/metrics');
    return response.data;
  }

  // Data Ingestion
  async triggerDataIngestion(): Promise<{ message: string; raw_records: number; prepared_records: number }> {
    const response = await this.client.post('/ingest');
    return response.data;
  }

  // Generic request method for flexibility
  async request<T>(config: AxiosRequestConfig): Promise<T> {
    const response = await this.client.request<T>(config);
    return response.data;
  }

  // Get session ID for external use
  getSessionId(): string {
    return this.sessionId;
  }

  // Set user ID after authentication
  setUserId(userId: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('user_id', userId);
    }
  }

  // Clear user session
  clearSession(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('user_id');
      localStorage.removeItem('session_id');
      this.sessionId = this.getOrCreateSessionId();
    }
  }
}

// Export singleton instance
export const apiService = new ApiService();

// React Query hooks helpers
export const recommendationKeys = {
  all: ['recommendations'] as const,
  lists: () => [...recommendationKeys.all, 'list'] as const,
  list: (filters: RecommendationRequest) => [...recommendationKeys.lists(), filters] as const,
  details: () => [...recommendationKeys.all, 'detail'] as const,
  detail: (id: string) => [...recommendationKeys.details(), id] as const,
};

export const profileKeys = {
  all: ['profile'] as const,
  detail: (sessionId: string) => [...profileKeys.all, sessionId] as const,
};
