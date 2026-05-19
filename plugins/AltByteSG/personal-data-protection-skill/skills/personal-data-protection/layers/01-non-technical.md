# Layer 01 — Non-technical / Organisational

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

Obligations that have no code component but must exist for the organisation to be compliant. These apply across all PDP-family jurisdictions.

## Data Protection Officer (DPO)

Most PDP-family statutes require designating at least one individual responsible for compliance and publishing their contact details. Specific triggers vary by jurisdiction (see `jurisdictions/<code>/obligations/01-accountability.md`).

**Action items:**
- Designate a primary DPO. For solo founders this is usually the founder; for small teams, often the CTO or COO.
- Designate a backup contact in case the primary is unreachable during an incident (the breach-notification clock does not pause).
- Publish the DPO email address publicly: privacy policy, in-app help/about, support page.
- Keep a written appointment record. Some regulators require it on request.

When the org grows past solo operator: appoint a backup DPO contact. When the org spans multiple jurisdictions: appoint per-jurisdiction DPOs or a single multi-jurisdiction DPO depending on local rules.

## Privacy policies and SOPs

Statutes require organisations to develop and implement policies and practices that meet the act's obligations. In practice this means:

| Document | Purpose |
|---|---|
| Public privacy policy | User-facing disclosure (what data, why, how shared, how retained, user rights) |
| Public terms & conditions | Contractual basis for the service, including consent to processing |
| Internal incident-response runbook | The on-call playbook for when something goes wrong (template at `templates/INCIDENT_RESPONSE.md.template`) |
| Internal staff acceptable-use policy (AUP) | The behavioural rules every person with prod access agrees to |
| Internal vendor / sub-processor register | Which third parties process user data, under which DPA, for what purpose |
| Internal retention schedule | What data lives how long and how it's purged |

The first two are public-facing. The rest are internal but should be maintained and reviewed.

## Staff Acceptable Use Policy (AUP)

**Critical when onboarding any second person who can access user data** (admin, contractor, support, future ops).

PDP-family statutes typically create personal criminal liability for individuals who knowingly or recklessly:
- Disclose personal data outside the organisation
- Use personal data for personal benefit, gain, or to harm the data subject
- Re-identify anonymised data without authorisation

**The organisation cannot indemnify a criminal sanction.** Every person with admin / database / support-tool access must:

1. Read and acknowledge the AUP in writing.
2. Receive a briefing on personal liability for misuse before getting credentials.
3. Have credentials provisioned via individual logins (no shared admin accounts).
4. Be subject to the audit-log review schedule (see [layer 07](07-operational.md)).

**Currently solo?** Skip the formal AUP, but write a one-page "rules for myself" — lists what you will and won't do with user data. The discipline of writing it down matters more than the audience.

## Vendor / sub-processor contracts

Each third party that processes user personal data must be governed by a Data Processing Agreement (DPA) or equivalent contractual binding. Maintain a register:

| Field | Why |
|---|---|
| Vendor name | — |
| What they do for you | Maps to a purpose declared in your privacy policy |
| Categories of data they receive | Used in privacy-policy sub-processor disclosure |
| Data residency (where they store it) | Triggers transfer obligations |
| DPA in force? Date signed? | Audit evidence |
| Sub-sub-processors they use | Disclose if material |
| Their breach notification commitment to you | Required for s26C-equivalent intermediary duty |

When adding a new vendor see [`checklists/new-vendor.md`](../checklists/new-vendor.md).

## Complaint handling

Statutes require a documented process to receive and respond to complaints about personal-data handling.

- **Channel:** a stable inbox (e.g. `privacy@yourdomain` or the DPO's address). Surface in the privacy policy and in-app.
- **SLA:** PDPC Singapore guidance is 30 calendar days. Other jurisdictions vary.
- **Tracking:** an issue tracker, even if just a tag in your existing one. Volume usually starts at zero and grows slowly; don't over-engineer.

## Onboarding any new staff member with prod access

Before they get credentials:

1. Sign AUP.
2. Briefing on personal liability for misuse.
3. Individual login (no shared credentials).
4. Document who/when/why in a staff access log.
5. Add to the audit-log review schedule.

When they leave:

1. Revoke production access same day.
2. Rotate any shared secrets they had access to.
3. Document in the staff access log.
