# RBAC and permission model

TravelMate centralizes authorization so that access is granted by verified identity plus explicit permissions, not by trusting client-provided role flags.

## Roles

The backend supports the following initial roles:

- `user`
- `moderator`
- `support`
- `verification_admin`
- `finance_admin`
- `security_admin`
- `travel_admin`
- `analytics_admin`
- `operations_admin`
- `super_admin`

## Permission checks

Permissions are centralized in the authorization layer and are enforced through `require_permission(...)` dependencies.

Examples:

- `profile.read`
- `profile.write`
- `verification.review`
- `verification.approve`
- `security.manage`
- `system.manage`

Admin routes are intentionally isolated under `/api/v1/admin/...` and require explicit permission checks. Normal user APIs do not expose admin functionality.

## Least privilege

The backend uses explicit permission boundaries for privileged operations and does not grant permission simply because a user is an administrator. Each protected endpoint must declare the required permission.

## Account status and session handling

The backend keeps account state and session state separate from the JWT itself. Suspended, restricted, deactivated, and deleted accounts are treated as security states rather than merely token states.
