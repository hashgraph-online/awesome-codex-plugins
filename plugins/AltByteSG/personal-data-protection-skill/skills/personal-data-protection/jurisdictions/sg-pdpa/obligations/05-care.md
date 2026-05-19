# Part 6 — Care of Data (s23–26)

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

## s23 — Accuracy obligation

**Rule (verbatim):** an organisation *"must make a reasonable effort to ensure that personal data collected by or on behalf of the organisation is accurate and complete"* if it is *"likely to be used... to make a decision that affects the individual"* or *"likely to be disclosed... to another organisation."*

**Practical effect:** for any field that drives a decision (matching, visibility, friend recommendations, country-restricted features) or is shared externally, the org must take reasonable steps to keep it accurate.

**Implementation layers:** [05 Feature/UX](../../../layers/05-feature-ux.md) (self-edit), [04 Controls](../../../layers/04-controls-and-processes.md) (verification flows).

**Operationalisation:**
- Self-edit always available for user-corrigible fields
- Email / phone verification flow (OTP)
- For high-impact auto-detected fields (country from IP, location): allow manual override

## s24 — Protection obligation

**Rule (verbatim):** an organisation *"must protect personal data in its possession or under its control by making reasonable security arrangements to prevent — (a) unauthorised access, collection, use, disclosure, copying, modification or disposal, or similar risks; and (b) the loss of any storage medium or device on which personal data is stored."*

**Practical effect:** the broadest of the Part 6 obligations — covers technical controls, operational discipline, and governance. Most PDPC enforcement action involves a s24 finding alongside others.

**Implementation layers:** [02 Architecture](../../../layers/02-architecture.md), [04 Controls](../../../layers/04-controls-and-processes.md), [01 Non-technical](../../../layers/01-non-technical.md).

**Operationalisation (the standard list):**
- Per-user data isolation (row-level security or equivalent at every read path)
- Privileged-function discipline (hardened search paths, explicit grants)
- Encryption in transit (TLS) and at rest
- Service / admin role separation
- Secret management via vault / secrets manager
- MFA for admin accounts
- Annual or per-PR security review of high-risk paths
- Audit logging of admin actions (mutations always; reads of personal data with throttle)
- PII redaction in operational logs

What "reasonable" means: in practice, PDPC weighs the sensitivity of the data, the size of the org, industry baselines, and whether the org *had* the relevant control documented in its policies. Documented + implemented + monitored beats undocumented + ad hoc.

## s25 — Retention limitation

**Rule (verbatim):** an organisation *"must cease to retain its documents containing personal data, or remove the means by which the personal data can be associated with particular individuals, as soon as it is reasonable to assume that — (a) the purpose for which that personal data was collected is no longer being served by retention of the personal data; and (b) retention is no longer necessary for legal or business purposes."*

**Practical effect:** retention beyond purpose is a violation. "We might want it later" is not a legal or business purpose.

**Implementation layers:** [03 Data model](../../../layers/03-data-model.md) (retention markers), [04 Controls](../../../layers/04-controls-and-processes.md) (sweep jobs), [06 Disclosure](../../../layers/06-disclosure.md) (privacy policy retention table).

**Operationalisation:**
- Per-category retention rule (e.g. messages > 6 months → purge; events > 90 days past → purge with chat; backups → bounded by platform retention window)
- Daily cleanup sweep aggregating per-category functions
- Account deletion: hard-delete owned data, SET NULL shared data with "Deleted User" attribution
- Retain accountability evidence (consent_log, admin_audit_log, deletion audit) — these survive account deletion as required by other obligations
- Document an inactivity policy for dormant accounts (e.g. delete / anonymise after 24 months) — frequently missed
- **Storage orphans count as retention failures.** Files in object storage (avatars, chat photos, attachments) that are still readable after the database row referencing them was deleted are still personal data — and you're still holding them past the purpose for which you collected them. Periodic orphan reaping (a scheduled job that compares object-storage keys to live DB references) is the standard mitigation. A `{userId}/...` path naming convention makes this O(n) instead of O(n²). See [layer 04](../../../layers/04-controls-and-processes.md#storage-cleanup-orchestration).

## s26 — Cross-border transfer (Transfer Limitation Obligation)

**Rule (verbatim):** an organisation *"must not transfer any personal data to a country or territory outside Singapore except in accordance with requirements prescribed... to ensure that organisations provide a standard of protection... that is comparable to the protection under this Act."*

**Practical effect:** every sub-processor outside Singapore is a cross-border transfer requiring a basis. The basis is typically contractual (sub-processor's DPA includes binding clauses) — this is the same pattern as the GDPR's Standard Contractual Clauses but lighter weight.

**Implementation layers:** [02 Architecture](../../../layers/02-architecture.md), [06 Disclosure](../../../layers/06-disclosure.md).

**Operationalisation:**
- Confirm primary database region (Singapore preferred for SG-targeted apps)
- For each sub-processor outside Singapore, rely on the vendor's DPA / contractual binding clauses (PDP Reg 10)
- List overseas transfers in the privacy policy (sub-processor table)
- Name the transfer mechanism in the privacy policy ("we rely on contractual clauses comparable to PDPA Transfer Limitation Obligation")

**Common sub-processors and the typical basis:**

| Sub-processor | Typical basis |
|---|---|
| Major cloud platforms (AWS, GCP, Azure) | Their published DPA contains binding clauses |
| Apple / Google as auth providers | Apple Developer Agreement / Google Cloud DPA |
| Notification providers (FCM, OneSignal) | Their DPA |
| Email providers (SendGrid, Resend, Postmark) | Their DPA |
| Crash reporting (Crashlytics, Sentry) | Their DPA |

If a vendor doesn't offer a DPA, that's a red flag — most reputable providers do.

## How the four obligations interact

These four obligations form a coherent chain:
- **Accuracy** (s23): the data we hold is right
- **Protection** (s24): only the right people can access it
- **Retention** (s25): we don't keep it longer than needed
- **Transfer** (s26): when it leaves Singapore, comparable protection follows it

A breach of one often implicates the others. PDPC enforcement actions frequently cite multiple Part 6 obligations together.
