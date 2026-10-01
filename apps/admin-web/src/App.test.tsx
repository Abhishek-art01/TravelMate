import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { AdminApiError } from './services/api/client'

const mocks = vi.hoisted(() => ({
  getSession: vi.fn(),
  onAuthStateChange: vi.fn(),
  signIn: vi.fn(),
  signOut: vi.fn(),
  checkAccess: vi.fn(),
  getSystemStatus: vi.fn(),
  listVerificationQueue: vi.fn(),
  getVerificationCase: vi.fn(),
  getSignedMediaUrl: vi.fn(),
  startCaseReview: vi.fn(),
  approveCase: vi.fn(),
  rejectCase: vi.fn(),
  requestCaseAction: vi.fn(),
}))

vi.mock('./services/auth/supabase', () => ({
  supabase: { auth: { getSession: mocks.getSession, onAuthStateChange: mocks.onAuthStateChange } },
  signIn: mocks.signIn,
  signOut: mocks.signOut,
}))

vi.mock('./services/api/admin', () => ({
  adminApi: {
    checkAccess: mocks.checkAccess,
    getSystemStatus: mocks.getSystemStatus,
    listVerificationQueue: mocks.listVerificationQueue,
    getVerificationCase: mocks.getVerificationCase,
    getSignedMediaUrl: mocks.getSignedMediaUrl,
    startCaseReview: mocks.startCaseReview,
    approveCase: mocks.approveCase,
    rejectCase: mocks.rejectCase,
    requestCaseAction: mocks.requestCaseAction,
  },
}))

const session = {
  access_token: 'admin-session-token',
  user: { id: 'session-user', email: 'operator@example.com', user_metadata: { role: 'super_admin' } },
}

function visit(path: string) {
  window.history.replaceState({}, '', path)
}

beforeEach(() => {
  vi.clearAllMocks()
  visit('/admin')
  mocks.getSession.mockResolvedValue({ data: { session: null }, error: null })
  mocks.onAuthStateChange.mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } })
  mocks.signOut.mockResolvedValue({ error: null })
  mocks.checkAccess.mockResolvedValue({ authorized: true, permissions: ['system.manage', 'users.read'] })
  mocks.getSystemStatus.mockResolvedValue({ ok: true, service: 'system', role: 'super_admin', permissions: ['system.manage'] })
})

afterEach(cleanup)

describe('TravelMate Admin Web security', () => {
  it('redirects an unauthenticated visitor to the admin-specific login', async () => {
    render(<App />)
    expect(await screen.findByRole('heading', { name: /admin sign in/i })).toBeInTheDocument()
  })

  it('denies an authenticated regular user using the backend 403', async () => {
    mocks.getSession.mockResolvedValue({ data: { session }, error: null })
    mocks.checkAccess.mockRejectedValue(new AdminApiError('Forbidden', 403, 'FORBIDDEN'))
    render(<App />)
    expect(await screen.findByRole('heading', { name: /access not permitted/i })).toBeInTheDocument()
    expect(screen.getByText(/you don’t have permission/i)).toBeInTheDocument()
  })

  it('allows an authorized scoped admin and renders no mock statistics', async () => {
    mocks.getSession.mockResolvedValue({ data: { session }, error: null })
    mocks.checkAccess.mockResolvedValue({ authorized: true, permissions: ['system.manage', 'users.read'] })
    render(<App />)
    expect(await screen.findByRole('heading', { name: /admin workspace/i })).toBeInTheDocument()
    expect(await screen.findByText(/operational metrics are not connected yet/i)).toBeInTheDocument()
    expect(screen.queryByText('128.4K')).not.toBeInTheDocument()
    expect(mocks.getSystemStatus).toHaveBeenCalledOnce()
  })

  it('does not expose user pages when the backend does not grant users.read', async () => {
    mocks.getSession.mockResolvedValue({ data: { session }, error: null })
    mocks.checkAccess.mockResolvedValue({ authorized: true, permissions: ['audit.read'] })
    visit('/admin/users')
    render(<App />)
    expect(await screen.findByRole('heading', { name: /access not permitted/i })).toBeInTheDocument()
  })

  it('renders the verification queue when granted verification.read', async () => {
    mocks.getSession.mockResolvedValue({ data: { session }, error: null })
    mocks.checkAccess.mockResolvedValue({ authorized: true, permissions: ['verification.read'] })
    mocks.listVerificationQueue.mockResolvedValue({
      items: [
        {
          id: 'case-12345678-abcd',
          user_id: 'u-1',
          user_display_name: 'Test Voyager',
          verification_type: 'government_id',
          status: 'submitted',
          attempt_number: 1,
          submitted_at: '2026-10-01T00:00:00Z',
          reviewer_id: null,
          expires_at: null,
          media_count: 1,
        },
      ],
      total: 1,
    })
    visit('/admin/verification')
    render(<App />)
    expect(await screen.findByRole('heading', { name: /verification review queue/i })).toBeInTheDocument()
    expect(await screen.findByText('Test Voyager')).toBeInTheDocument()
    expect(mocks.listVerificationQueue).toHaveBeenCalled()
  })

  it('blocks verification queue when verification.read is missing', async () => {
    mocks.getSession.mockResolvedValue({ data: { session }, error: null })
    mocks.checkAccess.mockResolvedValue({ authorized: true, permissions: ['users.read'] })
    visit('/admin/verification')
    render(<App />)
    expect(await screen.findByRole('heading', { name: /access not permitted/i })).toBeInTheDocument()
  })

  it('logs out from the authenticated console', async () => {
    mocks.getSession.mockResolvedValue({ data: { session }, error: null })
    const user = userEvent.setup()
    render(<App />)
    await user.click(await screen.findByRole('button', { name: /sign out/i }))
    expect(await screen.findByRole('heading', { name: /admin sign in/i })).toBeInTheDocument()
    expect(mocks.signOut).toHaveBeenCalledOnce()
  })
})
