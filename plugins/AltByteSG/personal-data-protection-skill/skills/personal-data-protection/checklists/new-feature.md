# Checklist — Adding or Modifying a Feature

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

Use when introducing or significantly changing any user-facing feature that touches personal data.

> Walk this checklist against the universal layer files (`../layers/`) for **how** to implement, and against the active jurisdiction's obligation files (`../jurisdictions/<code>/obligations/`) for **what** must be true.

## 1. What data does the feature touch?

List **every** data category the feature reads or writes. Be specific (`profiles.email`, not "user info").

If ANY entry is new (not already in your privacy policy's data categories section):
→ Run [`new-data-field.md`](new-data-field.md) for the new field.

## 2. Architecture review ([layer 02](../layers/02-architecture.md))

- [ ] No raw queries bypass per-user data isolation. Every read filters by current-user identity, enforced at the platform level (RLS or equivalent), not just at the application level.
- [ ] Any new privileged function follows the privileged-function discipline: documented, tightened search path / namespace, audit-logged.
- [ ] Any new external-domain call goes to a vendor that's already in the privacy policy sub-processor list — if not, run [`new-vendor.md`](new-vendor.md).
- [ ] No new place ships service / admin credentials to the client.

## 3. Data model review ([layer 03](../layers/03-data-model.md))

- [ ] If new tables added: per-user isolation enabled (RLS on the table, or equivalent platform mechanism, or RPC-only access).
- [ ] If new tables hold personal data: explicit access policies OR no policies at all (deny-by-default + RPC-only).
- [ ] If new foreign keys to the users table: chosen CASCADE vs SET NULL deliberately (CASCADE for owned data, SET NULL for shared).
- [ ] If new column holds a retention-bound value: documented retention rule + sweep job.
- [ ] If new column is personal data: added to the PII inventory.

## 4. Controls / processes review ([layer 04](../layers/04-controls-and-processes.md))

- [ ] If new admin endpoint added: role check at top + audit log call at end (mutation logger always; throttled read logger for personal-data reads).
- [ ] If new server-side function added that logs: uses sanitised logging helpers (`safeError` / `redactPII` / `redactId`) at every variable interpolation.
- [ ] If new retention rule introduced: cleanup function added to the canonical sweep.
- [ ] If new column in scope of the data-export endpoint: export updated in this PR (don't leave it as a TODO — the export must remain complete).

## 5. Feature / UX review ([layer 05](../layers/05-feature-ux.md))

- [ ] If new OS-level permission required: just-in-time request, soft-prompt before the OS dialog.
- [ ] If new opt-in / consent toggle introduced: settings UI to revoke is symmetric (same effort as granting).
- [ ] If photos uploaded: goes through re-encoding pipeline (EXIF stripped).
- [ ] If new account-data field added: included in delete-account cascade or SET NULL pattern.
- [ ] If new consent collected: writes to consent record with accurate timestamp (not pre-seeded before the user actually consented).

## 6. Disclosure review ([layer 06](../layers/06-disclosure.md))

- [ ] If new personal-data field collected: privacy policy data-categories section updated.
- [ ] If new purpose for existing data: privacy policy purposes table updated.
- [ ] If new retention rule: privacy policy retention table updated AND T&C mirror updated where applicable.
- [ ] If new permission: OS usage string + Android rationale updated.
- [ ] If T&C materially changes: bump T&C version in user-record column; decide on re-acceptance prompt.
- [ ] "Last updated" date bumped on any privacy policy or T&C change.

## 7. Operational review ([layer 07](../layers/07-operational.md))

- [ ] If new cron-relevant cleanup: hooked into the canonical sweep (don't create a new schedule).
- [ ] If feature creates new high-PII surface: consider whether breach-detection signals are needed.
- [ ] If feature touches admin tooling: confirm AUP applies to any new role / permission.

## 8. Jurisdiction-specific review

For each active jurisdiction (see SKILL.md Step 1), walk the relevant obligation files:

**Singapore PDPA** (if active): walk through `../jurisdictions/sg-pdpa/obligations/01–07` and verify the feature satisfies each that applies. Pay particular attention to:
- s14(2)(a) bundled consent — **if adding a new notification channel** (push, SMS, email, in-app): is consent bundled with signup T&Cs, or is it a separate explicit opt-in? Bundled is acceptable **only** if every notification on that channel is *transactional* (verification, friend requests, message delivery). The moment one *marketing* notification is added (digests, retention pushes, promotions), bundled consent is no longer sufficient — you need a separate marketing-opt-in toggle that defaults to **off**.
- s21 access (does the new field need to be in `export_user_data`?)
- s24 protection (RLS / equivalent on any new table)
- s25 retention (TTL on any new column? if storing files: orphan-reaping covered?)
- s26D(1) breach notification (does this feature widen the breach surface? add to runbook?)

**Thailand PDPA** (if active): walk `../jurisdictions/th-pdpa/obligations/01–07`. Particular attention:
- s26 sensitive personal data — broader than SG; add a separate explicit-consent modal where any sensitive category is in scope.
- s32 data portability — export format must be transferable to another controller.
- s34 right-to-restrict — if this feature touches data covered by an active restriction, the mutation path must check the restriction state.
- s37 breach notification (72h from awareness).

**Indonesia UU PDP** (if active): walk `../jurisdictions/id-pdp/obligations/01–07`. Particular attention:
- Pasal 22 form-of-consent — strict; non-compliant consent is null and void; ensure simple language, clear distinction from T&C.
- Pasal 25 — accessibility / alternative consent channels for users with disabilities.
- Pasal 34 mandatory DPIA — **does this feature trigger any of the 7 DPIA triggers** (automation, sensitive PD, large-scale, regular monitoring, data matching, novel tech, rights-restrictive)? If yes, the DPIA artefact must exist before launch.
- Pasal 31 RoPA — update the formal records-of-processing inventory with the new purpose / recipients.
- Pasal 40, 41 — 72-hour SLAs on consent withdrawal and processing-restriction respectively; encode as per-jurisdiction SLA constants in the corresponding handlers.
- Pasal 46 breach notification — 72h to **both** subject and regulator; subject notification is **not** gated on harm.

**Malaysia PDPA** (if active): walk `../jurisdictions/my-pdpa/obligations/01–07`. Particular attention:
- s7(3) — privacy notice and choice mechanism must be available in **both Bahasa Malaysia and English**. Translation review is a release blocker.
- s4 — sensitive personal data now includes **biometric data** (face embeddings, fingerprints, voice prints, gait, iris). Trigger a separate explicit-consent dialog under s40(1)(a).
- s9 / s5(1A) — if this feature changes who-processes-what, recall that data processors are now directly liable under s9 (post-1 April 2025).
- s12B breach notification — 72h Commissioner / 7d subject (per JPDP Guideline 25 Feb 2025). Confirm the runbook has the MY lane.
- s43A data portability — if the feature creates a new export surface, satisfy s43A by exposing a structured machine-readable format and a direct-transmission path.

## 9. Backwards compatibility

- [ ] No client-callable function signature change (or, if required, coordinated with version pinning / force-update).
- [ ] No removal of JSON keys from existing function return shapes.
- [ ] No tightened validation on existing functions that would silently break older clients.

## 10. Cross-references

After landing the PR:
- Update any project-level "Open compliance gaps" tracking if this PR closes or opens one.
- Verify the conditional / parking-lot items in your project's notes don't get triggered by this change (e.g. did you add the first marketing notification? → split consent toggles).
