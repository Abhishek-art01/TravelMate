import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '../components/ui'
import { travelApi, type Trip } from '../services/api/travel'

export default function TripsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'my' | 'discover'>('my')
  const [discoverQuery, setDiscoverQuery] = useState('')
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)

  const myTripsQuery = useQuery({
    queryKey: ['trips', 'my'],
    queryFn: ({ signal }) => travelApi.listMyTrips(signal),
  })

  const discoverTripsQuery = useQuery({
    queryKey: ['trips', 'discover', discoverQuery],
    queryFn: ({ signal }) => travelApi.discoverTrips(undefined, signal),
    enabled: activeTab === 'discover',
  })

  async function handleDelete(tripId: string) {
    setDeleting(true)
    try {
      await travelApi.deleteTrip(tripId)
      setDeleteConfirmId(null)
      await queryClient.invalidateQueries({ queryKey: ['trips', 'my'] })
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to delete trip')
    } finally {
      setDeleting(false)
    }
  }

  function formatDates(start: string, end: string) {
    const s = new Date(start)
    const e = new Date(end)
    const opts: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric', year: 'numeric' }
    return `${s.toLocaleDateString(undefined, opts)} – ${e.toLocaleDateString(undefined, opts)}`
  }

  return (
    <main className="trips-page-container">
      <header className="page-header">
        <div className="header-meta">
          <p className="eyebrow">YOUR TRAVEL PLANS</p>
          <h1>Trips & Itineraries</h1>
          <p className="page-description">
            Organize upcoming journeys, set companion preferences, and discover fellow travellers.
          </p>
        </div>
        <div className="header-actions">
          <Button variant="primary" onClick={() => navigate('/trips/new')}>
            + Plan a Trip
          </Button>
        </div>
      </header>

      <nav className="trips-tabs" aria-label="Trip Views">
        <button
          type="button"
          className={`tab-button ${activeTab === 'my' ? 'active' : ''}`}
          onClick={() => setActiveTab('my')}
          aria-selected={activeTab === 'my'}
          role="tab"
        >
          My Trips ({myTripsQuery.data?.total ?? 0})
        </button>
        <button
          type="button"
          className={`tab-button ${activeTab === 'discover' ? 'active' : ''}`}
          onClick={() => setActiveTab('discover')}
          aria-selected={activeTab === 'discover'}
          role="tab"
        >
          Discover Trips
        </button>
      </nav>

      {activeTab === 'my' && (
        <section aria-label="My Trips">
          {myTripsQuery.isLoading && (
            <div className="loading-state">
              <span className="spinner" />
              <p>Loading your trips…</p>
            </div>
          )}

          {myTripsQuery.isError && (
            <div className="error-card" role="alert">
              <p>Failed to load your trips: {myTripsQuery.error.message}</p>
              <Button variant="secondary" onClick={() => void myTripsQuery.refetch()}>
                Retry
              </Button>
            </div>
          )}

          {myTripsQuery.isSuccess && myTripsQuery.data.items.length === 0 && (
            <div className="empty-trips-state">
              <div className="empty-icon" aria-hidden="true">
                ✈️
              </div>
              <h2>No trips planned yet</h2>
              <p>Start your next adventure by creating an itinerary with your destination and travel dates.</p>
              <Button variant="primary" onClick={() => navigate('/trips/new')}>
                Create Your First Trip
              </Button>
            </div>
          )}

          {myTripsQuery.isSuccess && myTripsQuery.data.items.length > 0 && (
            <div className="trips-grid">
              {myTripsQuery.data.items.map((trip: Trip) => (
                <article key={trip.id} className="trip-card">
                  <div className="trip-card-header">
                    <span className={`status-pill status-${trip.status}`}>{trip.status}</span>
                    <span className="visibility-badge">{trip.visibility}</span>
                  </div>

                  <h3 className="trip-title">
                    <Link to={`/trips/${trip.id}`}>{trip.title}</Link>
                  </h3>

                  <div className="trip-destination-meta">
                    <span className="dest-icon" aria-hidden="true">
                      📍
                    </span>
                    <strong>{trip.destination.name}</strong>, {trip.destination.region}
                  </div>

                  <p className="trip-dates">{formatDates(trip.start_date, trip.end_date)}</p>

                  {trip.description && <p className="trip-snippet">{trip.description}</p>}

                  <div className="trip-badges">
                    <span className="companion-badge">
                      {trip.companion_preference.replace(/_/g, ' ')}
                    </span>
                    <span className="party-badge">Party of {trip.party_size}</span>
                  </div>

                  {trip.intents.length > 0 && (
                    <div className="trip-intents-list">
                      {trip.intents.map((intent) => (
                        <span key={intent} className="intent-chip">
                          {intent.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  )}

                  <footer className="trip-card-actions">
                    <Button variant="secondary" onClick={() => navigate(`/trips/${trip.id}`)}>
                      View Details
                    </Button>
                    <Button variant="secondary" onClick={() => navigate(`/trips/${trip.id}/edit`)}>
                      Edit
                    </Button>
                    <button
                      type="button"
                      className="button button-text delete-btn"
                      onClick={() => setDeleteConfirmId(trip.id)}
                    >
                      Delete
                    </button>
                  </footer>
                </article>
              ))}
            </div>
          )}
        </section>
      )}

      {activeTab === 'discover' && (
        <section aria-label="Discover Trips">
          <div className="discover-search-bar">
            <input
              type="text"
              className="field-input"
              placeholder="Filter discoverable trips…"
              value={discoverQuery}
              onChange={(e) => setDiscoverQuery(e.target.value)}
            />
          </div>

          {discoverTripsQuery.isLoading && (
            <div className="loading-state">
              <span className="spinner" />
              <p>Discovering public trips…</p>
            </div>
          )}

          {discoverTripsQuery.isSuccess && discoverTripsQuery.data.items.length === 0 && (
            <div className="empty-trips-state">
              <p>No public trips found matching your criteria. Check back soon or create your own discoverable trip!</p>
            </div>
          )}

          {discoverTripsQuery.isSuccess && discoverTripsQuery.data.items.length > 0 && (
            <div className="trips-grid">
              {discoverTripsQuery.data.items.map((trip) => (
                <article key={trip.id} className="trip-card">
                  <div className="trip-card-header">
                    <span className="visibility-badge">Public Trip</span>
                    {trip.creator_verified && <span className="verified-pill">✓ Verified Traveller</span>}
                  </div>
                  <h3 className="trip-title">{trip.title}</h3>
                  <div className="trip-destination-meta">
                    <strong>{trip.destination.name}</strong>, {trip.destination.country}
                  </div>
                  <p className="trip-dates">{formatDates(trip.start_date, trip.end_date)}</p>
                  {trip.creator_display_name && (
                    <p className="trip-creator">Host: {trip.creator_display_name}</p>
                  )}
                  <div className="trip-badges">
                    <span className="companion-badge">{trip.companion_preference.replace(/_/g, ' ')}</span>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirmId && (
        <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title">
          <div className="modal-content">
            <h2 id="delete-dialog-title">Delete Trip?</h2>
            <p>Are you sure you want to delete this trip itinerary? This action cannot be undone.</p>
            <div className="modal-actions">
              <Button variant="secondary" disabled={deleting} onClick={() => setDeleteConfirmId(null)}>
                Cancel
              </Button>
              <Button variant="primary" disabled={deleting} onClick={() => void handleDelete(deleteConfirmId)}>
                {deleting ? 'Deleting…' : 'Yes, Delete'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}
