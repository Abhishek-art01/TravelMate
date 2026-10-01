# TravelMate media architecture

Profile media follows a provider-independent service boundary:

`User Web -> TravelMate API -> MediaStorage -> Cloudflare R2`

Cloudinary is reserved for optional server-side image/video transformations. It is not required for local startup and is never exposed to the browser.

## Profile upload flow

1. An authenticated user requests `POST /api/v1/media/uploads` with a supported MIME type, size, and visibility.
2. The API validates profile-media limits, profile visibility requirements, and ownership.
3. The API creates a `media_assets` metadata row with a server-generated object key such as `profile/{media_id}/original.png`.
4. R2 returns a short-lived presigned PUT URL. The browser sends bytes directly to R2.
5. The client calls `POST /api/v1/media/uploads/{id}/complete`.
6. The API reads the stored object, checks size/content type, parses image bytes with Pillow, and records dimensions.
7. Valid media becomes `ready` but remains `pending_review`; moderation is intentionally not auto-approved.

Profile media is limited to configured JPEG, PNG, and WebP uploads. The API never accepts a client-supplied object key or public storage URL.

## Media categories

`profile_media`, `chat_media`, and `verification_media` are distinct metadata categories. This phase implements only profile media. Verification media must use separate storage namespaces, retention, audit, and permissions in Phase 5B.

## Delivery and deletion

Private/profile-only media uses short-lived signed GET URLs. Public media is eligible for signed delivery only after the profile is explicitly public/discoverable and the media is ready, approved, and marked public. Deletion marks metadata deleted and removes the storage object when the provider is available.
