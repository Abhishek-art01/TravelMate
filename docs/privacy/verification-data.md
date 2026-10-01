# Verification Data Privacy & Retention Policy

Identity verification artifacts contain sensitive personal data. TravelMate minimizes personal data collection, restricts internal and external visibility, enforces automated retention expiration, and guarantees complete deletion upon user request.

---

## 1. Data Minimization Principles

1. **Strict Purpose Limitation**: Data collected during identity verification is used solely to confirm the authenticity of the user's identity and detect duplicate or fraudulent accounts.
2. **What Is Collected**:
   - Verification document capture (e.g., passport, driving licence, voter ID) or biometric selfie/video.
   - Provider reference and session identifiers.
   - Timestamps of submission, review, and status changes.
   - Reviewer decision notes or failure codes.
3. **What Is Never Collected or Stored**:
   - Unmasked government national identity numbers (e.g. Aadhaar numbers) are never stored in plaintext in the TravelMate database.
   - Raw biometric template vectors are not extracted or retained by TravelMate internally.
   - Full credit, tax, or banking histories are not requested during identity verification.
4. **No Client Trust**: Clients cannot claim verified status. The verification outcome is determined exclusively by the server state machine and authorized provider/reviewer workflows.

---

## 2. Retention Periods & Auto-Pruning

Sensitive document media has strict, automated retention limits configured server-side:

| Artifact Type | Retention Period | Post-Expiry Action | Retained Metadata |
| :--- | :--- | :--- | :--- |
| **Government ID Media** | 30 days post-review | Permanently deleted from object storage | Verification status flag, review timestamp, decision code |
| **Selfie Media** | 30 days post-review | Permanently deleted from object storage | Verification status flag, review timestamp |
| **Video Verification Media** | 7 days post-review | Permanently deleted from object storage | Verification status flag, review timestamp |
| **Audit & Event Logs** | Configurable (e.g. 1 year) | Retained for compliance and auditability | Actor, timestamp, action type (no document bytes) |

### Automated Pruning Workflow

The backend provides `prune_expired_verification_media()`:
1. Identifies verification records whose `expires_at` timestamp has elapsed.
2. Deletes binary objects from the private Cloudflare R2 vault.
3. Sets `VerificationMedia.deleted_at = now()`, recording `VERIFICATION_MEDIA_DELETED` in the audit stream.
4. Retains only the high-level boolean verified badge for the user account.

---

## 3. Account Deletion Workflow (Right to Erasure)

When a user initiates account deletion (`delete_user_verification_data()`):

1. **Immediate Storage Purge**: All associated verification objects in the private storage vault (`verification/{user_id}/...`) are permanently deleted.
2. **Database Scrubbing**:
   - `VerificationMedia` rows are deleted.
   - `VerificationAttempt` records are scrubbed.
   - `VerificationRecord` rows are removed or anonymized.
3. **Audit Trail**: A final `ACCOUNT_VERIFICATION_DELETED` audit event is recorded with the target user ID scrubbed or pseudonymized per compliance guidelines.

---

## 4. Privacy Controls & AI Restrictions

- **No User Re-exposure**: To prevent credential harvesting and session hijacking, users cannot view or download previously uploaded identity documents from the web or mobile apps.
- **Zero Public Exposure**: Verification media is never displayed on user profiles, discovery cards, or search listings.
- **Strict AI Training Prohibition**: Identity documents, selfies, and verification videos are strictly quarantined and **never** used for training internal machine learning models, third-party generative AI, or marketing analytics.
- **Third-Party Sharing**: Verification data is shared only with the explicitly configured identity verification provider under strict Data Processing Agreements (DPAs).
