# Indonesia UU PDP — Jurisdiction Notes

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

| | |
|---|---|
| **Statute** | Undang-Undang Republik Indonesia Nomor 27 Tahun 2022 tentang Pelindungan Data Pribadi (UU PDP) |
| **Current text reflected** | Original 2022 enactment as published in the State Gazette |
| **Last verified** | 2026-05-03 |
| **In force since** | Enacted 17 October 2022; 2-year transition; full enforcement from **17 October 2024** |
| **Regulator** | To be appointed by Presidential Regulation (Pasal 58); currently administered through Komdigi (Kementerian Komunikasi dan Digital, formerly Kominfo) |
| **Statute citation** | UU No. 27 Tahun 2022, State Gazette of the Republic of Indonesia |
| **Pending amendments** | Subordinate Government Regulations (Peraturan Pemerintah, "PP") and Presidential Regulations (Peraturan Presiden) continue to refine specific obligations — verify the latest at [peraturan.go.id](https://peraturan.go.id) |

> **Translation caveat:** the binding text of UU PDP is the original **Bahasa Indonesia** version. As of last verification, no official English translation has been published by the Indonesian government. The content here is based on the maintainer's reading of the original Bahasa Indonesia text. **In any conflict, the Bahasa Indonesia original wins.** Use this skill as a starting framework; verify specific provisions against the Bahasa Indonesia statute and consult a qualified Indonesian privacy lawyer for binding interpretation.

> **Source copyright:** the statute is published in the State Gazette of the Republic of Indonesia; the consolidated text is hosted on [peraturan.go.id](https://peraturan.go.id). Indonesian statutes are generally treated as public materials, but layout, official translations, and Komdigi guidance may carry separate rights. Verbatim quotations and English renderings of statute language in this skill are short operative phrases reproduced with attribution for educational and engineering reference under fair-dealing principles — they are **not** licensed under this repository's MIT licence. See [DISCLAIMER.md § Copyright in source materials](../../../../DISCLAIMER.md#copyright-in-source-materials).

## Critical thresholds

- **Breach notification: within 72 hours** (3 × 24 jam) of the Data Controller becoming aware (Pasal 46(1)). Notification goes to **both** the Data Subject **and** the regulator (lembaga). For breaches "under certain circumstances," public notification is also required (Pasal 46(3)).
- **Maximum administrative fine (Pasal 57(3)):** **2% of annual revenue** of the offending Controller or Processor, applied per violation variable.
- **Other administrative sanctions (Pasal 57(2)):** written warning, temporary suspension of processing activities, deletion or destruction of Personal Data, in addition to or instead of the fine.
- **Criminal penalties (Pasal 67–68):**
  - **Up to 5 years imprisonment + IDR 5 billion fine** — unauthorized obtaining or use of another's Personal Data (Pasal 67(1)/(3))
  - **Up to 4 years imprisonment + IDR 4 billion fine** — unauthorized disclosure (Pasal 67(2))
  - **Up to 6 years imprisonment + IDR 6 billion fine** — falsification of Personal Data (Pasal 68)
- **Corporate criminal liability (Pasal 70):** for offences by a corporation under Pasal 67/68, fines may be **up to 10× the maximum** for a natural person, plus possible asset confiscation, business suspension, permanent activity ban, business location closure, licence revocation, or **dissolution of the corporation**.
- **Cross-border transfer (Pasal 56):** destination country must have equal-or-higher Personal Data protection standards; if not, must have adequate and binding safeguards; if neither, must have explicit data subject consent.
- **Processor reclassification (Pasal 51(6)):** if a Data Processor processes data outside the Data Controller's instructions, **the Processor is treated as the Controller** for that processing — shifting full liability.

## Obligations covered

The obligation files in `obligations/` map the active parts of the Act to the universal layers in `../../layers/`:

| File | Statute parts | Topic |
|---|---|---|
| [01-accountability.md](obligations/01-accountability.md) | BAB VI Bagian Kedua–Keempat (Pasal 19–54) | Controller / processor duties, records (Pasal 31), DPO (Pasal 53–54), DPIA (Pasal 34) |
| [02-consent.md](obligations/02-consent.md) | Pasal 4, 20–26 | Sensitive vs general data (Pasal 4); 6 lawful bases (Pasal 20); consent form (Pasal 22); child / disability consent (Pasal 25–26) |
| [03-purpose.md](obligations/03-purpose.md) | Pasal 16, 21, 27, 28 | Processing principles (Pasal 16); notification at consent (Pasal 21); purpose limitation (Pasal 27, 28) |
| [04-access-correction.md](obligations/04-access-correction.md) | BAB IV (Pasal 5–15) + Pasal 30, 32, 40, 41, 43 | Data subject rights, 72-hour response windows, automated-decision objection |
| [05-care.md](obligations/05-care.md) | Pasal 29, 35–39, 42, BAB VII (Pasal 55–56) | Accuracy, security, retention, domestic + cross-border transfer |
| [06-breach-notification.md](obligations/06-breach-notification.md) | Pasal 46 | 72-hour breach notification to subject AND regulator |
| [07-offences.md](obligations/07-offences.md) | BAB VIII (Pasal 57), BAB XIII–XIV (Pasal 65–73) | Administrative sanctions (2% revenue cap); criminal penalties; corporate criminal liability |

The reverse-lookup index (statute section → layer + obligation file) is at [statute-map.md](statute-map.md).

## What's intentionally not covered

- BAB IX (Lembaga / Authority — Pasal 58–61): governance / regulator structure, refined by Presidential Regulation
- BAB X (International Cooperation — Pasal 62): government-to-government cooperation, not relevant to compliance implementation
- BAB XI (Public Participation — Pasal 63): general civic participation provisions
- BAB XII (Dispute Resolution — Pasal 64): procedural — relevant during active disputes
- BAB XV–XVI (Transitional and Closing Provisions — Pasal 74–76): historical
- Subordinate Government Regulations (PP) and Presidential Regulations issued under the Act — these refine specific obligations and amend over time; verify current text at [peraturan.go.id](https://peraturan.go.id)

## Mental model: what makes Indonesia UU PDP distinctive

Compared to Singapore PDPA and Thailand PDPA:

- **Six GDPR-style lawful bases** (Pasal 20(2)): explicit consent, contract, legal obligation, vital interests, public-interest task, legitimate interests. Same structure as Thailand; broader than Singapore's enumerated 1st/2nd Schedule cases.
- **Specific Personal Data category** (Pasal 4): the Act splits Personal Data into "specific" (sensitive) and "general." The "specific" category covers data warranting heightened protection; the precise scope is detailed in subordinate regulations (verify current PP text).
- **72-hour breach notification window** (Pasal 46): notification to **both** the Data Subject **and** the regulator within 72 hours. Faster than Singapore's 3-day clock (in calendar days from assessment); same as Thailand.
- **3 × 24 hours response windows for many controller obligations**: correction (Pasal 30), access (Pasal 32), stop processing on consent withdrawal (Pasal 40), suspend / restrict (Pasal 41). Aggressive operational SLA — your customer-support / engineering teams must be set up for it.
- **Mandatory DPIA** (Pasal 34) for high-risk processing, with 7 enumerated triggers including automated decision-making, large-scale processing, sensitive data, systematic monitoring, data combining, new technologies, and processing that limits data subject rights.
- **Corporate criminal liability is broad** (Pasal 70): not just fines — courts can suspend operations, ban activities, revoke licences, or **dissolve the corporation**. Significantly broader sanction palette than Singapore or Thailand.
- **Right to object to automated decision-making and profiling** (Pasal 10): an explicit standalone right, comparable to GDPR Article 22.
- **Mandatory DPO triggers similar to GDPR Article 37** (Pasal 53): public-interest processing, large-scale regular monitoring, large-scale specific or criminal-records processing.

## Cross-references

- [`../../checklists/`](../../checklists/) — entry points for common engineering tasks; reference the universal layers + this jurisdiction's obligations.
- [`templates/INCIDENT_RESPONSE.md.template`](../../templates/INCIDENT_RESPONSE.md.template) — runbook template; the 72-hour clock for Indonesia is identical to Thailand's.
