export type AppEnvironment = 'development' | 'staging' | 'production';

export interface HealthStatus {
  status: 'ok' | 'ready';
  service: string;
  version: string;
}

export interface UserProfileSummary {
  id: string;
  displayName: string;
  age: number;
  bio?: string;
  city?: string;
  country?: string;
}

export interface ApiErrorResponse {
  message: string;
  code?: string;
  details?: Record<string, unknown>;
}
