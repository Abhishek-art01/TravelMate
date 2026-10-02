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

export type AdminDestination = {
  id: string
  name: string
  slug: string
  country: string
  country_code: string
  region: string
  city?: string | null
  description?: string | null
  latitude: number
  longitude: number
  timezone: string
  category: string
  status: string
  aliases: string[]
  created_at: string
  updated_at: string
}

export type AdminDestinationCreate = {
  name: string
  slug: string
  country: string
  country_code: string
  region: string
  city?: string | null
  description?: string | null
  latitude: number
  longitude: number
  timezone?: string
  category?: string
  status?: string
  aliases?: string[]
}

export type AdminDestinationUpdate = Partial<AdminDestinationCreate>

export type AdminDestinationListResponse = {
  items: AdminDestination[]
  total: number
  limit: number
  offset: number
}

export type AdminTrip = {
  id: string
  user_id: string
  user_email?: string | null
  destination_id: string
  destination: {
    id: string
    name: string
    slug: string
    country: string
    country_code: string
    region: string
    city?: string | null
    category: string
    latitude: number
    longitude: number
  }
  title: string
  description?: string | null
  start_date: string
  end_date: string
  status: string
  visibility: string
  companion_preference: string
  party_size: number
  intents: string[]
  created_at: string
  updated_at: string
}

export type AdminTripListResponse = {
  items: AdminTrip[]
  total: number
  limit: number
  offset: number
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
  listDestinations: (
    filters?: { query?: string; category?: string; status?: string; limit?: number; offset?: number },
    signal?: AbortSignal,
  ) => {
    const params = new URLSearchParams()
    if (filters?.query) params.append('query', filters.query)
    if (filters?.category && filters.category !== 'all') params.append('category', filters.category)
    if (filters?.status && filters.status !== 'all') params.append('status', filters.status)
    if (filters?.limit) params.append('limit', String(filters.limit))
    if (filters?.offset) params.append('offset', String(filters.offset))
    const qs = params.toString() ? `?${params.toString()}` : ''
    return adminApiRequest<AdminDestinationListResponse>(`/admin/destinations${qs}`, { signal })
  },
  createDestination: (payload: AdminDestinationCreate) =>
    adminApiRequest<AdminDestination>('/admin/destinations', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  updateDestination: (id: string, payload: AdminDestinationUpdate) =>
    adminApiRequest<AdminDestination>(`/admin/destinations/${encodeURIComponent(id)}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  listTrips: (
    filters?: { user_id?: string; destination_id?: string; status?: string; visibility?: string; limit?: number; offset?: number },
    signal?: AbortSignal,
  ) => {
    const params = new URLSearchParams()
    if (filters?.user_id) params.append('user_id', filters.user_id)
    if (filters?.destination_id) params.append('destination_id', filters.destination_id)
    if (filters?.status && filters.status !== 'all') params.append('status', filters.status)
    if (filters?.visibility && filters.visibility !== 'all') params.append('visibility', filters.visibility)
    if (filters?.limit) params.append('limit', String(filters.limit))
    if (filters?.offset) params.append('offset', String(filters.offset))
    const qs = params.toString() ? `?${params.toString()}` : ''
    return adminApiRequest<AdminTripListResponse>(`/admin/trips${qs}`, { signal })
  },
  listReports: (status?: string, limit?: number, offset?: number, signal?: AbortSignal) => {
    const params = new URLSearchParams()
    if (status && status !== 'all') params.append('status', status)
    if (limit) params.append('limit', String(limit))
    if (offset) params.append('offset', String(offset))
    const qs = params.toString() ? `?${params.toString()}` : ''
    return adminApiRequest<AdminReportListResponse>(`/admin/reports${qs}`, { signal })
  },
  updateReport: (
    reportId: string,
    status: 'pending' | 'under_review' | 'actioned' | 'dismissed',
    resolutionNotes?: string,
  ) =>
    adminApiRequest<AdminReport>(`/admin/reports/${encodeURIComponent(reportId)}`, {
      method: 'PATCH',
      body: JSON.stringify({ status, resolution_notes: resolutionNotes || null }),
    }),
}

export type AdminReport = {
  id: string
  reporter_id: string
  reported_id: string
  reason: string
  details?: string | null
  status: 'pending' | 'under_review' | 'actioned' | 'dismissed'
  reviewed_by_id?: string | null
  resolution_notes?: string | null
  created_at: string
  updated_at: string
}

export type AdminReportListResponse = {
  items: AdminReport[]
  total: number
}

