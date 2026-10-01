import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { profileApi, type Privacy } from '../services/api/profile'

export default function PrivacyPage() {
  const queryClient = useQueryClient()
  const settings = useQuery({ queryKey: ['profile', 'privacy'], queryFn: profileApi.getPrivacy, retry: false })
  const update = useMutation({
    mutationFn: (patch: Partial<Privacy>) => profileApi.updatePrivacy(patch),
    onSuccess: async () => queryClient.invalidateQueries({ queryKey: ['profile', 'privacy'] }),
  })

  if (settings.isLoading) return <main className="member-page"><h1>Loading your privacy settings…</h1><div className="skeleton-line" /></main>
  if (settings.isError || !settings.data) return <main className="member-page"><p className="eyebrow">YOUR BOUNDARIES</p><h1>Privacy settings unavailable</h1><p role="alert">{settings.error?.message ?? 'Please try again.'}</p><button className="button button-secondary" onClick={() => void settings.refetch()}>Retry</button></main>

  const value = settings.data
  const change = (patch: Partial<Privacy>) => update.mutate(patch)

  return (
    <div className="member-layout">
      <header className="member-header"><Link to="/home" className="brand-lockup"><span className="brand-mark">T</span><span>travelmate</span></Link><nav aria-label="Main navigation"><Link to="/home">Home</Link><Link to="/profile">Profile</Link><Link className="nav-active" to="/privacy">Privacy</Link></nav><Link className="header-link" to="/home">Back home</Link></header>
      <main className="member-page privacy-page"><p className="eyebrow">YOUR BOUNDARIES</p><h1>Privacy, on your terms.</h1><p className="page-lede">These settings are saved to your TravelMate account. Exact location remains unavailable to other users unless a future feature explicitly authorizes sharing.</p>
        {update.isError && <p className="form-error" role="alert">{update.error.message}</p>}
        <section className="settings-section"><div><h2>Profile visibility</h2><p>Choose whether your profile can appear in discovery.</p></div><select className="field-input setting-select" aria-label="Profile visibility" value={value.profile_visibility} onChange={(event) => change({ profile_visibility: event.target.value as Privacy['profile_visibility'] })}><option value="hidden">Hidden</option><option value="limited">Limited</option><option value="discoverable">Discoverable</option><option value="public">Public</option></select></section>
        <section className="settings-section"><div><h2>Discovery</h2><p>Allow your profile to appear to people with shared interests.</p></div><label className="switch"><input aria-label="Allow profile discovery" type="checkbox" checked={value.discovery_visibility} onChange={(event) => change({ discovery_visibility: event.target.checked })} /><span aria-hidden="true" /></label></section>
        <section className="settings-section"><div><h2>Location precision</h2><p>Choose a broad area or destination. TravelMate does not expose raw coordinates.</p></div><select className="field-input setting-select" aria-label="Location privacy" value={value.location_precision} onChange={(event) => change({ location_precision: event.target.value as Privacy['location_precision'] })}><option value="approximate">Approximate area</option><option value="destination">Destination only</option><option value="hidden">Keep hidden</option></select></section>
        <section className="settings-section"><div><h2>Explicit location sharing</h2><p>Allow exact location only when you explicitly request it for a specific feature.</p></div><label className="switch"><input aria-label="Allow explicit exact-location sharing" type="checkbox" checked={value.allow_exact_location_sharing} onChange={(event) => change({ allow_exact_location_sharing: event.target.checked })} /><span aria-hidden="true" /></label></section>
        <section className="settings-section"><div><h2>Personalization</h2><p>Use your activity to make recommendations more relevant.</p></div><label className="switch"><input aria-label="Allow personalization" type="checkbox" checked={value.personalization_enabled} onChange={(event) => change({ personalization_enabled: event.target.checked })} /><span aria-hidden="true" /></label></section>
        <section className="settings-section"><div><h2>Product communications</h2><p>Receive occasional updates about TravelMate.</p></div><label className="switch"><input aria-label="Receive product communications" type="checkbox" checked={value.communications_enabled} onChange={(event) => change({ communications_enabled: event.target.checked })} /><span aria-hidden="true" /></label></section>
        <div className="save-row"><span role="status">{update.isPending ? 'Saving to your account…' : update.isSuccess ? 'Saved to your account.' : 'Changes save automatically.'}</span></div>
      </main>
    </div>
  )
}
