import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Button } from '../components/ui'
import { profileApi, type CheckStatus, type UserVerificationOverview } from '../services/api/profile'

const VERIFICATION_TYPE_DETAILS: Record<string, { title: string; description: string; instructions: string }> = {
  government_id: {
    title: 'Government-Issued ID',
    description: 'Verify your legal name and age using a government-issued photo identity document.',
    instructions: 'Prepare an official, unexpired passport, driving licence, or national identity card. Photos must be clear and legible with all four corners visible.',
  },
  selfie: {
    title: 'Selfie Verification',
    description: 'Real-time selfie check to confirm identity against your photo identification.',
    instructions: 'Position your face in good lighting without hats, sunglasses, or heavy filters. Live camera capture will verify liveness.',
  },
  video: {
    title: 'Short Video Verification',
    description: 'Short dynamic video recording for enhanced travel community safety.',
    instructions: 'A brief 5-second video recording prompt confirming your presence and travel intent.',
  },
}

export default function VerificationPage() {
  const queryClient = useQueryClient()
  const overview = useQuery({
    queryKey: ['verification', 'overview'],
    queryFn: profileApi.getVerification,
    retry: false,
  })

  const [activeModalType, setActiveModalType] = useState<string | null>(null)
  const [sessionUrl, setSessionUrl] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const startMutation = useMutation({
    mutationFn: (type: string) => profileApi.startVerification(type),
    onSuccess: (data) => {
      setErrorMessage(null)
      if (data.session_url) {
        setSessionUrl(data.session_url)
      }
      void queryClient.invalidateQueries({ queryKey: ['verification', 'overview'] })
    },
    onError: (err: Error) => {
      setErrorMessage(err.message || 'Unable to start verification.')
    },
  })

  if (overview.isLoading) {
    return (
      <main className="member-page">
        <h1>Loading verification status…</h1>
        <div className="skeleton-line" />
      </main>
    )
  }

  const data: UserVerificationOverview = overview.data ?? {
    user_id: '',
    overall_status: 'not_started',
    is_verified: false,
    checks: {},
    verification_status: 'not_started',
    required_checks: [],
  }

  const emailCheck = data.checks?.email
  const socialCheck = data.checks?.social
  const selfieCheck = data.checks?.selfie
  const govIdCheck = data.checks?.government_id
  const videoCheck = data.checks?.video

  function openStartModal(type: string) {
    setErrorMessage(null)
    setSessionUrl(null)
    setActiveModalType(type)
  }

  function handleStart(type: string) {
    startMutation.mutate(type)
  }

  function renderStatusBadge(status?: string) {
    const s = (status || 'not_started').toLowerCase()
    let className = 'badge-neutral'
    let label = 'Not started'

    if (s === 'verified') {
      className = 'badge-success'
      label = 'Verified'
    } else if (s === 'in_review' || s === 'submitted') {
      className = 'badge-pending'
      label = 'In review'
    } else if (s === 'in_progress' || s === 'pending') {
      className = 'badge-pending'
      label = 'In progress'
    } else if (s === 'requires_action') {
      className = 'badge-action'
      label = 'Action required'
    } else if (s === 'rejected') {
      className = 'badge-error'
      label = 'Rejected'
    }

    return <span className={`verification-badge ${className}`}>{label}</span>
  }

  function renderChannelCard(
    typeKey: string,
    check?: CheckStatus,
    interactive = false,
  ) {
    const info = VERIFICATION_TYPE_DETAILS[typeKey]
    const title = info?.title ?? typeKey.replaceAll('_', ' ').toUpperCase()
    const desc = info?.description ?? ''
    const currentStatus = check?.status ?? 'not_started'
    const canStart = interactive && (currentStatus === 'not_started' || currentStatus === 'rejected' || currentStatus === 'requires_action')
    const remaining = check?.attempts_remaining ?? 3

    return (
      <article className="verification-card" key={typeKey}>
        <div className="card-top">
          <div className="card-heading">
            <span className="channel-eyebrow">{typeKey.replaceAll('_', ' ').toUpperCase()}</span>
            <h2>{title}</h2>
          </div>
          {renderStatusBadge(currentStatus)}
        </div>
        <p className="card-desc">{desc || check?.details || 'Channel status and trust verification.'}</p>
        {check?.details && desc && <p className="card-note"><em>Note: {check.details}</em></p>}
        {interactive && (
          <div className="card-actions">
            {canStart && (
              <Button
                variant="primary"
                onClick={() => openStartModal(typeKey)}
                disabled={startMutation.isPending || remaining <= 0}
              >
                {currentStatus === 'requires_action' ? 'Update submission' : currentStatus === 'rejected' ? 'Retry verification' : 'Begin verification'}
              </Button>
            )}
            {interactive && <span className="remaining-text">Attempts remaining: {remaining}</span>}
          </div>
        )}
      </article>
    )
  }

  return (
    <div className="member-layout">
      <header className="member-header">
        <Link to="/home" className="brand-lockup">
          <span className="brand-mark">T</span>
          <span>travelmate</span>
        </Link>
        <nav aria-label="Main navigation">
          <Link to="/home">Home</Link>
          <Link to="/profile">Profile</Link>
          <Link className="nav-active" to="/settings/verification">Verification</Link>
          <Link to="/privacy">Privacy</Link>
        </nav>
        <Link className="header-link" to="/home">Back home</Link>
      </header>

      <main className="member-page verification-page">
        <p className="eyebrow">TRUST & SAFETY FOUNDATION</p>
        <h1>Identity Verification Center</h1>
        <p className="page-lede">
          TravelMate verifies identity so that you can connect with verified travellers safely.
          Identity documents and biometric checks are stored in a dedicated, private vault with
          strict retention policies and are never made public or attached to your profile.
        </p>

        {errorMessage && (
          <div className="form-error" role="alert">
            <p><strong>Verification Notice:</strong> {errorMessage}</p>
          </div>
        )}

        <section className="verification-grid" aria-label="Verification Channels">
          {/* 1. Email Channel */}
          <article className="verification-card" key="email">
            <div className="card-top">
              <div className="card-heading">
                <span className="channel-eyebrow">AUTHENTICATION SIGNAL</span>
                <h2>Email Verification</h2>
              </div>
              {renderStatusBadge(emailCheck?.status)}
            </div>
            <p className="card-desc">
              Your registered email address is verified through your authentication account.
            </p>
            {emailCheck?.details && <p className="card-note">{emailCheck.details}</p>}
          </article>

          {/* 2. Social Identity Signal */}
          <article className="verification-card" key="social">
            <div className="card-top">
              <div className="card-heading">
                <span className="channel-eyebrow">IDENTITY SIGNAL</span>
                <h2>Social Provider Identity</h2>
              </div>
              {renderStatusBadge(socialCheck?.status)}
            </div>
            <p className="card-desc">
              Connected identity signals from supported identity providers.
            </p>
            <p className="card-note">
              <em>Social login contributes to account signals, but is separate from official identity verification.</em>
            </p>
          </article>

          {/* 3. Government ID */}
          {renderChannelCard('government_id', govIdCheck, true)}

          {/* 4. Selfie Verification */}
          {renderChannelCard('selfie', selfieCheck, true)}

          {/* 5. Video Verification */}
          {renderChannelCard('video', videoCheck, true)}
        </section>

        {/* Modal: Pre-start safety notice & Consent */}
        {activeModalType && (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="modal-title">
            <div className="modal-card">
              <span className="channel-eyebrow">CONFIRM IDENTITY VERIFICATION</span>
              <h2 id="modal-title">{VERIFICATION_TYPE_DETAILS[activeModalType]?.title}</h2>
              <div className="modal-body">
                <p><strong>Instructions:</strong> {VERIFICATION_TYPE_DETAILS[activeModalType]?.instructions}</p>
                <div className="privacy-callout">
                  <h3>Privacy & Security Notice</h3>
                  <ul>
                    <li><strong>Required Data:</strong> Official government photo identification or biometric selfie/video.</li>
                    <li><strong>Purpose:</strong> Solely to verify your identity, prevent impersonation, and safeguard the travel community.</li>
                    <li><strong>Strict Storage Isolation:</strong> Verification media is stored in an encrypted, private vault (separate from public profile photos).</li>
                    <li><strong>Provider Processing:</strong> A dedicated, specialized verification provider processes session documents. Documents are never fed into general-purpose AI.</li>
                    <li><strong>Retention & Deletion:</strong> Data is automatically pruned according to our retention schedule or upon verified account deletion.</li>
                  </ul>
                </div>

                {sessionUrl ? (
                  <div className="provider-ready-box">
                    <p className="form-success">Verification session initialized!</p>
                    <a
                      href={sessionUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="button button-primary"
                    >
                      Open Verification Portal <span aria-hidden="true">↗</span>
                    </a>
                  </div>
                ) : (
                  startMutation.isError && (
                    <p className="form-error" role="alert">
                      {startMutation.error.message}
                    </p>
                  )
                )}
              </div>

              <div className="modal-actions">
                <Button
                  variant="ghost"
                  onClick={() => {
                    setActiveModalType(null)
                    setSessionUrl(null)
                    setErrorMessage(null)
                  }}
                >
                  Close
                </Button>
                {!sessionUrl && (
                  <Button
                    variant="primary"
                    disabled={startMutation.isPending}
                    onClick={() => handleStart(activeModalType)}
                  >
                    {startMutation.isPending ? 'Starting session…' : 'I Understand & Continue'}
                  </Button>
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="member-footer">
        <span>TRAVELMATE · SECURE IDENTITY VERIFICATION</span>
        <span>PRIVATE VAULT · LEAST PRIVILEGE AUDITING</span>
      </footer>
    </div>
  )
}
