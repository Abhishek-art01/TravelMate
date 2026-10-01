# Profile data and privacy

TravelMate stores profile, preference, and privacy state server-side. The browser is not the source of truth.

## Data minimization

- date of birth is used for the server-side 18+ check and is never returned in own or public profile responses
- age is calculated from the stored date of birth when needed
- email/provider identity remains in account responses, not public profile responses
- exact location is not collected during profile creation and no raw coordinates are exposed
- profile media is stored as metadata in PostgreSQL and bytes in object storage, not in the database

## Visibility enforcement

The backend controls `public`, `discoverable`, `limited`, and `hidden` profile states. Public profile lookup returns 404 for hidden, limited, incomplete, or non-discoverable profiles. Media is separately filtered by ready state, moderation state, deletion state, and explicit public visibility.

## Browser storage

Onboarding progress stores only a step marker in session storage. Date of birth, profile fields, preferences, privacy settings, media metadata, and authentication secrets are not stored in localStorage. Privacy and preference updates use authenticated API requests.

Retention, deletion workflows, consent language, and legal/compliance decisions require product and professional privacy review. Verification data is intentionally deferred to Phase 5B.
