export interface RestaurantRecommendation {
  restaurant_name: string;
  location: string;
  cuisine: string;
  estimated_cost: number;
  rating: number;
  final_score: number;
  score_breakdown: {
    rule_score: number;
    llm_score: number;
    personalization_score: number;
    weight_rule: number;
    weight_llm: number;
    weight_personal: number;
  };
  reason: string;
  explanation: string;
  confidence: 'low' | 'medium' | 'high';
}

export interface RecommendationRequest {
  user_id?: string;
  session_id: string;
  location: string;
  budget: 'low' | 'medium' | 'high';
  preferred_cuisine?: string;
  min_rating?: number;
  additional_preferences?: string[];
  top_n?: number;
}

export interface RecommendationResponse {
  total_candidates: number;
  returned_count: number;
  fallback_used: boolean;
  fallback_reason?: string;
  relaxation_steps: string[];
  experiment_variant: string;
  prompt_version: string;
  cache_hit: boolean;
  recommendations: RestaurantRecommendation[];
}

export interface FeedbackRequest {
  user_id?: string;
  session_id: string;
  restaurant_name: string;
  location: string;
  cuisine: string;
  signal_type: 'explicit' | 'implicit';
  signal_name: 'like' | 'dislike' | 'click' | 'dwell' | 'conversion' | 'skip';
  value: number;
}

export interface FeedbackResponse {
  message: string;
  personalization_delta: number;
}

export interface UserProfile {
  user_key: string;
  total_events: number;
  top_cuisines: Record<string, number>;
  favored_budget_bands: Record<string, number>;
  last_activity?: string;
}

export interface FilterOptions {
  location: string;
  budget: 'low' | 'medium' | 'high';
  preferred_cuisine: string;
  min_rating: number;
  top_n: number;
}

export interface SearchFilters {
  location: string;
  budget: 'low' | 'medium' | 'high';
  cuisine: string;
  minRating: number;
  maxDistance?: number;
  dietaryRestrictions?: string[];
}

export interface CuisineOption {
  value: string;
  label: string;
  icon?: string;
}

export interface BudgetOption {
  value: 'low' | 'medium' | 'high';
  label: string;
  range: string;
  min: number;
  max: number;
}

export interface LocationSuggestion {
  name: string;
  type: 'city' | 'locality' | 'landmark';
}

export interface ApiError {
  error: string;
  message: string;
  timestamp: string;
  request_id?: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
  uptime_seconds: number;
  database_status: string;
  llm_status: string;
}

export interface MetricsResponse {
  counters: Record<string, number>;
  gauges: Record<string, number>;
  timers: Record<string, number[]>;
  timestamp: string;
}
