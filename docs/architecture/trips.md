# Trips Domain Architecture

TravelMate implements a modular, privacy-aware trip planning and discovery domain designed as the structural foundation for future companion matching, recommendation engines, and group travel.

```text
User Web / Admin Web
        │
        ▼
TravelMate API (/api/v1/me/trips, /api/v1/trips, /api/v1/admin/trips)
        │
        ▼
TripService
        ├── TripState Machine (Status transitions & guards)
        ├── TravelDateService (Boundary-inclusive overlap calculations)
        ├── LocationService (Destination foreign key & coordinate resolution)
        └── TripRepository (PostgreSQL / PostGIS persistence)
```

---

## 1. Domain Entities & Relationships

The trip model associates travelers with authoritative destinations and future matching preferences:

- **Trip**:
  - `id`: Stable UUID primary key.
  - `user_id`: Foreign key reference to authenticated user.
  - `destination_id`: Authoritative destination reference (`destinations.id`).
  - `title`: Trip heading (e.g. "Cherry Blossom Photography in Kyoto").
  - `description`: Optional itinerary details or traveler notes.
  - `start_date` & `end_date`: Inclusive calendar dates (ISO 8601 `YYYY-MM-DD`).
  - `status`: Lifecycle state (`draft`, `planned`, `active`, `completed`, `cancelled`, `archived`).
  - `visibility`: Discovery boundary (`private`, `matches_only`, `discoverable`, `public`).
  - `companion_preference`: Social intent (`travelling_alone`, `open_to_companion`, `travelling_with_group`).
  - `party_size`: Size of traveling group (1 to 50).
- **TripIntent**:
  - Normalized join entity mapping trips to standardized travel tags (`sightseeing`, `backpacking`, `foodie`, `culture`, `relaxation`, `adventure`, `nature`, `budget`, `luxury`).

---

## 2. Trip Lifecycle State Machine

The trip lifecycle enforces deterministic status transitions via `can_transition_trip(current_status, new_status)`:

```text
                    ┌──────────────┐
                    │    DRAFT     │
                    └──────┬───────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
      ┌─────────────┐             ┌─────────────┐
      │   PLANNED   ├────────────►│  CANCELLED  │
      └──────┬──────┘             └──────┬──────┘
             │                           │
             ▼                           ▼
      ┌─────────────┐             ┌─────────────┐
      │   ACTIVE    │             │  ARCHIVED   │
      └──────┬──────┘             └─────────────┘
             │                           ▲
             ▼                           │
      ┌─────────────┐                    │
      │  COMPLETED  ├────────────────────┘
      └─────────────┘
```

### Transition Matrix
- **DRAFT** → `PLANNED`, `CANCELLED`
- **PLANNED** → `ACTIVE`, `CANCELLED`, `DRAFT`
- **ACTIVE** → `COMPLETED`, `CANCELLED`
- **COMPLETED** → `ARCHIVED`
- **CANCELLED** → `ARCHIVED`, `PLANNED` (reactivation)
- **ARCHIVED** → `PLANNED` (un-archiving)

Direct transitions from `COMPLETED` to `ACTIVE` or `CANCELLED` to `ACTIVE` without moving back through `PLANNED` are disallowed.

---

## 3. Date Validation & Overlap Calculation

### Date Constraints
- `start_date <= end_date` (enforced both at Pydantic schema validation and via database check constraint `ck_trip_dates`).
- `end_date - start_date <= 365 days` (preventing runaway booking spans).

### Overlap Detection
Two date ranges $[S_1, E_1]$ and $[S_2, E_2]$ overlap if and only if:
$$\text{overlap} = (S_1 \le E_2) \land (S_2 \le E_1)$$

This formulation is boundary-inclusive: single-day meetings where $E_1 = S_2$ are recognized as overlapping. In SQL discovery queries, date overlap is computed directly:
```sql
WHERE trips.start_date <= :filter_end_date
  AND trips.end_date >= :filter_start_date
```

---

## 4. Visibility Boundaries

1. **private**:
   - Visible exclusively to the trip creator and privileged operators with `travel.read`.
   - Never indexed or returned in discovery feeds.
2. **matches_only**:
   - Reserved for companion matching algorithm where mutual interests or profile verification criteria must be met before visibility is granted.
3. **discoverable**:
   - Queryable via public discovery endpoints (`GET /api/v1/trips`) with destination, date overlap, and intent filters.
   - Creator profile data is sanitized (display name, verification badge, avatar; no private contact information).
4. **public**:
   - Publicly accessible travel plan.

---

## 5. Security & Anti-IDOR Protections

1. **Anti-Enumeration via 404**:
   - In `/api/v1/me/trips/{trip_id}`, if the trip exists but belongs to a different user, the service returns `404 Not Found` rather than `403 Forbidden`. This eliminates ID enumeration attacks where attackers probe UUID existence.
2. **Privilege Scoping**:
   - Regular users can only modify their own trips.
   - Admin listing (`GET /api/v1/admin/trips`) requires RBAC permission `travel.read`.
   - Super admins have full travel audit visibility.
