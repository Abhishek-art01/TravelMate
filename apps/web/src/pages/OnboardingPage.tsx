import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button, Input, TextArea } from '../components/ui'
import { profileApi } from '../services/api/profile'
import type { OnboardingDraft, TravelIntent } from '../types/app'

const stepTitles = ['A quick hello', 'Your profile', 'What brings you out there?', 'Your privacy']
const intentOptions: { value: TravelIntent; label: string }[] = [
  { value: 'dating', label: 'Dating / romance' },
  { value: 'relationship', label: 'A serious relationship' },
  { value: 'casual', label: 'Casual dating' },
  { value: 'travel-companion', label: 'Travel companion' },
  { value: 'friends', label: 'Friends & social' },
  { value: 'local-guide', label: 'Meet locals' },
  { value: 'activity-partner', label: 'Activity partner' },
]
const languageOptions = ['Hindi', 'Bengali', 'Telugu', 'Marathi', 'Tamil', 'Gujarati', 'Kannada', 'Malayalam', 'Punjabi', 'Odia', 'Assamese', 'Urdu', 'English', 'Other']
const interestOptions = ['Food walks', 'Hiking', 'Photography', 'Heritage', 'Art & design', 'Live music', 'Beaches', 'Local culture']
const draftKey = 'travelmate-onboarding-draft'
const today = new Date()
const maxDateOfBirth = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
const emptyDraft: OnboardingDraft = {
  ageConfirmed: false,
  displayName: '',
  dateOfBirth: '',
  bio: '',
  genderIdentity: '',
  datingPreference: '',
  discoveryPreference: '',
  travelIntentions: [],
  languages: [],
  interests: [],
  profileVisibility: 'private',
  locationPrivacy: 'approximate',
  exactLocationSharing: false,
}

function restoreDraft(): { draft: OnboardingDraft; step: number } {
  try {
    const saved = sessionStorage.getItem(draftKey)
    if (!saved) return { draft: emptyDraft, step: 0 }
    const parsed = JSON.parse(saved) as { draft: Partial<OnboardingDraft>; step: number }
    return { draft: { ...emptyDraft, ...parsed.draft, dateOfBirth: '' }, step: Math.min(parsed.step, 3) }
  } catch {
    return { draft: emptyDraft, step: 0 }
  }
}

function isAdult(dateOfBirth: string) {
  const [year, month, day] = dateOfBirth.split('-').map(Number)
  if (!year || !month || !day) return false
  const now = new Date()
  let age = now.getFullYear() - year
  if (now.getMonth() + 1 < month || (now.getMonth() + 1 === month && now.getDate() < day)) age -= 1
  return age >= 18
}

