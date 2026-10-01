# Verification Security & Access Controls

TravelMate enforces strict security controls for all identity documents and biometric verification artifacts. Government IDs, selfies, and verification videos are classified as **Tier 1 Restricted Data**.

---

## 1. Security Domain Isolation

Standard social features and identity verification use completely isolated pipelines:

| Property | Profile Media Pipeline | Verification Media Pipeline |
| :--- | :--- | :--- |
| **Object Key Prefix** | `profile/{user_id}/...` | `verification/{user_id}/{verification_id}/...` |
| **Bucket Policy** | Private storage with CDN caching for public images | Private bucket; CDN completely disabled |
| **Access URL** | Short-lived signed URL or public CDN URL | Short-lived signed URL only (120s TTL) |
| **RBAC Requirement** | Standard user session / public profile visibility | Explicit `verification.media.read` role permission |
| **Audit Logging** | Operational upload events | Mandatory audit record per media access |

The storage adapter validates object keys server-side and raises an exception if any operation targets keys outside the `verification/` namespace.

---

## 2. Least Privilege Role-Based Access Control (RBAC)

Verification permissions are granular and decoupled:

| Permission | Scope & Purpose |
| :--- | :--- |
| `verification.read` | View verification cases, status history, and queue listings. Cannot view document media. |
| `verification.review` | Assign reviewer, update review notes, request user action. |
| `verification.media.read` | Request short-lived presigned URLs to inspect identity documents and selfies. |
| `verification.approve` | Formally grant `VERIFIED` status to an identity case. |
| `verification.reject` | Mark an identity case as `REJECTED` with an audit reason. |

### Separation of Duties Matrix

Administrative roles are strictly scoped:

| Role | `verification.read` | `verification.review` | `verification.media.read` | `verification.approve` | `verification.reject` |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Super Admin** |  Yes |  Yes |  Yes |  Yes |  Yes |
| **Verification Admin** |  Yes |  Yes |  Yes |  Yes |  Yes |
| **Security Admin** |  No |  No |  No |  No |  No |
| **Moderator** |  No |  No |  No |  No |  No |
| **Support Agent** |  No |  No |  No |  No |  No |

> **Strict Isolation Rule**: Support agents handling user inquiries and moderators reviewing public content have **zero access** to identity documents, verification queues, or presigned media URLs. Only designated verification personnel can access identity verification tools.

---

## 3. Short-Lived Signed URL Policy

1. **Server-Side Generation**: Presigned URLs are generated solely by the backend using signed AWS SigV4 credentials.
2. **Ephemeral Lifespan**: Presigned GET URLs for verification media expire after **120 seconds** (`VERIFICATION_PRESIGNED_TTL_SECONDS = 120`).
3. **No Caching**: HTTP headers forbid client or browser disk caching of verification documents (`Cache-Control: no-store, private`).
4. **Credential Isolation**: Cloudflare R2 credentials are never transmitted to client applications, browsers, or non-admin services.

---

## 4. Webhook Security

External identity provider webhooks are protected against tampering, spoofing, and replay attacks:

1. **HMAC-SHA256 Signatures**: Every incoming webhook must provide a signature in its request header computed with the shared `VERIFICATION_WEBHOOK_SECRET`.
2. **Constant-Time Verification**: Signatures are compared using constant-time algorithms (`hmac.compare_digest`) to prevent timing side-channel attacks.
3. **Replay Window Enforcement**: Requests include a timestamp header. Any webhook with a timestamp deviating by more than **300 seconds** from server time is rejected.
4. **Idempotency**: Webhook payloads are logged and processed idempotently using provider transaction references.

---

## 5. Audit Event Logging Catalog

Every sensitive operation generates two immutable audit records:
1. `AuditLog` entry in the primary system audit log for platform-wide observability.
2. `VerificationEvent` entry in the identity case event stream for administrative review.

### Audited Actions

- `VERIFICATION_STARTED`: User initiates a verification session.
- `VERIFICATION_SUBMITTED`: User submits documents or biometric captures.
- `VERIFICATION_REVIEW_STARTED`: Reviewer claims or opens a case.
- `VERIFICATION_MEDIA_ACCESSED`: Reviewer requests a signed media URL (records actor, media ID, client IP).
- `VERIFICATION_APPROVED`: Case approved and user status upgraded.
- `VERIFICATION_REJECTED`: Case rejected with justification code.
- `VERIFICATION_ACTION_REQUESTED`: Reviewer requests updated documents from user.
- `VERIFICATION_MEDIA_DELETED`: Media objects purged via retention policy or account deletion.

### Audit Privacy Guarantee
Audit logs record metadata only: actor ID, target user ID, case ID, action type, timestamp, IP address, and decision reason. **Audit logs never store document images, raw selfie data, or full government ID numbers.**
