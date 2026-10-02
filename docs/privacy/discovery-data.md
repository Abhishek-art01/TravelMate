# TravelMate Privacy — Discovery Data Protections

## 1. Zero Location Leakage

TravelMate enforces strict privacy guarantees on user geographic coordinates during discovery:
1. **Never Raw GPS**: Precise GPS coordinates are never returned in discovery candidates (`approx_latitude` and `approx_longitude` are snapped according to the Phase 6 ~5 km grid fuzzing algorithm).
2. **Hidden Location Precision**: If a user sets `location_precision = 'hidden'`, coordinates, distance metrics, and current city are stripped and returned as `null`.
3. **No Continuous Tracking**: Coordinates are updated only through explicit user actions; continuous background location logging is prohibited.

---

## 2. Private Trip Protections

- Trips marked as `visibility = 'private'` are never loaded or displayed in `DiscoveryCandidateRead.trips`.
- Private trips do not participate in public discovery scoring or country/destination search results.
- Only trips with `status IN ('planned', 'active')` and `visibility IN ('discoverable', 'public')` are visible to matching candidates.

---

## 3. Profile Discovery Controls

Users maintain autonomous control over discovery visibility:
- `discovery_visibility`: When set to `false`, the profile is instantly excluded from all discovery feeds across the platform.
- `profile_visibility`: If set to `hidden` or `private`, the user is omitted from candidate generation.
- Media assets must have `moderation_status == 'approved'` and `visibility IN ('public', 'profile_only')` before appearing on a discovery card.
