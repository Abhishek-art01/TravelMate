import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getSessionSnapshot } from '../services/auth/auth'
import { Button, Input, TextArea } from '../components/ui'
import { useTranslation } from 'react-i18next'

const ONBOARDING_STEPS = 10;

export default function OnboardingPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [token, setToken] = useState<string | null>(null)
  
  // Form State
  const [name, setName] = useState('')
  const [dob, setDob] = useState('')
  const [gender, setGender] = useState('')
  const [pronouns, setPronouns] = useState('')
  
  const [attraction, setAttraction] = useState('')
  const [datingIntention, setDatingIntention] = useState('')
  const [discovery, setDiscovery] = useState('everyone')
  
  const [travelIntention, setTravelIntention] = useState('')
  
  const [languages, setLanguages] = useState<string[]>([])
  const [interests, setInterests] = useState<string[]>([])
  
  const [bio, setBio] = useState('')
  const [lat, setLat] = useState<number | null>(null)
  const [lng, setLng] = useState<number | null>(null)

  useEffect(() => {
    getSessionSnapshot().then(({ session }) => {
      if (session) setToken(session.access_token)
    })
  }, [])

  const apiCall = async (endpoint: string, body: any) => {
    if (!token) throw new Error('Not authenticated')
    const res = await fetch(`/api/v1/onboarding/step/${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(body)
    })
    if (!res.ok) {
      const txt = await res.text()
      throw new Error(txt || 'Failed to save step')
    }
    return res.json()
  }

  const handleNext = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      if (step === 2) {
        if (!name || !dob || !gender) throw new Error('Please fill all required fields.')
        await apiCall('basic-info', { display_name: name, date_of_birth: dob, gender_identity: gender, pronouns })
      } else if (step === 3) {
        await apiCall('dating-preferences', { attraction_preference: attraction, dating_intention: datingIntention, discovery_preference: discovery })
      } else if (step === 4) {
        if (!travelIntention) throw new Error('Please select a travel intention.')
        await apiCall('travel-intentions', { primary_intention: travelIntention, additional_intentions: [] })
      } else if (step === 5) {
        if (languages.length === 0) throw new Error('Please select at least one language.')
        await apiCall('languages', { languages })
      } else if (step === 6) {
        if (interests.length === 0) throw new Error('Please select at least one interest.')
        await apiCall('interests', { interests })
      } else if (step === 7) {
        if (!bio) throw new Error('Please write a short bio.')
        await apiCall('bio', { bio })
      } else if (step === 8) {
        // Mock photo step
        await apiCall('photos', { photos: ['mock-url-123'] })
      } else if (step === 9) {
        if (!lat || !lng) throw new Error('GPS is compulsory. Please allow location access.')
        await apiCall('location', { latitude: lat, longitude: lng })
      } else if (step === 10) {
        await apiCall('privacy', { profile_visibility: 'discoverable', location_precision: 'approximate' })
        await apiCall('complete', {})
        navigate('/home')
        return
      }
      setStep(s => Math.min(ONBOARDING_STEPS, s + 1))
    } catch (err: any) {
      setError(err.message || 'An error occurred.')
    } finally {
      setBusy(false)
    }
  }

  const handleLocationRequest = () => {
    if (navigator.geolocation) {
      setBusy(true)
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setLat(pos.coords.latitude)
          setLng(pos.coords.longitude)
          setBusy(false)
        },
        (err) => {
          setError('Location access denied. This is required for TravelMate.')
          setBusy(false)
        }
      )
    } else {
      setError('Geolocation is not supported by your browser.')
    }
  }

  const toggleLanguage = (lang: string) => {
    setLanguages(prev => prev.includes(lang) ? prev.filter(l => l !== lang) : [...prev, lang])
  }

  const toggleInterest = (interest: string) => {
    setInterests(prev => prev.includes(interest) ? prev.filter(i => i !== interest) : [...prev, interest])
  }

  return (
    <main className="auth-layout">
      <section className="auth-story" aria-label="Onboarding Progress">
        <div className="brand-lockup">
          <span className="brand-mark"><img src="/logo-icon.png" alt="TravelMate" /></span>
          <span>travelmate</span>
        </div>
        <div className="story-copy">
          <p className="eyebrow" style={{ color: 'var(--lime)' }}>STEP {step} OF {ONBOARDING_STEPS}</p>
          <h1>Let's build your <em>profile.</em></h1>
          <p>We use this information to find you the best matches and travel companions.</p>
          
          <div style={{ marginTop: '32px', display: 'flex', gap: '4px', maxWidth: '300px' }}>
            {Array.from({ length: ONBOARDING_STEPS }).map((_, i) => (
              <div key={i} style={{ flex: 1, height: '4px', background: i < step ? 'var(--lime)' : 'rgba(255,255,255,0.2)', borderRadius: '2px' }} />
            ))}
          </div>
        </div>
        <div className="story-foot"><span>ALMOST THERE</span></div>
      </section>

      <section className="auth-panel">
        <div className="auth-mobile-brand">
          <span className="brand-mark"><img src="/logo-icon.png" alt="TravelMate" /></span>
        </div>
        <div className="auth-form-wrap" style={{ maxWidth: '500px' }}>
          
          <form className="onboarding-form" onSubmit={handleNext}>
            {step === 1 && (
              <>
                <p className="eyebrow">WELCOME TO TRAVELMATE</p>
                <h2>Ready to explore?</h2>
                <p className="auth-subtitle">We need a few details to get your profile ready for the world. It only takes a minute.</p>
              </>
            )}

            {step === 2 && (
              <>
                <p className="eyebrow">BASIC IDENTITY</p>
                <h2>Who are you?</h2>
                
                <label>Display Name *</label>
                <Input value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Alex" required />
                
                <label>Date of Birth *</label>
                <Input type="date" value={dob} onChange={e => setDob(e.target.value)} required />
                
                <label>Gender Identity *</label>
                <select value={gender} onChange={e => setGender(e.target.value)} className="w-full border p-3 rounded" style={{ borderColor: 'var(--line)', borderRadius: '8px' }} required>
                  <option value="">Select gender...</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="nonbinary">Non-binary</option>
                  <option value="other">Other / Prefer not to say</option>
                </select>

                <label>Pronouns (Optional)</label>
                <Input value={pronouns} onChange={e => setPronouns(e.target.value)} placeholder="e.g. they/them" />
              </>
            )}

            {step === 3 && (
              <>
                <p className="eyebrow">DATING & DISCOVERY</p>
                <h2>Who are you looking for?</h2>
                
                <label>I am attracted to...</label>
                <select value={attraction} onChange={e => setAttraction(e.target.value)} className="w-full border p-3 rounded" style={{ borderColor: 'var(--line)', borderRadius: '8px' }}>
                  <option value="">Select preference...</option>
                  <option value="men">Men</option>
                  <option value="women">Women</option>
                  <option value="everyone">Everyone</option>
                </select>

                <label>Dating Intention</label>
                <select value={datingIntention} onChange={e => setDatingIntention(e.target.value)} className="w-full border p-3 rounded" style={{ borderColor: 'var(--line)', borderRadius: '8px' }}>
                  <option value="">Select intention...</option>
                  <option value="serious">A serious relationship</option>
                  <option value="casual">Casual dating</option>
                  <option value="not_sure">Not sure yet</option>
                </select>
              </>
            )}

            {step === 4 && (
              <>
                <p className="eyebrow">TRAVEL INTENTIONS</p>
                <h2>Why are you traveling?</h2>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '16px' }}>
                  {['dating_romantic', 'travel_companion', 'friends_social', 'local_guide', 'activity_partner'].map(intent => (
                    <label key={intent} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '16px', border: '1px solid var(--line)', borderRadius: '8px', cursor: 'pointer', background: travelIntention === intent ? 'var(--paper)' : 'transparent' }}>
                      <input type="radio" name="intent" value={intent} checked={travelIntention === intent} onChange={() => setTravelIntention(intent)} style={{ width: '20px', height: '20px' }} />
                      <span style={{ fontSize: '1.1rem' }}>{intent.replace('_', ' ').toUpperCase()}</span>
                    </label>
                  ))}
                </div>
              </>
            )}

            {step === 5 && (
              <>
                <p className="eyebrow">LANGUAGES</p>
                <h2>What languages do you speak?</h2>
                <p className="auth-subtitle">Select all that apply. (Minimum 1 required)</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                  {['English', 'Spanish', 'French', 'German', 'Italian', 'Portuguese', 'Japanese', 'Korean', 'Chinese'].map(lang => (
                    <button type="button" key={lang} onClick={() => toggleLanguage(lang)} style={{ padding: '10px 20px', borderRadius: '30px', border: '1px solid var(--line)', background: languages.includes(lang) ? 'var(--green)' : 'transparent', color: languages.includes(lang) ? 'white' : 'var(--ink)' }}>
                      {lang}
                    </button>
                  ))}
                </div>
              </>
            )}

            {step === 6 && (
              <>
                <p className="eyebrow">INTERESTS</p>
                <h2>What do you love doing?</h2>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                  {['Photography', 'Hiking', 'Food Walks', 'Nightlife', 'Museums', 'Surfing', 'Architecture', 'Live Music'].map(interest => (
                    <button type="button" key={interest} onClick={() => toggleInterest(interest)} style={{ padding: '10px 20px', borderRadius: '30px', border: '1px solid var(--line)', background: interests.includes(interest) ? 'var(--green)' : 'transparent', color: interests.includes(interest) ? 'white' : 'var(--ink)' }}>
                      {interest}
                    </button>
                  ))}
                </div>
              </>
            )}

            {step === 7 && (
              <>
                <p className="eyebrow">ABOUT YOU</p>
                <h2>Write a short bio</h2>
                <p className="auth-subtitle">Tell potential matches a bit about your vibe and what kind of trips you enjoy.</p>
                <TextArea value={bio} onChange={e => setBio(e.target.value)} rows={5} placeholder="I love exploring hidden cafes and..." required />
              </>
            )}

            {step === 8 && (
              <>
                <p className="eyebrow">PROFILE PHOTO</p>
                <h2>Put a face to the name</h2>
                <p className="auth-subtitle">Profiles with photos get 80% more matches.</p>
                <div style={{ border: '2px dashed var(--line)', padding: '60px', textAlign: 'center', borderRadius: '12px', background: '#f9f9f9' }}>
                  <span style={{ fontSize: '3rem' }}>📸</span>
                  <p style={{ marginTop: '16px', fontWeight: 'bold' }}>Tap to upload</p>
                  <p style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>(Simulated for onboarding)</p>
                </div>
              </>
            )}

            {step === 9 && (
              <>
                <p className="eyebrow">LOCATION</p>
                <h2>Where are you starting from?</h2>
                <p className="auth-subtitle">TravelMate needs your location to show you relevant matches and destinations.</p>
                {!lat ? (
                  <Button type="button" onClick={handleLocationRequest} style={{ padding: '20px', fontSize: '1.1rem' }}>Allow GPS Access</Button>
                ) : (
                  <div style={{ padding: '20px', background: 'var(--lime)', color: 'var(--green-dark)', borderRadius: '8px', fontWeight: 'bold', textAlign: 'center' }}>
                    ✅ Location Acquired securely.
                  </div>
                )}
              </>
            )}

            {step === 10 && (
              <>
                <p className="eyebrow">PRIVACY & DISCOVERY</p>
                <h2>You're in control</h2>
                <p className="auth-subtitle">By finishing, your profile will become visible to others based on your discovery preferences. Your exact location is never shared.</p>
                <div style={{ padding: '20px', background: '#f0f5f2', borderRadius: '8px', marginTop: '16px' }}>
                  <h4 style={{ margin: '0 0 8px' }}>Discovery Status</h4>
                  <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--muted)' }}>Public (Discoverable)</p>
                </div>
              </>
            )}

            {error && <p className="form-error" role="alert" style={{ marginTop: '16px' }}>{error}</p>}

            <div style={{ display: 'flex', gap: '12px', marginTop: '32px' }}>
              {step > 1 && (
                <Button type="button" variant="secondary" onClick={() => setStep(s => s - 1)} disabled={busy}>Back</Button>
              )}
              <Button type="submit" disabled={busy} style={{ flex: 1 }}>
                {busy ? 'Saving...' : step === 10 ? 'Complete Profile' : step === 1 ? 'Get Started' : 'Continue'}
              </Button>
            </div>
          </form>
        </div>
      </section>
    </main>
  )
}
