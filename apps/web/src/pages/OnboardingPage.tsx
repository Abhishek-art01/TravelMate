import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, Input, TextArea } from '../components/ui'
import { profileApi } from '../services/api/profile'
import type { OnboardingDraft, TravelIntent } from '../types/app'

const intentOptions: { value: TravelIntent; label: string }[] = [
  { value: 'dating_romantic', label: 'Dating / romance' },
  { value: 'serious_relationship', label: 'A serious relationship' },
  { value: 'casual_dating', label: 'Casual dating' },
  { value: 'travel_companion', label: 'Travel companion' },
  { value: 'friends_social', label: 'Friends & social' },
  { value: 'local_guide', label: 'Meet locals' },
  { value: 'activity_partner', label: 'Activity partner' },
]
const languageOptions = [
  { code: 'hi', label: 'Hindi' }, { code: 'bn', label: 'Bengali' }, { code: 'te', label: 'Telugu' },
  { code: 'mr', label: 'Marathi' }, { code: 'ta', label: 'Tamil' }, { code: 'gu', label: 'Gujarati' },
  { code: 'kn', label: 'Kannada' }, { code: 'ml', label: 'Malayalam' }, { code: 'pa', label: 'Punjabi' },
  { code: 'or', label: 'Odia' }, { code: 'as', label: 'Assamese' }, { code: 'ur', label: 'Urdu' }, { code: 'en', label: 'English' },
]
const interestOptions = [
  { code: 'food_walks', label: 'Food walks' }, { code: 'hiking', label: 'Hiking' },
  { code: 'photography', label: 'Photography' }, { code: 'heritage', label: 'Heritage' },
  { code: 'art_design', label: 'Art & design' }, { code: 'live_music', label: 'Live music' },
  { code: 'beaches', label: 'Beaches' }, { code: 'local_culture', label: 'Local culture' },
]
const stepKey = 'travelmate-onboarding-step'
const maxDate = new Date().toISOString().slice(0, 10)
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
  profileVisibility: 'hidden',
  locationPrivacy: 'approximate',
  exactLocationSharing: false,
}

