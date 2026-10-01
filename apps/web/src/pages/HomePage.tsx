import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../app/providers/auth-context'
import { Button } from '../components/ui'
import { profileApi } from '../services/api/profile'

export default function HomePage() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const profile = useQuery({ queryKey: ['profile', 'me'], queryFn: profileApi.getMe, retry: false })
  const verification = useQuery({ queryKey: ['verification', 'status'], queryFn: profileApi.getVerification, retry: false })

  async function logout() {
    await signOut()
    navigate('/login', { replace: true })
  }

  const displayName = user?.user_metadata?.display_name ?? user?.email?.split('@')[0] ?? 'traveller'
  const verificationLabel = verification.data?.verification_status?.replaceAll('_', ' ') ?? 'Not started'

  return (
    <div className="member-layout">
      <header className="member-header"><Link to="/home" className="brand-lockup"><span className="brand-mark">T</span><span>travelmate</span></Link><nav aria-label="Main navigation"><Link className="nav-active" to="/home">Home</Link><Link to="/profile">Profile</Link><Link to="/privacy">Privacy</Link></nav><Button variant="ghost" onClick={() => void logout()}>Sign out <span aria-hidden="true">↗</span></Button></header>
      <main className="home-main">
        <section className="home-intro"><div><p className="eyebrow">YOUR JOURNEY, YOUR PACE</p><h1>Good to have you here,<br /><em>{displayName}.</em></h1><p>Every good trip starts with a little curiosity.</p></div><span className="compass-art" aria-hidden="true">N<span>✳</span></span></section>
        <section className="home-grid" aria-label="Your TravelMate account">
          <article className="home-feature"><div className="feature-kicker"><span>01</span><span>PROFILE</span></div><h2>{profile.isLoading ? 'Checking your profile…' : profile.data ? 'Make this place yours.' : 'Start with the basics.'}</h2><p>{profile.isError ? 'Your profile details are not available yet. Continue setup and we’ll let the API validate them.' : 'Add a name and short introduction. Your birthday stays private.'}</p><Link className="text-link" to={profile.data ? '/profile' : '/onboarding'}>{profile.data ? 'View your profile' : 'Continue setup'} <span aria-hidden="true">↗</span></Link></article>
          <article className="home-status"><div className="feature-kicker"><span>02</span><span>VERIFICATION</span></div><div className="status-dot" /><h2>{verification.isLoading ? 'Checking status…' : verificationLabel}</h2><p>Verification is separate from signing in. Your documents remain private.</p><span className="status-note">STATUS FROM TRAVELMATE API</span></article>
          <article className="home-privacy"><div className="feature-kicker"><span>03</span><span>PRIVACY</span></div><h2>Keep your coordinates to yourself.</h2><p>Your precise location is never public by default. Choose what to share, and when.</p><Link className="text-link" to="/privacy">Review privacy <span aria-hidden="true">↗</span></Link><span className="privacy-symbol" aria-hidden="true">⌖</span></article>
        </section>
        {profile.isError && <p className="inline-note" role="status">Profile API: {profile.error.message}</p>}
      </main>
      <footer className="member-footer"><span>TRAVELMATE · INDIA AND EVERYWHERE</span><span>GOOD PEOPLE. OPEN ROADS.</span></footer>
    </div>
  )
}
