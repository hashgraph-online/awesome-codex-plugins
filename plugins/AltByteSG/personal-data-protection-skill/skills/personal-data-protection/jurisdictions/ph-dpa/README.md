# Philippines DPA — Jurisdiction Notes

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

| | |
|---|---|
| **Statute** | Data Privacy Act of 2012 (Republic Act No. 10173) |
| **Current text reflected** | RA 10173 as in force at the last verification date, read with the NPC Implementing Rules and Regulations (IRR) of 2016 and operative NPC Circulars |
| **Last verified** | 2026-05-14 |
| **Most recent material amendment** | RA 10173 itself has not been amended; substantive change happens through NPC Circulars and Advisories. Recent operative circulars include NPC Circular 16-03 (Personal Data Breach Management) and NPC Circular 2022-04 (rules on the exercise of data subject rights) |
| **Regulator** | National Privacy Commission (NPC) — [privacy.gov.ph](https://privacy.gov.ph) |
| **Statute on the Official Gazette** | [officialgazette.gov.ph — RA 10173](https://www.officialgazette.gov.ph/2012/08/15/republic-act-no-10173/) |
| **NPC Implementing Rules and Regulations (IRR), 2016** | [privacy.gov.ph — IRR](https://privacy.gov.ph/implementing-rules-and-regulations-of-republic-act-no-10173-known-as-the-data-privacy-act-of-2012/) |
| **NPC Issuances (Circulars + Advisories)** | [privacy.gov.ph/issuances](https://privacy.gov.ph/npc-issuances/) |
| **Pending amendments / guidance** | A long-discussed amendment bill has been filed in successive Congresses but has not been enacted as of the last verification date — track updates from the NPC and the Senate / House committees on ICT |

> **Source copyright:** RA 10173 is a public Act of the Congress of the Philippines and the IRR is a public regulation issued by the NPC; both are reproducible for educational and reference purposes. Verbatim quotations in this skill are short operative phrases reproduced with attribution. See [DISCLAIMER.md § Copyright in source materials](../../../../DISCLAIMER.md#copyright-in-source-materials).

## Critical thresholds

- **Breach notification to NPC: 72 hours** from knowledge of, or reasonable belief in, a personal data breach that meets the trigger (§ 38(b) IRR; NPC Circular 16-03 § 11–12). Same 72-hour clock applies to notification of affected data subjects.
- **Trigger for mandatory notification:** the breach involves (i) **sensitive personal information** or (ii) information that may be used to **enable identity fraud**, AND there is reasonable belief such information has been **acquired by an unauthorised person**, AND the unauthorised acquisition is **likely to give rise to a real risk of serious harm**. All three must be present (NPC Circular 16-03 § 11). Where only some are present the controller still keeps an internal record and the annual incident report.
- **Annual Security Incident Report** to NPC by **31 March** each year, covering all security incidents and personal data breaches (whether notifiable or not) from the preceding calendar year (NPC Circular 16-03 § 17).
- **Right-to-rights response window:** the controller must act on a data subject's request to exercise rights *"within a reasonable period"* — NPC Circular 2022-04 § 11 sets **15 calendar days** as the default, extendable once by 15 days for complex requests.
- **Maximum criminal penalties (RA 10173 §§ 25–32):**
  - Unauthorised processing of personal information — 1 to 3 years + ₱500,000 to ₱2,000,000 (§ 25(a))
  - Unauthorised processing of sensitive personal information — 3 to 6 years + ₱500,000 to ₱4,000,000 (§ 25(b))
  - Negligent access (PI) — 1 to 3 years + ₱500,000 to ₱2,000,000 (§ 26(a))
  - Negligent access (SPI) — 3 to 6 years + ₱500,000 to ₱4,000,000 (§ 26(b))
  - Improper disposal — 6 months to 3 years + ₱100,000 to ₱1,000,000 (§ 27; PI / SPI tier dependent)
  - Processing for unauthorised purposes — 1.5 to 7 years + up to ₱2,000,000 (§ 28)
  - Unauthorised access or intentional breach — 1 to 3 years + ₱500,000 to ₱2,000,000 (§ 29)
  - **Concealment of security breaches** — 1.5 to 5 years + ₱500,000 to ₱1,000,000 (§ 30)
  - Malicious disclosure — 1.5 to 5 years + ₱500,000 to ₱1,000,000 (§ 31)
  - Unauthorised disclosure — 1 to 5 years + ₱500,000 to ₱2,000,000 (§ 32)
  - **Combination or series** of the above — 3 to 6 years + ₱1,000,000 to ₱5,000,000 (§ 33)
- **Officer liability** (§ 34): where the offender is a **juridical person** (corporation, partnership, association), the **responsible officers who participated in or by their gross negligence allowed** the offence are personally liable for the prison terms above, in addition to the corporate fine.

## Application — read this first

- The Act applies to the processing of **all types of personal information** and to **any natural and juridical person** involved in personal information processing (§ 4 RA 10173). Carve-outs in § 4 cover government employee performance information, journalists, banks under specific banking laws, and processing for research purposes — read the section before relying on a carve-out.
- **Extraterritorial reach** (§ 6): the Act applies to (a) acts done or practices engaged in **within the Philippines**, (b) acts done outside the Philippines if the entity has a **link to the Philippines** (e.g., a contract entered in the Philippines, a juridical entity unincorporated but maintaining an office / branch / agency in the Philippines, or processing of personal information about Philippine citizens or residents) and (c) processing by an entity **with personal information about Philippine citizens or residents**. Practical effect: a foreign SaaS with Philippine users is in scope.
- **Personal Information Controller (PIC)** is the equivalent of a "controller"; **Personal Information Processor (PIP)** is the equivalent of a "processor". Both terms appear throughout this skill.

## Obligations covered

The obligation files in `obligations/` map the active parts of the Act and IRR to the universal layers in `../../layers/`:

| File | Statute parts | Topic |
|---|---|---|
| [01-accountability.md](obligations/01-accountability.md) | §§ 21, 22 RA 10173; §§ 14, 50 IRR | PIC accountability, vendor flow-down (engineering surface only — DPO appointment and NPC registration are paperwork, see `What's intentionally not covered` below) |
| [02-consent.md](obligations/02-consent.md) | §§ 3(b), 12, 13 RA 10173; §§ 19, 21–22 IRR | Lawful bases for PI and SPI, definition of consent, withdrawal |
| [03-purpose.md](obligations/03-purpose.md) | § 11 RA 10173; § 18 IRR | General data privacy principles (transparency, legitimate purpose, proportionality), notice content |
| [04-access-correction.md](obligations/04-access-correction.md) | § 16 RA 10173; § 34 IRR; NPC Circular 2022-04; NPC Circular 18-01 | Eight data subject rights — informed, access, rectification, erasure / blocking, object, data portability, damages, complaint |
| [05-care.md](obligations/05-care.md) | §§ 20, 21 RA 10173; §§ 25–29, 44–45 IRR; NPC Circular 16-01; § 21 RA 10173 | Security measures (organisational, physical, technical), retention, cross-border accountability |
| [06-breach-notification.md](obligations/06-breach-notification.md) | § 20(f) RA 10173; § 38 IRR; NPC Circular 16-03 | Breach assessment, 72-hour NPC + subject notification, annual incident report, concealment offence |
| [07-offences.md](obligations/07-offences.md) | §§ 25–37 RA 10173 | Criminal offences, penalty ranges, officer liability under § 34 |

The reverse-lookup index (statute / IRR / Circular section → layer + obligation file) is at [statute-map.md](statute-map.md).

## What's intentionally not covered

The following are within the regulatory surface but not engineering-relevant; this skill keeps them out to stay engineer-focused (see the [project README](../../../../README.md) on scope):

- **DPO appointment** (§ 14 IRR; NPC Advisory 2017-01) — a mandatory governance task for every PIC and PIP, regardless of size. The engineering touch-point is reduced to "the privacy notice and Data Subject Rights flow must surface a working DPO contact channel" (covered in [01-accountability.md](obligations/01-accountability.md)). Appointment, qualifications, and notification to the NPC are paperwork outside the scope of this skill.
- **Registration of Data Processing Systems with the NPC** (NPC Circular 17-01 as amended) — required where the PIC / PIP processes the personal information of at least 1,000 individuals OR meets other listed criteria. This is a paperwork obligation that does not change what the application does.
- **DPIA / Privacy Impact Assessment** (NPC Advisory 2017-03) — strongly encouraged but **not statutorily mandatory**. Where high-risk processing is in play, the controller is expected to have a PIA on file. The PIA itself is a governance artefact; the engineering inputs (data flows, risks, mitigations) are already captured by the layer files.
- **NPC enforcement and complaint procedure** (NPC Rules of Procedure) — relevant during an active complaint or enforcement action; not for ongoing compliance.

## Mental model: what makes Philippines DPA distinctive (engineering view)

If you've worked with Singapore PDPA or any of the other SEA regimes covered in this skill, the things to recalibrate when implementing an app or backend for PH users:

- **GDPR-shaped substantive surface, with PH-specific operational rules.** Lawful bases (§ 12), data subject rights (§ 16), and the controller / processor split mirror GDPR closely. The operational layer (notification windows, registration, DPIA encouragement) is set by the NPC and differs from EU practice.
- **Six lawful bases for PI (§ 12)** — consent, contract, legal obligation, vital interests, public order / national emergency, and **legitimate interests** (with a balancing test). The legitimate-interests basis is genuine and engineering-usable, unlike SG/MY which restrict consent-alternative bases to a narrower enumerated list.
- **Sensitive personal information requires its own basis under § 13** — and the SPI categories are broad: health, education, genetic, sexual life, government-issued identifiers (SSS, GSIS, TIN, PhilHealth, etc.), and more. **Government identifiers are SPI in PH but are usually plain PI in SG/MY** — design national-ID handling around the SPI tier.
- **Eight data subject rights** (§ 16 RA 10173 + NPC Circular 18-01 portability) — informed, access, rectification, erasure / blocking, object, data portability, damages, complaint. The right to **damages** is unusual: data subjects can claim civil indemnity directly under the Act. Pair the rights flow with an audit trail per request.
- **Breach trigger is information-type-driven, not harm-only.** SG/MY require an assessment of *significant harm*; PH requires assessment of *real risk of serious harm* AND specific information categories (SPI or identity-fraud-enabling info). The combined-test is narrower than ID's "always notify" but wider than SG's significant-scale gating.
- **Concealment of breaches is its own offence** (§ 30): 1.5 to 5 years prison + ₱500,000 to ₱1,000,000. The textbook trap is "we'll notify after we figure out what happened" — the clock starts on knowledge / reasonable belief, not confirmation.
- **Officer criminal liability (§ 34) is automatic for juridical-person offences** — directors, officers, or employees responsible for the act personally serve the prison term, in addition to the corporate fine. Reflect in staff AUP, change-management approval flows, and access-grant procedures.
- **No statutory cross-border transfer mechanism (no whitelist, no SCCs, no BCRs).** § 21 makes the PIC **accountable for personal information transferred to a third party** — domestically or abroad — for processing. Realistic engineering basis: vendor data-sharing / outsourcing agreements with the NPC-recommended clauses, plus documented due diligence on the recipient's controls. NPC Circular 2020-03 (data sharing agreements in the private sector) is the operative reference.

## Cross-references

- [`../../checklists/`](../../checklists/) — entry points for common engineering tasks; reference the universal layers + this jurisdiction's obligations.
- [`../sg-pdpa/README.md`](../sg-pdpa/README.md) — Singapore PDPA, the closest neighbour by structure (both are SEA principle-based regimes).
- [`../my-pdpa/README.md`](../my-pdpa/README.md) — Malaysia PDPA, similar 72-hour breach lane.
- [`templates/INCIDENT_RESPONSE.md.template`](../../templates/INCIDENT_RESPONSE.md.template) — runbook template; for PH, the operational clock to encode is **72 hours to NPC AND to affected data subjects**, with the additional **31 March annual incident report** to NPC.
