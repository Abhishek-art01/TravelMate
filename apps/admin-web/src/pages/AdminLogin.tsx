import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { isSupabaseConfigured } from '../app/config/env'
import { signIn } from '../services/auth/supabase'
import { Button } from '../components/Button'

export default function AdminLogin() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const location = useLocation()

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const { error: authError } = await signIn(email, password)
      if (authError) throw authError
      const destination = (location.state as { from?: string } | null)?.from ?? '/admin'
      navigate(destination, { replace: true })
    } catch {
      setError('Sign-in could not be completed. Check your details or try again shortly.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="login-page">
      <section className="login-aside"><Link className="admin-brand" to="/admin/login"><span className="admin-mark"><img src="/logo-icon.png" alt="TravelMate" /></span><span><strong>TravelMate</strong><small>ADMIN CONSOLE</small></span></Link><div><p className="eyebrow">OPERATIONS · TRUST · SAFETY</p><h1>Clarity for the work that matters.</h1><p>Administrative access is verified by the TravelMate API for every session.</p></div><span className="aside-footer">INTERNAL OPERATIONS</span></section>
      <section className="login-main"><div className="login-form-wrap"><p className="eyebrow">SECURE SIGN IN</p><h2>Admin sign in</h2><p className="login-intro">Use your TravelMate account. Console access is checked separately by the backend.</p>
        {!isSupabaseConfigured && <p className="notice notice-warning" role="status">Set the public Supabase URL and anon key for this Admin Web environment.</p>}
        {error && <p className="notice notice-error" role="alert">{error}</p>}
        <form onSubmit={(event) => void submit(event)}>
          <label htmlFor="admin-email">Email</label><input id="admin-email" type="email" autoComplete="username" required maxLength={254} value={email} onChange={(event) => setEmail(event.target.value)} />
          <label htmlFor="admin-password">Password</label>
          <div className="password-input-wrap">
            <input id="admin-password" type={showPassword ? 'text' : 'password'} autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} />
            <button
              type="button"
              className="password-toggle-btn"
              onClick={() => setShowPassword((prev) => !prev)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              title={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24" />
                  <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68" />
                  <path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61" />
                  <line x1="2" y1="2" x2="22" y2="22" />
                </svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
              )}
            </button>
          </div>
          <Button className="login-submit" disabled={busy || !isSupabaseConfigured} type="submit">{busy ? 'Verifying…' : 'Continue securely'} <span aria-hidden="true">→</span></Button>
        </form>
        <p className="access-note">Successful authentication does not guarantee admin access. Permissions are checked by the backend before console routes load.</p>
      </div><footer>TRAVELMATE · INTERNAL CONSOLE</footer></section>
    </main>
  )
}
