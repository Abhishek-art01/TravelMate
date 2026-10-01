import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import ProfilePage from './ProfilePage'

const mocks = vi.hoisted(() => ({
  getProfile: vi.fn(),
  update: vi.fn(),
  getMedia: vi.fn(),
  authorizeMediaUpload: vi.fn(),
  completeMediaUpload: vi.fn(),
  deleteMedia: vi.fn(),
  reorderMedia: vi.fn(),
}))

vi.mock('../services/api/profile', () => ({
  profileApi: {
    getProfile: mocks.getProfile,
    update: mocks.update,
    getMedia: mocks.getMedia,
    authorizeMediaUpload: mocks.authorizeMediaUpload,
    completeMediaUpload: mocks.completeMediaUpload,
    deleteMedia: mocks.deleteMedia,
    reorderMedia: mocks.reorderMedia,
  },
}))

const profile = {
  profile_id: 'profile-1',
  user_id: 'user-1',
  display_name: 'Mira',
  age: 31,
  bio: 'City walks',
  gender_identity: null,
  profile_visibility: 'hidden' as const,
  discovery_visibility: false,
  profile_status: 'draft',
  completion_percentage: 40,
  created_at: '2026-10-01T00:00:00Z',
  updated_at: '2026-10-01T00:00:00Z',
}

const image = {
  media_id: 'media-1',
  media_type: 'profile_media' as const,
  processing_status: 'ready' as const,
  moderation_status: 'pending_review' as const,
  visibility: 'profile_only' as const,
  mime_type: 'image/png',
  size_bytes: 96,
  width: 24,
  height: 16,
  sort_order: 0,
  created_at: '2026-10-01T00:00:00Z',
  download_url: 'https://cdn.test/signed-read',
}
const secondImage = { ...image, media_id: 'media-2', sort_order: 1 }

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<MemoryRouter><QueryClientProvider client={queryClient}><ProfilePage /></QueryClientProvider></MemoryRouter>)
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.getProfile.mockResolvedValue(profile)
  mocks.update.mockResolvedValue(profile)
  mocks.getMedia.mockResolvedValue({ items: [image, secondImage], next_cursor: null })
  mocks.authorizeMediaUpload.mockResolvedValue({ media_id: 'media-new', upload_url: 'https://upload.test/signed', expires_at: '', required_headers: { 'Content-Type': 'image/png' } })
  mocks.completeMediaUpload.mockResolvedValue({ ...image, media_id: 'media-new' })
  mocks.deleteMedia.mockResolvedValue(undefined)
  mocks.reorderMedia.mockResolvedValue({ ...image, sort_order: 0 })
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('persisted profile and media UI', () => {
  it('loads the backend profile and saves edits through the API', async () => {
    const user = userEvent.setup()
    renderPage()
    const name = await screen.findByLabelText('Display name')
    await user.clear(name)
    await user.type(name, 'Mira S')
    await user.click(screen.getByRole('button', { name: /save profile/i }))
    await waitFor(() => expect(mocks.update.mock.calls[0]?.[0]).toEqual({
      display_name: 'Mira S',
      bio: 'City walks',
      gender_identity: null,
      profile_visibility: 'hidden',
    }))
    expect(await screen.findByRole('status')).toHaveTextContent(/profile saved/i)
  })

  it('authorizes a short-lived upload, sends bytes to its signed URL, then confirms with the API', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status: 200 })))
    const user = userEvent.setup()
    renderPage()
    const input = await screen.findByLabelText('Upload profile photo')
    const file = new File(['controlled test image bytes'], 'portrait.png', { type: 'image/png' })
    await user.upload(input, file)
    await waitFor(() => expect(mocks.authorizeMediaUpload).toHaveBeenCalledWith({ mime_type: 'image/png', size_bytes: file.size, visibility: 'profile_only' }))
    await waitFor(() => expect(vi.mocked(fetch)).toHaveBeenCalledWith('https://upload.test/signed', expect.objectContaining({ method: 'PUT', body: file })))
    await waitFor(() => expect(mocks.completeMediaUpload).toHaveBeenCalledWith('media-new'))
  })

  it('surfaces a backend upload authorization failure safely', async () => {
    mocks.authorizeMediaUpload.mockRejectedValue(new Error('You do not have permission to upload media.'))
    const user = userEvent.setup()
    renderPage()
    const input = await screen.findByLabelText('Upload profile photo')
    await user.upload(input, new File(['test'], 'portrait.png', { type: 'image/png' }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/permission to upload/i)
    expect(mocks.completeMediaUpload).not.toHaveBeenCalled()
  })

  it('requires confirmation before deletion and supports reorder', async () => {
    const user = userEvent.setup()
    renderPage()
    await user.click((await screen.findAllByRole('button', { name: /^delete$/i }))[0])
    expect(await screen.findByRole('dialog')).toHaveTextContent(/delete this photo/i)
    await user.click(screen.getByRole('button', { name: /cancel/i }))
    expect(mocks.deleteMedia).not.toHaveBeenCalled()

    await user.click(screen.getByRole('button', { name: /set primary/i }))
    await waitFor(() => expect(mocks.reorderMedia).toHaveBeenCalledWith('media-2', 0))

    await user.click((await screen.findAllByRole('button', { name: /^delete$/i }))[0])
    await user.click(await screen.findByRole('button', { name: /confirm deletion/i }))
    await waitFor(() => expect(mocks.deleteMedia).toHaveBeenCalledWith('media-1'))
  })
})
