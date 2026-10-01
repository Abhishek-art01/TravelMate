import { useRef, useState, type ChangeEvent, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Button, Input, TextArea } from '../components/ui'
import { profileApi, type ProfileMedia } from '../services/api/profile'

const imageTypes = new Set(['image/jpeg', 'image/png', 'image/webp'])
const maxPhotoBytes = 10 * 1024 * 1024

export default function ProfilePage() {
  const queryClient = useQueryClient()
  const fileInput = useRef<HTMLInputElement>(null)
  const profile = useQuery({ queryKey: ['profile', 'me'], queryFn: profileApi.getProfile, retry: false })
  const media = useQuery({ queryKey: ['profile', 'media'], queryFn: () => profileApi.getMedia(), retry: false })
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [replaceTarget, setReplaceTarget] = useState<string | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<ProfileMedia | null>(null)
  const [saved, setSaved] = useState(false)

  const updateProfile = useMutation({
    mutationFn: profileApi.update,
    onSuccess: async () => {
      setSaved(true)
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['profile', 'me'] }),
        queryClient.invalidateQueries({ queryKey: ['me'] }),
      ])
    },
  })

  async function submitProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaved(false)
    const values = new FormData(event.currentTarget)
    await updateProfile.mutateAsync({
      display_name: String(values.get('display_name') ?? '').trim(),
      bio: String(values.get('bio') ?? '').trim() || null,
      gender_identity: String(values.get('gender_identity') ?? '').trim() || null,
      profile_visibility: String(values.get('profile_visibility') ?? 'hidden') as 'public' | 'discoverable' | 'limited' | 'hidden',
    }).catch(() => undefined)
  }

  async function uploadPhoto(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    setError('')
    setMessage('')
    if (!imageTypes.has(file.type)) {
      setError('Choose a JPEG, PNG, or WebP image.')
      return
    }
    if (file.size <= 0 || file.size > maxPhotoBytes) {
      setError('This photo exceeds the 10 MB profile-image limit.')
      return
    }
    setBusy(true)
    let mediaId: string | undefined
    try {
      const authorization = await profileApi.authorizeMediaUpload({
        mime_type: file.type,
        size_bytes: file.size,
        visibility: profile.data?.profile_visibility === 'public' || profile.data?.profile_visibility === 'discoverable' ? 'public' : 'profile_only',
      })
      mediaId = authorization.media_id
      const controller = new AbortController()
      const timer = window.setTimeout(() => controller.abort(), 60_000)
      let response: Response
      try {
        response = await fetch(authorization.upload_url, {
          method: 'PUT',
          headers: authorization.required_headers,
          body: file,
          signal: controller.signal,
        })
      } finally {
        window.clearTimeout(timer)
      }
      if (!response.ok) throw new Error('The secure upload did not complete. Please try again.')
      await profileApi.completeMediaUpload(mediaId)
      if (replaceTarget) {
        setMessage('Replacement uploaded. The previous photo stays in place until the new upload completes moderation.')
        setReplaceTarget(null)
      } else {
        setMessage('Photo uploaded. It remains private to your profile while moderation is pending.')
      }
      await queryClient.invalidateQueries({ queryKey: ['profile', 'media'] })
      await queryClient.invalidateQueries({ queryKey: ['profile', 'me'] })
      await queryClient.invalidateQueries({ queryKey: ['me'] })
    } catch (cause) {
      if (mediaId) await profileApi.deleteMedia(mediaId).catch(() => undefined)
      setError((cause as Error).message || 'The photo could not be uploaded. Please retry.')
    } finally {
      setBusy(false)
      setReplaceTarget(null)
    }
  }

  async function deletePhoto() {
    if (!deleteTarget) return
    setBusy(true)
    setError('')
    try {
      await profileApi.deleteMedia(deleteTarget.media_id)
      setDeleteTarget(null)
      setMessage('Photo deleted from your profile.')
      await queryClient.invalidateQueries({ queryKey: ['profile', 'media'] })
      await queryClient.invalidateQueries({ queryKey: ['profile', 'me'] })
    } catch (cause) {
      setError((cause as Error).message || 'The photo could not be deleted. Please retry.')
    } finally {
      setBusy(false)
    }
  }

  async function setPrimary(item: ProfileMedia) {
    setBusy(true)
    setError('')
    try {
      await profileApi.reorderMedia(item.media_id, 0)
      await queryClient.invalidateQueries({ queryKey: ['profile', 'media'] })
      setMessage('Primary photo order updated.')
    } catch (cause) {
      setError((cause as Error).message || 'Photo order could not be updated.')
    } finally {
      setBusy(false)
    }
  }

  const items = [...(media.data?.items ?? [])].sort((first, second) => first.sort_order - second.sort_order)
  return (
    <div className="member-layout">
      <header className="member-header"><Link to="/home" className="brand-lockup"><span className="brand-mark">T</span><span>travelmate</span></Link><nav aria-label="Main navigation"><Link to="/home">Home</Link><Link className="nav-active" to="/profile">Profile</Link><Link to="/privacy">Privacy</Link></nav><Link className="header-link" to="/home">Back home</Link></header>
      <main className="member-page profile-page"><p className="eyebrow">YOUR PROFILE</p><h1>A little more you.</h1><p className="page-lede">Your profile is stored securely in TravelMate. Your exact date of birth is never returned by profile-read APIs.</p>
        {profile.isLoading && <div className="skeleton-line" aria-label="Loading profile" />}
        {profile.isError && <section className="empty-state"><h2>Profile details aren’t available.</h2><p role="alert">{profile.error.message}</p><Button variant="secondary" onClick={() => void profile.refetch()}>Retry</Button></section>}
        {profile.data && <>
          <section className="profile-progress" aria-label={`Profile completion ${profile.data.completion_percentage} percent`}><div><span>PROFILE COMPLETION</span><strong>{profile.data.completion_percentage}%</strong></div><div className="completion-progress"><span style={{ width: `${profile.data.completion_percentage}%` }} /></div><p>Completion is calculated by the backend from saved profile, preference, interest, and approved media data.</p></section>
          <form key={profile.data.profile_id} className="profile-edit-form" onSubmit={(event) => void submitProfile(event)}>
            <label htmlFor="profile-name">Display name</label><Input id="profile-name" name="display_name" required minLength={2} maxLength={80} defaultValue={profile.data.display_name ?? ''} />
            <label htmlFor="profile-bio">Bio</label><TextArea id="profile-bio" name="bio" maxLength={500} rows={4} defaultValue={profile.data.bio ?? ''} />
            <label htmlFor="profile-gender">Gender identity <span className="label-note">Optional</span></label><select id="profile-gender" name="gender_identity" className="field-input" defaultValue={profile.data.gender_identity ?? ''}><option value="">Prefer not to say</option><option>Woman</option><option>Man</option><option>Non-binary</option><option>Self-describe</option></select>
            <label htmlFor="profile-visibility">Profile visibility</label><select id="profile-visibility" name="profile_visibility" className="field-input" defaultValue={profile.data.profile_visibility}><option value="hidden">Hidden</option><option value="limited">Limited</option><option value="discoverable">Discoverable</option><option value="public">Public</option></select>
            <div className="form-actions"><Button disabled={updateProfile.isPending} type="submit">{updateProfile.isPending ? 'Saving…' : 'Save profile'}</Button>{saved && <span role="status">Profile saved.</span>}</div>
            {updateProfile.isError && <p className="form-error" role="alert">{updateProfile.error.message}</p>}
          </form>
          <section className="profile-media-section"><div className="section-heading"><div><p className="eyebrow">PROFILE MEDIA</p><h2>Your photos</h2></div><Button disabled={busy || items.length >= 6} onClick={() => { setReplaceTarget(null); fileInput.current?.click() }}>{busy ? 'Working…' : 'Upload photo'} <span aria-hidden="true">＋</span></Button></div>
            <p className="media-note">JPEG, PNG, or WebP · up to 10 MB · uploads are checked server-side and remain pending moderation until reviewed.</p>
            <input ref={fileInput} className="visually-hidden" type="file" aria-label="Upload profile photo" accept="image/jpeg,image/png,image/webp" onChange={(event) => void uploadPhoto(event)} />
            {message && <p className="form-success" role="status">{message}</p>}{error && <p className="form-error" role="alert">{error}</p>}
            {media.isLoading && <div className="skeleton-line" aria-label="Loading photos" />}
            {media.isError && <p className="form-error" role="alert">{media.error.message}</p>}
            {!media.isLoading && items.length === 0 && <div className="empty-state"><h2>No profile photos yet.</h2><p>Photos are stored privately and are never available by permanent public object URL.</p></div>}
            <div className="media-grid">{items.map((item, index) => <article className="media-item" key={item.media_id}><div className="media-preview">{item.download_url && item.processing_status === 'ready' ? <img src={item.download_url} alt="Your profile upload" /> : <span>Processing</span>}</div><div className="media-meta"><span>{item.moderation_status.replaceAll('_', ' ')}</span><span>{item.width && item.height ? `${item.width} × ${item.height}` : 'Validating'}</span></div><div className="media-actions"><Button variant="secondary" disabled={busy} onClick={() => void setPrimary(item)}>{index === 0 ? 'Primary' : 'Set primary'}</Button><Button variant="secondary" disabled={busy} onClick={() => { setReplaceTarget(item.media_id); fileInput.current?.click() }}>Replace</Button><Button variant="ghost" disabled={busy} onClick={() => setDeleteTarget(item)}>Delete</Button></div></article>)}</div>
          </section>
        </>}
      </main>
      {deleteTarget && <div className="dialog-scrim"><section className="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="delete-title"><p className="eyebrow">REMOVE PROFILE PHOTO</p><h2 id="delete-title">Delete this photo?</h2><p>The media record will be marked deleted and its object removed from storage. This cannot be undone.</p><div className="form-actions"><Button variant="secondary" disabled={busy} onClick={() => setDeleteTarget(null)}>Cancel</Button><Button disabled={busy} onClick={() => void deletePhoto()}>{busy ? 'Deleting…' : 'Confirm deletion'}</Button></div></section></div>}
    </div>
  )
}
