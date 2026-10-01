import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'

const mocks = vi.hoisted(() => ({
  getSessionSnapshot: vi.fn(), getSession: vi.fn(), signInWithPassword: vi.fn(), signUpWithEmail: vi.fn(),
  signInWithOAuth: vi.fn(), sendPasswordReset: vi.fn(), signOut: vi.fn(), onAuthStateChange: vi.fn(),
  getMe: vi.fn(), getProfile: vi.fn(), getPreferences: vi.fn(), getPrivacy: vi.fn(), getVerification: vi.fn(),
  createProfile: vi.fn(), updateProfile: vi.fn(), updatePreferences: vi.fn(), updatePrivacy: vi.fn(),
  getMedia: vi.fn(), authorizeMediaUpload: vi.fn(), completeMediaUpload: vi.fn(), deleteMedia: vi.fn(), reorderMedia: vi.fn(),
}))

vi.mock('./services/auth/auth', () => ({
  supabase: { auth: { getSession: mocks.getSession, onAuthStateChange: mocks.onAuthStateChange } },
  getSessionSnapshot: mocks.getSessionSnapshot,
  signInWithPassword: mocks.signInWithPassword,
  signUpWithEmail: mocks.signUpWithEmail,
  signInWithOAuth: mocks.signInWithOAuth,
  sendPasswordReset: mocks.sendPasswordReset,
  signOut: mocks.signOut,
}))

vi.mock('./app/config/env', () => ({
  appConfig: { apiBaseUrl: 'http://localhost:8000/api/v1', supabaseUrl: 'https://unit-test.supabase.co', supabaseAnonKey: 'public-test-key' },
  isSupabaseConfigured: true,
  configuredOAuthProviders: [],
}))

vi.mock('./services/api/profile', () => ({
  profileApi: {
    getMe: mocks.getMe, getProfile: mocks.getProfile, getPreferences: mocks.getPreferences,
    getPrivacy: mocks.getPrivacy, getVerification: mocks.getVerification, create: mocks.createProfile,
    update: mocks.updateProfile, updatePreferences: mocks.updatePreferences, updatePrivacy: mocks.updatePrivacy,
    getMedia: mocks.getMedia, authorizeMediaUpload: mocks.authorizeMediaUpload,
    completeMediaUpload: mocks.completeMediaUpload, deleteMedia: mocks.deleteMedia, reorderMedia: mocks.reorderMedia,
  },
}))

const userSession = {
  access_token: 'access-token-test',
  user: { id: 'user-1', email: 'traveller@example.com', user_metadata: { display_name: 'Mira' } },
} as unknown as { access_token: string; user: { id: string; email: string; user_metadata: { display_name: string } } }

function visit(path: string) {
  window.history.replaceState({}, '', path)
}

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  sessionStorage.clear()
  visit('/')
  mocks.getSessionSnapshot.mockResolvedValue({ session: null, user: null })
  mocks.getSession.mockResolvedValue({ data: { session: null }, error: null })
  mocks.onAuthStateChange.mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } })
  mocks.signOut.mockResolvedValue({ error: null })
  mocks.getMe.mockResolvedValue({ user_id: 'user-1', email: 'traveller@example.com', provider: 'email', profile_status: 'draft', account_status: 'active', completion_percentage: 0 })
  mocks.getProfile.mockResolvedValue({ profile_id: 'profile-1', user_id: 'user-1', display_name: null, age: null, bio: null, gender_identity: null, profile_visibility: 'hidden', discovery_visibility: false, profile_status: 'draft', completion_percentage: 0, created_at: '', updated_at: '' })
  mocks.getPreferences.mockResolvedValue({ dating_intentions: [], dating_preferences: [], discovery_preferences: [], travel_intentions: [], languages: [], interests: [], minimum_age: 18, maximum_age: null })
  mocks.getPrivacy.mockResolvedValue({ profile_visibility: 'hidden', discovery_visibility: false, location_precision: 'approximate', allow_exact_location_sharing: false, personalization_enabled: false, communications_enabled: true })
  mocks.getVerification.mockResolvedValue({ user_id: 'user-1', verification_status: 'not_started', required_checks: [] })
  mocks.getMedia.mockResolvedValue({ items: [], next_cursor: null })
  mocks.createProfile.mockImplementation(async (payload) => {
    mocks.getProfile.mockResolvedValue({ profile_id: 'profile-1', user_id: 'user-1', display_name: payload.display_name, age: 31, bio: payload.bio ?? null, gender_identity: payload.gender_identity ?? null, profile_visibility: 'hidden', discovery_visibility: false, profile_status: 'draft', completion_percentage: 40, created_at: '', updated_at: '' })
    return { profile_id: 'profile-1', user_id: 'user-1', ...payload, completion_percentage: 40 }
  })
  mocks.updateProfile.mockResolvedValue({ profile_id: 'profile-1' })
  mocks.updatePreferences.mockResolvedValue({})
  mocks.updatePrivacy.mockImplementation(async (patch) => {
    const next = { ...(await mocks.getPrivacy()), ...patch }
    mocks.getPrivacy.mockResolvedValue(next)
    return next
  })
  mocks.authorizeMediaUpload.mockResolvedValue({ media_id: 'media-1', upload_url: 'https://storage.test/upload', expires_at: '', required_headers: { 'Content-Type': 'image/png' } })
  mocks.completeMediaUpload.mockResolvedValue({ media_id: 'media-1' })
  mocks.deleteMedia.mockResolvedValue(undefined)
  mocks.reorderMedia.mockResolvedValue({ media_id: 'media-1' })
})

