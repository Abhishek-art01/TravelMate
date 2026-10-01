import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { adminApi } from '../services/api/admin'

export default function AdminVerificationQueue() {
  const [statusFilter, setStatusFilter] = useState('all')
  const [typeFilter, setTypeFilter] = useState('all')

  const queueQuery = useQuery({
    queryKey: ['admin', 'verification', 'queue', statusFilter, typeFilter],
    queryFn: ({ signal }) => adminApi.listVerificationQueue(statusFilter, typeFilter, signal),
  })

  return (
    <div className="module-view">
      <header className="module-header">
        <p className="eyebrow">IDENTITY OPERATIONS</p>
        <h1>Verification Review Queue</h1>
        <p className="module-description">
          Review submitted identity verification documents and manage user verification status.
          Sensitive verification media access requires explicit permissions.
        </p>
      </header>

      <section className="filter-bar" aria-label="Queue Filters">
        <div className="filter-group">
          <label htmlFor="status-filter">Status:</label>
          <select
            id="status-filter"
            className="select-input"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">All Statuses</option>
            <option value="submitted">Submitted</option>
            <option value="in_review">In Review</option>
            <option value="requires_action">Requires Action</option>
            <option value="verified">Verified</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="type-filter">Verification Type:</label>
          <select
            id="type-filter"
            className="select-input"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="all">All Types</option>
            <option value="government_id">Government ID</option>
            <option value="selfie">Selfie</option>
            <option value="video">Video</option>
          </select>
        </div>

        <span className="queue-count">
          Total Cases: {queueQuery.data?.total ?? 0}
        </span>
      </section>

      {queueQuery.isLoading && (
        <div className="loading-state">
          <span className="spinner" />
          <p>Loading verification cases…</p>
        </div>
      )}

      {queueQuery.isError && (
        <div className="error-card" role="alert">
          <p><strong>Failed to load verification queue:</strong> {queueQuery.error.message}</p>
          <button className="button button-secondary" onClick={() => void queueQuery.refetch()}>
            Retry
          </button>
        </div>
      )}

      {queueQuery.isSuccess && (
        <div className="table-responsive">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Case ID</th>
                <th>Traveller</th>
                <th>Type</th>
                <th>Status</th>
                <th>Attempt</th>
                <th>Submitted</th>
                <th>Reviewer</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {queueQuery.data.items.length === 0 ? (
                <tr>
                  <td colSpan={8} className="empty-cell">
                    No verification cases match the selected filters.
                  </td>
                </tr>
              ) : (
                queueQuery.data.items.map((c) => (
                  <tr key={c.id}>
                    <td>
                      <span className="mono-id">{c.id.slice(0, 8)}…</span>
                    </td>
                    <td>
                      <div className="traveller-cell">
                        <span className="traveller-name">{c.user_display_name || 'Anonymous User'}</span>
                        <span className="traveller-sub">{c.user_email || c.user_id.slice(0, 8)}</span>
                      </div>
                    </td>
                    <td>
                      <span className="type-badge">{c.verification_type.replaceAll('_', ' ')}</span>
                    </td>
                    <td>
                      <span className={`status-badge status-${c.status}`}>{c.status}</span>
                    </td>
                    <td>#{c.attempt_number}</td>
                    <td>{c.submitted_at ? new Date(c.submitted_at).toLocaleDateString() : '—'}</td>
                    <td>{c.reviewed_by ? <span className="mono-id">{c.reviewed_by.slice(0, 6)}…</span> : '—'}</td>
                    <td>
                      <Link to={`/admin/verification/${c.id}`} className="button button-small button-secondary">
                        Review Case
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
