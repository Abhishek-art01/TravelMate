import { adminApiRequest } from './client'

export type AdminAccess = {
  authorized: true
  permissions: string[]
}

export type SystemStatus = {
  ok: boolean
  service: string
  role: string
  permissions: string[]
}

export type AdminVerificationSummary = {
  id: string
  user_id: string
  user_display_name?: string | null
  user_email?: string | null
  verification_type: string
  status: string
  attempt_number: number
  submitted_at?: string | null
  reviewed_at?: string | null
  reviewed_by?: string | null
}

export type AdminVerificationQueue = {
  items: AdminVerificationSummary[]
  total: number
  limit: number
  offset: number
}

export type AdminVerificationEvent = {
  id: string
  event_type: string
  actor_type: string
  actor_id?: string | null
  details?: string | null
  created_at: string
}

export type AdminVerificationAttempt = {
  id: string
  attempt_number: number
  status: string
  failure_reason?: string | null
  created_at: string
}

export type AdminVerificationMedia = {
  media_id: string
  media_type: string
  mime_type: string
  size_bytes: number
  created_at: string
}

export type AdminVerificationDetail = {
  id: string
  user_id: string
  user_display_name?: string | null
  user_email?: string | null
  verification_type: string
  status: string
  attempt_number: number
  submitted_at?: string | null
  reviewed_at?: string | null
  reviewed_by?: string | null
  review_decision_reason?: string | null
  created_at: string
  updated_at: string
  attempts: AdminVerificationAttempt[]
  events: AdminVerificationEvent[]
  media: AdminVerificationMedia[]
}

export type AdminSignedMediaUrl = {
  media_id: string
  download_url: string
  expires_at: string
}

export const adminApi = {
  checkAccess: (signal?: AbortSignal) => adminApiRequest<AdminAccess>('/admin/access', { signal }),
  getSystemStatus: (signal?: AbortSignal) => adminApiRequest<SystemStatus>('/admin/system', { signal }),
  listVerificationQueue: (status?: string, type?: string, signal?: AbortSignal) => {
    const params = new URLSearchParams()
    if (status && status !== 'all') params.append('status', status)
    if (type && type !== 'all') params.append('type', type)
    const qs = params.toString() ? `?${params.toString()}` : ''
    return adminApiRequest<AdminVerificationQueue>(`/admin/verification${qs}`, { signal })
  },
  getVerificationCase: (id: string, signal?: AbortSignal) =>
    adminApiRequest<AdminVerificationDetail>(`/admin/verification/${encodeURIComponent(id)}`, { signal }),
  getSignedMediaUrl: (verificationId: string, mediaId: string) =>
    adminApiRequest<AdminSignedMediaUrl>(
      `/admin/verification/${encodeURIComponent(verificationId)}/media/${encodeURIComponent(mediaId)}/url`,
    ),
  startCaseReview: (verificationId: string) =>
    adminApiRequest<AdminVerificationSummary>(`/admin/verification/${encodeURIComponent(verificationId)}/review`, {
      method: 'POST',
    }),
  approveCase: (verificationId: string, reason?: string) =>
    adminApiRequest<AdminVerificationSummary>(`/admin/verification/${encodeURIComponent(verificationId)}/approve`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),
  rejectCase: (verificationId: string, reason: string) =>
    adminApiRequest<AdminVerificationSummary>(`/admin/verification/${encodeURIComponent(verificationId)}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),
  requestCaseAction: (verificationId: string, reason: string) =>
    adminApiRequest<AdminVerificationSummary>(
      `/admin/verification/${encodeURIComponent(verificationId)}/request-action`,
      {
        method: 'POST',
        body: JSON.stringify({ reason }),
      },
    ),
}
