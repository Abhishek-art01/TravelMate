import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { configuredOAuthProviders, isSupabaseConfigured } from '../app/config/env'
import { Button, Input, PasswordInput } from '../components/ui'
import { signInWithOAuth, signUpWithEmail } from '../services/auth/auth'

export default function SignupPage() {
  const { t } = useTranslation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const { data, error: signupError } = await signUpWithEmail(email, password)
      if (signupError) throw signupError
      if (data.session) navigate('/onboarding', { replace: true })
      else setNotice('Check your inbox for a confirmation link. We’ll continue onboarding after you confirm.')
    } catch {
      setError('We couldn’t create your account. Check your details and try again.')
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
    <main className="auth-layout signup-layout">
      <section className="auth-story" aria-label="Join TravelMate" style={{ background: 'linear-gradient(135deg, var(--coral), #b34a30)' }}>
        <div className="brand-lockup"><span className="brand-mark"><img src="/logo-icon.png" alt="TravelMate" /></span><span>travelmate</span></div>
        <div className="story-copy">
          <p className="eyebrow" style={{ color: '#fff' }}>YOUR NEXT CHAPTER</p>
          <h1 style={{ color: '#fff' }}>Start an unforgettable <em>journey.</em></h1>
          <p style={{ color: '#ffeadb' }}>Join thousands of singles traveling the world. Create your profile, find your matches, and start planning today.</p>
        </div>
        <div className="story-foot" style={{ color: '#fff' }}><span>ADVENTURE AWAITS</span></div>
      </section>
      <section className="auth-panel">
        <div className="auth-mobile-brand"><span className="brand-mark"><img src="/logo-icon.png" alt="TravelMate" /></span><span>travelmate</span></div>
        <div className="auth-form-wrap">
          <p className="eyebrow">CREATE ACCOUNT</p>
          <h2>Join TravelMate</h2>
          <p className="auth-subtitle">A little about you. A lot still to discover.</p>
          
          {!isSupabaseConfigured && <p className="config-note" role="status">Add config to connect authentication.</p>}
          {notice && <p className="form-success" role="status">{notice}</p>}
          {error && <p className="form-error" role="alert">{error}</p>}
          
          {configuredOAuthProviders.length > 0 && (
            <div className="oauth-row" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {configuredOAuthProviders.map((provider) => (
                <Button key={provider} variant="secondary" disabled={busy || !isSupabaseConfigured} onClick={() => void oauth(provider)}>
                  <span className={`provider-icon ${provider === 'apple' ? 'provider-apple' : ''}`}>
                    {provider === 'google' ? 'G' : provider === 'instagram' ? '📷' : '●'}
                  </span> 
                  Sign up with {provider === 'google' ? 'Google' : provider === 'instagram' ? 'Instagram' : 'Apple'}
                </Button>
              ))}
            </div>
          )}
          {configuredOAuthProviders.length > 0 && <div className="divider"><span>or sign up with email</span></div>}
          
          <form className="auth-form" onSubmit={(event) => void onSubmit(event)}>
            <label htmlFor="email">Email address</label>
            <Input id="email" type="email" autoComplete="email" required maxLength={254} value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" />
            
            <label htmlFor="password">Create Password</label>
            <PasswordInput id="password" autoComplete="new-password" required minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="At least 8 characters" />
            
            <p className="age-note">TravelMate is for adults 18 and over. We’ll confirm your age during profile setup.</p>
            
            <Button className="submit-button" disabled={busy || !isSupabaseConfigured} type="submit">{busy ? 'Creating account…' : 'Sign Up'}<span aria-hidden="true">↗</span></Button>
          </form>
          
          <p className="switch-auth">Already have an account? <Link to="/login">Log in here</Link></p>
          <p className="legal-copy">By joining, you agree to our <a href="#terms">Terms</a> and <a href="#privacy">Privacy Policy</a>.</p>
        </div>
      </section>
    </main>
  )
}
