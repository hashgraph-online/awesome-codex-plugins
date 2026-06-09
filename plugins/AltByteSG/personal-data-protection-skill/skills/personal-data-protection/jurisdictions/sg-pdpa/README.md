# Singapore PDPA — Jurisdiction Notes

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

| | |
|---|---|
| **Statute** | Personal Data Protection Act 2012 (No. 26 of 2012) |
| **Current text reflected** | Version in force as at 1 May 2026 |
| **Last verified** | 2026-05-02 |
| **Most recent material amendment** | Personal Data Protection (Amendment) Act 2020 (commenced 1 February 2021; financial penalty ceiling at s48J(3) commenced 1 October 2022) |
| **Regulator** | Personal Data Protection Commission (PDPC) — [www.pdpc.gov.sg](https://www.pdpc.gov.sg) |
| **Statute on Singapore Statutes Online** | [sso.agc.gov.sg/Act/PDPA2012](https://sso.agc.gov.sg/Act/PDPA2012) |
| **Pending amendments** | None known as at last verification date |

> **Source copyright:** the statute text is Crown copyright held by the Attorney-General's Chambers and published on Singapore Statutes Online subject to the [SSO Terms of Use](https://sso.agc.gov.sg/Help/TermsOfUse). Verbatim quotations in this skill are short operative phrases reproduced with attribution for educational and engineering reference under fair-dealing principles — they are **not** licensed under this repository's MIT licence. See [DISCLAIMER.md § Copyright in source materials](../../../../DISCLAIMER.md#copyright-in-source-materials).

## Critical thresholds

- **Breach notification to PDPC: 3 calendar days** after assessing as notifiable (s26D(1)). Days, not business days.
- **Significant scale threshold:** ≥ 500 affected individuals (PDP Notification of Data Breaches Regulations 2021).
- **Maximum financial penalty cap (s48J(3)):**
  - SGD 1M for organisations with Singapore turnover ≤ SGD 10M
  - 10% of Singapore turnover for organisations above SGD 10M
- **Individual criminal liability** (s48D / s48E / s48F): SGD 5,000 fine and/or 2 years imprisonment per offence

## Obligations covered

The obligation files in `obligations/` map the active parts of the Act to the universal layers in `../../layers/`:

| File | Statute parts | Topic |
|---|---|---|
| [01-accountability.md](obligations/01-accountability.md) | Part 3 (s11–12) | DPO designation, policies, complaint handling |
| [02-consent.md](obligations/02-consent.md) | Part 4 Div 1 (s13–17) | Consent collection, withdrawal, deemed consent, exceptions |
| [03-purpose.md](obligations/03-purpose.md) | Part 4 Div 2 (s18–20) | Purpose limitation, notification of purpose |
| [04-access-correction.md](obligations/04-access-correction.md) | Part 5 (s21–22A) | Access right, correction right, preservation duty |
| [05-care.md](obligations/05-care.md) | Part 6 (s23–26) | Accuracy, protection, retention, transfer outside Singapore |
| [06-breach-notification.md](obligations/06-breach-notification.md) | Part 6A (s26A–E) | Breach assessment, PDPC notification, individual notification |
| [07-offences.md](obligations/07-offences.md) | Part 9B (s48D–F) | Personal criminal liability for staff |

The reverse-lookup index (statute section → layer + obligation file) is at [statute-map.md](statute-map.md).

## What's intentionally not covered

The following are within the Act but not relevant to most consumer applications and are excluded from this skill to keep the surface focused:

- Part 9 (Do Not Call Registry) — applies to telemarketing-style messages to Singapore phone numbers; out of scope for app-style products that don't make outbound marketing calls.
- Parts 9C–9D (Enforcement, Appeals) — procedural; relevant during an active enforcement action, not for ongoing compliance.
- First/Second Schedule items irrelevant to a consumer app (debt collection, credit bureau operations, employment-context exemptions).

If your application uses outbound voice / SMS marketing to Singapore users, you'll need the Do Not Call sections in addition to this skill.

## Mental model: what makes Singapore PDPA distinctive

If you've worked with GDPR or another framework, the things to recalibrate:

- **Lawful bases are simpler.** Consent is the default; the "legitimate interest"-style alternatives (s17 + 1st/2nd Schedule) are an enumerated list of cases, not a balancing test.
- **Breach notification is faster and stricter** than most jurisdictions: 3 calendar days vs the 72-hour business standard elsewhere.
- **Individual criminal liability** (s48D/E/F) is unusual — not just civil penalties on the org, but personal criminal exposure for staff who knowingly misuse data. Reflect this in the staff AUP (see [layer 01](../../layers/01-non-technical.md)).
- **Accountability ("demonstrable compliance")** is structural: regulators expect the org to show its work — DPO, policies, training records, audit logs, breach assessments.

## Cross-references

- [`../../checklists/`](../../checklists/) — entry points for common engineering tasks; reference the universal layers + this jurisdiction's obligations.
- [`templates/INCIDENT_RESPONSE.md.template`](../../templates/INCIDENT_RESPONSE.md.template) — runbook template, includes the SG-specific 3-day clock.
