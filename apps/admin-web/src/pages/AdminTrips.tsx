import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { adminApi, type AdminTrip } from '../services/api/admin'

export default function AdminTrips() {
  const [statusFilter, setStatusFilter] = useState('all')
  const [visibilityFilter, setVisibilityFilter] = useState('all')
  const [selectedTrip, setSelectedTrip] = useState<AdminTrip | null>(null)

  const tripsQuery = useQuery({
    queryKey: ['admin', 'trips', statusFilter, visibilityFilter],
    queryFn: ({ signal }) =>
      adminApi.listTrips(
        {
          status: statusFilter,
          visibility: visibilityFilter,
          limit: 50,
        },
        signal,
      ),
  })

  return (
    <div className="module-view">
      <header className="module-header">
        <p className="eyebrow">TRAVEL OPERATIONS</p>
        <h1>Trip Operations</h1>
        <p className="module-description">
          Review itineraries across the platform, companion requests, visibility boundaries, and status lifecycles.
        </p>
      </header>

      <section className="filter-bar" aria-label="Trip Filters">
        <div className="filter-group">
          <label htmlFor="status-filter">Status:</label>
          <select
            id="status-filter"
            className="select-input"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">All Statuses</option>
            <option value="planned">Planned</option>
            <option value="active">Active</option>
            <option value="completed">Completed</option>
            <option value="draft">Draft</option>
            <option value="cancelled">Cancelled</option>
            <option value="archived">Archived</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="visibility-filter">Visibility:</label>
          <select
            id="visibility-filter"
            className="select-input"
            value={visibilityFilter}
            onChange={(e) => setVisibilityFilter(e.target.value)}
          >
            <option value="all">All Visibilities</option>
            <option value="discoverable">Discoverable</option>
            <option value="public">Public</option>
            <option value="matches_only">Matches Only</option>
            <option value="private">Private</option>
          </select>
        </div>

        <span className="queue-count">
          Total Trips: {tripsQuery.data?.total ?? 0}
        </span>
      </section>

      {tripsQuery.isLoading && (
        <div className="loading-state">
          <span className="spinner" />
          <p>Loading trips…</p>
        </div>
      )}

      {tripsQuery.isError && (
        <div className="error-card" role="alert">
          <p><strong>Failed to load trips:</strong> {tripsQuery.error.message}</p>
          <button type="button" className="button button-secondary" onClick={() => void tripsQuery.refetch()}>
            Retry
          </button>
        </div>
      )}

      {tripsQuery.isSuccess && (
        <div className="table-responsive">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Trip & Destination</th>
                <th>Traveller</th>
                <th>Dates</th>
                <th>Party & Companion</th>
                <th>Visibility</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {tripsQuery.data.items.length === 0 ? (
                <tr>
                  <td colSpan={7} className="empty-cell">
                    No trips match the selected filters.
                  </td>
                </tr>
              ) : (
                tripsQuery.data.items.map((trip) => (
                  <tr key={trip.id}>
                    <td>
                      <div className="traveller-cell">
                        <span className="traveller-name">{trip.title}</span>
                        <span className="traveller-sub">
                          {trip.destination.name}, {trip.destination.country}
                        </span>
                      </div>
                    </td>
                    <td>
                      <div className="traveller-cell">
                        <span className="mono-id">{trip.user_id.slice(0, 8)}…</span>
                        {trip.user_email && <span className="traveller-sub">{trip.user_email}</span>}
                      </div>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.74rem' }}>
                        {trip.start_date} → {trip.end_date}
                      </span>
                    </td>
                    <td>
                      <span className="type-badge">
                        {trip.companion_preference.replaceAll('_', ' ')}
                      </span>
                      <div style={{ fontSize: '0.68rem', color: 'var(--muted)', marginTop: 2 }}>
                        Party of {trip.party_size}
                      </div>
                    </td>
                    <td>
                      <span className="type-badge" style={{ background: '#f0f5f2' }}>
                        {trip.visibility}
                      </span>
                    </td>
                    <td>
                      <span className={`status-badge status-${trip.status}`}>{trip.status}</span>
                    </td>
                    <td>
                      <button
                        type="button"
                        className="button button-small button-secondary"
                        onClick={() => setSelectedTrip(trip)}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Inspect Trip Modal */}
      {selectedTrip && (
        <div className="admin-modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="modal-title">
          <div className="admin-modal-card" style={{ maxWidth: 520 }}>
            <h2 id="modal-title">{selectedTrip.title}</h2>
            <p>
              Trip Details &amp; Operational Metadata
            </p>

            <div style={{ display: 'grid', gap: 12, fontSize: '0.8rem', margin: '16px 0' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8, paddingBottom: 8, borderBottom: '1px solid var(--line)' }}>
                <strong style={{ color: 'var(--muted)' }}>Trip ID</strong>
                <span className="mono-id">{selectedTrip.id}</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8, paddingBottom: 8, borderBottom: '1px solid var(--line)' }}>
                <strong style={{ color: 'var(--muted)' }}>Traveller ID</strong>
                <span className="mono-id">{selectedTrip.user_id}</span>
              </div>

              {selectedTrip.user_email && (
                <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8, paddingBottom: 8, borderBottom: '1px solid var(--line)' }}>
                  <strong style={{ color: 'var(--muted)' }}>Traveller Email</strong>
                  <span>{selectedTrip.user_email}</span>
                </div>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8, paddingBottom: 8, borderBottom: '1px solid var(--line)' }}>
                <strong style={{ color: 'var(--muted)' }}>Destination</strong>
                <span>
                  {selectedTrip.destination.name}, {selectedTrip.destination.region}, {selectedTrip.destination.country}
                  {' '}({selectedTrip.destination.latitude.toFixed(4)}, {selectedTrip.destination.longitude.toFixed(4)})
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8, paddingBottom: 8, borderBottom: '1px solid var(--line)' }}>
                <strong style={{ color: 'var(--muted)' }}>Dates</strong>
                <span>{selectedTrip.start_date} to {selectedTrip.end_date}</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8, paddingBottom: 8, borderBottom: '1px solid var(--line)' }}>
                <strong style={{ color: 'var(--muted)' }}>Status</strong>
                <span>
                  <span className={`status-badge status-${selectedTrip.status}`}>{selectedTrip.status}</span>
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8, paddingBottom: 8, borderBottom: '1px solid var(--line)' }}>
                <strong style={{ color: 'var(--muted)' }}>Visibility</strong>
                <span>{selectedTrip.visibility}</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8, paddingBottom: 8, borderBottom: '1px solid var(--line)' }}>
                <strong style={{ color: 'var(--muted)' }}>Companion</strong>
                <span>{selectedTrip.companion_preference.replaceAll('_', ' ')} (Party of {selectedTrip.party_size})</span>
              </div>

              {selectedTrip.intents.length > 0 && (
                <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8, paddingBottom: 8, borderBottom: '1px solid var(--line)' }}>
                  <strong style={{ color: 'var(--muted)' }}>Intents</strong>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {selectedTrip.intents.map((intent) => (
                      <span key={intent} className="type-badge">{intent}</span>
                    ))}
                  </div>
                </div>
              )}

              {selectedTrip.description && (
                <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8, paddingBottom: 8, borderBottom: '1px solid var(--line)' }}>
                  <strong style={{ color: 'var(--muted)' }}>Description</strong>
                  <span>{selectedTrip.description}</span>
                </div>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8 }}>
                <strong style={{ color: 'var(--muted)' }}>Created At</strong>
                <span className="mono-id">{new Date(selectedTrip.created_at).toLocaleString()}</span>
              </div>
            </div>

            <div className="admin-modal-actions">
              <button
                type="button"
                className="button button-secondary"
                onClick={() => setSelectedTrip(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
