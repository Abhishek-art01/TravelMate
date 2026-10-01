import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { DestinationSelector } from '../components/DestinationSelector'
import { TravelMateMap } from '../components/TravelMateMap'
import { Button, Input, TextArea } from '../components/ui'
import { travelApi, type DestinationSummary } from '../services/api/travel'

const INTENT_CHOICES = [
  { value: 'travel_companion', label: 'Travel companion' },
  { value: 'friends_social', label: 'Friends & socializing' },
  { value: 'local_guide', label: 'Meet locals / explore culture' },
  { value: 'activity_partner', label: 'Outdoor / activity partner' },
  { value: 'dating_romantic', label: 'Dating / romance' },
  { value: 'serious_relationship', label: 'Serious relationship' },
  { value: 'casual_dating', label: 'Casual dating' },
]

export default function TripNewPage() {
  const navigate = useNavigate()
  const [destination, setDestination] = useState<DestinationSummary | null>(null)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [visibility, setVisibility] = useState('discoverable')
  const [companionPreference, setCompanionPreference] = useState('open_to_companion')
  const [partySize, setPartySize] = useState(1)
  const [selectedIntents, setSelectedIntents] = useState<string[]>(['travel_companion'])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function toggleIntent(value: string) {
    setSelectedIntents((prev) =>
      prev.includes(value) ? prev.filter((i) => i !== value) : [...prev, value]
    )
  }

  function handleDestinationSelect(dest: DestinationSummary | null) {
    setDestination(dest)
    if (dest && !title) {
      setTitle(`Trip to ${dest.name}`)
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)

    if (!destination) {
      setError('Please select a destination.')
      return
    }
    if (!title.trim()) {
      setError('Please enter a trip title.')
      return
    }
    if (!startDate || !endDate) {
      setError('Please select both start and end dates.')
      return
    }
    if (startDate > endDate) {
      setError('Trip start date must be before or equal to end date.')
      return
    }

    setSubmitting(true)
    try {
      await travelApi.createTrip({
        destination_id: destination.id,
        title: title.trim(),
        description: description.trim() || null,
        start_date: startDate,
        end_date: endDate,
        visibility,
        companion_preference: companionPreference,
        party_size: partySize,
        intents: selectedIntents,
      })
      navigate('/trips')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create trip')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="trip-form-container">
      <header className="page-header">
        <p className="eyebrow">NEW ITINERARY</p>
        <h1>Plan a New Trip</h1>
        <p className="page-description">
          Set your travel destination, planned dates, and companion preferences.
        </p>
      </header>

      {error && (
        <div className="error-card" role="alert">
          <p>{error}</p>
        </div>
      )}

      <form className="trip-form" onSubmit={(e) => void handleSubmit(e)}>
        {/* Step 1: Destination */}
        <fieldset className="form-section">
          <legend className="section-title">1. Destination</legend>
          <DestinationSelector
            value={destination}
            onChange={handleDestinationSelect}
            label="Where are you travelling?"
          />
          {destination && (
            <div className="destination-preview-box">
              <TravelMateMap
                latitude={destination.latitude}
                longitude={destination.longitude}
                title={destination.name}
                mode="destination"
                height={160}
              />
            </div>
          )}
        </fieldset>

        {/* Step 2: Dates */}
        <fieldset className="form-section">
          <legend className="section-title">2. Travel Dates</legend>
          <div className="form-row">
            <div className="form-col">
              <label htmlFor="trip-start-date" className="field-label">
                Start Date
              </label>
              <Input
                id="trip-start-date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                required
              />
            </div>
            <div className="form-col">
              <label htmlFor="trip-end-date" className="field-label">
                End Date
              </label>
              <Input
                id="trip-end-date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                required
              />
            </div>
          </div>
        </fieldset>

        {/* Step 3: Travel Intent */}
        <fieldset className="form-section">
          <legend className="section-title">3. Travel Intent</legend>
          <p className="section-help">What kind of experience are you seeking on this trip?</p>
          <div className="choice-grid">
            {INTENT_CHOICES.map((choice) => (
              <label
                key={choice.value}
                className={`choice-chip ${selectedIntents.includes(choice.value) ? 'selected' : ''}`}
              >
                <input
                  type="checkbox"
                  checked={selectedIntents.includes(choice.value)}
                  onChange={() => toggleIntent(choice.value)}
                />
                {choice.label}
              </label>
            ))}
          </div>
        </fieldset>

        {/* Step 4: Companion Preference */}
        <fieldset className="form-section">
          <legend className="section-title">4. Companion Preference</legend>
          <div className="radio-options-grid">
            <label className={`radio-card ${companionPreference === 'open_to_companion' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="companion"
                value="open_to_companion"
                checked={companionPreference === 'open_to_companion'}
                onChange={(e) => setCompanionPreference(e.target.value)}
              />
              <div className="radio-content">
                <strong>Open to Companions</strong>
                <span>Welcoming fellow travellers to join part or all of the trip.</span>
              </div>
            </label>
            <label className={`radio-card ${companionPreference === 'travelling_alone' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="companion"
                value="travelling_alone"
                checked={companionPreference === 'travelling_alone'}
                onChange={(e) => setCompanionPreference(e.target.value)}
              />
              <div className="radio-content">
                <strong>Travelling Solo</strong>
                <span>Travelling independently, open to occasional meetups or local tips.</span>
              </div>
            </label>
            <label className={`radio-card ${companionPreference === 'travelling_with_group' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="companion"
                value="travelling_with_group"
                checked={companionPreference === 'travelling_with_group'}
                onChange={(e) => setCompanionPreference(e.target.value)}
              />
              <div className="radio-content">
                <strong>Group Travel</strong>
                <span>Already travelling with friends or family.</span>
              </div>
            </label>
          </div>
        </fieldset>

        {/* Step 5: Visibility */}
        <fieldset className="form-section">
          <legend className="section-title">5. Trip Visibility & Privacy</legend>
          <div className="select-field-group">
            <label htmlFor="trip-visibility" className="field-label">
              Who can see this trip?
            </label>
            <select
              id="trip-visibility"
              className="field-input"
              value={visibility}
              onChange={(e) => setVisibility(e.target.value)}
            >
              <option value="discoverable">Discoverable (Visible in discovery to compatible members)</option>
              <option value="public">Public (Visible to all TravelMate users)</option>
              <option value="matches_only">Matches Only (Visible only to confirmed matches)</option>
              <option value="private">Private (Only visible to you)</option>
            </select>
          </div>
        </fieldset>

        {/* Step 6: Details */}
        <fieldset className="form-section">
          <legend className="section-title">6. Trip Details</legend>
          <label htmlFor="trip-title" className="field-label">
            Trip Title
          </label>
          <Input
            id="trip-title"
            placeholder="e.g. Exploring Cafes & Heritage in Mumbai"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            maxLength={120}
          />

          <label htmlFor="trip-description" className="field-label" style={{ marginTop: '12px', display: 'block' }}>
            Description (Optional)
          </label>
          <TextArea
            id="trip-description"
            placeholder="Share highlights of your itinerary, activities you want to do, or dining spots…"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={4}
            maxLength={2000}
          />

          <div className="party-size-field">
            <label htmlFor="party-size" className="field-label">
              Party Size
            </label>
            <input
              id="party-size"
              type="number"
              className="field-input"
              min={1}
              max={50}
              value={partySize}
              onChange={(e) => setPartySize(Math.max(1, Math.min(50, Number(e.target.value))))}
            />
          </div>
        </fieldset>

        <div className="form-actions">
          <Button variant="secondary" type="button" onClick={() => navigate('/trips')}>
            Cancel
          </Button>
          <Button variant="primary" type="submit" disabled={submitting}>
            {submitting ? 'Creating Trip…' : 'Create Itinerary'}
          </Button>
        </div>
      </form>
    </main>
  )
}
