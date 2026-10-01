import { apiRequest } from './client'

export type ProfileSnapshot = {
  user_id: string
  email: string | null
  role: string
  account_status: string
  provider: string
}

export type ProfileCreate = {
  display_name: string
  date_of_birth: string
  bio?: string
}

export type ProfileCreated = {
  profile: { profile_id: string; display_name: string; age: number; bio: string | null; status: string }
  user: { user_id: string; role?: string }
  privacy: { location_visibility: string; verification_media_private: boolean }
}

export type VerificationSnapshot = {
  user_id: string
  verification_status: string
  required_checks: string[]
}

export const profileApi = {
  getMe: () => apiRequest<ProfileSnapshot>('/users/me'),
  create: (payload: ProfileCreate) => apiRequest<ProfileCreated>('/profiles', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  getVerification: () => apiRequest<VerificationSnapshot>('/verification/status'),
}
