import { useState } from 'react'
import { Link } from 'react-router-dom'

type PrivacySettings = {
  profileVisibility: 'private' | 'connections' | 'community'
  discoveryVisibility: boolean
  locationMode: 'approximate' | 'destination' | 'hidden'
  exactLocation: boolean
  personalization: boolean
  communications: boolean
}

const defaults: PrivacySettings = {
  profileVisibility: 'private',
  discoveryVisibility: true,
  locationMode: 'approximate',
  exactLocation: false,
  personalization: false,
  communications: true,
}
const storageKey = 'travelmate-privacy-preferences'

function readSettings(): PrivacySettings {
  try {
    const value = localStorage.getItem(storageKey)
    return value ? { ...defaults, ...JSON.parse(value) as Partial<PrivacySettings> } : defaults
  } catch {
    localStorage.removeItem(storageKey)
    return defaults
  }
}

export default function PrivacyPage() {
  const [settings, setSettings] = useState(readSettings)
  const [saved, setSaved] = useState(false)

  function update<K extends keyof PrivacySettings>(key: K, value: PrivacySettings[K]) {
    setSettings((current) => ({ ...current, [key]: value }))
    setSaved(false)
  }

  function save() {
    localStorage.setItem(storageKey, JSON.stringify(settings))
    setSaved(true)
  }

  return (
    <div className="member-layout">
      <header className="member-header"><Link to="/home" className="brand-lockup"><span className="brand-mark">T</span><span>travelmate</span></Link><nav aria-label="Main navigation"><Link to="/home">Home</Link><Link to="/profile">Profile</Link><Link className="nav-active" to="/privacy">Privacy</Link></nav><Link className="header-link" to="/home">Back home</Link></header>
      <main className="member-page privacy-page"><p className="eyebrow">YOUR BOUNDARIES</p><h1>Privacy, on your terms.</h1><p className="page-lede">Exact location is never public by default. These preferences are stored on this device; server-side preference sync is not yet available.</p>
        <section className="settings-section"><div><h2>Profile visibility</h2><p>Choose who can come across your profile.</p></div><select className="field-input setting-select" aria-label="Profile visibility" value={settings.profileVisibility} onChange={(event) => update('profileVisibility', event.target.value as PrivacySettings['profileVisibility'])}><option value="private">Private until I choose</option><option value="connections">Connections only</option><option value="community">TravelMate community</option></select></section>
        <section className="settings-section"><div><h2>Discovery</h2><p>Allow your profile to appear to people with shared interests.</p></div><label className="switch"><input aria-label="Allow profile discovery" type="checkbox" checked={settings.discoveryVisibility} onChange={(event) => update('discoveryVisibility', event.target.checked)} /><span aria-hidden="true" /></label></section>
        <section className="settings-section"><div><h2>Location privacy</h2><p>Use an approximate area or destination. No GPS coordinates are shown.</p></div><select className="field-input setting-select" aria-label="Location privacy" value={settings.locationMode} onChange={(event) => update('locationMode', event.target.value as PrivacySettings['locationMode'])}><option value="approximate">Approximate area</option><option value="destination">Destination only</option><option value="hidden">Keep hidden</option></select></section>
        <section className="settings-section"><div><h2>Explicit location sharing</h2><p>Exact location can only be shared by you for a specific feature.</p></div><label className="switch"><input aria-label="Allow explicit exact-location sharing" type="checkbox" checked={settings.exactLocation} onChange={(event) => update('exactLocation', event.target.checked)} /><span aria-hidden="true" /></label></section>
        <section className="settings-section"><div><h2>Personalization</h2><p>Use your activity to make recommendations more relevant.</p></div><label className="switch"><input aria-label="Allow personalization" type="checkbox" checked={settings.personalization} onChange={(event) => update('personalization', event.target.checked)} /><span aria-hidden="true" /></label></section>
        <section className="settings-section"><div><h2>Product communications</h2><p>Receive occasional updates about TravelMate.</p></div><label className="switch"><input aria-label="Receive product communications" type="checkbox" checked={settings.communications} onChange={(event) => update('communications', event.target.checked)} /><span aria-hidden="true" /></label></section>
        <div className="save-row"><span role="status">{saved ? 'Saved on this device.' : 'Changes are not saved until you confirm.'}</span><button type="button" className="button button-primary" onClick={save}>Save preferences <span aria-hidden="true">↗</span></button></div>
      </main>
    </div>
  )
}
