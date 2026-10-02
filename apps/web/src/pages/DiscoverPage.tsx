import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Button } from '../components/ui'
import { discoveryApi, type DiscoveryCandidate, type DiscoveryFilters } from '../services/api/discovery'

export default function DiscoverPage() {
  const queryClient = useQueryClient()
  const [filters, setFilters] = useState<DiscoveryFilters>({})
  const [activeCursor, setActiveCursor] = useState<string | null>(null)
  const [candidatesList, setCandidatesList] = useState<DiscoveryCandidate[]>([])
  const [matchedCandidate, setMatchedCandidate] = useState<DiscoveryCandidate | null>(null)
  const [reportingUser, setReportingUser] = useState<DiscoveryCandidate | null>(null)
  const [reportReason, setReportReason] = useState<string>('inappropriate_content')
  const [reportDetails, setReportDetails] = useState<string>('')
  const [reportSuccess, setReportSuccess] = useState<string | null>(null)
  const [blockingUser, setBlockingUser] = useState<DiscoveryCandidate | null>(null)
  const [blockReason, setBlockReason] = useState<string>('')
  const [blockSuccess, setBlockSuccess] = useState<string | null>(null)

  // Fetch candidates
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['discovery', 'candidates', filters, activeCursor],
    queryFn: async () => {
      const res = await discoveryApi.getCandidates(filters, activeCursor)
      if (activeCursor) {
        setCandidatesList((prev) => [...prev, ...res.items])
      } else {
        setCandidatesList(res.items)
      }
      return res
    },
  })

  // Like / Pass mutation
  const interactMutation = useMutation({
    mutationFn: async ({ candidate, type }: { candidate: DiscoveryCandidate; type: 'like' | 'pass' }) => {
      const res = await discoveryApi.recordInteraction(candidate.id, type)
      return { candidate, type, isMatch: res.is_match }
    },
    onSuccess: ({ candidate, type, isMatch }) => {
      // Remove candidate from list
      setCandidatesList((prev) => prev.filter((c) => c.id !== candidate.id))
      if (type === 'like' && isMatch) {
        setMatchedCandidate(candidate)
      }
    },
  })

  // Block mutation
  const blockMutation = useMutation({
    mutationFn: async ({ userId, reason }: { userId: string; reason?: string }) => {
      return discoveryApi.blockUser(userId, reason)
    },
    onSuccess: (_, { userId }) => {
      setCandidatesList((prev) => prev.filter((c) => c.id !== userId))
      setBlockingUser(null)
      setBlockSuccess('User has been blocked.')
      setTimeout(() => setBlockSuccess(null), 4000)
      void queryClient.invalidateQueries({ queryKey: ['discovery'] })
    },
  })

  // Report mutation
  const reportMutation = useMutation({
    mutationFn: async ({
      reportedId,
      reason,
      details,
    }: {
      reportedId: string
      reason: string
      details?: string
    }) => {
      return discoveryApi.reportUser(reportedId, reason, details)
    },
    onSuccess: () => {
      setReportingUser(null)
      setReportDetails('')
      setReportSuccess('Thank you. Your report has been submitted to moderation.')
      setTimeout(() => setReportSuccess(null), 5000)
    },
  })

  const handleFilterChange = (key: keyof DiscoveryFilters, value: string | number | undefined) => {
    setActiveCursor(null)
    setFilters((prev) => ({
      ...prev,
      [key]: value || undefined,
    }))
  }

  const resetFilters = () => {
    setActiveCursor(null)
    setFilters({})
  }

  return (
    <div className="member-layout">
      <header className="member-header">
        <Link to="/home" className="brand-lockup">
          <span className="brand-mark">
            <img src="/logo-icon.png" alt="TravelMate" />
          </span>
          <span>travelmate</span>
        </Link>
        <nav aria-label="Main navigation">
          <Link to="/home">Home</Link>
          <Link to="/discover" className="nav-active">
            Discover
          </Link>
          <Link to="/trips">Trips</Link>
          <Link to="/profile">Profile</Link>
          <Link to="/settings/verification">Verification</Link>
          <Link to="/privacy">Privacy</Link>
        </nav>
        <Link className="header-link" to="/home">
          Back home
        </Link>
      </header>

      <main className="discover-main">
        <div className="discover-header-row">
          <div>
            <p className="eyebrow">DISCOVERY & MATCHING</p>
            <h1>Connect with Fellow Travelers</h1>
            <p className="page-lede">
              Discover verified companions matching your destination, dates, and travel style.
            </p>
          </div>
        </div>

        {/* Notifications */}
        {blockSuccess && (
          <div className="form-success" role="status" style={{ marginBottom: 16 }}>
            {blockSuccess}
          </div>
        )}
        {reportSuccess && (
          <div className="form-success" role="status" style={{ marginBottom: 16 }}>
            {reportSuccess}
          </div>
        )}

        {/* Mutual Match Banner */}
        {matchedCandidate && (
          <section className="match-banner" aria-label="Mutual match celebration">
            <div className="match-banner-content">
              <span className="match-sparkle" aria-hidden="true">
                ✨
              </span>
              <div>
                <h2>It’s a Match!</h2>
                <p>
                  You and <strong>{matchedCandidate.display_name}</strong> are both interested in connecting for travel!
                </p>
              </div>
              <Button variant="primary" onClick={() => setMatchedCandidate(null)}>
                Awesome
              </Button>
            </div>
          </section>
        )}

        {/* Filter Toolbar */}
        <section className="discover-filters-card" aria-label="Discovery filters">
          <div className="filters-header">
            <h3>Filters</h3>
            {(filters.intent || filters.gender || filters.country_code || filters.start_date || filters.end_date) && (
              <button type="button" className="text-link" onClick={resetFilters}>
                Clear all filters
              </button>
            )}
          </div>
          <div className="filters-grid">
            <div className="filter-field">
              <label htmlFor="filter-intent">Travel Intent</label>
              <select
                id="filter-intent"
                className="field-input"
                value={filters.intent || ''}
                onChange={(e) => handleFilterChange('intent', e.target.value)}
              >
                <option value="">Any intent</option>
                <option value="travel_companion">Travel Companion</option>
                <option value="friends_social">Friends & Social</option>
                <option value="activity_partner">Activity Partner</option>
                <option value="local_guide">Local Guide</option>
                <option value="dating_romantic">Dating / Romantic</option>
              </select>
            </div>

            <div className="filter-field">
              <label htmlFor="filter-country">Country Code</label>
              <input
                id="filter-country"
                type="text"
                placeholder="e.g. IN, FR, JP"
                maxLength={2}
                className="field-input"
                value={filters.country_code || ''}
                onChange={(e) => handleFilterChange('country_code', e.target.value.toUpperCase())}
              />
            </div>

            <div className="filter-field">
              <label htmlFor="filter-start-date">From Date</label>
              <input
                id="filter-start-date"
                type="date"
                className="field-input"
                value={filters.start_date || ''}
                onChange={(e) => handleFilterChange('start_date', e.target.value)}
              />
            </div>

            <div className="filter-field">
              <label htmlFor="filter-end-date">To Date</label>
              <input
                id="filter-end-date"
                type="date"
                className="field-input"
                value={filters.end_date || ''}
                onChange={(e) => handleFilterChange('end_date', e.target.value)}
              />
            </div>

            <div className="filter-field">
              <label htmlFor="filter-gender">Gender</label>
              <select
                id="filter-gender"
                className="field-input"
                value={filters.gender || ''}
                onChange={(e) => handleFilterChange('gender', e.target.value)}
              >
                <option value="">Any gender</option>
                <option value="woman">Woman</option>
                <option value="man">Man</option>
                <option value="non_binary">Non-binary</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
        </section>

        {/* Content Area */}
        {isLoading && !candidatesList.length ? (
          <div className="route-loading" role="status">
            <span className="spinner" />
            <p>Searching for discoverable travelers…</p>
          </div>
        ) : isError ? (
          <div className="form-error" role="alert">
            <p>Could not load discovery candidates: {(error as Error).message}</p>
            <Button variant="secondary" onClick={() => void refetch()}>
              Try again
            </Button>
          </div>
        ) : candidatesList.length === 0 ? (
          <div className="discover-empty-state">
            <div className="empty-icon" aria-hidden="true">
              🗺️
            </div>
            <h2>No discoverable travelers found</h2>
            <p>
              We couldn’t find anyone matching your exact preferences right now. As more travelers plan trips and update
              their profiles, new candidates will appear here.
            </p>
            <Button variant="secondary" onClick={resetFilters}>
              Reset filters
            </Button>
          </div>
        ) : (
          <>
            <div className="candidates-count-row">
              <span className="count-label">
                Showing <strong>{candidatesList.length}</strong> traveler{candidatesList.length !== 1 ? 's' : ''}
              </span>
              {isFetching && <span className="small-spinner" aria-hidden="true" />}
            </div>

            <div className="candidates-grid">
              {candidatesList.map((candidate) => (
                <article key={candidate.id} className="candidate-card">
                  {/* Photo & Top Badges */}
                  <div className="candidate-media-wrap">
                    {candidate.photo_url ? (
                      <img
                        src={candidate.photo_url}
                        alt={candidate.display_name}
                        className="candidate-photo"
                      />
                    ) : (
                      <div className="candidate-photo-placeholder">
                        <span>{candidate.display_name.charAt(0).toUpperCase()}</span>
                      </div>
                    )}
                    <div className="candidate-score-pill">
                      <span className="score-number">{candidate.match_score}%</span>
                      <span className="score-label">Match</span>
                    </div>
                  </div>

                  {/* Body Info */}
                  <div className="candidate-body">
                    <div className="candidate-name-row">
                      <h2>
                        {candidate.display_name}, {candidate.age}
                      </h2>
                      {candidate.is_verified && (
                        <span className="verified-badge" title="Verified Identity">
                          ✓ Verified
                        </span>
                      )}
                    </div>

                    {candidate.approx_city && (
                      <p className="candidate-location">
                        📍 {candidate.approx_city}
                        {candidate.approx_country ? `, ${candidate.approx_country}` : ''}
                        {candidate.approx_distance_km !== null && candidate.approx_distance_km !== undefined ? (
                          <span className="distance-tag"> (~{Math.round(candidate.approx_distance_km)} km)</span>
                        ) : null}
                      </p>
                    )}

                    {candidate.bio && <p className="candidate-bio">{candidate.bio}</p>}

                    {/* Safe Match Reasons */}
                    {candidate.match_reasons.length > 0 && (
                      <div className="match-reasons-box">
                        <span className="reasons-title">Why you match:</span>
                        <ul className="reasons-list">
                          {candidate.match_reasons.map((reason, idx) => (
                            <li key={idx}>✨ {reason}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Upcoming Trips */}
                    {candidate.trips.length > 0 && (
                      <div className="candidate-section">
                        <span className="section-label">Planned Trip</span>
                        {candidate.trips.map((trip) => (
                          <div key={trip.id} className="candidate-trip-card">
                            <strong>{trip.destination_name}</strong>
                            <span className="trip-dates">
                              {trip.start_date} – {trip.end_date}
                            </span>
                            {trip.intents.length > 0 && (
                              <div className="trip-intents-tags">
                                {trip.intents.map((intent) => (
                                  <span key={intent} className="intent-tag">
                                    {intent.replace(/_/g, ' ')}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Interests & Languages */}
                    {(candidate.interests.length > 0 || candidate.languages.length > 0) && (
                      <div className="candidate-tags-row">
                        {candidate.interests.map((interest) => (
                          <span key={interest} className="interest-pill">
                            #{interest.replace(/_/g, ' ')}
                          </span>
                        ))}
                        {candidate.languages.map((lang) => (
                          <span key={lang} className="lang-pill">
                            🗣 {lang.toUpperCase()}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Actions: Pass / Like / More */}
                    <div className="candidate-card-actions">
                      <button
                        type="button"
                        className="action-btn pass-btn"
                        title="Pass"
                        disabled={interactMutation.isPending}
                        onClick={() => interactMutation.mutate({ candidate, type: 'pass' })}
                      >
                        ✕ Pass
                      </button>

                      <button
                        type="button"
                        className="action-btn like-btn"
                        title="Connect / Like"
                        disabled={interactMutation.isPending}
                        onClick={() => interactMutation.mutate({ candidate, type: 'like' })}
                      >
                        ♥ Connect
                      </button>
                    </div>

                    {/* Safety actions: Block & Report */}
                    <div className="candidate-safety-row">
                      <button
                        type="button"
                        className="safety-link"
                        onClick={() => setReportingUser(candidate)}
                      >
                        Report
                      </button>
                      <span>·</span>
                      <button
                        type="button"
                        className="safety-link"
                        onClick={() => setBlockingUser(candidate)}
                      >
                        Block
                      </button>
                    </div>
                  </div>
                </article>
              ))}
            </div>

            {/* Pagination Cursor */}
            {data?.next_cursor && (
              <div className="discover-pagination-wrap">
                <Button
                  variant="secondary"
                  disabled={isFetching}
                  onClick={() => setActiveCursor(data.next_cursor || null)}
                >
                  {isFetching ? 'Loading more…' : 'Load more travelers'}
                </Button>
              </div>
            )}
          </>
        )}

        {/* Block Modal */}
        {blockingUser && (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="block-modal-title">
            <div className="modal-card">
              <h3 id="block-modal-title">Block {blockingUser.display_name}?</h3>
              <p>
                They will no longer appear in your discovery, and they will never be able to see your profile or trips.
              </p>
              <div className="filter-field" style={{ margin: '14px 0' }}>
                <label htmlFor="block-reason-input">Reason (optional)</label>
                <input
                  id="block-reason-input"
                  type="text"
                  className="field-input"
                  placeholder="e.g. Unwanted contact"
                  value={blockReason}
                  onChange={(e) => setBlockReason(e.target.value)}
                />
              </div>
              <div className="modal-actions">
                <Button variant="ghost" onClick={() => setBlockingUser(null)}>
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  disabled={blockMutation.isPending}
                  onClick={() => blockMutation.mutate({ userId: blockingUser.id, reason: blockReason })}
                >
                  {blockMutation.isPending ? 'Blocking…' : 'Confirm Block'}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Report Modal */}
        {reportingUser && (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="report-modal-title">
            <div className="modal-card">
              <h3 id="report-modal-title">Report {reportingUser.display_name}</h3>
              <p>Reports are strictly reviewed by the TravelMate moderation team.</p>
              <div className="filter-field" style={{ margin: '14px 0' }}>
                <label htmlFor="report-reason-select">Reason</label>
                <select
                  id="report-reason-select"
                  className="field-input"
                  value={reportReason}
                  onChange={(e) => setReportReason(e.target.value)}
                >
                  <option value="inappropriate_content">Inappropriate Content</option>
                  <option value="harassment">Harassment</option>
                  <option value="spam_or_commercial">Spam or Commercial</option>
                  <option value="fake_profile">Fake Profile</option>
                  <option value="safety_concern">Safety Concern</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div className="filter-field" style={{ margin: '14px 0' }}>
                <label htmlFor="report-details-input">Details (optional)</label>
                <textarea
                  id="report-details-input"
                  className="field-input"
                  placeholder="Explain the issue..."
                  rows={3}
                  value={reportDetails}
                  onChange={(e) => setReportDetails(e.target.value)}
                />
              </div>
              <div className="modal-actions">
                <Button variant="ghost" onClick={() => setReportingUser(null)}>
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  disabled={reportMutation.isPending}
                  onClick={() =>
                    reportMutation.mutate({
                      reportedId: reportingUser.id,
                      reason: reportReason,
                      details: reportDetails,
                    })
                  }
                >
                  {reportMutation.isPending ? 'Submitting…' : 'Submit Report'}
                </Button>
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="member-footer">
        <span>TRAVELMATE DISCOVERY ENGINE</span>
        <span>EXPLAINABLE COMPATIBILITY · PRIVACY PRESERVED</span>
      </footer>
    </div>
  )
}
