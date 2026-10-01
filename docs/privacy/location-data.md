# Location Data Minimization & Privacy Policy

This policy defines TravelMate's technical controls and operational safeguards governing geographic and location-related personal data in compliance with the EU General Data Protection Regulation (GDPR) and the Digital Personal Data Protection (DPDP) Act 2023.

---

## 1. Purpose-Driven Collection Principle

TravelMate adheres strictly to purpose-bound data collection:

- **No Gratuitous Location Prompts**: The client application never prompts the user for browser/device geolocation merely because the home page or dashboard is opened.
- **Explicit Trigger**: Geolocation is only requested when the user initiates an explicit location-aware action (e.g. "Find destinations near me" or "Update my travel base").
- **Purpose Transparency**: When requesting location access, the interface explicitly discloses:
  1. Why location is required (e.g. nearby destination calculation).
  2. What precision is retained (approximate ~5km centroid vs exact).
  3. Who can view the data (private by default).
  4. How to revoke access or delete the stored record.

---

## 2. Data Minimization & Anti-Tracking Architecture

1. **Zero Continuous Tracking**:
   - TravelMate does not run background location listeners or periodic GPS pings.
   - The platform never collects route traces, breadcrumbs, speed, or velocity vectors.
2. **Single-Record Constraint**:
   - The database maintains at most **one** current record per user in `user_locations`.
   - Updating location overwrites the existing coordinates in-place; historical coordinates are not archived into an append-only audit trail.
3. **Decoupling from Verification**:
   - Verification documents (passports, driver's licenses) are stored in an isolated, private Cloudflare R2 bucket (`VERIFICATION_MEDIA`). They are never correlated with or exposed through geospatial queries.

---

## 3. Retention & Deletion Rights

### User Self-Service Deletion
Travelers possess absolute control over their stored location data:
- Calling `DELETE /api/v1/me/location` immediately and permanently purges the user's `user_locations` record.
- The UI provides an instantaneous "Clear Saved Location" action in account and privacy settings.

### Account Termination & Cascading Purge
When a user deletes their TravelMate account:
- Database foreign key constraints enforce `ON DELETE CASCADE` across `user_locations`, deleting all stored geospatial records.
- Associated trips are either soft-deleted/archived or cascaded in accordance with the user's data retention request.

---

## 4. International Regulatory Alignment

| Regulatory Mandate | Statutory Reference | TravelMate Implementation |
| :--- | :--- | :--- |
| **Lawfulness of Processing** | GDPR Art. 6(1)(a) | Explicit consent obtained prior to capturing browser coordinates. |
| **Data Minimisation** | GDPR Art. 5(1)(c) | GPS coordinates snapped to ~5km centroids; raw GPS purged upon user request; historical path tracking banned. |
| **Storage Limitation** | GDPR Art. 5(1)(e) | Single active location record per user; no historical trail persistence. |
| **Purpose Limitation** | DPDP Act 2023 Sec. 6 | Clear notice provided before access; location used strictly for destination discovery and trip planning. |
| **Right to Erasure** | GDPR Art. 17 / DPDP Sec. 12 | One-click programmatic deletion via `DELETE /api/v1/me/location`. |
