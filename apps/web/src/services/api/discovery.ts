import { apiRequest } from './client'

export interface DiscoveryTrip {
  id: string
  destination_id: string
  destination_name: string
  city?: string | null
  region?: string | null
  country: string
  country_code: string
  start_date: string
  end_date: string
  companion_preference: string
  party_size: number
  intents: string[]
}

export interface DiscoveryCandidate {
  id: string
  display_name: string
  age: number
  bio?: string | null
  gender_identity?: string | null
  is_verified: boolean
  photo_url?: string | null
  approx_city?: string | null
  approx_country?: string | null
  approx_latitude?: number | null
  approx_longitude?: number | null
  approx_distance_km?: number | null
  trips: DiscoveryTrip[]
  travel_intentions: string[]
  interests: string[]
  languages: string[]
  match_score: number
  match_reasons: string[]
}

export interface DiscoveryListResponse {
  items: DiscoveryCandidate[]
  next_cursor?: string | null
  total: number
}

export interface DiscoveryInteraction {
  id: string
  user_id: string
  target_user_id: string
  interaction_type: 'like' | 'pass'
  is_match: boolean
  created_at: string
}

export interface DiscoveryFilters {
  destination_id?: string
  country_code?: string
  start_date?: string
  end_date?: string
  intent?: string
  gender?: string
  min_age?: number
  max_age?: number
}

export const discoveryApi = {
  async getCandidates(filters: DiscoveryFilters = {}, cursor?: string | null): Promise<DiscoveryListResponse> {
    const params = new URLSearchParams()
    if (filters.destination_id) params.set('destination_id', filters.destination_id)
    if (filters.country_code) params.set('country_code', filters.country_code)
    if (filters.start_date) params.set('start_date', filters.start_date)
    if (filters.end_date) params.set('end_date', filters.end_date)
    if (filters.intent) params.set('intent', filters.intent)
    if (filters.gender) params.set('gender', filters.gender)
    if (filters.min_age) params.set('min_age', filters.min_age.toString())
    if (filters.max_age) params.set('max_age', filters.max_age.toString())
    if (cursor) params.set('cursor', cursor)
    params.set('limit', '10')

    const qs = params.toString()
    return apiRequest<DiscoveryListResponse>(`/api/v1/discovery${qs ? `?${qs}` : ''}`)
  },

  async getCandidateDetail(userId: string): Promise<DiscoveryCandidate> {
    return apiRequest<DiscoveryCandidate>(`/api/v1/discovery/${userId}`)
  },

  async recordInteraction(userId: string, interactionType: 'like' | 'pass'): Promise<DiscoveryInteraction> {
    return apiRequest<DiscoveryInteraction>(`/api/v1/discovery/${userId}/interaction`, {
      method: 'POST',
      body: JSON.stringify({ interaction_type: interactionType }),
    })
  },

  async blockUser(userId: string, reason?: string): Promise<{ id: string }> {
    return apiRequest<{ id: string }>(`/api/v1/me/blocks/${userId}`, {
      method: 'POST',
      body: JSON.stringify({ reason: reason || 'Blocked from discovery' }),
    })
  },

  async unblockUser(userId: string): Promise<void> {
    await apiRequest<void>(`/api/v1/me/blocks/${userId}`, {
      method: 'DELETE',
    })
  },

  async reportUser(reportedId: string, reason: string, details?: string): Promise<{ id: string }> {
    return apiRequest<{ id: string }>('/api/v1/reports', {
      method: 'POST',
      body: JSON.stringify({
        reported_id: reportedId,
        reason,
        details: details || null,
      }),
    })
  },
}
