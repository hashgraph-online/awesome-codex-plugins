# Offences and Penalties — s5(2), s12B(3), s40(3), s129(5), s130, s133

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

MY PDPA backs every Principle with a discrete offence rather than a general civil penalty regime. The 2024 Amendment (A1727) raised the principle-breach maximum and introduced two new offences (breach-notification failure, and the data-portability obligation in s43A operates via s5(2) by extension of the Access Principle).

## s5(2) — Principle breach (amended 2024)

**Rule (verbatim):** *"Subject to sections 45 and 46, a data controller who contravenes subsection (1) commits an offence and shall, on conviction, be liable to a fine not exceeding one million ringgit or to imprisonment for a term not exceeding three years or to both."* (s5(2) as amended by A1727 item 4(b))

**Pre-amendment (before 1 April 2025):** RM 300,000 / 2 years. **Post-amendment:** **RM 1,000,000 / 3 years**.

**Scope:** any breach of any of the seven Principles (General s6; Notice & Choice s7; Disclosure s8; Security s9; Retention s10; Data Integrity s11; Access s12) — **and**, post-A1727 item 4(a), a data processor's breach of s9 via s5(1A) carries the same penalty.

## s12B(3) — Failure to notify breach (new 2024)

**Rule (verbatim):** *"A data controller who contravenes subsection (1) commits an offence and shall, on conviction, be liable to a fine not exceeding two hundred and fifty thousand ringgit or imprisonment for a term not exceeding two years or to both."*

Triggered by failure to notify the Commissioner under s12B(1). Subject-notification (s12B(2)) failure is not separately criminalised but feeds into the body-corporate-liability assessment.

## s40(3) — Sensitive personal data breach

**Rule (verbatim):** *"A person who contravenes subsection (1) commits an offence and shall, on conviction, be liable to a fine not exceeding two hundred thousand ringgit or to imprisonment for a term not exceeding two years or to both."*

Triggered by processing sensitive personal data (now including **biometric data** post-A1727) without explicit consent or another s40(1)(b)/(c) basis. **Lower than the principle-breach maximum** despite addressing more sensitive data — this is a 2010 calibration that was not lifted by the 2024 amendments.

## s129(5) — Cross-border transfer breach

**Rule (verbatim):** *"A data controller who contravenes subsection (1) commits an offence and shall, on conviction, be liable to a fine not exceeding three hundred thousand ringgit or to imprisonment for a term not exceeding two years or to both."*

Note: as amended (A1727 item 12), the substantive prohibition lives in the post-amendment s129 conditions framework. Penalty unchanged at **RM 300,000 / 2 years**.

## s130 — Unlawful collecting / sale of personal data

**Rule (summary):** s130(1) criminalises *"knowingly or recklessly, without the consent of the data user"*, collecting / disclosing / procuring disclosure of personal data held by another data controller. s130(5) extends to offering personal data for sale.

**Penalty (s130(7)):** **RM 500,000 / 3 years**.

**Practical effect:** this targets external bad actors (data brokers, scrapers, fraudsters) but also engages where a **departing employee** scrapes user records on the way out. Ensure offboarding revokes credentials immediately and audit-logs cover bulk read/export operations.

## s131 — Abetment and attempt

A person who abets or attempts an offence under the Act is liable to the same penalty (s131(1)). Preparatory acts are punishable up to half the maximum imprisonment term (s131(2)).

## s132 — Compounding

The Commissioner, with the Public Prosecutor's written consent, may compound any compoundable offence by accepting up to **50% of the maximum fine** in lieu of prosecution.

**Practical effect:** in practice, many enforcement actions resolve via compounding rather than prosecution. The willingness of the regulator to compound is influenced by the controller's evidence trail (DPO appointment, breach-register quality, remediation steps taken).

## s133 — Offences by body corporate [critical for engineering leadership]

**Rule (verbatim):** *"If a body corporate commits an offence under this Act, any person who at the time of the commission of the offence was a director, chief executive officer, chief operating officer, manager, secretary or other similar officer of the body corporate or was purporting to act in any such capacity or was in any manner or to any extent responsible for the management of any of the affairs of the body corporate or was assisting in such management — (a) may be charged severally or jointly in the same proceedings with the body corporate; and (b) if the body corporate is found to have committed the offence, shall be deemed to have committed that offence unless, having regard to the nature of his functions in that capacity and to all circumstances, he proves — (i) that the offence was committed without his knowledge, consent or connivance; and (ii) that he had taken all reasonable precautions and exercised due diligence to prevent the commission of the offence."*

**Practical effect:** **deemed liability**, not gatekeeper liability. Where the body corporate is convicted, the named officers are presumed to have committed the offence; the burden flips to the officer to prove the two-part defence (no knowledge AND due diligence).

**The "all reasonable precautions and due diligence" defence is the single most important reason engineering teams keep good records.** Without:
- Written security policy approved by the leadership;
- DPO appointment and registration (s12A);
- Documented risk assessments;
- Breach register;
- Vendor inventory and DPAs;
- Audit logs for sensitive-data access;
- Training records;

…there is no evidence to anchor the defence. With them, a director facing the s133 deeming provision has something to point to.

**s133(2)** also extends liability via the act of an employee or agent acting in the course of employment / on behalf of the controller. The principal is liable for the employee's breach under the same head of penalty. Mitigations: AUP, training, monitoring, documented disciplinary action when an employee breaches.

## s134 — Prosecution by Public Prosecutor's consent only

No prosecution under the Act is instituted except by or with the written consent of the Public Prosecutor. This is a procedural filter that practically directs cases through compounding-first.

## What's at stake — at-a-glance

| Offence | Section | Maximum fine | Maximum imprisonment |
|---|---|---|---|
| Principle breach (any of s6–s12) | s5(2) | RM 1,000,000 | 3 years |
| Failure to notify breach to Commissioner | s12B(3) | RM 250,000 | 2 years |
| Sensitive personal data breach | s40(3) | RM 200,000 | 2 years |
| Cross-border transfer breach | s129(5) | RM 300,000 | 2 years |
| Unlawful collecting / sale of personal data | s130(7) | RM 500,000 | 3 years |
| Non-compliance with applicable code of practice | s29 | RM 100,000 | 1 year |
| Abetment / attempt | s131 | as for the underlying offence | as for the underlying offence (≤½ for preparatory acts) |
| Body-corporate liability — directors / officers deemed | s133 | as for the underlying offence | as for the underlying offence |

The penalty calibration is **per offence**, not annual-turnover-based (unlike SG-PDPA's s48J(3) 10%-turnover ceiling). Multiple breaches stack.

## Mental model

- **Most engineering-relevant routes to penalty: s5(2) Security + s12B(3) breach notification + s40 sensitive data.** These are where typical incidents land.
- **Director liability is real and is deeming, not gatekeeper.** The engineering audit trail is the input to the s133 defence.
- **Compounding is the realistic resolution path.** The regulator's willingness to compound is shaped by the evidence trail, not the underlying severity alone.
- **Corporate / personal exposure is parallel.** A single breach can land the body corporate **and** the responsible officer simultaneously under s133(1).