function initialStep(): number | null {
  const value = Number(sessionStorage.getItem(stepKey))
  return Number.isInteger(value) && value >= 0 && value <= 3 ? value : null
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
  const queryClient = useQueryClient()
  const profile = useQuery({ queryKey: ['profile', 'me'], queryFn: profileApi.getProfile, retry: false })
  const preferences = useQuery({ queryKey: ['profile', 'preferences'], queryFn: profileApi.getPreferences, retry: false })
  const privacy = useQuery({ queryKey: ['profile', 'privacy'], queryFn: profileApi.getPrivacy, retry: false })
  const [savedStep, setSavedStep] = useState<number | null>(initialStep)
  const [edits, setEdits] = useState<Partial<OnboardingDraft>>({})
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [complete, setComplete] = useState(false)
  const navigate = useNavigate()

  const serverProfile = profile.data
  const serverPreferences = preferences.data
  const serverPrivacy = privacy.data
  const derivedStep = serverProfile?.display_name && serverProfile.age !== null
    ? (serverPreferences && [serverPreferences.dating_intentions, serverPreferences.travel_intentions, serverPreferences.languages, serverPreferences.interests].some((values) => values.length > 0) ? 3 : 2)
    : 0
  const step = savedStep ?? derivedStep
  const draft: OnboardingDraft = {
    ...emptyDraft,
    ageConfirmed: edits.ageConfirmed ?? false,
    displayName: edits.displayName ?? serverProfile?.display_name ?? '',
    dateOfBirth: edits.dateOfBirth ?? '',
    bio: edits.bio ?? serverProfile?.bio ?? '',
    genderIdentity: edits.genderIdentity ?? serverProfile?.gender_identity ?? '',
    datingPreference: edits.datingPreference ?? serverPreferences?.dating_preferences[0] ?? '',
    discoveryPreference: edits.discoveryPreference ?? serverPreferences?.discovery_preferences[0] ?? '',
    travelIntentions: edits.travelIntentions ?? serverPreferences?.travel_intentions as TravelIntent[] ?? [],
    languages: edits.languages ?? serverPreferences?.languages ?? [],
    interests: edits.interests ?? serverPreferences?.interests ?? [],
    profileVisibility: edits.profileVisibility ?? serverPrivacy?.profile_visibility ?? serverProfile?.profile_visibility ?? 'hidden',
    locationPrivacy: edits.locationPrivacy ?? serverPrivacy?.location_precision ?? 'approximate',
    exactLocationSharing: edits.exactLocationSharing ?? serverPrivacy?.allow_exact_location_sharing ?? false,
  }

  function update<K extends keyof OnboardingDraft>(key: K, value: OnboardingDraft[K]) {
    setEdits((current) => ({ ...current, [key]: value }))
  }

  function goToStep(nextStep: number) {
    setSavedStep(nextStep)
    sessionStorage.setItem(stepKey, String(nextStep))
  }

  function toggleListValue(field: 'languages' | 'interests' | 'travelIntentions', value: string) {
    const current = draft[field] as string[]
    const next = current.includes(value) ? current.filter((item) => item !== value) : [...current, value]
    update(field, next as OnboardingDraft[typeof field])
  }

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    if (!draft.ageConfirmed) {
      setError('Please confirm that you are 18 or older to continue.')
      goToStep(0)
      return
    }
    if (!isAdult(draft.dateOfBirth)) {
      setError('TravelMate is for people aged 18 and over. Please check your date of birth.')
      return
    }
    setBusy(true)
    try {
      await profileApi.create({
        display_name: draft.displayName.trim(),
        date_of_birth: draft.dateOfBirth,
        bio: draft.bio.trim() || undefined,
        gender_identity: draft.genderIdentity.trim() || null,
      })
      await queryClient.invalidateQueries({ queryKey: ['profile', 'me'] })
      goToStep(2)
      update('dateOfBirth', '')
    } catch (cause) {
      const apiError = cause as Error & { status?: number }
      setError(apiError.status === 422 ? 'TravelMate is for people aged 18 and over. The API rejected this date of birth.' : apiError.message || 'We couldn’t save your profile. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  async function savePreferences() {
    setBusy(true)
    setError('')
    try {
      await profileApi.updatePreferences({
        dating_intentions: draft.travelIntentions.filter((value) => ['dating_romantic', 'serious_relationship', 'casual_dating'].includes(value)),
        dating_preferences: draft.datingPreference ? [draft.datingPreference] : [],
        discovery_preferences: draft.discoveryPreference ? [draft.discoveryPreference] : [],
        travel_intentions: draft.travelIntentions.filter((value) => !['dating_romantic', 'serious_relationship', 'casual_dating'].includes(value)),
        languages: draft.languages,
        interests: draft.interests,
        minimum_age: 18,
        maximum_age: null,
      })
      await queryClient.invalidateQueries({ queryKey: ['profile', 'preferences'] })
      goToStep(3)
    } catch (cause) {
      setError((cause as Error).message || 'We couldn’t save your preferences. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  async function savePrivacy(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      await profileApi.updatePrivacy({
        profile_visibility: draft.profileVisibility,
        discovery_visibility: draft.profileVisibility === 'public' || draft.profileVisibility === 'discoverable',
        location_precision: draft.locationPrivacy,
        allow_exact_location_sharing: draft.exactLocationSharing,
      })
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['profile', 'privacy'] }),
        queryClient.invalidateQueries({ queryKey: ['profile', 'me'] }),
        queryClient.invalidateQueries({ queryKey: ['me'] }),
      ])
      sessionStorage.removeItem(stepKey)
      setSavedStep(null)
      setComplete(true)
    } catch (cause) {
      setError((cause as Error).message || 'We couldn’t save your privacy settings. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  if (profile.isLoading || preferences.isLoading || privacy.isLoading) {
    return <main className="onboarding-layout"><section className="onboarding-content"><p className="eyebrow">YOUR PROFILE</p><h1>Restoring your setup…</h1><div className="skeleton-line" /></section></main>
  }
  if (profile.isError || preferences.isError || privacy.isError) {
    const loadError = profile.error ?? preferences.error ?? privacy.error
    return <main className="onboarding-layout"><section className="onboarding-content"><p className="eyebrow">YOUR PROFILE</p><h1>Couldn’t load your saved setup.</h1><p>{loadError?.message ?? 'Please try again.'}</p><Button onClick={() => void Promise.all([profile.refetch(), preferences.refetch(), privacy.refetch()])}>Retry</Button></section></main>
  }

  if (complete) {
    const completion = profile.data?.completion_percentage ?? 0
    return <main className="onboarding-layout"><div className="onboarding-top"><Link className="brand-lockup" to="/home"><span className="brand-mark"><img src="/logo-icon.png" alt="TravelMate" /></span><span>travelmate</span></Link></div><section className="onboarding-content completion"><p className="eyebrow">SAVED TO YOUR PROFILE</p><h1>Welcome aboard, {draft.displayName || 'traveller'}.</h1><p>Your profile and preferences are saved. Profile completion is calculated by TravelMate from persisted profile data and approved media.</p><div className="completion-progress"><span style={{ width: `${completion}%` }} /></div><p>{completion}% profile completion</p><Button onClick={() => navigate('/home')}>Go to your home <span aria-hidden="true">↗</span></Button></section></main>
  }

  const stepTitles = ['A quick hello', 'Your profile', 'What brings you out there?', 'Your privacy']
  return (
    <main className="onboarding-layout">
      <header className="onboarding-top"><Link className="brand-lockup" to="/home"><span className="brand-mark"><img src="/logo-icon.png" alt="TravelMate" /></span><span>travelmate</span></Link><span className="step-counter">STEP {step + 1} / 4</span></header>
      <div className="onboarding-progress" aria-label={`Step ${step + 1} of 4`}><span style={{ width: `${((step + 1) / 4) * 100}%` }} /></div>
      <section className="onboarding-content">
        <p className="eyebrow">GETTING TO KNOW YOU</p><h1>{stepTitles[step]}</h1>
        <p className="onboarding-intro">{step === 0 ? 'A few thoughtful details make it easier to meet the right travel people.' : step === 1 ? 'Your date of birth is used only for the 18+ check and is never shown on your public profile.' : step === 2 ? 'Keep these choices yours. Identity, dating preferences, and discovery are separate.' : 'Your exact location stays private unless you choose to share it for a specific feature.'}</p>
        {error && <p className="form-error" role="alert">{error}</p>}
        {step === 0 && <div className="onboarding-card"><span className="large-step">01</span><h2>Adults only, by design.</h2><p>TravelMate is for people aged 18 and over. The backend validates your date of birth when your profile is saved.</p><label className="check-row"><input type="checkbox" checked={draft.ageConfirmed} onChange={(event) => update('ageConfirmed', event.target.checked)} /><span>I confirm that I am 18 years old or older.</span></label><Button disabled={!draft.ageConfirmed} onClick={() => goToStep(1)}>Continue <span aria-hidden="true">→</span></Button></div>}
        {step === 1 && <form className="onboarding-form" onSubmit={(event) => void saveProfile(event)}><label htmlFor="display-name">Name you’d like to use</label><Input id="display-name" required minLength={2} maxLength={80} autoComplete="nickname" value={draft.displayName} onChange={(event) => update('displayName', event.target.value)} placeholder="Your display name" /><label htmlFor="dob">Date of birth <span className="label-note">Private · 18+ only</span></label><Input id="dob" type="date" required max={maxDate} value={draft.dateOfBirth} onChange={(event) => update('dateOfBirth', event.target.value)} /><label htmlFor="bio">A little about you <span className="label-note">Optional</span></label><TextArea id="bio" maxLength={500} rows={4} value={draft.bio} onChange={(event) => update('bio', event.target.value)} placeholder="What do you love finding on the road?" /><div className="form-actions"><Button variant="secondary" type="button" onClick={() => goToStep(0)}>Back</Button><Button disabled={busy} type="submit">{busy ? 'Saving…' : 'Save and continue'} <span aria-hidden="true">→</span></Button></div></form>}
        {step === 2 && <div className="onboarding-form"><label htmlFor="gender">Gender identity <span className="label-note">Optional</span></label><select id="gender" className="field-input" value={draft.genderIdentity} onChange={(event) => update('genderIdentity', event.target.value)}><option value="">Prefer not to say</option><option>Woman</option><option>Man</option><option>Non-binary</option><option>Self-describe</option></select><label htmlFor="dating-preference">Dating preference <span className="label-note">Optional · separate from identity</span></label><select id="dating-preference" className="field-input" value={draft.datingPreference} onChange={(event) => update('datingPreference', event.target.value)}><option value="">Choose later</option><option value="women">Women</option><option value="men">Men</option><option value="all_genders">All genders</option><option value="not_dating">Not looking to date</option></select><label htmlFor="discovery">Discovery preference <span className="label-note">Optional</span></label><select id="discovery" className="field-input" value={draft.discoveryPreference} onChange={(event) => update('discoveryPreference', event.target.value)}><option value="">Choose later</option><option value="shared_interests">Shared interests</option><option value="similar_travel_intentions">Similar travel intentions</option><option value="same_destination">People visiting the same destination</option></select><fieldset className="choice-fieldset"><legend>Travel intentions <span className="label-note">Choose any</span></legend><div className="choice-grid">{intentOptions.map((option) => <label key={option.value} className={`choice-chip ${draft.travelIntentions.includes(option.value) ? 'selected' : ''}`}><input type="checkbox" checked={draft.travelIntentions.includes(option.value)} onChange={() => toggleListValue('travelIntentions', option.value)} />{option.label}</label>)}</div></fieldset><fieldset className="choice-fieldset"><legend>Languages you speak <span className="label-note">Choose any</span></legend><div className="choice-grid">{languageOptions.map((option) => <label key={option.code} className={`choice-chip ${draft.languages.includes(option.code) ? 'selected' : ''}`}><input type="checkbox" checked={draft.languages.includes(option.code)} onChange={() => toggleListValue('languages', option.code)} />{option.label}</label>)}</div></fieldset><fieldset className="choice-fieldset"><legend>Interests <span className="label-note">Optional · choose any</span></legend><div className="choice-grid">{interestOptions.map((option) => <label key={option.code} className={`choice-chip ${draft.interests.includes(option.code) ? 'selected' : ''}`}><input type="checkbox" checked={draft.interests.includes(option.code)} onChange={() => toggleListValue('interests', option.code)} />{option.label}</label>)}</div></fieldset><div className="form-actions"><Button variant="secondary" onClick={() => goToStep(1)}>Back</Button><Button disabled={busy} onClick={() => void savePreferences()}>{busy ? 'Saving…' : 'Save preferences'} <span aria-hidden="true">→</span></Button></div></div>}
        {step === 3 && <form className="onboarding-form" onSubmit={(event) => void savePrivacy(event)}><label htmlFor="visibility">Profile visibility</label><select id="visibility" className="field-input" value={draft.profileVisibility} onChange={(event) => update('profileVisibility', event.target.value as OnboardingDraft['profileVisibility'])}><option value="hidden">Hidden until I choose</option><option value="limited">Limited</option><option value="discoverable">Discoverable</option><option value="public">Public</option></select><label htmlFor="location-privacy">Location shown to others</label><select id="location-privacy" className="field-input" value={draft.locationPrivacy} onChange={(event) => update('locationPrivacy', event.target.value as OnboardingDraft['locationPrivacy'])}><option value="approximate">Approximate area only</option><option value="destination">Destination only</option><option value="hidden">Keep it hidden</option></select><label className="check-row"><input type="checkbox" checked={draft.exactLocationSharing} onChange={(event) => update('exactLocationSharing', event.target.checked)} /><span>Allow exact location only when I explicitly share it for a feature.</span></label><p className="privacy-callout">We don’t request browser location. These privacy choices are saved to your account.</p><div className="form-actions"><Button variant="secondary" type="button" onClick={() => goToStep(2)}>Back</Button><Button disabled={busy} type="submit">{busy ? 'Saving…' : 'Save privacy and finish'} <span aria-hidden="true">↗</span></Button></div></form>}
      </section>
      <footer className="onboarding-footer"><span>YOUR DETAILS STAY YOURS</span><span>18+ COMMUNITY</span></footer>
    </main>
  )
}