export default function OnboardingPage() {
  const initial = restoreDraft()
  const [draft, setDraft] = useState<OnboardingDraft>(initial.draft)
  const [step, setStep] = useState(initial.step)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [complete, setComplete] = useState(false)
  const navigate = useNavigate()

  function update<K extends keyof OnboardingDraft>(key: K, value: OnboardingDraft[K]) {
    const next = { ...draft, [key]: value }
    setDraft(next)
    sessionStorage.setItem(draftKey, JSON.stringify({ draft: { ...next, dateOfBirth: '' }, step }))
  }

  function goToStep(nextStep: number) {
    setStep(nextStep)
    sessionStorage.setItem(draftKey, JSON.stringify({ draft: { ...draft, dateOfBirth: '' }, step: nextStep }))
  }

  function toggleIntent(value: TravelIntent) {
    const intents = draft.travelIntentions.includes(value)
      ? draft.travelIntentions.filter((item) => item !== value)
      : [...draft.travelIntentions, value]
    update('travelIntentions', intents)
  }

  function toggleListValue(field: 'languages' | 'interests', value: string) {
    const current = draft[field]
    update(field, current.includes(value) ? current.filter((item) => item !== value) : [...current, value])
  }

  async function submitProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    if (!draft.ageConfirmed) {
      setError('Please confirm that you are 18 or older to continue.')
      return
    }
    if (!isAdult(draft.dateOfBirth)) {
      setError('TravelMate is for people aged 18 and over. Please check your date of birth.')
      setStep(1)
      return
    }
    setBusy(true)
    try {
      await profileApi.create({
        display_name: draft.displayName.trim(),
        date_of_birth: draft.dateOfBirth,
        bio: draft.bio.trim() || undefined,
      })
      localStorage.setItem('travelmate-privacy-preferences', JSON.stringify({
        profileVisibility: draft.profileVisibility === 'friends' ? 'connections' : draft.profileVisibility === 'public' ? 'community' : 'private',
        discoveryVisibility: Boolean(draft.discoveryPreference),
        locationMode: draft.locationPrivacy,
        exactLocation: draft.exactLocationSharing,
        personalization: false,
        communications: true,
      }))
      sessionStorage.removeItem(draftKey)
      setComplete(true)
    } catch (cause) {
      const apiError = cause as Error & { status?: number }
      setError(apiError.status === 422 ? 'The API could not accept this date of birth. TravelMate is for people 18 and over.' : apiError.message || 'We couldn’t save your profile. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  if (complete) {
    return <main className="onboarding-layout"><div className="onboarding-top"><Link className="brand-lockup" to="/home"><span className="brand-mark">T</span><span>travelmate</span></Link></div><section className="onboarding-content completion"><p className="eyebrow">YOUR FIRST STEP, DONE</p><h1>Welcome aboard, {draft.displayName}.</h1><p>Your basic profile was accepted by the current API. Dating, discovery, language, and interest preferences are not synced to a backend yet; privacy choices are saved on this device.</p><Button onClick={() => navigate('/home')}>Go to your home <span aria-hidden="true">↗</span></Button></section></main>
  }

  return (
    <main className="onboarding-layout">
      <header className="onboarding-top"><Link className="brand-lockup" to="/home"><span className="brand-mark">T</span><span>travelmate</span></Link><span className="step-counter">STEP {step + 1} / 4</span></header>
      <div className="onboarding-progress" aria-label={`Step ${step + 1} of 4`}><span style={{ width: `${((step + 1) / 4) * 100}%` }} /></div>
      <section className="onboarding-content">
        <p className="eyebrow">GETTING TO KNOW YOU</p><h1>{stepTitles[step]}</h1>
        <p className="onboarding-intro">{step === 0 ? 'A few thoughtful details make it easier to meet the right travel people.' : step === 1 ? 'Your date of birth is used only for the 18+ check and is never shown on your public profile.' : step === 2 ? 'Keep these choices yours. Identity, dating preferences, and discovery are separate.' : 'Your exact location stays private unless you choose to share it for a specific feature.'}</p>
        {error && <p className="form-error" role="alert">{error}</p>}
        {step === 0 && <div className="onboarding-card"><span className="large-step">01</span><h2>Adults only, by design.</h2><p>TravelMate is a social travel and dating community for people aged 18 and over. Your date of birth is checked securely by the API.</p><label className="check-row"><input type="checkbox" checked={draft.ageConfirmed} onChange={(event) => update('ageConfirmed', event.target.checked)} /><span>I confirm that I am 18 years old or older.</span></label><Button disabled={!draft.ageConfirmed} onClick={() => goToStep(1)}>Continue <span aria-hidden="true">→</span></Button></div>}
        {step === 1 && <form className="onboarding-form" onSubmit={(event) => { event.preventDefault(); if (!isAdult(draft.dateOfBirth)) { setError('TravelMate is for people aged 18 and over. Please check your date of birth.'); return } goToStep(2) }}><label htmlFor="display-name">Name you’d like to use</label><Input id="display-name" required minLength={2} maxLength={80} autoComplete="nickname" value={draft.displayName} onChange={(event) => update('displayName', event.target.value)} placeholder="Your display name" /><label htmlFor="dob">Date of birth <span className="label-note">Private · 18+ only</span></label><Input id="dob" type="date" required max={maxDateOfBirth} value={draft.dateOfBirth} onChange={(event) => update('dateOfBirth', event.target.value)} /><label htmlFor="bio">A little about you <span className="label-note">Optional</span></label><TextArea id="bio" maxLength={500} rows={4} value={draft.bio} onChange={(event) => update('bio', event.target.value)} placeholder="What do you love finding on the road?" /><div className="form-actions"><Button variant="secondary" type="button" onClick={() => goToStep(0)}>Back</Button><Button type="submit">Continue <span aria-hidden="true">→</span></Button></div></form>}
        {step === 2 && <div className="onboarding-form">
          <label htmlFor="gender">Gender identity <span className="label-note">Optional</span></label>
          <select id="gender" className="field-input" value={draft.genderIdentity} onChange={(event) => update('genderIdentity', event.target.value)}><option value="">Prefer not to say</option><option>Woman</option><option>Man</option><option>Non-binary</option><option>Self-describe</option></select>
          <label htmlFor="dating-preference">Dating preference <span className="label-note">Optional · separate from identity</span></label>
          <select id="dating-preference" className="field-input" value={draft.datingPreference} onChange={(event) => update('datingPreference', event.target.value)}><option value="">Choose later</option><option>Women</option><option>Men</option><option>All genders</option><option>Not looking to date</option></select>
          <label htmlFor="discovery">Discovery preference <span className="label-note">Optional</span></label>
          <select id="discovery" className="field-input" value={draft.discoveryPreference} onChange={(event) => update('discoveryPreference', event.target.value)}><option value="">Choose later</option><option>Shared interests</option><option>Similar travel intentions</option><option>People visiting the same destination</option></select>
          <fieldset className="choice-fieldset"><legend>Travel intentions <span className="label-note">Choose any</span></legend><div className="choice-grid">{intentOptions.map((option) => <label key={option.value} className={`choice-chip ${draft.travelIntentions.includes(option.value) ? 'selected' : ''}`}><input type="checkbox" checked={draft.travelIntentions.includes(option.value)} onChange={() => toggleIntent(option.value)} />{option.label}</label>)}</div></fieldset>
          <fieldset className="choice-fieldset"><legend>Languages you speak <span className="label-note">Choose any</span></legend><div className="choice-grid">{languageOptions.map((language) => <label key={language} className={`choice-chip ${draft.languages.includes(language) ? 'selected' : ''}`}><input type="checkbox" checked={draft.languages.includes(language)} onChange={() => toggleListValue('languages', language)} />{language}</label>)}</div></fieldset>
          <fieldset className="choice-fieldset"><legend>Interests <span className="label-note">Optional · choose any</span></legend><div className="choice-grid">{interestOptions.map((interest) => <label key={interest} className={`choice-chip ${draft.interests.includes(interest) ? 'selected' : ''}`}><input type="checkbox" checked={draft.interests.includes(interest)} onChange={() => toggleListValue('interests', interest)} />{interest}</label>)}</div></fieldset>
          <div className="form-actions"><Button variant="secondary" onClick={() => goToStep(1)}>Back</Button><Button onClick={() => goToStep(3)}>Continue <span aria-hidden="true">→</span></Button></div>
        </div>}
        {step === 3 && <form className="onboarding-form" onSubmit={(event) => void submitProfile(event)}><label htmlFor="visibility">Profile visibility</label><select id="visibility" className="field-input" value={draft.profileVisibility} onChange={(event) => update('profileVisibility', event.target.value as OnboardingDraft['profileVisibility'])}><option value="private">Private until I choose</option><option value="friends">People I connect with</option><option value="public">Visible to the community</option></select><label htmlFor="location-privacy">Location shown to others</label><select id="location-privacy" className="field-input" value={draft.locationPrivacy} onChange={(event) => update('locationPrivacy', event.target.value)}><option value="approximate">Approximate area only</option><option value="destination">Destination only</option><option value="hidden">Keep it hidden</option></select><label className="check-row"><input type="checkbox" checked={draft.exactLocationSharing} onChange={(event) => update('exactLocationSharing', event.target.checked)} /><span>Allow exact location only when I explicitly share it for a feature.</span></label><p className="privacy-callout">We don’t request browser location during setup. These preferences are saved on this device until the privacy API is available.</p><div className="form-actions"><Button variant="secondary" type="button" onClick={() => goToStep(2)}>Back</Button><Button disabled={busy} type="submit">{busy ? 'Saving…' : 'Finish setup'} <span aria-hidden="true">↗</span></Button></div></form>}
      </section>
      <footer className="onboarding-footer"><span>YOUR DETAILS STAY YOURS</span><span>18+ COMMUNITY</span></footer>
    </main>
  )
}
