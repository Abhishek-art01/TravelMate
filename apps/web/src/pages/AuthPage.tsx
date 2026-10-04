import { useEffect, useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { configuredOAuthProviders, isSupabaseConfigured } from '../app/config/env'
import { Button, Input, PasswordInput } from '../components/ui'
import { sendPasswordReset, signInWithOAuth, signInWithPassword, signUpWithEmail, supabase } from '../services/auth/auth'

type Mode = 'login' | 'signup' | 'forgot' | 'callback'

export default function AuthPage({ mode }: { mode: Mode }) {
  const { t } = useTranslation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    if (mode === 'callback') {
      void supabase.auth.getSession().then(({ data, error: sessionError }) => {
        if (sessionError) setError('We could not complete sign-in. Please try again.')
        else if (data.session) navigate('/onboarding', { replace: true })
        else setNotice('The sign-in link has been checked. You can return to TravelMate.')
      })
    }
  }, [mode, navigate])

  if (mode === 'callback') {
    return <main className="callback-screen"><span className="brand-mark"><img src="/logo-icon.png" alt="TravelMate" /></span><p className="eyebrow">TRAVELMATE</p><h1>Finishing your sign-in</h1>{error ? <p role="alert" className="form-error">{error}</p> : <p aria-live="polite">{notice || 'Checking your secure sign-in link…'}</p>}</main>
  }

  const title = mode === 'signup' ? t('auth.signupTitle') : mode === 'forgot' ? t('auth.forgotTitle') : t('auth.loginTitle')
  const isForgot = mode === 'forgot'

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setNotice('')
    try {
      if (mode === 'forgot') {
        const { error: resetError } = await sendPasswordReset(email)
        if (resetError) throw resetError
        setNotice('If an account matches that email, a recovery link will arrive shortly.')
        return
      }
      if (mode === 'signup') {
        const { data, error: signupError } = await signUpWithEmail(email, password)
        if (signupError) throw signupError
        if (data.session) navigate('/onboarding', { replace: true })
        else setNotice('Check your inbox for a confirmation link. We’ll continue onboarding after you confirm.')
        return
      }
      const { error: loginError } = await signInWithPassword(email, password)
      if (loginError) throw loginError
      navigate((location.state as { from?: string } | null)?.from ?? '/home', { replace: true })
    } catch {
      setError(mode === 'signup' ? 'We couldn’t create your account. Check your details and try again.' : 'We couldn’t complete that request. Check your details or try again shortly.')
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
      <section className="auth-story" aria-label="TravelMate introduction">
        <div className="brand-lockup"><span className="brand-mark"><img src="/logo-icon.png" alt="TravelMate" /></span><span>travelmate</span></div>
        <div className="story-copy"><p className="eyebrow">GO SOMEWHERE. MEET SOMEONE.</p><h1>Some journeys are better <em>shared.</em></h1><p>Find your people, discover a place, and let the good stories happen naturally.</p></div>
        <div className="story-foot"><span>MADE FOR OPEN ROADS</span><span>01 / 03</span></div>
        <div className="story-stamp" aria-hidden="true">IN<br />↗</div>
      </section>
      <section className="auth-panel">
        <div className="auth-mobile-brand"><span className="brand-mark"><img src="/logo-icon.png" alt="TravelMate" /></span><span>travelmate</span></div>
        <div className="auth-form-wrap">
          <p className="eyebrow">{mode === 'signup' ? 'YOUR NEXT CHAPTER' : mode === 'forgot' ? 'ACCOUNT RECOVERY' : 'GOOD TO SEE YOU'}</p>
          <h2>{title}</h2>
          <p className="auth-subtitle">{mode === 'signup' ? 'A little about you. A lot still to discover.' : isForgot ? 'Enter your email and we’ll send a secure recovery link.' : 'Pick up where curiosity left off.'}</p>
          {!isSupabaseConfigured && <p className="config-note" role="status">Add `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` to connect authentication.</p>}
          {notice && <p className="form-success" role="status">{notice}</p>}
          {error && <p className="form-error" role="alert">{error}</p>}
          {!isForgot && mode !== 'signup' && configuredOAuthProviders.length > 0 && (
            <div className="oauth-row" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {configuredOAuthProviders.map((provider) => (
                <Button key={provider} variant="secondary" disabled={busy || !isSupabaseConfigured} onClick={() => void oauth(provider)}>
                  <span className={`provider-icon ${provider === 'apple' ? 'provider-apple' : ''}`}>
                    {provider === 'google' ? 'G' : provider === 'instagram' ? '📷' : '●'}
                  </span> 
                  Continue with {provider === 'google' ? 'Google' : provider === 'instagram' ? 'Instagram' : 'Apple'}
                </Button>
              ))}
            </div>
          )}
          {!isForgot && mode !== 'signup' && configuredOAuthProviders.length > 0 && <div className="divider"><span>or continue with email</span></div>}
          <form className="auth-form" onSubmit={(event) => void onSubmit(event)}>
            <label htmlFor="email">{t('auth.email')}</label>
            <Input id="email" type="email" autoComplete="email" required maxLength={254} value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" />
            {!isForgot && <>
              <div className="password-label"><label htmlFor="password">{t('auth.password')}</label>{mode === 'login' && <Link to="/forgot-password">Forgot?</Link>}</div>
              <PasswordInput id="password" autoComplete={mode === 'signup' ? 'new-password' : 'current-password'} required minLength={mode === 'signup' ? 8 : 1} value={password} onChange={(event) => setPassword(event.target.value)} placeholder={mode === 'signup' ? 'At least 8 characters' : 'Your password'} />
            </>}
            {mode === 'signup' && <p className="age-note">TravelMate is for adults 18 and over. We’ll confirm your age during profile setup.</p>}
            <Button className="submit-button" disabled={busy || !isSupabaseConfigured} type="submit">{busy ? 'Please wait…' : isForgot ? 'Send recovery link' : mode === 'signup' ? t('auth.signupAction') : t('auth.loginAction')}<span aria-hidden="true">↗</span></Button>
          </form>
          <p className="switch-auth">{isForgot ? 'Remembered your password?' : mode === 'signup' ? 'Already have an account?' : 'New to TravelMate?'} <Link to={isForgot || mode === 'signup' ? '/login' : '/signup'}>{isForgot || mode === 'signup' ? 'Sign in' : 'Create an account'}</Link></p>
          <p className="legal-copy">By continuing, you agree to our <a href="#terms">Terms</a> and <a href="#privacy">Privacy Policy</a>.</p>
        </div>
        <footer className="auth-footer"><span>© 2026 TRAVELMATE</span><span>TRAVEL WITH INTENTION</span></footer>
      </section>
    </main>
  )
}
