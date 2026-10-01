import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({ getSession: vi.fn() }))

vi.mock('../auth/supabase', () => ({ supabase: { auth: { getSession: mocks.getSession } } }))
vi.mock('../../app/config/env', () => ({ adminConfig: { apiBaseUrl: 'https://admin-api.travelmate.test/api/v1' } }))

import { AdminApiError, adminApiRequest } from './client'

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn())
  mocks.getSession.mockResolvedValue({ data: { session: { access_token: 'signed-access-token' } }, error: null })
})

afterEach(() => vi.unstubAllGlobals())

describe('Admin API client', () => {
  it('attaches the current Supabase access token', async () => {
    vi.mocked(fetch).mockResolvedValue(new Response(JSON.stringify({ authorized: true }), { status: 200 }))
    await expect(adminApiRequest('/admin/access')).resolves.toEqual({ authorized: true })
    const call = vi.mocked(fetch).mock.calls[0]
    expect(call?.[0]).toBe('https://admin-api.travelmate.test/api/v1/admin/access')
    expect(new Headers(call?.[1]?.headers).get('Authorization')).toBe('Bearer signed-access-token')
  })

  it('normalizes backend 403 responses and preserves request IDs', async () => {
    vi.mocked(fetch).mockResolvedValue(new Response(JSON.stringify({ error: { code: 'FORBIDDEN' } }), {
      status: 403,
      headers: { 'Content-Type': 'application/json', 'X-Request-ID': 'admin-request-7' },
    }))
    await expect(adminApiRequest('/admin/users')).rejects.toMatchObject({
      name: 'AdminApiError',
      status: 403,
      code: 'FORBIDDEN',
      requestId: 'admin-request-7',
      message: 'You do not have permission to access the administration console.',
    })
  })

  it('does not leak backend message text', async () => {
    vi.mocked(fetch).mockResolvedValue(new Response(JSON.stringify({ error: { message: 'private internal detail' } }), { status: 500 }))
    await expect(adminApiRequest('/admin/system')).rejects.toBeInstanceOf(AdminApiError)
    await expect(adminApiRequest('/admin/system')).rejects.toMatchObject({ message: 'The service had a problem. Try again later.' })
  })
})
