# Identity Verification Architecture

TravelMate implements a provider-independent, multi-channel identity verification system that strictly isolates sensitive identity artifacts from public profile data.

```text
User Web / Mobile
       │
       ▼
TravelMate API (/api/v1/me/verification/...)
       │
       ▼
VerificationService
       ├── VerificationState Machine
       ├── VerificationStorage (Cloudflare R2 Private Vault)
       └── VerificationProvider (Protocol Boundary)
                 ├── NotConfiguredVerificationProvider
                 ├── MockVerificationProvider (Local / Test)
                 └── Future Vendors (e.g. DigiLocker, Persona, Veriff, Onfido)
```

---

## 1. Provider-Independent Boundary

TravelMate core business logic does not depend directly on vendor-specific SDKs or schemas. All verification vendors implement the `VerificationProvider` protocol:

```python
class VerificationProvider(Protocol):
    @property
    def provider_name(self) -> str: ...

    async def create_session(
        self,
        user_id: str,
        verification_type: VerificationType,
        attempt_number: int,
    ) -> ProviderSession: ...

    async def get_session_status(
        self,
        provider_reference: str,
    ) -> ProviderStatusResult: ...

    async def cancel_session(
        self,
        provider_reference: str,
    ) -> bool: ...

    async def verify_webhook_signature(
        self,
        payload_bytes: bytes,
        signature_header: str,
        timestamp_header: str | None = None,
    ) -> bool: ...

    async def parse_webhook_payload(
        self,
        payload_bytes: bytes,
    ) -> WebhookEventPayload: ...
```

### Configuration States
- **`not_configured`** (default for fresh environments): The backend explicitly returns `status="not_configured"` to the client. The system **never** fabricates a false verification success in development or staging.
- **`mock`**: Configured in test and local development setups with explicit HMAC signature validation for end-to-end webhook testing.
- **Vendor Provider**: Real production provider adapters (e.g., DigiLocker, Persona, Veriff) translate vendor webhooks and session lifecycles into standardized TravelMate events.

---

## 2. Verification Channels

TravelMate tracks 5 verification channels independently:

| Channel | Identifier | Description | Source of Truth |
| :--- | :--- | :--- | :--- |
| **Email** | `EMAIL` | Account email ownership | Supabase Auth identity sync |
| **Social** | `SOCIAL` | Third-party OAuth identity | Social OAuth provider sync |
| **Selfie** | `SELFIE` | Biometric facial liveness check | Verification Provider |
| **Government ID** | `GOVERNMENT_ID` | Official passport, voter ID, driving licence | Verification Provider + Admin Review |
| **Video** | `VIDEO` | Short liveness video recording | Verification Provider + Admin Review |

### Channel Isolation Principle
Each channel maintains its own independent status, attempt count, timestamps, and provider references. A user may have:
```text
email = VERIFIED
social = VERIFIED
selfie = PENDING
government_id = VERIFIED
video = NOT_STARTED
```
Social login signals (e.g., Google or Apple OAuth) confirm external account linkage, but **never** mark government ID or selfie verification as completed.

---

## 3. Secure Verification Storage Architecture

Verification media is treated as a separate security domain from standard profile photos:

$$\text{PROFILE\_MEDIA} \neq \text{VERIFICATION\_MEDIA}$$

- **Storage Namespace**: Strictly isolated server-side prefix:
  ```text
  verification/{user_id}/{verification_id}/{media_id}.{ext}
  ```
- **Bucket Configuration**: Dedicated private Cloudflare R2 bucket. No public CDN, no public domain, and no bucket browsing.
- **Access Model**: Short-lived presigned URLs (default 120 seconds TTL) generated on-demand only for authorized administrators holding `verification.media.read`.
- **Validation**: Any storage operation with a key outside `verification/` is immediately rejected with a `ValueError`.

---

## 4. Verification State Machine

The lifecycle of each verification record follows strict, deterministic transitions:

```text
               ┌───────────────┐
               │  NOT_STARTED  │
               └───────┬───────┘
                       │ start session
                       ▼
               ┌───────────────┐
               │    PENDING    │
               └───────┬───────┘
                       │ client captures
                       ▼
               ┌───────────────┐
               │  IN_PROGRESS  │
               └───────┬───────┘
                       │ submit media
                       ▼
               ┌───────────────┐
               │   SUBMITTED   │
               └───────┬───────┘
                       │ reviewer assigned / automated processing
                       ▼
               ┌───────────────┐
               │   IN_REVIEW   │
               └───┬───┬───┬───┘
     approve       │   │   │ reject
 ┌─────────────────┘   │   └─────────────────┐
 ▼                     ▼                     ▼
┌──────────┐ ┌──────────────────┐ ┌──────────┐
│ VERIFIED │ │ REQUIRES_ACTION  │ │ REJECTED │
└──────────┘ └─────────┬────────┘ └──────────┘
                       │ user re-submits
                       └──────► (IN_PROGRESS)
```

Terminal or exceptional states:
- `EXPIRED`: Session exceeded allowed TTL (default 24 hours).
- `CANCELLED`: User or system explicitly aborted the verification session.
- `SUSPENDED`: Security investigation or repeated verification irregularities flagged the record.

---

## 5. Verification Attempt Tracking and Limits

To prevent enumeration, brute-forcing, and identity fraud:
- Attempt counters are incremented server-side upon session creation.
- A configurable limit (`VERIFICATION_MAX_ATTEMPTS = 3`) restricts consecutive failed attempts.
- When the attempt threshold is reached without passing, new sessions are blocked until administrative reset or cooling-off period expiry.
- Simultaneous active sessions for the same verification type are prevented; existing unsubmitted sessions must be cancelled or completed first.

---

## 6. Webhook Processing Flow

External identity providers communicate verification results through signed webhooks:

1. **Endpoint**: `POST /api/v1/webhooks/verification/{provider}`
2. **Signature Verification**:
   - Provider signs payload with HMAC-SHA256 using `VERIFICATION_WEBHOOK_SECRET`.
   - Backend performs constant-time comparison (`hmac.compare_digest`).
   - Replay protection window rejects requests with timestamps older than 300 seconds.
3. **Payload Parsing**:
   - Provider adapter parses vendor-specific payload into a normalized `WebhookEventPayload`.
4. **State Transition**:
   - `VerificationService` applies state transition according to the state machine.
   - Generates an immutable `VerificationEvent` and system `AuditLog`.
5. **Idempotency**: Duplicate webhook event deliveries are recognized by provider reference and event type, ensuring safe retries.
