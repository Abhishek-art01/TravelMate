import { apiRequest } from './client'

export interface DestinationSummary {
  id: string
  name: string
  slug: string
  country: string
  country_code: string
  region: string
  city: string | null
  category: string
  latitude: number
  longitude: number
}

export interface Destination extends DestinationSummary {
  description: string | null
  timezone: string
  status: string
  aliases: string[]
  created_at: string
  updated_at: string
}

export interface DestinationListResponse {
  items: Destination[]
  total: number
  limit: number
  offset: number
}

export interface Trip {
  id: string
  user_id: string
  destination_id: string
  destination: DestinationSummary
  title: string
  description: string | null
  start_date: string
  end_date: string
  status: 'draft' | 'planned' | 'active' | 'completed' | 'cancelled' | 'archived'
  visibility: 'private' | 'matches_only' | 'discoverable' | 'public'
  companion_preference: 'travelling_alone' | 'open_to_companion' | 'travelling_with_group'
  party_size: number
  intents: string[]
  created_at: string
  updated_at: string
}

export interface PublicTrip {
  id: string
  destination: DestinationSummary
  title: string
  description: string | null
  start_date: string
  end_date: string
  companion_preference: string
  party_size: number
  intents: string[]
  creator_display_name: string | null
  creator_avatar_url: string | null
  creator_verified: boolean
  created_at: string
}

export interface TripCreatePayload {
  destination_id: string
  title: string
  description?: string | null
  start_date: string
  end_date: string
  visibility: string
  companion_preference: string
  party_size: number
  intents: string[]
}

export interface TripUpdatePayload {
  destination_id?: string
  title?: string
  description?: string | null
  start_date?: string
  end_date?: string
  status?: string
  visibility?: string
  companion_preference?: string
  party_size?: number
  intents?: string[]
}

export interface TripListResponse {
  items: Trip[]
  total: number
  limit: number
  offset: number
}

export interface PublicTripListResponse {
  items: PublicTrip[]
  total: number
  limit: number
  offset: number
}

export interface UserLocation {
  id: string
  user_id: string
  latitude: number | null
  longitude: number | null
  approx_latitude: number
  approx_longitude: number
  precision: string
  sharing_mode: string
  source: string
  city: string | null
  region: string | null
  country_code: string | null
  captured_at: string
  updated_at: string
}

export const travelApi = {
  async listDestinations(
    params?: { q?: string; country_code?: string; category?: string; limit?: number; offset?: number },
    signal?: AbortSignal,
  ): Promise<DestinationListResponse> {
    const query = new URLSearchParams()
    if (params?.q) query.set('q', params.q)
    if (params?.country_code) query.set('country_code', params.country_code)
    if (params?.category) query.set('category', params.category)
    if (params?.limit) query.set('limit', String(params.limit))
    if (params?.offset) query.set('offset', String(params.offset))
    const qs = query.toString()
    return apiRequest<DestinationListResponse>(`/destinations${qs ? `?${qs}` : ''}`, { signal })
  },

  async searchDestinations(q: string, limit = 10, signal?: AbortSignal): Promise<DestinationListResponse> {
    const query = new URLSearchParams({ q, limit: String(limit) })
    return apiRequest<DestinationListResponse>(`/destinations/search?${query.toString()}`, { signal })
  },

  async getNearbyDestinations(
    lat: number,
    lon: number,
    radiusKm = 100,
    signal?: AbortSignal,
  ): Promise<{ items: { destination: DestinationSummary; distance_km: number }[]; total: number }> {
    const query = new URLSearchParams({ lat: String(lat), lon: String(lon), radius_km: String(radiusKm) })
    return apiRequest(`/destinations/nearby?${query.toString()}`, { signal })
  },

  async getDestination(idOrSlug: string, signal?: AbortSignal): Promise<Destination> {
    return apiRequest<Destination>(`/destinations/${encodeURIComponent(idOrSlug)}`, { signal })
  },

  async listMyTrips(signal?: AbortSignal): Promise<TripListResponse> {
    return apiRequest<TripListResponse>('/me/trips', { signal })
  },

  async getMyTrip(id: string, signal?: AbortSignal): Promise<Trip> {
    return apiRequest<Trip>(`/me/trips/${encodeURIComponent(id)}`, { signal })
  },

  async createTrip(payload: TripCreatePayload): Promise<Trip> {
    return apiRequest<Trip>('/me/trips', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async updateTrip(id: string, payload: TripUpdatePayload): Promise<Trip> {
    return apiRequest<Trip>(`/me/trips/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },

  async deleteTrip(id: string): Promise<{ ok: boolean; deleted: boolean }> {
    return apiRequest<{ ok: boolean; deleted: boolean }>(`/me/trips/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    })
  },

  async discoverTrips(
    params?: { destination_id?: string; start_date?: string; end_date?: string; companion_preference?: string; intent?: string; limit?: number; offset?: number },
    signal?: AbortSignal,
  ): Promise<PublicTripListResponse> {
    const query = new URLSearchParams()
    if (params?.destination_id) query.set('destination_id', params.destination_id)
    if (params?.start_date) query.set('start_date', params.start_date)
    if (params?.end_date) query.set('end_date', params.end_date)
    if (params?.companion_preference) query.set('companion_preference', params.companion_preference)
    if (params?.intent) query.set('intent', params.intent)
    if (params?.limit) query.set('limit', String(params.limit))
    if (params?.offset) query.set('offset', String(params.offset))
    const qs = query.toString()
    return apiRequest<PublicTripListResponse>(`/trips${qs ? `?${qs}` : ''}`, { signal })
  },

  async getPublicTrip(id: string, signal?: AbortSignal): Promise<PublicTrip> {
    return apiRequest<PublicTrip>(`/trips/${encodeURIComponent(id)}`, { signal })
  },

  async getMyLocation(signal?: AbortSignal): Promise<UserLocation | null> {
    return apiRequest<UserLocation | null>('/me/location', { signal })
  },

  async updateMyLocation(payload: {
    latitude?: number
    longitude?: number
    precision: string
    sharing_mode: string
    source: string
    city?: string
    region?: string
    country_code?: string
  }): Promise<UserLocation> {
    return apiRequest<UserLocation>('/me/location', {
      method: 'PUT',
      body: JSON.stringify(payload),
    })
  },

  async deleteMyLocation(): Promise<{ ok: boolean; deleted: boolean }> {
    return apiRequest<{ ok: boolean; deleted: boolean }>('/me/location', {
      method: 'DELETE',
    })
  },
}
