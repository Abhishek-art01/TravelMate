import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { profileApi } from '../services/api/profile'

export default function ProfilePage() {
  const profile = useQuery({ queryKey: ['profile', 'me'], queryFn: profileApi.getMe, retry: false })
  return (
    <div className="member-layout">
      <header className="member-header"><Link to="/home" className="brand-lockup"><span className="brand-mark">T</span><span>travelmate</span></Link><nav aria-label="Main navigation"><Link to="/home">Home</Link><Link className="nav-active" to="/profile">Profile</Link><Link to="/privacy">Privacy</Link></nav><Link className="header-link" to="/home">Back home</Link></header>
      <main className="member-page"><p className="eyebrow">YOUR PROFILE</p><h1>A little more you.</h1><p className="page-lede">Only the details you choose to share belong on your profile.</p>
        {profile.isLoading ? <div className="skeleton-line" aria-label="Loading profile" /> : profile.isError ? <section className="empty-state"><h2>Profile details aren’t available yet.</h2><p>{profile.error.message}</p><Link className="text-link" to="/onboarding">Continue profile setup ↗</Link></section> : <section className="profile-summary"><div className="avatar" aria-hidden="true">{profile.data?.email?.slice(0, 1).toUpperCase() ?? 'T'}</div><div><h2>{profile.data?.email}</h2><p>Account: {profile.data?.account_status}</p><p>Signed in with: {profile.data?.provider}</p></div><span className="privacy-pill">BIRTHDAY PRIVATE</span></section>}
          <div className="profile-action"><p>The current API exposes account/profile status. Editing and profile-completion endpoints are not available yet.</p><Link className="button button-primary" to="/onboarding">Set up profile <span aria-hidden="true">↗</span></Link></div>
      </main>
    </div>
  )
}
