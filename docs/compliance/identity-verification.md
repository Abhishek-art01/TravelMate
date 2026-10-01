# Identity Verification Compliance & Legal Readiness

This document outlines the regulatory compliance architecture for TravelMate's identity verification infrastructure, with specific focus on alignment with the **Digital Personal Data Protection Act, 2023 (DPDPA)** of India, and provides an explicit checklist of items requiring review by qualified Indian legal and privacy counsel before production deployment.

---

## 1. Digital Personal Data Protection Act (DPDPA 2023) Alignment

As a Data Fiduciary under the DPDPA, TravelMate's verification subsystem is architected around foundational statutory obligations:

### Notice and Explicit Consent (Section 5 & 6)
- **Granular Consent**: Before initiating document upload or selfie capture, users are presented with clear, plain-language notice specifying:
  - Exact items of personal data collected.
  - Purpose for processing (verifying traveller authenticity and preventing impersonation).
  - Data retention schedule and right of withdrawal.
- **Language Accessibility**: Verification consent dialogs support multi-language localizations (starting with English and Hindi).

### Purpose Limitation (Section 7)
- Verification data is strictly partitioned and used solely for identity validation.
- It is technically prohibited from being fed into advertising engines, recommender algorithms, or behavioral profiling systems.

### Reasonable Security Safeguards (Section 8)
- End-to-end TLS encryption in transit.
- AES-256 server-side encryption at rest in Cloudflare R2 private vaults.
- Decoupled RBAC preventing unauthorized internal access.
- Ephemeral presigned URLs (120-second TTL) for all media inspection.

### Rights of the Data Principal (Sections 11–14)
- **Right to Access & Summary**: Users can view the verification status of each channel.
- **Right to Correction & Erasure**: Users can re-submit documents if rejected, or trigger complete deletion of verification data upon account closure.
- **Grievance Redressal**: Direct escalation pathway to TravelMate's appointed Grievance Officer.

---

## 2. Special Considerations for Indian Identity Documents

Identity verification in India is subject to specific statutory frameworks and guidelines issued by UIDAI, MeitY, and the Ministry of Road Transport and Highways (MoRTH):

### Aadhaar Safeguards (Aadhaar Act, 2016 & Regulations)
- **No Unmasked Aadhaar Storage**: TravelMate enforces a strict policy **forbidding the storage of plaintext, unmasked 12-digit Aadhaar numbers or physical Aadhaar card images**.
- **Masked Aadhaar / DigiLocker Integration**: When accepting Indian identity proofs, the platform prioritizes:
  1. Government-approved DigiLocker API integration where available.
  2. Offline Aadhaar XML verification with cryptographic signature validation.
  3. Redacted/masked Aadhaar uploads where only the last 4 digits remain visible.

### Alternative Documents
- Indian Passport, Voter ID (EPIC), and Driving Licence are supported as non-Aadhaar alternatives with identical security partitioning and retention policies.

---

## 3. Legal Counsel Review Checklist

Before enabling live identity verification in production in India, the following items **must be reviewed and signed off by qualified Indian legal and privacy counsel**:

- [ ] **Privacy Notice & Consent Agreement**: Review and approve the legal text in the user verification consent modal (`/settings/verification`) to ensure full compliance with DPDPA Section 5 Notice requirements.
- [ ] **Aadhaar Policy & DigiLocker Agreement**: Validate compliance with UIDAI circulars on Aadhaar masking, storage restrictions, and terms of service for third-party DigiLocker or KYC aggregators.
- [ ] **Data Retention Schedule**: Formally certify the 30-day retention period for government IDs and 7-day retention period for video recordings against sector-specific legal retention requirements.
- [ ] **Cross-Border Data Transfer**: If Cloudflare R2 buckets or identity verification providers operate data centers outside India, verify compliance with Central Government rules under DPDPA Section 16 regarding data transfer restrictions.
- [ ] **Data Processing Agreements (DPAs)**: Execute binding DPAs with all third-party identity verification vendors, establishing their status as Data Processors bound to DPDPA obligations.
- [ ] **Breach Notification Protocol**: Finalize incident response procedures for notifying the Data Protection Board of India (DPBI) and affected users within statutory timelines in the event of an identity data breach.
- [ ] **Grievance Officer Appointment**: Formally designate and publish the contact details of the statutory Grievance Officer in accordance with the Information Technology (Intermediary Guidelines and Digital Media Ethics Code) Rules and DPDPA.
