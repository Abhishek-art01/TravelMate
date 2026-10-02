import { cleanup, render, screen, within } from '@testing-library/react'
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
  listDestinations: vi.fn(),
  createDestination: vi.fn(),
  updateDestination: vi.fn(),
  listTrips: vi.fn(),
  listReports: vi.fn(),
  updateReport: vi.fn(),
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
    listDestinations: mocks.listDestinations,
    createDestination: mocks.createDestination,
    updateDestination: mocks.updateDestination,
    listTrips: mocks.listTrips,
    listReports: mocks.listReports,
    updateReport: mocks.updateReport,
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

  it('toggles password visibility between masked and plain text on admin login', async () => {
    const user = userEvent.setup()
    render(<App />)
    const passwordInput = await screen.findByLabelText('Password')
    expect(passwordInput).toHaveAttribute('type', 'password')
    const toggleButton = screen.getByRole('button', { name: /show password/i })
    await user.click(toggleButton)
    expect(passwordInput).toHaveAttribute('type', 'text')
    expect(screen.getByRole('button', { name: /hide password/i })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /hide password/i }))
    expect(passwordInput).toHaveAttribute('type', 'password')
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

  it('renders destinations catalog when granted travel.manage and opens add modal', async () => {
    mocks.getSession.mockResolvedValue({ data: { session }, error: null })
    mocks.checkAccess.mockResolvedValue({ authorized: true, permissions: ['travel.manage'] })
    mocks.listDestinations.mockResolvedValue({
      items: [
        {
          id: 'dest-tokyo-1',
          name: 'Tokyo',
          slug: 'tokyo',
          country: 'Japan',
          country_code: 'JPN',
          region: 'Kanto',
          city: 'Tokyo',
          description: 'Vibrant metropolis',
          latitude: 35.6762,
          longitude: 139.6503,
          timezone: 'Asia/Tokyo',
          category: 'city',
          status: 'active',
          aliases: ['Edo', 'Tokio'],
          created_at: '2026-10-01T00:00:00Z',
          updated_at: '2026-10-01T00:00:00Z',
        },
      ],
      total: 1,
      limit: 50,
      offset: 0,
    })
    visit('/admin/destinations')
    const user = userEvent.setup()
    render(<App />)
    expect(await screen.findByRole('heading', { name: /destination catalog/i })).toBeInTheDocument()
    expect(await screen.findByText('Tokyo')).toBeInTheDocument()
    expect(screen.getByText('Edo, Tokio')).toBeInTheDocument()

    // Open add destination modal
    await user.click(screen.getByRole('button', { name: /\+ add destination/i }))
    expect(await screen.findByRole('heading', { name: /add new destination/i })).toBeInTheDocument()
  })

  it('blocks destinations catalog when travel.manage is missing', async () => {
    mocks.getSession.mockResolvedValue({ data: { session }, error: null })
    mocks.checkAccess.mockResolvedValue({ authorized: true, permissions: ['travel.read'] })
    visit('/admin/destinations')
    render(<App />)
    expect(await screen.findByRole('heading', { name: /access not permitted/i })).toBeInTheDocument()
  })

  it('renders trips operations table when granted travel.read and opens inspect modal', async () => {
    mocks.getSession.mockResolvedValue({ data: { session }, error: null })
    mocks.checkAccess.mockResolvedValue({ authorized: true, permissions: ['travel.read'] })
    mocks.listTrips.mockResolvedValue({
      items: [
        {
          id: 'trip-kyoto-1',
          user_id: 'user-traveller-1',
          user_email: 'traveller@example.com',
          destination_id: 'dest-kyoto',
          destination: {
            id: 'dest-kyoto',
            name: 'Kyoto',
            slug: 'kyoto',
            country: 'Japan',
            country_code: 'JPN',
            region: 'Kansai',
            city: 'Kyoto',
            category: 'cultural',
            latitude: 35.0116,
            longitude: 135.7681,
          },
          title: 'Autumn in Kyoto',
          description: 'Exploring temples and maple foliage',
          start_date: '2026-11-01',
          end_date: '2026-11-10',
          status: 'planned',
          visibility: 'discoverable',
          companion_preference: 'open_to_companion',
          party_size: 2,
          intents: ['sightseeing', 'culture'],
          created_at: '2026-10-01T00:00:00Z',
          updated_at: '2026-10-01T00:00:00Z',
        },
      ],
      total: 1,
      limit: 50,
      offset: 0,
    })
    visit('/admin/trips')
    const user = userEvent.setup()
    render(<App />)
    expect(await screen.findByRole('heading', { name: /trip operations/i })).toBeInTheDocument()
    expect(await screen.findByText('Autumn in Kyoto')).toBeInTheDocument()
    expect(screen.getByText(/Kyoto, Japan/)).toBeInTheDocument()

    // Inspect trip
    await user.click(screen.getByRole('button', { name: /inspect/i }))
    const dialog = await screen.findByRole('dialog')
    expect(dialog).toBeInTheDocument()
    expect(within(dialog).getByText('traveller@example.com')).toBeInTheDocument()
    expect(within(dialog).getByText('Exploring temples and maple foliage')).toBeInTheDocument()
  })

  it('blocks trips operations when travel.read is missing', async () => {
    mocks.getSession.mockResolvedValue({ data: { session }, error: null })
    mocks.checkAccess.mockResolvedValue({ authorized: true, permissions: ['users.read'] })
    visit('/admin/trips')
    render(<App />)
    expect(await screen.findByRole('heading', { name: /access not permitted/i })).toBeInTheDocument()
  })

  it('renders reports moderation table when granted moderation.read and allows actioning', async () => {
    mocks.getSession.mockResolvedValue({ data: { session }, error: null })
    mocks.checkAccess.mockResolvedValue({
      authorized: true,
      permissions: ['moderation.read', 'moderation.action'],
    })
    mocks.listReports.mockResolvedValue({
      items: [
        {
          id: 'report-101',
          reporter_id: 'user-reporter-uuid-1',
          reported_id: 'user-bad-uuid-2',
          reason: 'inappropriate_content',
          details: 'User has abusive content in bio',
          status: 'pending',
          reviewed_by_id: null,
          resolution_notes: null,
          created_at: '2026-10-02T10:00:00Z',
          updated_at: '2026-10-02T10:00:00Z',
        },
      ],
      total: 1,
    })
    mocks.updateReport.mockResolvedValue({
      id: 'report-101',
      reporter_id: 'user-reporter-uuid-1',
      reported_id: 'user-bad-uuid-2',
      reason: 'inappropriate_content',
      details: 'User has abusive content in bio',
      status: 'actioned',
      reviewed_by_id: 'mod-1',
      resolution_notes: 'Profile updated and warned',
      created_at: '2026-10-02T10:00:00Z',
      updated_at: '2026-10-02T10:05:00Z',
    })

    visit('/admin/reports')
    const user = userEvent.setup()
    render(<App />)

    expect(await screen.findByRole('heading', { name: /user reports queue/i })).toBeInTheDocument()
    expect(await screen.findByText('inappropriate content')).toBeInTheDocument()
    expect(screen.getByText('User has abusive content in bio')).toBeInTheDocument()

    // Action report
    await user.click(screen.getByRole('button', { name: /^action$/i }))
    const modal = await screen.findByRole('dialog')
    expect(modal).toBeInTheDocument()
    expect(within(modal).getByRole('heading', { name: /action safety report/i })).toBeInTheDocument()

    // Confirm action
    await user.click(within(modal).getByRole('button', { name: /confirm action/i }))
    expect(mocks.updateReport).toHaveBeenCalledWith('report-101', 'actioned', '')
  })

  it('blocks reports moderation when moderation.read is missing', async () => {
    mocks.getSession.mockResolvedValue({ data: { session }, error: null })
    mocks.checkAccess.mockResolvedValue({ authorized: true, permissions: ['travel.read'] })
    visit('/admin/reports')
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
