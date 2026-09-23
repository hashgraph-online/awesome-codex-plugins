# Checklist — Adding a New Personal-Data Field

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

Use when adding a column, JSON field, or storage path that holds personal data about a user.

## 1. Classify the field

What kind of personal data is this?

- [ ] Identifier (UUID, email, phone, username) — already covered by your existing patterns
- [ ] Profile attribute (name, birthday, country, bio) — already covered
- [ ] Location (lat/lng, city, region) — **sensitive**
- [ ] Health (allergies, medical conditions) — **sensitive when paired with identity**
- [ ] Authentication credential (token, hash, secret) — **sensitive**
- [ ] User-generated content (post, message, photo) — covered
- [ ] Behaviour / activity (likes, saves, RSVPs) — covered
- [ ] Children's data (DOB indicating minor, parental info) — **extra-sensitive**
- [ ] Financial information — **sensitive**
- [ ] Other (specify)

If **sensitive** or **other**, also flag in the PR description so reviewers know to apply heightened scrutiny.

## 2. Jurisdiction check

**Do this before the data model and disclosure steps** — the lawful basis, consent
mechanics, and sensitive-data classification below all change what you build.

For each active jurisdiction, confirm:

- [ ] **Singapore PDPA** — does the field fit the existing s17 / 1st-Schedule lawful basis, or does it need explicit consent? If consent: when is it recorded?
- [ ] **Thailand PDPA** — six-base structure (s24); chosen lawful basis documented. If the field is sensitive (s26 broad list), explicit consent dialog required.
- [ ] **Indonesia UU PDP** — six-base structure (Pasal 20); chosen lawful basis documented. If the field is "Specific" Personal Data (Pasal 4: health, biometric, genetic, criminal, children's, financial), explicit consent + **DPIA trigger check** (Pasal 34). RoPA updated (Pasal 31).
- [ ] **Malaysia PDPA** — basis under s6 (consent default + s6(2) carve-outs); s6(3) data-minimisation test (lawful purpose + necessity + non-excessive). If sensitive (s4 incl. **biometric data**), explicit consent under s40(1)(a) + separate consent screen. Recipients list update (s44).
- [ ] **Philippines DPA** — lawful criteria under § 12 (personal information) or § 13 (sensitive personal information); SPI is a **closed statutory list** (race, marital status, age, religion, health, education, genetic, government-issued identifiers, and proceedings) — if the field lands in it, § 13 consent must be **written, electronic-signed, and obtained before processing**. Confirm the field is covered by the NPC-registered processing system description (§ 24 IRR).
- [ ] **Vietnam PDPL** — classify against **Decree Điều 4** (sensitive, closed list) first; anything identifying that is not listed is **basic** by Điều 3(11). Watch four that are sensitive in VN and not elsewhere: **positioning-service location**, **e-ID credentials and ID-card images**, **bank credentials / card / transaction / credit data**, and **behaviour-tracking data on telecom, social and online services** — i.e. ordinary product analytics. If sensitive, Decree Điều 4(2) requires access-limiting permissions, a documented processing procedure and security measures. Consent is per-purpose and cannot be bundled or inferred from silence (Điều 9(4)).

If you flagged the field **sensitive** in step 1:

- [ ] Recorded in your runbook's breach-assessment matrix as a "deemed significant harm" category — exposure of even a single record may be notifiable. Confirm the threshold against each active jurisdiction's `obligations/06-breach-notification.md`.

## 3. Data model ([layer 03](../layers/03-data-model.md))

- [ ] Per-user isolation is enabled on the table (RLS or equivalent).
- [ ] Default value chosen deliberately:
  - `NULL` if optional and the user must opt in
  - `false` for boolean opt-in toggles (no auto-grant)
  - `true` only for transactional / essential defaults that match user expectation at signup
- [ ] If storage-backed: path naming follows the convention `{userId}/...` if user-owned, `{containerId}/...` if shared.
- [ ] **If sensitive (step 1):** encrypted at rest column-level, where the platform supports it. Decide this now — retrofitting encryption means a second migration.

## 4. Lifecycle

For each phase, verify:

- [ ] **Creation** — when is this field first populated? Is consent recorded if appropriate?
- [ ] **Update** — can the user correct it (Correction obligation)? Is there a self-service edit surface, or a documented channel?
- [ ] **Deletion** — what happens on account deletion? CASCADE (owned) or SET NULL (shared)?
- [ ] **Export** — included in the data-export response? **If not, must be added** (Access obligation requires *all* held PII).
- [ ] **Retention** — does it have a TTL? If yes, where does the cleanup run?

## 5. Disclosure ([layer 06](../layers/06-disclosure.md))

- [ ] Privacy policy data-categories section lists the new field with the exact category.
- [ ] Privacy policy purposes table updated if there's a new purpose.
- [ ] Privacy policy retention table updated if a TTL applies.
- [ ] If the field flows to a sub-processor (e.g. push token to FCM, OAuth token to Apple): privacy policy sub-processor table row updated.
- [ ] OS permission usage string updated if a new prompt fires.
- [ ] Jurisdiction-specific notice requirements from step 2 are satisfied (e.g. MY s7(3) bilingual notice).

## 6. Logging hygiene ([layer 04](../layers/04-controls-and-processes.md))

- [ ] No `console.log` / `print` / `debugPrint` includes the raw field value in any server-side function or admin tooling.
- [ ] If logged for ops, run through `redactPII` (or your equivalent helper).

## 7. Admin visibility

- [ ] If this field appears in any admin read endpoint: that endpoint is audit-logged via the throttled read logger.
- [ ] If admin can edit it: that mutation calls the audit logger.
- [ ] **If sensitive (step 1):** access tightened beyond default — even authenticated users may not need it; consider service-only access via a function that strips it on read.

## 8. Sub-processor flow

If the field is **transmitted** to a third party (push body, OAuth token, email content, webhook payload, etc.):

- [ ] Vendor is in the privacy policy sub-processor table.
- [ ] Vendor's DPA covers this category of data.
- [ ] If new vendor: run [`new-vendor.md`](new-vendor.md).

## 9. Backwards compatibility

- [ ] Adding the column doesn't break older clients (they ignore unknown response fields).
- [ ] Adding it to the data-export endpoint is a JSON addition — safe.
- [ ] Adding it as a required parameter to an existing function is a breaking change — coordinate with client version pinning / force-update.
