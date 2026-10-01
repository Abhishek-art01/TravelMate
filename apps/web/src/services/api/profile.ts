import { apiRequest } from './client'

export type AccountSnapshot = {
  user_id: string
  email: string | null
  provider: string
  account_status: string
  profile_status: string
  completion_percentage: number
}

export type ProfileWrite = {
  display_name: string
  date_of_birth?: string
  bio?: string | null
  gender_identity?: string | null
  profile_visibility?: 'public' | 'discoverable' | 'limited' | 'hidden'
  discovery_visibility?: boolean
}

export type OwnProfile = {
  profile_id: string
  user_id: string
  display_name: string | null
  age: number | null
  bio: string | null
  gender_identity: string | null
  profile_visibility: 'public' | 'discoverable' | 'limited' | 'hidden'
  discovery_visibility: boolean
  profile_status: string
  completion_percentage: number
  created_at: string
  updated_at: string
}

export type Preferences = {
  dating_intentions: string[]
  dating_preferences: string[]
  discovery_preferences: string[]
  travel_intentions: string[]
  languages: string[]
  interests: string[]
  minimum_age: number
  maximum_age: number | null
}

export type Privacy = {
  profile_visibility: 'public' | 'discoverable' | 'limited' | 'hidden'
  discovery_visibility: boolean
  location_precision: 'hidden' | 'approximate' | 'destination'
  allow_exact_location_sharing: boolean
  personalization_enabled: boolean
  communications_enabled: boolean
}

export type ProfileMedia = {
  media_id: string
  media_type: 'profile_media'
  processing_status: 'pending' | 'uploading' | 'processing' | 'ready' | 'failed' | 'deleted'
  moderation_status: 'pending_review' | 'approved' | 'rejected' | 'requires_review'
  visibility: 'public' | 'profile_only' | 'private'
  mime_type: string
  size_bytes: number
  width: number | null
  height: number | null
  sort_order: number
  created_at: string
  download_url: string | null
}

export type MediaPage = { items: ProfileMedia[]; next_cursor: string | null }
export type UploadAuthorization = { media_id: string; upload_url: string; expires_at: string; required_headers: Record<string, string> }
export type VerificationSnapshot = { user_id: string; verification_status: string; required_checks: string[] }

export const profileApi = {
  getMe: () => apiRequest<AccountSnapshot>('/me'),
  getProfile: () => apiRequest<OwnProfile>('/me/profile'),
  create: (payload: Required<Pick<ProfileWrite, 'display_name' | 'date_of_birth'>> & ProfileWrite) => apiRequest<OwnProfile>('/profiles', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  update: (payload: ProfileWrite) => apiRequest<OwnProfile>('/me/profile', { method: 'PUT', body: JSON.stringify(payload) }),
  getPreferences: () => apiRequest<Preferences>('/me/preferences'),
  updatePreferences: (payload: Preferences) => apiRequest<Preferences>('/me/preferences', { method: 'PUT', body: JSON.stringify(payload) }),
  getPrivacy: () => apiRequest<Privacy>('/me/privacy'),
  getVerification: () => apiRequest<VerificationSnapshot>('/verification/status'),
  updatePrivacy: (payload: Partial<Privacy>) => apiRequest<Privacy>('/me/privacy', { method: 'PUT', body: JSON.stringify(payload) }),
  getMedia: (after?: string, signal?: AbortSignal) => apiRequest<MediaPage>(`/media?limit=24${after ? `&after=${encodeURIComponent(after)}` : ''}`, { signal }),
  authorizeMediaUpload: (payload: { mime_type: string; size_bytes: number; visibility: ProfileMedia['visibility'] }) => apiRequest<UploadAuthorization>('/media/uploads', { method: 'POST', body: JSON.stringify(payload) }),
  completeMediaUpload: (mediaId: string) => apiRequest<ProfileMedia>(`/media/uploads/${encodeURIComponent(mediaId)}/complete`, { method: 'POST' }),
  deleteMedia: (mediaId: string) => apiRequest<void>(`/media/${encodeURIComponent(mediaId)}`, { method: 'DELETE' }),
  reorderMedia: (mediaId: string, sort_order: number) => apiRequest<ProfileMedia>(`/media/${encodeURIComponent(mediaId)}/order`, { method: 'PATCH', body: JSON.stringify({ sort_order }) }),
}
