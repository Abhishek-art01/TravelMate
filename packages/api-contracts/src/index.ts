export interface HealthResponse {
  status: 'ok' | 'ready';
  service: string;
  version: string;
}

export interface AuthenticationSession {
  accessToken: string;
  refreshToken?: string;
  expiresAt: string;
}

export interface UserResponse {
  id: string;
  displayName: string;
  email?: string;
  verified: boolean;
}
