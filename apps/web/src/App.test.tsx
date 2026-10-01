import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'

const mocks = vi.hoisted(() => ({
  getSessionSnapshot: vi.fn(),
  getSession: vi.fn(),
  signInWithPassword: vi.fn(),
  signUpWithEmail: vi.fn(),
  signInWithOAuth: vi.fn(),
  sendPasswordReset: vi.fn(),
  signOut: vi.fn(),
  onAuthStateChange: vi.fn(),
  getMe: vi.fn(),
  getVerification: vi.fn(),
  createProfile: vi.fn(),
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
    getMe: mocks.getMe,
    getVerification: mocks.getVerification,
    create: mocks.createProfile,
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
  mocks.getMe.mockResolvedValue({ user_id: 'user-1', email: 'traveller@example.com', profile_status: 'complete', account_status: 'active' })
  mocks.getVerification.mockResolvedValue({ user_id: 'user-1', verification_status: 'not_started', required_checks: [] })
  mocks.createProfile.mockResolvedValue({ profile: { profile_id: 'profile-1' } })
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

  it('saves privacy preferences locally and restores them', async () => {
    mocks.getSessionSnapshot.mockResolvedValue({ session: userSession, user: userSession.user })
    visit('/privacy')
    const user = userEvent.setup()
    const firstRender = render(<App />)
    const discovery = await screen.findByRole('checkbox', { name: /allow profile discovery/i })
    await user.click(discovery)
    await user.click(screen.getByRole('button', { name: /save preferences/i }))
    expect(await screen.findByRole('status')).toHaveTextContent(/saved on this device/i)
    firstRender.unmount()
    render(<App />)
    expect(await screen.findByRole('checkbox', { name: /allow profile discovery/i })).not.toBeChecked()
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

  it('restores a safe onboarding draft without persisting date of birth', async () => {
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
    expect(sessionStorage.getItem('travelmate-onboarding-draft')).not.toContain('1995-01-01')
    firstRender.unmount()
    render(<App />)
    expect(await screen.findByRole('heading', { name: /what brings you out there/i })).toBeInTheDocument()
  })

  it('shows backend age rejection instead of claiming profile completion', async () => {
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
    await user.click(await screen.findByRole('button', { name: /continue/i }))
    await user.click(await screen.findByRole('button', { name: /finish setup/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/API could not accept this date of birth/i)
    await waitFor(() => expect(mocks.createProfile).toHaveBeenCalledWith({ display_name: 'Mira', date_of_birth: '1995-01-01', bio: undefined }))
  })

  it('saves chosen privacy controls locally only after profile submission succeeds', async () => {
    mocks.getSessionSnapshot.mockResolvedValue({ session: userSession, user: userSession.user })
    visit('/onboarding')
    const user = userEvent.setup()
    render(<App />)
    await user.click(await screen.findByRole('checkbox', { name: /i confirm that i am 18/i }))
    await user.click(screen.getByRole('button', { name: /continue/i }))
    await user.type(await screen.findByLabelText(/name you’d like to use/i), 'Mira')
    await user.type(screen.getByLabelText(/date of birth/i), '1995-01-01')
    await user.click(screen.getByRole('button', { name: /continue/i }))
    await user.click(await screen.findByRole('button', { name: /continue/i }))
    await user.selectOptions(await screen.findByLabelText('Profile visibility'), 'public')
    await user.selectOptions(screen.getByLabelText('Location shown to others'), 'hidden')
    await user.click(screen.getByRole('checkbox', { name: /allow exact location/i }))
    await user.click(screen.getByRole('button', { name: /finish setup/i }))
    expect(await screen.findByRole('heading', { name: /welcome aboard, mira/i })).toBeInTheDocument()
    expect(JSON.parse(localStorage.getItem('travelmate-privacy-preferences') ?? '{}')).toMatchObject({
      profileVisibility: 'community',
      locationMode: 'hidden',
      exactLocation: true,
    })
  })
})
