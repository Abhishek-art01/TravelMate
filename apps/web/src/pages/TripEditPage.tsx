import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, Input, TextArea } from '../components/ui'
import { travelApi, type Trip } from '../services/api/travel'

const INTENT_CHOICES = [
  { value: 'travel_companion', label: 'Travel companion' },
  { value: 'friends_social', label: 'Friends & socializing' },
  { value: 'local_guide', label: 'Meet locals / explore culture' },
  { value: 'activity_partner', label: 'Outdoor / activity partner' },
  { value: 'dating_romantic', label: 'Dating / romance' },
  { value: 'serious_relationship', label: 'Serious relationship' },
  { value: 'casual_dating', label: 'Casual dating' },
]

function TripEditForm({ trip, id }: { trip: Trip; id: string }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [title, setTitle] = useState(trip.title)
  const [description, setDescription] = useState(trip.description || '')
  const [startDate, setStartDate] = useState(trip.start_date)
  const [endDate, setEndDate] = useState(trip.end_date)
  const [status, setStatus] = useState(trip.status)
  const [visibility, setVisibility] = useState(trip.visibility)
  const [companionPreference, setCompanionPreference] = useState(trip.companion_preference)
  const [partySize, setPartySize] = useState(trip.party_size)
  const [selectedIntents, setSelectedIntents] = useState<string[]>(trip.intents)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function toggleIntent(value: string) {
    setSelectedIntents((prev) =>
      prev.includes(value) ? prev.filter((i) => i !== value) : [...prev, value]
    )
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)

    if (!title.trim()) {
      setError('Please enter a trip title.')
      return
    }
    if (startDate > endDate) {
      setError('Trip start date must be before or equal to end date.')
      return
    }

    setSubmitting(true)
    try {
      await travelApi.updateTrip(id, {
        title: title.trim(),
        description: description.trim() || null,
        start_date: startDate,
        end_date: endDate,
        status,
        visibility,
        companion_preference: companionPreference,
        party_size: partySize,
        intents: selectedIntents,
      })
      await queryClient.invalidateQueries({ queryKey: ['trips'] })
      navigate(`/trips/${id}`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to update trip')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="trip-form" onSubmit={(e) => void handleSubmit(e)}>
      <fieldset className="form-section">
        <legend className="section-title">Status & Visibility</legend>
        <div className="form-row">
          <div className="form-col">
            <label htmlFor="trip-status" className="field-label">
              Trip Status
            </label>
            <select
              id="trip-status"
              className="field-input"
              value={status}
              onChange={(e) => setStatus(e.target.value as Trip['status'])}
            >
              <option value="draft">Draft</option>
              <option value="planned">Planned</option>
              <option value="active">Active (Currently travelling)</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
              <option value="archived">Archived</option>
            </select>
          </div>
          <div className="form-col">
            <label htmlFor="trip-visibility" className="field-label">
              Visibility
            </label>
            <select
              id="trip-visibility"
              className="field-input"
              value={visibility}
              onChange={(e) => setVisibility(e.target.value as Trip['visibility'])}
            >
              <option value="discoverable">Discoverable</option>
              <option value="public">Public</option>
              <option value="matches_only">Matches Only</option>
              <option value="private">Private</option>
            </select>
          </div>
        </div>
      </fieldset>

      <fieldset className="form-section">
        <legend className="section-title">Dates & Details</legend>
        <div className="form-row">
          <div className="form-col">
            <label htmlFor="edit-start-date" className="field-label">
              Start Date
            </label>
            <Input
              id="edit-start-date"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              required
            />
          </div>
          <div className="form-col">
            <label htmlFor="edit-end-date" className="field-label">
              End Date
            </label>
            <Input
              id="edit-end-date"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              required
            />
          </div>
        </div>

        <label htmlFor="edit-trip-title" className="field-label">
          Trip Title
        </label>
        <Input
          id="edit-trip-title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          maxLength={120}
        />

        <label htmlFor="edit-trip-description" className="field-label" style={{ marginTop: '12px', display: 'block' }}>
          Description
        </label>
        <TextArea
          id="edit-trip-description"
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

      <fieldset className="form-section">
        <legend className="section-title">Companion Preferences</legend>
        <div className="select-field-group">
          <label htmlFor="companion-preference" className="field-label">
            Companion Preference
          </label>
          <select
            id="companion-preference"
            className="field-input"
            value={companionPreference}
            onChange={(e) => setCompanionPreference(e.target.value as Trip['companion_preference'])}
          >
            <option value="open_to_companion">Open to Companions</option>
            <option value="travelling_alone">Travelling Solo</option>
            <option value="travelling_with_group">Travelling with Group</option>
          </select>
        </div>

        <div className="choice-grid" style={{ marginTop: '1rem' }}>
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

      {error && (
        <div className="error-card" role="alert" style={{ marginBottom: '16px' }}>
          <p>{error}</p>
        </div>
      )}

      <div className="form-actions">
        <Button variant="secondary" type="button" onClick={() => navigate(`/trips/${id}`)}>
          Cancel
        </Button>
        <Button variant="primary" type="submit" disabled={submitting}>
          {submitting ? 'Saving Changes…' : 'Save Changes'}
        </Button>
      </div>
    </form>
  )
}

export default function TripEditPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const tripQuery = useQuery({
    queryKey: ['trips', 'detail', id],
    queryFn: ({ signal }) => travelApi.getMyTrip(id!, signal),
    enabled: Boolean(id),
  })

  if (tripQuery.isLoading) {
    return (
      <main className="trip-form-container">
        <div className="loading-state">
          <span className="spinner" />
          <p>Loading trip details…</p>
        </div>
      </main>
    )
  }

  if (tripQuery.isError || !tripQuery.data) {
    return (
      <main className="trip-form-container">
        <div className="error-card" role="alert">
          <p>Failed to load trip: {tripQuery.error?.message || 'Not found'}</p>
          <Button variant="secondary" onClick={() => navigate('/trips')}>
            Return to My Trips
          </Button>
        </div>
      </main>
    )
  }

  return (
    <main className="trip-form-container">
      <nav className="breadcrumb-nav" aria-label="Breadcrumb">
        <Link to={`/trips/${id}`}>← Back to Trip</Link>
      </nav>

      <header className="page-header">
        <p className="eyebrow">EDIT ITINERARY</p>
        <h1>Edit Trip Itinerary</h1>
        <p className="page-description">
          Destination: <strong>{tripQuery.data.destination.name}</strong>, {tripQuery.data.destination.country}
        </p>
      </header>

      <TripEditForm trip={tripQuery.data} id={id!} />
    </main>
  )
}
