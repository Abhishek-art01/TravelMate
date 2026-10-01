import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { hasPermission, useAdminAccess } from '../app/permissions/useAdminAccess'
import { adminApi, type AdminSignedMediaUrl } from '../services/api/admin'

export default function AdminVerificationDetail() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const access = useAdminAccess()
  const permissions = access.data?.permissions ?? []

  const canReadMedia = hasPermission(permissions, 'verification.media.read')
  const canReview = hasPermission(permissions, 'verification.review')
  const canApprove = hasPermission(permissions, 'verification.approve')
  const canReject = hasPermission(permissions, 'verification.reject')

  const [mediaUrls, setMediaUrls] = useState<Record<string, AdminSignedMediaUrl>>({})
  const [mediaError, setMediaError] = useState<string | null>(null)
  const [rejectReason, setRejectReason] = useState('')
  const [actionReason, setActionReason] = useState('')
  const [showRejectModal, setShowRejectModal] = useState(false)
  const [showActionModal, setShowActionModal] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  const caseQuery = useQuery({
    queryKey: ['admin', 'verification', 'detail', id],
    queryFn: ({ signal }) => adminApi.getVerificationCase(id!, signal),
    enabled: Boolean(id),
  })

  const startReviewMutation = useMutation({
    mutationFn: () => adminApi.startCaseReview(id!),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'verification', 'detail', id] }),
    onError: (err: Error) => setActionError(err.message),
  })

  const approveMutation = useMutation({
    mutationFn: (reason?: string) => adminApi.approveCase(id!, reason),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'verification', 'detail', id] }),
    onError: (err: Error) => setActionError(err.message),
  })

  const rejectMutation = useMutation({
    mutationFn: (reason: string) => adminApi.rejectCase(id!, reason),
    onSuccess: () => {
      setShowRejectModal(false)
      setRejectReason('')
      void queryClient.invalidateQueries({ queryKey: ['admin', 'verification', 'detail', id] })
    },
    onError: (err: Error) => setActionError(err.message),
  })

  const requestActionMutation = useMutation({
    mutationFn: (reason: string) => adminApi.requestCaseAction(id!, reason),
    onSuccess: () => {
      setShowActionModal(false)
      setActionReason('')
      void queryClient.invalidateQueries({ queryKey: ['admin', 'verification', 'detail', id] })
    },
    onError: (err: Error) => setActionError(err.message),
  })

  async function handleFetchMediaUrl(mediaId: string) {
    setMediaError(null)
    try {
      const res = await adminApi.getSignedMediaUrl(id!, mediaId)
      setMediaUrls((prev) => ({ ...prev, [mediaId]: res }))
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch secure media URL'
      setMediaError(msg)
    }
  }

  if (caseQuery.isLoading) {
    return (
      <div className="module-view">
        <div className="loading-state">
          <span className="spinner" />
          <p>Loading verification case…</p>
        </div>
      </div>
    )
  }

  if (caseQuery.isError || !caseQuery.data) {
    return (
      <div className="module-view">
        <div className="error-card" role="alert">
          <p><strong>Case not found or inaccessible:</strong> {caseQuery.error?.message ?? 'Unknown error'}</p>
          <Link to="/admin/verification" className="button button-secondary">
            Return to queue
          </Link>
        </div>
      </div>
    )
  }

  const caseData = caseQuery.data

  return (
    <div className="module-view case-detail-view">
      <header className="module-header">
        <div className="header-breadcrumbs">
          <Link to="/admin/verification">← Back to verification queue</Link>
        </div>
        <div className="case-title-row">
          <div>
            <p className="eyebrow">VERIFICATION CASE #{caseData.id.slice(0, 8)}</p>
            <h1>{caseData.user_display_name || 'Traveller'} — {caseData.verification_type.replaceAll('_', ' ')}</h1>
          </div>
          <span className={`status-badge status-${caseData.status}`}>{caseData.status}</span>
        </div>
      </header>

      {actionError && (
        <div className="error-card" role="alert">
          <p>{actionError}</p>
        </div>
      )}

      {/* Case Overview Grid */}
      <section className="case-meta-grid" aria-label="Case Overview">
        <div className="meta-card">
          <span className="meta-label">User ID</span>
          <span className="meta-value mono-id">{caseData.user_id}</span>
        </div>
        <div className="meta-card">
          <span className="meta-label">Email</span>
          <span className="meta-value">{caseData.user_email || 'Not available'}</span>
        </div>
        <div className="meta-card">
          <span className="meta-label">Attempt Number</span>
          <span className="meta-value">#{caseData.attempt_number}</span>
        </div>
        <div className="meta-card">
          <span className="meta-label">Submitted At</span>
          <span className="meta-value">{caseData.submitted_at ? new Date(caseData.submitted_at).toLocaleString() : '—'}</span>
        </div>
        <div className="meta-card">
          <span className="meta-label">Assigned Reviewer</span>
          <span className="meta-value">{caseData.reviewed_by ? <span className="mono-id">{caseData.reviewed_by}</span> : 'Unassigned'}</span>
        </div>
        <div className="meta-card">
          <span className="meta-label">Reviewed At</span>
          <span className="meta-value">{caseData.reviewed_at ? new Date(caseData.reviewed_at).toLocaleString() : '—'}</span>
        </div>
      </section>

      {caseData.review_decision_reason && (
        <section className="decision-callout">
          <h3>Review Decision Notes</h3>
          <p>{caseData.review_decision_reason}</p>
        </section>
      )}

      {/* Review Actions Bar */}
      <section className="action-bar" aria-label="Case Review Actions">
        {caseData.status === 'submitted' && canReview && (
          <button
            className="button button-primary"
            disabled={startReviewMutation.isPending}
            onClick={() => startReviewMutation.mutate()}
          >
            {startReviewMutation.isPending ? 'Starting review…' : 'Start Review'}
          </button>
        )}

        {canApprove && caseData.status !== 'verified' && (
          <button
            className="button button-primary"
            disabled={approveMutation.isPending}
            onClick={() => approveMutation.mutate('Approved by administrative reviewer.')}
          >
            {approveMutation.isPending ? 'Approving…' : 'Approve Verification'}
          </button>
        )}

        {canReview && caseData.status !== 'verified' && caseData.status !== 'requires_action' && (
          <button
            className="button button-secondary"
            onClick={() => {
              setActionError(null)
              setShowActionModal(true)
            }}
          >
            Request Action
          </button>
        )}

        {canReject && caseData.status !== 'rejected' && (
          <button
            className="button button-danger"
            onClick={() => {
              setActionError(null)
              setShowRejectModal(true)
            }}
          >
            Reject Verification
          </button>
        )}
      </section>

      {/* Sensitive Media Section */}
      <section className="detail-section" aria-label="Sensitive Verification Documents">
        <div className="section-title">
          <h2>Verification Documents & Media</h2>
          <span className="security-tag">PRIVATE STORAGE VAULT</span>
        </div>

        {!canReadMedia ? (
          <div className="permission-notice" role="alert">
            <p>
              <strong>Access Restricted:</strong> You do not possess the <code>verification.media.read</code> permission.
              Sensitive verification documents (government IDs, selfies, and videos) cannot be accessed without explicit media authorization.
            </p>
          </div>
        ) : (
          <div>
            {mediaError && <div className="error-card" role="alert"><p>{mediaError}</p></div>}
            {caseData.media.length === 0 ? (
              <p className="empty-notice">No media documents attached to this case.</p>
            ) : (
              <div className="media-list">
                {caseData.media.map((m) => {
                  const signed = mediaUrls[m.media_id]
                  return (
                    <article className="media-case-item" key={m.media_id}>
                      <div className="media-info">
                        <span className="media-type-pill">{m.media_type}</span>
                        <span className="media-meta">{m.mime_type} · {(m.size_bytes / 1024).toFixed(1)} KB</span>
                        <span className="media-date">Uploaded: {new Date(m.created_at).toLocaleDateString()}</span>
                      </div>
                      <div className="media-actions">
                        {!signed ? (
                          <button
                            className="button button-small button-secondary"
                            onClick={() => void handleFetchMediaUrl(m.media_id)}
                          >
                            Generate Secure View URL
                          </button>
                        ) : (
                          <div className="signed-view-box">
                            <a
                              href={signed.download_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="button button-small button-primary"
                            >
                              Open Private Document ↗
                            </a>
                            <span className="signed-timer">Expires in ~120s</span>
                          </div>
                        )}
                      </div>
                    </article>
                  )
                })}
              </div>
            )}
          </div>
        )}
      </section>

      {/* Case Audit Timeline */}
      <section className="detail-section" aria-label="Case Audit Timeline">
        <div className="section-title">
          <h2>Audit & Event Timeline</h2>
          <span className="security-tag">TAMPER-EVIDENT LOGS</span>
        </div>
        {caseData.events.length === 0 ? (
          <p className="empty-notice">No audit events recorded yet.</p>
        ) : (
          <ul className="audit-timeline">
            {caseData.events.map((e) => (
              <li key={e.id} className="timeline-item">
                <div className="timeline-marker" />
                <div className="timeline-content">
                  <div className="timeline-header">
                    <span className="event-name">{e.event_type}</span>
                    <span className="event-time">{new Date(e.created_at).toLocaleString()}</span>
                  </div>
                  <span className="event-actor">Actor: {e.actor_type} ({e.actor_id || 'system'})</span>
                  {e.details && <p className="event-details">{e.details}</p>}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Modal: Reject Case */}
      {showRejectModal && (
        <div className="admin-modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="reject-title">
          <div className="admin-modal-card">
            <h2 id="reject-title">Reject Verification Case</h2>
            <p>Please enter the specific rationale for rejecting this verification submission. This reason is recorded in audit logs and communicated to the traveller.</p>
            <textarea
              className="field-input"
              rows={4}
              placeholder="e.g. Identity document expired, name mismatch, or image unreadable."
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
            />
            <div className="admin-modal-actions">
              <button className="button button-ghost" onClick={() => setShowRejectModal(false)}>
                Cancel
              </button>
              <button
                className="button button-danger"
                disabled={!rejectReason.trim() || rejectMutation.isPending}
                onClick={() => rejectMutation.mutate(rejectReason)}
              >
                {rejectMutation.isPending ? 'Rejecting…' : 'Confirm Rejection'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Request Action */}
      {showActionModal && (
        <div className="admin-modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="action-title">
          <div className="admin-modal-card">
            <h2 id="action-title">Request Action From Traveller</h2>
            <p>Specify the required corrective action (e.g. clearer photo or different document type).</p>
            <textarea
              className="field-input"
              rows={4}
              placeholder="e.g. Please provide a clear photo of the back side of your driving licence."
              value={actionReason}
              onChange={(e) => setActionReason(e.target.value)}
            />
            <div className="admin-modal-actions">
              <button className="button button-ghost" onClick={() => setShowActionModal(false)}>
                Cancel
              </button>
              <button
                className="button button-primary"
                disabled={!actionReason.trim() || requestActionMutation.isPending}
                onClick={() => requestActionMutation.mutate(actionReason)}
              >
                {requestActionMutation.isPending ? 'Requesting…' : 'Send Action Request'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
