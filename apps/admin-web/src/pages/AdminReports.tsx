import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { hasPermission, useAdminAccess } from '../app/permissions/useAdminAccess'
import { adminApi, type AdminReport } from '../services/api/admin'

export default function AdminReports() {
  const access = useAdminAccess()
  const canAction = hasPermission(access.data?.permissions ?? [], 'moderation.action')

  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [reports, setReports] = useState<AdminReport[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actioningReport, setActioningReport] = useState<AdminReport | null>(null)
  const [targetStatus, setTargetStatus] = useState<'actioned' | 'dismissed'>('actioned')
  const [resolutionNotes, setResolutionNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const fetchReports = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await adminApi.listReports(statusFilter)
      setReports(res.items)
    } catch (err) {
      setError((err as Error).message || 'Failed to load reports')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void fetchReports()
  }, [statusFilter])

  const handleUpdate = async () => {
    if (!actioningReport) return
    setSubmitting(true)
    try {
      await adminApi.updateReport(actioningReport.id, targetStatus, resolutionNotes)
      setActioningReport(null)
      setResolutionNotes('')
      setSuccessMessage(`Report ${targetStatus === 'actioned' ? 'actioned' : 'dismissed'} successfully.`)
      setTimeout(() => setSuccessMessage(null), 4000)
      await fetchReports()
    } catch (err) {
      setError((err as Error).message || 'Failed to update report')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="admin-page">
      <div className="admin-header-row">
        <div>
          <p className="eyebrow">MODERATION & SAFETY</p>
          <h1>User Reports Queue</h1>
          <p className="page-lede">
            Review and resolve safety reports submitted by members. All outcomes are logged for audit compliance.
          </p>
        </div>
        <Link to="/admin" className="button button-secondary">
          Dashboard
        </Link>
      </div>

      {successMessage && (
        <div className="form-success" role="status" style={{ marginBottom: 16 }}>
          {successMessage}
        </div>
      )}
      {error && (
        <div className="form-error" role="alert" style={{ marginBottom: 16 }}>
          {error}
        </div>
      )}

      {/* Filter Tabs */}
      <div className="filter-tabs-row" style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        {(['all', 'pending', 'under_review', 'actioned', 'dismissed'] as const).map((tab) => (
          <button
            key={tab}
            type="button"
            className={`button ${statusFilter === tab ? 'button-primary' : 'button-secondary'}`}
            style={{ fontSize: '0.85rem', padding: '6px 14px', minHeight: 38 }}
            onClick={() => setStatusFilter(tab)}
          >
            {tab.replace('_', ' ').toUpperCase()}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loading-box" style={{ padding: 40, textAlign: 'center' }}>
          <p>Loading moderation queue…</p>
        </div>
      ) : reports.length === 0 ? (
        <div className="empty-box" style={{ padding: 40, textAlign: 'center', background: '#fff', border: '1px solid #dce3dc', borderRadius: 8 }}>
          <h2>No reports found</h2>
          <p style={{ color: '#71807a' }}>There are no reports matching the selected status filter.</p>
        </div>
      ) : (
        <div className="table-responsive" style={{ background: '#fff', border: '1px solid #dce3dc', borderRadius: 8, overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#f4f6f1', borderBottom: '1px solid #dce3dc', fontSize: '0.8rem', color: '#71807a' }}>
                <th style={{ padding: '12px 16px' }}>REASON</th>
                <th style={{ padding: '12px 16px' }}>REPORTED USER</th>
                <th style={{ padding: '12px 16px' }}>REPORTER</th>
                <th style={{ padding: '12px 16px' }}>DETAILS</th>
                <th style={{ padding: '12px 16px' }}>STATUS</th>
                <th style={{ padding: '12px 16px' }}>DATE</th>
                <th style={{ padding: '12px 16px' }}>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((report) => (
                <tr key={report.id} style={{ borderBottom: '1px solid #eef2ef' }}>
                  <td style={{ padding: '12px 16px', fontWeight: 600 }}>
                    {report.reason.replace(/_/g, ' ')}
                  </td>
                  <td style={{ padding: '12px 16px', fontFamily: 'monospace', fontSize: '0.85rem' }}>
                    {report.reported_id.slice(0, 8)}…
                  </td>
                  <td style={{ padding: '12px 16px', fontFamily: 'monospace', fontSize: '0.85rem' }}>
                    {report.reporter_id.slice(0, 8)}…
                  </td>
                  <td style={{ padding: '12px 16px', fontSize: '0.85rem', maxWidth: 260 }}>
                    {report.details || '—'}
                    {report.resolution_notes && (
                      <div style={{ marginTop: 4, color: '#1c5748', fontSize: '0.8rem' }}>
                        <em>Note: {report.resolution_notes}</em>
                      </div>
                    )}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span
                      style={{
                        padding: '3px 8px',
                        borderRadius: 12,
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        background:
                          report.status === 'pending'
                            ? '#fff3d9'
                            : report.status === 'actioned'
                            ? '#ffe8e4'
                            : report.status === 'dismissed'
                            ? '#edf2ef'
                            : '#e3f2fd',
                        color:
                          report.status === 'pending'
                            ? '#744d1b'
                            : report.status === 'actioned'
                            ? '#a13d2f'
                            : report.status === 'dismissed'
                            ? '#506058'
                            : '#1565c0',
                      }}
                    >
                      {report.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px', fontSize: '0.85rem', color: '#71807a' }}>
                    {new Date(report.created_at).toLocaleDateString()}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    {canAction && report.status === 'pending' ? (
                      <div style={{ display: 'flex', gap: 6 }}>
                        <button
                          type="button"
                          className="button button-primary"
                          style={{ minHeight: 32, padding: '0 10px', fontSize: '0.8rem' }}
                          onClick={() => {
                            setActioningReport(report)
                            setTargetStatus('actioned')
                          }}
                        >
                          Action
                        </button>
                        <button
                          type="button"
                          className="button button-secondary"
                          style={{ minHeight: 32, padding: '0 10px', fontSize: '0.8rem' }}
                          onClick={() => {
                            setActioningReport(report)
                            setTargetStatus('dismissed')
                          }}
                        >
                          Dismiss
                        </button>
                      </div>
                    ) : (
                      <span style={{ fontSize: '0.8rem', color: '#909c95' }}>
                        {report.status !== 'pending' ? 'Resolved' : 'Read-only'}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Resolution Modal */}
      {actioningReport && (
        <div
          role="dialog"
          aria-modal="true"
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'grid',
            placeContent: 'center',
            padding: 20,
            zIndex: 1000,
          }}
        >
          <div
            style={{
              background: '#fff',
              borderRadius: 8,
              padding: 24,
              maxWidth: 440,
              width: '100%',
              boxShadow: '0 10px 30px rgba(0,0,0,0.2)',
            }}
          >
            <h3>
              {targetStatus === 'actioned' ? 'Action Safety Report' : 'Dismiss Report'}
            </h3>
            <p style={{ color: '#71807a', fontSize: '0.9rem' }}>
              Reason: <strong>{actioningReport.reason.replace(/_/g, ' ')}</strong>
            </p>
            <div style={{ margin: '14px 0' }}>
              <label
                htmlFor="resolution-notes-input"
                style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}
              >
                Resolution Notes (optional)
              </label>
              <textarea
                id="resolution-notes-input"
                className="field-input"
                style={{ width: '100%', minHeight: 80, padding: 8, borderRadius: 4, border: '1px solid #cbd6ce' }}
                placeholder="Audit notes on actions taken or rationale for dismissal..."
                value={resolutionNotes}
                onChange={(e) => setResolutionNotes(e.target.value)}
              />
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button
                type="button"
                className="button button-ghost"
                onClick={() => setActioningReport(null)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="button button-primary"
                disabled={submitting}
                onClick={handleUpdate}
              >
                {submitting ? 'Submitting…' : `Confirm ${targetStatus === 'actioned' ? 'Action' : 'Dismissal'}`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
