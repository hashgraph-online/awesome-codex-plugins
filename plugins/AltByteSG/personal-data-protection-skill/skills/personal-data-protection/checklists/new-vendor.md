# Checklist — Adding a New Sub-processor / Third-Party Vendor

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

Use when wiring up a new external service that will receive, process, or store user personal data (push notifications, email delivery, analytics, error tracking, payments, identity, etc.).

## 1. Is it actually a sub-processor?

A **sub-processor** processes user personal data on your behalf. It is NOT:

- Pure transit infrastructure (CDN, edge cache) where data passes through but isn't stored
- Source-code hosting / CI / developer tooling that never sees production user data
- Vendors that only see aggregate / anonymised metrics with no re-identification path

**Inclusion test:** does the vendor receive a value that maps to an individual user (UUID, email, name, IP, device ID, etc.)?

If yes → sub-processor → continue this checklist.
If no → not a sub-processor → no privacy-policy disclosure needed (but still document in your internal vendor register).

## 2. Contract / DPA

- [ ] Signed / accepted Data Processing Agreement (DPA) is in place.
- [ ] DPA covers the active jurisdictions explicitly OR provides "comparable protection" sufficient for the active jurisdictions' transfer obligations.
- [ ] Sub-sub-processors that the vendor uses are acceptable / disclosed by them.
- [ ] DPA includes a breach-notification flow-down clause requiring the vendor to notify you with enough lead time for you to hit the strictest active clock — typically **≤24 hours from the vendor's discovery** so you can still file the MY 72h s12B(1) Commissioner notification, the TH/ID 72h authority notification, or the SG 3-day post-assessment notification (s26C(3)).
- [ ] DPA covers the data residency you need.

## 3. Architecture ([layer 02](../layers/02-architecture.md))

- [ ] Vendor's data residency confirmed and documented.
- [ ] Authentication credentials stored in your secret manager or platform vault — never in source.
- [ ] Credential rotation procedure documented in your incident-response runbook.
- [ ] No client-side credential exposure (the app does not ship the API key).

## 4. Disclosure ([layer 06](../layers/06-disclosure.md))

- [ ] Privacy policy sub-processor table has a new row (or an existing row updated) with:
  - Provider name (use the legal entity name where it differs from the brand)
  - Specific purpose (what they do for you)
  - Data categories processed
  - Region (or "global infrastructure" with a note about contractual binding)
- [ ] If the new vendor is the same legal entity as an existing row (e.g. another Google service), update the existing row instead of adding a new one.
- [ ] Closing paragraph "Sub-processor list updated: …" date is bumped.
- [ ] Privacy policy "Last updated" date bumped.
- [ ] If material change, decide on user notification (in-app banner / email).

## 5. Cross-border transfer basis

For each active jurisdiction:

- [ ] **Singapore PDPA s26** — vendor's DPA contains binding clauses comparable to PDPA Transfer Limitation Obligation (PDP Reg 10).
- [ ] **Indonesia UU PDP** — Pasal 56 3-tier hierarchy: adequacy → adequate-and-binding safeguards → consent. No published adequacy list — most realistic basis is Tier 2 vendor DPA with binding clauses.
- [ ] **Thailand PDPA** — verify the cross-border basis (adequacy / explicit consent / contractual safeguards) is satisfied.
- [ ] **Malaysia PDPA s129** — post-A1727 (1 April 2025) the Ministerial whitelist regime is **deleted**. Realistic basis is **s129(3)(f) due diligence**: vendor DPA + cert audits (ISO 27001 / SOC 2) + a documented assessment that the destination won't process the data in a manner that would contravene the Act if it were Malaysia. Burden of proof is on you as controller.

## 6. Logging hygiene ([layer 04](../layers/04-controls-and-processes.md))

- [ ] Server-side code calling the vendor uses sanitised logging helpers (`safeError` / `redactPII`) at every `console.*` / `print` / equivalent.
- [ ] Vendor's error responses run through `redactPII` (vendors notoriously echo submitted PII back in errors — emails, tokens, IDs).
- [ ] If the vendor returns rich JSON errors, parse and log only the error code / type, not the full body.

## 7. Activation gating

If the vendor is wired but not yet actively sending data:

- [ ] Add to the project's "wired but inactive" parking-lot list.
- [ ] Privacy policy update is NOT required until activation (no data has actually flowed).
- [ ] When activating, the privacy policy update lands in the same PR as the activation switch.

## 8. Incident-response coverage

Update `docs/INCIDENT_RESPONSE.md`:

- [ ] Add a containment row for the new credential (rotate where, update where).
- [ ] Add a row for vendor-reported breach scenarios (how do they notify you?).

## 9. Vendor renewal / review

- [ ] Add to the quarterly vendor review schedule.
- [ ] Note the DPA renewal date if it has one.

## 10. Jurisdiction-specific notes

| Jurisdiction | Particular considerations |
|---|---|
| **Singapore PDPA** | s26 transfer + s11(2) responsibility for processor. Most vendor DPAs cover this with standard contractual clauses. |
| **Indonesia UU PDP** | Cross-border requires adequacy OR explicit consent OR safeguards. Vendor DPA usually provides safeguards. Pasal 51–52 also imposes processor obligations parallel to controller — confirm vendor's RoPA practice. |
| **Thailand PDPA** | Similar to Indonesia. Note PDPC Thailand has not formally designated adequate jurisdictions — rely on contractual safeguards. |
| **Malaysia PDPA** | Post-A1727 (1 April 2025) the processor is **directly bound** by the Security Principle (s9) under s5(1A) and must appoint its own DPO under s12A(2). Confirm the vendor has appointed and registered a DPO with JPDP — the vendor's DPO appointment is now an evidence item, not just contractual. Cross-border whitelist is gone — rely on s129(3)(f) due diligence. |
