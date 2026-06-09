# Thailand PDPA — Jurisdiction Notes

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

| | |
|---|---|
| **Statute** | Personal Data Protection Act, B.E. 2562 (2019) |
| **Current text reflected** | Original 2019 text as published in Government Gazette |
| **Last verified** | 2026-05-03 (against PDPC Thailand-published English translation) |
| **In force since** | 1 June 2022 (delayed twice from the original 28 May 2020 effective date) |
| **Regulator** | Personal Data Protection Committee Thailand — [www.pdpc.or.th](https://www.pdpc.or.th) |
| **Statute citation** | Government Gazette No. 136 Chapter 69 Gor (27 May 2019) |
| **Pending amendments** | Subordinate notifications and ministerial regulations issued by PDPC Thailand after enactment continue to refine specific obligations — verify the latest at [pdpc.or.th](https://www.pdpc.or.th) |

> **Translation caveat:** the binding text of the Thailand PDPA is the original Thai-language version published in the Royal Thai Government Gazette. PDPC Thailand publishes an English translation explicitly labelled "unofficial." The content here is based on that unofficial translation. **In any conflict, the Thai original wins.** Use this skill as a starting framework; verify specific provisions against the Thai original and consult a qualified Thai privacy lawyer for binding interpretation.

> **Source copyright:** the Thai original is published by the Royal Thai Government Gazette; the unofficial English translation is published by PDPC Thailand under PDPC Thailand's own terms. Verbatim quotations in this skill are short operative phrases reproduced with attribution for educational and engineering reference under fair-dealing principles — they are **not** licensed under this repository's MIT licence. See [DISCLAIMER.md § Copyright in source materials](../../../../DISCLAIMER.md#copyright-in-source-materials).

## Critical thresholds

- **Breach notification to PDPC: within 72 hours** after the Data Controller becomes aware (s37(4)). For breaches likely to result in **high risk to rights and freedoms**, also notify affected data subjects "without delay."
- **Cross-border transfers (s28):** destination country / international organisation must have adequate Personal Data protection standards as prescribed by PDPC, OR the transfer must fall within the 6 enumerated exceptions.
- **Maximum administrative fines (Part II of Chapter VII):**
  - **THB 5 million** — for violations involving sensitive Personal Data (s26) or sensitive-data cross-border transfers
  - **THB 3 million** — for general violations of consent, purpose limitation, retention, security, cross-border rules
  - **THB 1 million** — for procedural failures (notification, records, DPO designation)
- **Maximum criminal penalties (Part I of Chapter VII):**
  - **Up to 1 year imprisonment + THB 1M fine** — for use/disclosure or cross-border transfer of sensitive data without consent for unlawful benefit (s79 paragraph 2)
  - **Up to 6 months imprisonment + THB 500k fine** — for s79 paragraph 1 violations (causing damage / reputation impairment) and s80 (unauthorised disclosure by official duty-holders)
- **Personal criminal liability** (s81): if a juristic person commits an offence due to the instructions or omissions of any director, manager, or responsible person, **that individual is also personally punished** with the same penalty.

## Obligations covered

The obligation files in `obligations/` map the active parts of the Act to the universal layers in `../../layers/`:

| File | Statute parts | Topic |
|---|---|---|
| [01-accountability.md](obligations/01-accountability.md) | Chapter I (s8–18); s37, s39, s41–42 | PDPC, controller / processor duties, records, DPO |
| [02-consent.md](obligations/02-consent.md) | Chapter II Part I (s19–21); s24 (bases); s26 (sensitive) | Consent, lawful bases, sensitive data |
| [03-purpose.md](obligations/03-purpose.md) | s21–s23, s25 | Purpose limitation, data minimization, notification of purpose |
| [04-access-correction.md](obligations/04-access-correction.md) | Chapter III (s30–36) | Access, portability, objection, erasure, restriction, accuracy |
| [05-care.md](obligations/05-care.md) | s35 (accuracy), s37(1)–(3) (security), s28–29 (cross-border), s40 (processor) | Care of data |
| [06-breach-notification.md](obligations/06-breach-notification.md) | s37(4) | 72-hour PDPC notification |
| [07-offences.md](obligations/07-offences.md) | Chapter VII (s79–90) | Criminal + administrative penalties; personal liability |

The reverse-lookup index (statute section → layer + obligation file) is at [statute-map.md](statute-map.md).

## What's intentionally not covered

- Chapter IV (Office of the PDPC, s43–70) — administrative / governance structure of the regulator; not relevant to compliance implementation
- Chapter V (Complaints, s71–76) — procedural; relevant during an active complaint, not for ongoing compliance
- Chapter VI (Civil Liability, s77–78) — civil damages framework; relevant during litigation
- Transitional provisions (s91–96) — initial setup of the regulator; historical
- Royal Decrees and PDPC Notifications issued under the Act — these refine specific obligations and amend over time; verify current text at [pdpc.or.th](https://www.pdpc.or.th)

## Mental model: what makes Thailand PDPA distinctive

Compared to Singapore PDPA:

- **Six GDPR-style lawful bases** (s24) instead of consent + enumerated exceptions: consent, contract, legal obligation, vital interests, public interest task, legitimate interests, plus research/archival under safeguards.
- **Stricter sensitive-data category** (s26): broader than Singapore's deemed-significant-harm list. Includes racial/ethnic origin, political opinions, religious/philosophical beliefs, sexual behavior, criminal records, health, disability, trade union, genetic, biometric.
- **Faster breach window: 72 hours** vs Singapore's 3 calendar days. (Both are strict — Singapore is calendar days, Thailand is hours from awareness.)
- **Tiered administrative penalties** (1M / 3M / 5M THB) rather than a single cap. Sensitive-data violations are at the highest tier.
- **Personal liability is broader**: s81 catches directors/managers whose instructions OR omissions led to the corporate offence — not limited to active misuse like Singapore's s48D/E/F.
- **Cross-border requires adequacy OR explicit exception**: closer to GDPR's adequacy-decision model than Singapore's contractual-comparable-protection approach. Within-affiliate transfers under a PDPC-certified Personal Data Protection Policy (s29) are the Thai equivalent of Binding Corporate Rules.
- **Mandatory representative in Thailand** (s37(5)): controllers outside Thailand serving Thai users must designate a written representative in the Kingdom.

## Cross-references

- [`../../checklists/`](../../checklists/) — entry points for common engineering tasks; reference the universal layers + this jurisdiction's obligations.
- [`templates/INCIDENT_RESPONSE.md.template`](../../templates/INCIDENT_RESPONSE.md.template) — runbook template, includes the 72-hour clock for Thailand.
