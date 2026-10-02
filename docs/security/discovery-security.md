# TravelMate Security — Discovery & Safety Controls

## 1. Bidirectional Block Enforcement

Safety in discovery requires strict bidirectional exclusion:
1. **Feed Isolation**: If User $A$ blocks User $B$:
   - $B$ will never appear in $A$'s discovery candidates.
   - $A$ will never appear in $B$'s discovery candidates.
2. **Direct Lookup Denial**: Invoking `GET /api/v1/discovery/{id}` across a blocked relationship returns HTTP 404 (preventing user enumeration or confirmation of block status).
3. **Database Constraints**: `UserBlock` enforces `blocker_id != blocked_id` and unique composite key `(blocker_id, blocked_id)`.

---

## 2. Anti-Abuse & Rate Limiting

- **Interactions**: Duplicate swipes are processed idempotently without generating redundant database rows.
- **Request Boundaries**: Page limit is strictly clamped (`1 <= limit <= 50`). Arbitrary offsets are avoided via base64 encoded cursor tokens.
- **Anti-Enumeration**: Private profiles, deleted accounts, suspended accounts, and non-existent users all return uniform 404 responses.
- **No Self-Interactions**: Direct database checks and API validations reject attempts to swipe on, block, or report oneself with HTTP 400.

---

## 3. Moderation RBAC Permissions

Admin operations on reported users are strictly partitioned:
- `moderation.read`: Grants permission to view the report queue (`GET /api/v1/admin/reports`).
- `moderation.action`: Grants permission to resolve or dismiss reports with mandatory audit notes (`PATCH /api/v1/admin/reports/{id}`).
