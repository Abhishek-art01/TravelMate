import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { TravelMateMap } from '../components/TravelMateMap'
import { Button } from '../components/ui'
import { travelApi } from '../services/api/travel'

export default function TripDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [deleteConfirm, setDeleteConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const tripQuery = useQuery({
    queryKey: ['trips', 'detail', id],
    queryFn: ({ signal }) => travelApi.getMyTrip(id!, signal),
    enabled: Boolean(id),
  })

  async function handleDelete() {
    if (!id) return
    setDeleting(true)
    try {
      await travelApi.deleteTrip(id)
      await queryClient.invalidateQueries({ queryKey: ['trips'] })
      navigate('/trips')
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to delete trip')
      setDeleting(false)
    }
  }

  function formatDates(start: string, end: string) {
    const s = new Date(start)
    const e = new Date(end)
    const opts: Intl.DateTimeFormatOptions = { month: 'long', day: 'numeric', year: 'numeric' }
    return `${s.toLocaleDateString(undefined, opts)} – ${e.toLocaleDateString(undefined, opts)}`
  }

  if (tripQuery.isLoading) {
    return (
      <main className="trip-detail-container">
        <div className="loading-state">
          <span className="spinner" />
          <p>Loading trip itinerary…</p>
        </div>
      </main>
    )
  }

  if (tripQuery.isError || !tripQuery.data) {
    return (
      <main className="trip-detail-container">
        <div className="error-card" role="alert">
          <h2>Trip Not Found</h2>
          <p>This trip itinerary could not be located or you don’t have permission to view it.</p>
          <Button variant="secondary" onClick={() => navigate('/trips')}>
            Return to My Trips
          </Button>
        </div>
      </main>
    )
  }

  const trip = tripQuery.data

  return (
    <main className="trip-detail-container">
      <nav className="breadcrumb-nav" aria-label="Breadcrumb">
        <Link to="/trips">← Back to Trips</Link>
      </nav>

      <header className="trip-detail-header">
        <div className="trip-status-row">
          <span className={`status-pill status-${trip.status}`}>{trip.status}</span>
          <span className="visibility-badge">{trip.visibility}</span>
        </div>
        <h1>{trip.title}</h1>
        <p className="trip-detail-destination">
          📍 {trip.destination.name}, {trip.destination.region} ({trip.destination.country})
        </p>
        <p className="trip-detail-dates">{formatDates(trip.start_date, trip.end_date)}</p>
      </header>

      <section className="trip-detail-map-section">
        <TravelMateMap
          latitude={trip.destination.latitude}
          longitude={trip.destination.longitude}
          title={trip.destination.name}
          mode="destination"
          height={240}
        />
      </section>

      {trip.description && (
        <section className="trip-detail-section">
          <h2>About this Itinerary</h2>
          <p className="trip-description-text">{trip.description}</p>
        </section>
      )}

      <section className="trip-detail-section">
        <h2>Companion & Group Settings</h2>
        <div className="trip-meta-grid">
          <div className="meta-card">
            <span className="meta-label">Preference</span>
            <strong className="meta-value">{trip.companion_preference.replace(/_/g, ' ')}</strong>
          </div>
          <div className="meta-card">
            <span className="meta-label">Party Size</span>
            <strong className="meta-value">{trip.party_size} {trip.party_size === 1 ? 'person' : 'people'}</strong>
          </div>
        </div>
      </section>

      {trip.intents.length > 0 && (
        <section className="trip-detail-section">
          <h2>Travel Intentions</h2>
          <div className="trip-intents-list">
            {trip.intents.map((intent) => (
              <span key={intent} className="intent-chip">
                {intent.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </section>
      )}

      <footer className="trip-detail-actions">
        <Button variant="primary" onClick={() => navigate(`/trips/${trip.id}/edit`)}>
          Edit Itinerary
        </Button>
        <Button variant="secondary" onClick={() => setDeleteConfirm(true)}>
          Delete Trip
        </Button>
      </footer>

      {deleteConfirm && (
        <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="delete-trip-title">
          <div className="modal-content">
            <h2 id="delete-trip-title">Delete Trip?</h2>
            <p>Are you sure you want to delete “{trip.title}”? This action cannot be undone.</p>
            <div className="modal-actions">
              <Button variant="secondary" disabled={deleting} onClick={() => setDeleteConfirm(false)}>
                Cancel
              </Button>
              <Button variant="primary" disabled={deleting} onClick={() => void handleDelete()}>
                {deleting ? 'Deleting…' : 'Yes, Delete'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}
