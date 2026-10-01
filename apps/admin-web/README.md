# TravelMate Admin Web

Separate administrative console for TravelMate operations. It uses the existing Supabase Auth project for identity and verifies console access with `GET /api/v1/admin/access` before rendering protected routes. The backend remains the security boundary and continues enforcing permissions for every API operation.

## Browser-safe environment

Configure public values in the workspace `.env`:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-public-anon-key
```

Do not expose service-role keys, database credentials, signing keys, payment secrets, or other server credentials in this app.

## Development

Run `npm run dev --workspace apps/admin-web` from the repository root. The application listens on port 4173 by default.

## Connected API surface and limitations

- `GET /api/v1/admin/access` verifies admin access and returns effective permissions.
- `GET /api/v1/admin/system` is requested only when `system.manage` is granted.

All other modules are permission-guarded shells and explicitly report their missing API contract. Users, verification queues, moderation/reports, sessions/revocation, audit logs, support/grievances, payments, trips, analytics, and role management are not yet backed by admin APIs. No sample records, operational metrics, or simulated actions are displayed. Secure verification media access is not available yet.
