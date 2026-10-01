import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({ getSession: vi.fn() }))

vi.mock('../auth/auth', () => ({ supabase: { auth: { getSession: mocks.getSession } } }))
vi.mock('../../app/config/env', () => ({ appConfig: { apiBaseUrl: 'https://api.travelmate.test/api/v1' } }))

import { ApiRequestError, apiRequest } from './client'
import { profileApi } from './profile'

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn())
  mocks.getSession.mockResolvedValue({ data: { session: { access_token: 'verified-session-token' } } })
})

afterEach(() => vi.unstubAllGlobals())

describe('central API client', () => {
  it('attaches the session token and returns JSON data', async () => {
    vi.mocked(fetch).mockResolvedValue(new Response(JSON.stringify({ user_id: 'user-1' }), { status: 200 }))
    const result = await apiRequest<{ user_id: string }>('/users/me')
    expect(result).toEqual({ user_id: 'user-1' })
    expect(vi.mocked(fetch).mock.calls[0]?.[1]?.headers).toBeInstanceOf(Headers)
    expect(new Headers(vi.mocked(fetch).mock.calls[0]?.[1]?.headers).get('Authorization')).toBe('Bearer verified-session-token')
  })

  it('returns a safe error with request ID and invalidates auth on 401', async () => {
    const unauthorized = vi.fn()
    window.addEventListener('travelmate:unauthorized', unauthorized)
    vi.mocked(fetch).mockResolvedValue(new Response(JSON.stringify({ error: { code: 'AUTHENTICATION_REQUIRED', message: 'internal detail' } }), {
      status: 401,
      headers: { 'X-Request-ID': 'request-42', 'Content-Type': 'application/json' },
    }))
    try {
      await expect(apiRequest('/users/me')).rejects.toMatchObject({
        name: 'ApiRequestError',
        status: 401,
        code: 'AUTHENTICATION_REQUIRED',
        requestId: 'request-42',
        message: 'Your session has ended. Sign in again.',
      })
      expect(unauthorized).toHaveBeenCalledOnce()
    } finally {
      window.removeEventListener('travelmate:unauthorized', unauthorized)
    }
  })

  it('provides a non-enumerating error when a profile is forbidden', async () => {
    vi.mocked(fetch).mockResolvedValue(new Response('{}', { status: 403 }))
    await expect(apiRequest('/admin/system')).rejects.toBeInstanceOf(ApiRequestError)
    await expect(apiRequest('/admin/system')).rejects.toMatchObject({
      message: 'You don’t have access to this action.',
      status: 403,
    })
  })

  it('sends profile creation using the backend profile schema', async () => {
    vi.mocked(fetch).mockResolvedValue(new Response(JSON.stringify({ profile: { profile_id: 'profile-1' } }), { status: 200 }))
    await profileApi.create({ display_name: 'Mira', date_of_birth: '1995-01-01', bio: 'Mountain walks' })
    expect(vi.mocked(fetch).mock.calls[0]?.[0]).toBe('https://api.travelmate.test/api/v1/profiles')
    expect(vi.mocked(fetch).mock.calls[0]?.[1]?.method).toBe('POST')
    expect(vi.mocked(fetch).mock.calls[0]?.[1]?.body).toBe(JSON.stringify({ display_name: 'Mira', date_of_birth: '1995-01-01', bio: 'Mountain walks' }))
  })
})
