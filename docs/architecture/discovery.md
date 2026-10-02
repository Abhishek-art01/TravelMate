# TravelMate Architecture — Discovery & Matching Engine Foundation

## 1. Overview & Core Unit of Matching

TravelMate's discovery engine connects travelers based on shared itineraries, timing, and travel intentions without relying on opaque, non-deterministic AI models.

The foundational matching unit is defined as:
$$\text{Candidate} = \text{Person} \times \text{Destination} \times \text{Dates} \times \text{Travel Intent} \times \text{Compatibility}$$

The engine computes candidates dynamically from authoritative database records, ensuring real-time consistency with user privacy preferences, blocked relationships, and trip statuses.

---

## 2. Hard Eligibility Filters vs. Soft Matching Signals

### Hard Eligibility Filters (Binary Disqualification)
A candidate is immediately disqualified from discovery if any of the following apply:
1. **Self-match**: Users cannot browse or interact with their own profile (`user_id == current_user_id`).
2. **Account Status**: User is not `active` or `deleted_at` is set.
3. **Profile Status & Visibility**: Profile is not public/discoverable or `discovery_visibility == false`.
4. **Age Verification**: User is younger than 18 or has no validated date of birth.
5. **Bidirectional Block**: Either user has blocked the other (`UserBlock` in either direction).
6. **Interaction History**: Current user has already swiped/interacted (`DiscoveryInteraction`).
7. **Age Preference Mismatch**: Candidate's age violates viewer's `minimum_age`/`maximum_age`, or viewer's age violates candidate's `minimum_age`/`maximum_age`.
8. **Private Trip Isolation**: Private trips (`visibility == 'private'`) are strictly excluded from trip-based matching.

### Soft Matching Signals & Scoring Weights
Compatible candidates receive an explainable match score between 0 and 100:

| Dimension | Points | Condition |
| :--- | :--- | :--- |
| **Destination Match** | +30 | Viewer and candidate have planned trips to the exact same destination ID. |
| **Country Match** | +15 | Planned trips are in the same country (fallback if destination IDs differ). |
| **Date Overlap (Strong)** | +20 | Boundary-inclusive overlap $\ge 3$ days. |
| **Date Overlap (Partial)**| +15 | Boundary-inclusive overlap of 1–2 days. |
| **Travel Intent Match** | +15 | Common travel intent in planned trips or profile preferences. |
| **Shared Interests** | Up to +15 | +3 points per shared interest code up to a maximum of 15. |
| **Shared Languages** | Up to +10 | +5 points per shared spoken language code up to 10. |
| **Companion Preference**| +5 | Candidate has `open_to_companion` or shared dating intentions. |
| **Profile Completeness** | Up to +5 | Proportional boost based on profile completion percentage ($5\%$). |

---

## 3. Explainable Match Explanations

To maintain transparency and trust without exposing proprietary internal ranking weights or sensitive moderation flags, the system generates human-readable explanations:
- *"Traveling to Paris, France"*
- *"Travel dates overlap by 5 days"*
- *"Similar travel intent: Travel Companion"*
- *"Shared interests: Art & Design, Hiking"*
- *"Shared language: EN, FR"*
- *"Nearby (~15 km)"* (only where approximate coordinates are shared)

---

## 4. Cursor-Based Pagination

To prevent offset drift, handle ties deterministically, and avoid arbitrary full-table scans, discovery endpoints employ cursor-based pagination:
1. **Sort Order**: Deterministic compound ordering by `match_score DESC`, then `user_id ASC`.
2. **Cursor Encoding**: Safe base64 token representing `{last_score}:{last_user_id}`.
3. **Cursor Decoding**: Validates format; returns HTTP 400 `INVALID_CURSOR` on malformed tokens.
4. **Bounded Limits**: Page sizes are strictly clamped between 1 and 50 items.