afterEach(cleanup)

describe('TravelMate user app', () => {
  it('redirects unauthenticated visitors to login', async () => {
    render(<App />)
    expect(await screen.findByRole('heading', { name: /your next story starts here/i })).toBeInTheDocument()
  })

  it('restores a Supabase session and opens the member home', async () => {
    mocks.getSessionSnapshot.mockResolvedValue({ session: userSession, user: userSession.user })
    render(<App />)
    expect(await screen.findByText(/good to have you here/i)).toBeInTheDocument()
    expect(await screen.findByText(/not started/i)).toBeInTheDocument()
  })

  it('shows an account-neutral error after a failed login', async () => {
    visit('/login')
    mocks.signInWithPassword.mockResolvedValue({ error: new Error('invalid credentials') })
    const user = userEvent.setup()
    render(<App />)
    await user.type(await screen.findByLabelText('Email address'), 'traveller@example.com')
    await user.type(screen.getByLabelText('Password'), 'incorrect-pass')
    await user.click(screen.getByRole('button', { name: /sign in/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('We couldn’t complete that request.')
    expect(screen.queryByText(/invalid credentials/i)).not.toBeInTheDocument()
  })

  it('creates an account through Supabase and communicates email confirmation', async () => {
    visit('/signup')
    mocks.signUpWithEmail.mockResolvedValue({ data: { session: null, user: { id: 'new-user' } }, error: null })
    const user = userEvent.setup()
    render(<App />)
    await user.type(await screen.findByLabelText('Email address'), 'new@example.com')
    await user.type(screen.getByLabelText('Password'), 'long-enough-password')
    await user.click(screen.getByRole('button', { name: /create account/i }))
    expect(await screen.findByRole('status')).toHaveTextContent(/check your inbox/i)
    expect(mocks.signUpWithEmail).toHaveBeenCalledWith('new@example.com', 'long-enough-password')
  })

  it('signs out and returns the user to login', async () => {
    mocks.getSessionSnapshot.mockResolvedValue({ session: userSession, user: userSession.user })
    const user = userEvent.setup()
    render(<App />)
    await user.click(await screen.findByRole('button', { name: /sign out/i }))
    expect(await screen.findByRole('heading', { name: /your next story starts here/i })).toBeInTheDocument()
    expect(mocks.signOut).toHaveBeenCalledOnce()
  })

  it('expires the local session when the API returns an unauthorized event', async () => {
    mocks.getSessionSnapshot.mockResolvedValue({ session: userSession, user: userSession.user })
    render(<App />)
    expect(await screen.findByRole('button', { name: /sign out/i })).toBeInTheDocument()
    window.dispatchEvent(new Event('travelmate:unauthorized'))
    expect(await screen.findByRole('heading', { name: /your next story starts here/i })).toBeInTheDocument()
    expect(mocks.signOut).toHaveBeenCalledOnce()
  })

  it('persists privacy settings to the API and avoids localStorage', async () => {
    mocks.getSessionSnapshot.mockResolvedValue({ session: userSession, user: userSession.user })
    visit('/privacy')
    const user = userEvent.setup()
    const firstRender = render(<App />)
    await user.click(await screen.findByRole('checkbox', { name: /allow profile discovery/i }))
    expect(await screen.findByRole('status')).toHaveTextContent(/saved to your account/i)
    expect(mocks.updatePrivacy).toHaveBeenCalledWith({ discovery_visibility: true })
    expect(localStorage.getItem('travelmate-privacy-preferences')).toBeNull()
    firstRender.unmount()
    render(<App />)
    expect(await screen.findByRole('checkbox', { name: /allow profile discovery/i })).toBeChecked()
  })

  it('asks users to confirm 18+ and blocks underage onboarding dates', async () => {
    mocks.getSessionSnapshot.mockResolvedValue({ session: userSession, user: userSession.user })
    visit('/onboarding')
    const user = userEvent.setup()
    render(<App />)
    await user.click(await screen.findByRole('checkbox', { name: /i confirm that i am 18/i }))
    await user.click(screen.getByRole('button', { name: /continue/i }))
    await user.type(await screen.findByLabelText(/name you’d like to use/i), 'Mira')
    await user.type(screen.getByLabelText(/date of birth/i), '2015-01-01')
    await user.click(screen.getByRole('button', { name: /continue/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/for people aged 18 and over/i)
    expect(mocks.createProfile).not.toHaveBeenCalled()
  })

  it('restores onboarding progress without persisting date of birth', async () => {
    mocks.getSessionSnapshot.mockResolvedValue({ session: userSession, user: userSession.user })
    visit('/onboarding')
    const user = userEvent.setup()
    const firstRender = render(<App />)
    await user.click(await screen.findByRole('checkbox', { name: /i confirm that i am 18/i }))
    await user.click(screen.getByRole('button', { name: /continue/i }))
    await user.type(await screen.findByLabelText(/name you’d like to use/i), 'Mira')
    await user.type(screen.getByLabelText(/date of birth/i), '1995-01-01')
    await user.click(screen.getByRole('button', { name: /continue/i }))
    expect(await screen.findByRole('heading', { name: /what brings you out there/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/dating preference/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/discovery preference/i)).toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: 'Hindi' })).toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: 'Urdu' })).toBeInTheDocument()
    expect(sessionStorage.getItem('travelmate-onboarding-step')).toBe('2')
    expect(JSON.stringify(sessionStorage)).not.toContain('1995-01-01')
    firstRender.unmount()
    render(<App />)
    expect(await screen.findByRole('heading', { name: /what brings you out there/i })).toBeInTheDocument()
  })

  it('shows backend profile rejection without claiming profile completion', async () => {
    mocks.getSessionSnapshot.mockResolvedValue({ session: userSession, user: userSession.user })
    mocks.createProfile.mockRejectedValue(Object.assign(new Error('validation failed'), { status: 422 }))
    visit('/onboarding')
    const user = userEvent.setup()
    render(<App />)
    await user.click(await screen.findByRole('checkbox', { name: /i confirm that i am 18/i }))
    await user.click(screen.getByRole('button', { name: /continue/i }))
    await user.type(await screen.findByLabelText(/name you’d like to use/i), 'Mira')
    await user.type(screen.getByLabelText(/date of birth/i), '1995-01-01')
    await user.click(screen.getByRole('button', { name: /continue/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/API rejected this date of birth/i)
    await waitFor(() => expect(mocks.createProfile).toHaveBeenCalledWith({ display_name: 'Mira', date_of_birth: '1995-01-01', bio: undefined, gender_identity: null }))
  })

  it('persists onboarding preferences and privacy through backend APIs', async () => {
    mocks.getSessionSnapshot.mockResolvedValue({ session: userSession, user: userSession.user })
    visit('/onboarding')
    const user = userEvent.setup()
    render(<App />)
    await user.click(await screen.findByRole('checkbox', { name: /i confirm that i am 18/i }))
    await user.click(screen.getByRole('button', { name: /continue/i }))
    await user.type(await screen.findByLabelText(/name you’d like to use/i), 'Mira')
    await user.type(screen.getByLabelText(/date of birth/i), '1995-01-01')
    await user.click(screen.getByRole('button', { name: /continue/i }))
    await user.click(await screen.findByRole('button', { name: /save preferences/i }))
    await user.selectOptions(await screen.findByLabelText('Profile visibility'), 'public')
    await user.selectOptions(screen.getByLabelText('Location shown to others'), 'hidden')
    await user.click(screen.getByRole('checkbox', { name: /allow exact location/i }))
    await user.click(await screen.findByRole('button', { name: /save privacy and finish/i }))
    expect(await screen.findByRole('heading', { name: /welcome aboard, mira/i })).toBeInTheDocument()
    expect(mocks.updatePreferences).toHaveBeenCalledOnce()
    expect(mocks.updatePrivacy).toHaveBeenCalledWith({
      profile_visibility: 'public',
      discovery_visibility: true,
      location_precision: 'hidden',
      allow_exact_location_sharing: true,
    })
    expect(localStorage.getItem('travelmate-privacy-preferences')).toBeNull()
  })
})
