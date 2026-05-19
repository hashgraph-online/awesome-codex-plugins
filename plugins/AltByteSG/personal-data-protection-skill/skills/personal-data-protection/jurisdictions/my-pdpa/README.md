# Malaysia PDPA — Jurisdiction Notes

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

| | |
|---|---|
| **Statute** | Personal Data Protection Act 2010 (Act 709) |
| **Current text reflected** | Act 709 as amended by the Personal Data Protection (Amendment) Act 2024 (Act A1727), all provisions in force as at 1 June 2025 |
| **Last verified** | 2026-05-04 |
| **Most recent material amendment** | Personal Data Protection (Amendment) Act 2024 (Act A1727) — Royal Assent 9 October 2024; staged commencement under P.U.(B) 522/2024 (1 January 2025, 1 April 2025, 1 June 2025) |
| **Regulator** | Department of Personal Data Protection (Jabatan Perlindungan Data Peribadi, JPDP) under the Ministry of Digital — [www.pdp.gov.my](https://www.pdp.gov.my) |
| **Statute on Federal Legislation portal** | [lom.agc.gov.my](https://lom.agc.gov.my) (search Act 709 / Act A1727); JPDP-published consolidated PDF: [Act 709 EN/BM](https://www.pdp.gov.my/ppdpv1/wp-content/uploads/2024/07/UNDANG-UNDANG-MALAYSIA_AKTA_PERLINDUNGAN_DATA_PERIBADI_2010_709_MALAY_AND-ENG_V2022.pdf), [Act A1727](https://www.pdp.gov.my/ppdpv1/wp-content/uploads/2024/11/Act-A1727.pdf) |
| **Operative JPDP guidelines (issued 25 February 2025; effective 1 June 2025)** | Personal Data Protection Guideline on the Appointment of Data Protection Officer; Personal Data Protection Guideline on Data Breach Notification |
| **Pending amendments / guidance** | Subordinate regulations on data portability period under s43A(3) and on cross-border safeguards under s129(2) post-whitelist still expected; check JPDP for updates |

> **Source copyright:** the statute text (Act 709 and Act A1727) is published by Percetakan Nasional Malaysia Berhad as Appointed Printer to the Government of Malaysia. Verbatim quotations in this skill are short operative phrases reproduced with attribution for educational and engineering reference under fair-dealing principles — they are **not** licensed under this repository's MIT licence. See [DISCLAIMER.md § Copyright in source materials](../../../../DISCLAIMER.md#copyright-in-source-materials).

## Critical thresholds

- **Breach notification to the Commissioner: 72 hours** from when the breach is discovered (statute says "as soon as practicable" at s12B(1); the **72-hour benchmark** is set by the JPDP Personal Data Protection Guideline on Data Breach Notification, 25 February 2025).
- **Affected-individual notification:** "without unnecessary delay" where the breach causes or is likely to cause **significant harm** (s12B(2)); the Guideline specifies **within 7 days after notifying the Commissioner**.
- **DPO mandatory** where the controller / processor handles personal data of **more than 20,000** individuals, OR **sensitive personal data** (incl. biometric data) of **more than 10,000** individuals (per the JPDP DPO Appointment Guideline). DPO must be registered via the Personal Data Protection System within 21 days of appointment.
- **Maximum financial penalties (post-A1727):**
  - Principle breach (s5(2)) — **RM 1,000,000** and/or 3 years imprisonment (raised from RM 300,000 / 2 years)
  - Sensitive personal data breach (s40(3)) — RM 200,000 and/or 2 years (unchanged)
  - Cross-border transfer breach (s129(5)) — RM 300,000 and/or 2 years (unchanged)
  - Breach-notification failure (s12B(3)) — RM 250,000 and/or 2 years (new)
  - Unlawful collecting / sale of personal data (s130(7)) — RM 500,000 and/or 3 years
- **Director / officer liability** (s133): directors and senior officers are deemed to have committed the offence with the body corporate unless they prove (i) absence of knowledge / consent / connivance, AND (ii) all reasonable precautions and due diligence to prevent it.

## Application — read this first

- Act 709 applies to **commercial transactions** only (s2(1)). Government-to-citizen processing by federal or state government is **excluded** (s2(2)). Practical effect: if your project is a purely public-sector backend, PDPA does not apply — but most consumer-facing apps are commercial and so do.
- Territorial reach (s3): applies to a data controller (a) established in Malaysia and processing personal data **in or out of Malaysia**, or (b) not established in Malaysia but using **equipment in Malaysia for processing other than transit**. So a foreign SaaS that hosts data on a Malaysian region or runs servers in Malaysia is in scope.
- "Data subject" excludes a **deceased individual** (s4 as amended by A1727 item 3(f)).

## Obligations covered

The obligation files in `obligations/` map the active parts of the Act to the universal layers in `../../layers/`:

| File | Statute parts | Topic |
|---|---|---|
| [01-accountability.md](obligations/01-accountability.md) | s12A (new); Part II Div 3 (s21–29) | DPO appointment + registration, codes of practice, vendor obligations |
| [02-consent.md](obligations/02-consent.md) | s6 (General Principle), s38, s40, s43; s4 sensitive-PD definition | Consent, withdrawal, sensitive personal data, direct marketing |
| [03-purpose.md](obligations/03-purpose.md) | s7 (Notice & Choice Principle), s8 (Disclosure Principle), s39, s41 | Notice content, language, purpose limitation, disclosure constraints |
| [04-access-correction.md](obligations/04-access-correction.md) | s30–37; s42; s43A (new) | Access right, correction right, refusal protocol, prevention of processing causing damage/distress, **data portability** |
| [05-care.md](obligations/05-care.md) | s9 (Security), s10 (Retention), s11 (Data Integrity), s44, s129 | Protection, retention/destruction, accuracy, record-keeping, cross-border transfer (post-whitelist) |
| [06-breach-notification.md](obligations/06-breach-notification.md) | s12B (new); JPDP Breach-Notification Guideline 25 Feb 2025 | Breach assessment, 72-hour Commissioner notification, 7-day subject notification |
| [07-offences.md](obligations/07-offences.md) | s5(2), s12B(3), s40(3), s129(5), s130, s133 | Penalties; director / senior officer liability |

The reverse-lookup index (statute section → layer + obligation file) is at [statute-map.md](statute-map.md).

## What's intentionally not covered

The following are within the Act but not relevant to most consumer applications and are excluded from this skill to keep the surface focused:

- Part III (s45–46) — Exemption: procedural ministerial-exemption mechanism, not engineering-relevant.
- Part IV (s47–60) — Commissioner appointment, functions, powers: institutional.
- Part V (s61–69) — Personal Data Protection Fund: institutional.
- Part VI (s70–82) — Advisory Committee: institutional.
- Part VII (s83–100) — Appeal Tribunal: procedural; relevant during an active appeal, not for ongoing compliance.
- Part VIII (s101–127) — Inspection: procedural; engages during regulator inspection.
- Registration of data users (Part II Div 2, s13–20) — applies to **classes of data users specified by Ministerial order** (e.g., financial services, healthcare, telecoms). Whether your organisation must register is a per-class assessment outside the scope of this engineering skill; check the latest Personal Data Protection (Class of Data Users) Order.

If your application participates in a registered class of data users, you will need the registration regime (s13–20) plus your sector's code of practice in addition to this skill.

## Mental model: what makes Malaysia PDPA distinctive (engineering view)

If you've worked with Singapore PDPA, GDPR, or another framework, the things to recalibrate when implementing an app or backend:

- **Principles-based** rather than obligation-list-based. The seven Personal Data Protection Principles (s5(1) → ss.6–12) are the *whole* substantive surface engineers map onto code — General, Notice & Choice, Disclosure, Security, Retention, Data Integrity, Access. Everything else (Division 4 rights, breach notification, cross-border) hangs off them.
- **Direct duty on data processors** is new (1 April 2025 under A1727 item 4 → s5(1A), item 5 → s9, and item 6 → s12A(2)). If your app is a B2B SaaS processing on behalf of customer-controllers, you now have your own statutory floor — security controls, DPO, breach-notification flow-down — separate from your customer DPA.
- **Bilingual notice** (s7(3)): the privacy notice and choice mechanism must be available in **both** Bahasa Malaysia and English. Bake this into release engineering — translation review is a release blocker, not an afterthought.
- **Cross-border transfer no longer requires a whitelist.** The original s129(1) Ministerial whitelist mechanism was deleted by A1727 item 12 (effective 1 April 2025). Realistic engineering basis for routine cloud-region or SaaS-vendor processing is **s129(3)(f) due diligence** — vendor DPA + cert audits (ISO 27001 / SOC 2) + a documented assessment, kept current.
- **Sensitive personal data now includes biometric data** (s4 as amended). Anything resulting from technical processing of physical, physiological, or behavioural characteristics — face embeddings, fingerprint hashes, voice prints, gait patterns — is treated as sensitive and requires **explicit consent** under s40(1)(a). On-device biometrics that never cross the wire are out of scope; any embedding that crosses to your server is in.
- **Breach detection is now a functional requirement.** Pre-2024 there was no statutory breach-notification clock. Post-1 June 2025, your detection and triage pipeline has to be reliable enough to support a 72-hour Commissioner notification (s12B(1) + JPDP Guideline) — make sure logging, alerting, and on-call rotations can carry that weight.

## Cross-references

- [`../../checklists/`](../../checklists/) — entry points for common engineering tasks; reference the universal layers + this jurisdiction's obligations.
- [`../sg-pdpa/README.md`](../sg-pdpa/README.md) — Singapore PDPA, the closest neighbour by structure (both are SEA principle-based regimes); divergences listed in [`../_index.md`](../_index.md).
- [`templates/INCIDENT_RESPONSE.md.template`](../../templates/INCIDENT_RESPONSE.md.template) — runbook template; for MY, the operational clock to encode is **72 hours to Commissioner / 7 days to subjects**.
