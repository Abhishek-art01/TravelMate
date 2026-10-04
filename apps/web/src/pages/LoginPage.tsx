import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { configuredOAuthProviders, isSupabaseConfigured } from '../app/config/env'
import { Button, Input, PasswordInput } from '../components/ui'
import { signInWithOAuth, signInWithPassword } from '../services/auth/auth'

export default function LoginPage() {
  const { t } = useTranslation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const location = useLocation()
  const navigate = useNavigate()

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const { error: loginError } = await signInWithPassword(email, password)
      if (loginError) throw loginError
      navigate((location.state as { from?: string } | null)?.from ?? '/home', { replace: true })
    } catch {
      setError('We couldn’t sign you in. Check your credentials or try again shortly.')
    } finally {
      setBusy(false)
    }
  }

  async function oauth(provider: 'google' | 'apple' | 'instagram') {
    setBusy(true)
    setError('')
    try {
      const { error: oauthError } = await signInWithOAuth(provider)
      if (oauthError) throw oauthError
    } catch {
      setError(`We couldn’t continue with ${provider === 'google' ? 'Google' : provider === 'instagram' ? 'Instagram' : 'Apple'}. Please try again.`)
      setBusy(false)
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-story" aria-label="Welcome Back">
        <div className="brand-lockup"><span className="brand-mark"><img src="/logo-icon.png" alt="TravelMate" /></span><span>travelmate</span></div>
        <div className="story-copy">
          <p className="eyebrow">WELCOME BACK</p>
          <h1>Resume your <em>journey.</em></h1>
          <p>Your matches and itineraries are waiting for you. Log in to continue where you left off.</p>
        </div>
        <div className="story-foot"><span>MADE FOR OPEN ROADS</span></div>
      </section>
      <section className="auth-panel">
        <div className="auth-mobile-brand"><span className="brand-mark"><img src="/logo-icon.png" alt="TravelMate" /></span><span>travelmate</span></div>
        <div className="auth-form-wrap">
          <p className="eyebrow">GOOD TO SEE YOU</p>
          <h2>Log In to TravelMate</h2>
          <p className="auth-subtitle">Pick up where curiosity left off.</p>
          
          {!isSupabaseConfigured && <p className="config-note" role="status">Add config to connect authentication.</p>}
          {error && <p className="form-error" role="alert">{error}</p>}
          
          {configuredOAuthProviders.length > 0 && (
            <div className="oauth-row" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {configuredOAuthProviders.map((provider) => (
                <Button key={provider} variant="secondary" disabled={busy || !isSupabaseConfigured} onClick={() => void oauth(provider)}>
                  <span className={`provider-icon ${provider === 'apple' ? 'provider-apple' : ''}`}>
                    {provider === 'google' ? 'G' : provider === 'instagram' ? '📷' : '●'}
                  </span> 
                  Log in with {provider === 'google' ? 'Google' : provider === 'instagram' ? 'Instagram' : 'Apple'}
                </Button>
              ))}
            </div>
          )}
          {configuredOAuthProviders.length > 0 && <div className="divider"><span>or log in with email</span></div>}
          
          <form className="auth-form" onSubmit={(event) => void onSubmit(event)}>
            <label htmlFor="email">Email address</label>
            <Input id="email" type="email" autoComplete="email" required maxLength={254} value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" />
            
            <div className="password-label">
              <label htmlFor="password">Password</label>
              <Link to="/forgot-password">Forgot?</Link>
            </div>
            <PasswordInput id="password" autoComplete="current-password" required minLength={1} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Your password" />
            
            <Button className="submit-button" disabled={busy || !isSupabaseConfigured} type="submit">{busy ? 'Logging in…' : 'Log In'}<span aria-hidden="true">↗</span></Button>
          </form>
          
          <p className="switch-auth">New to TravelMate? <Link to="/signup">Create an account</Link></p>
        </div>
      </section>
    </main>
  )
}
