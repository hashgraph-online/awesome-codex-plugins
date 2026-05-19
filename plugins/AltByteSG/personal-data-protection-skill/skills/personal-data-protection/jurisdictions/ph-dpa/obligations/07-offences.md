# Criminal Offences and Penalties — §§ 25–37 RA 10173

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

PH treats data privacy violations as **criminal offences** with personal prison time, in addition to corporate fines. § 34 makes the **responsible officers personally liable** for offences committed by juridical persons. § 35 aggravates penalties to the maximum period when at least 100 data subjects are affected. The combination — personal prison time, aggravation by scale, and a discrete concealment offence — is the most punitive criminal regime among the four SEA jurisdictions covered in this skill.

## Engineering implications, up front

- **Engineering managers, security leads, DPOs, and developers with production access can serve prison time** for offences committed in the corporate context (§ 34). The "I was just following instructions" defence does not work where the officer participated in or by gross negligence allowed the act.
- **The 100-person aggravation threshold (§ 35) is low.** Almost any production breach in a consumer-facing app meets it. Aggravation pushes the penalty to the **maximum period** of the underlying offence — for SPI processing, that's the top of 6 years and ₱4M.
- **Concealment is its own offence (§ 30).** Delay-to-investigate during a real breach is the textbook trap.
- **Corporate fines stack with personal prison terms** — the company pays the fine and the officer serves the time. They are not alternatives.

## §§ 25–32 — The principal offences

| § | Offence | Personal prison | Personal fine (₱) | Engineering scenario |
|---|---|---|---|---|
| **25(a)** | Unauthorised processing of PI | 1–3 years | ₱500k–₱2M | Processing without a § 12 lawful basis (no valid consent, no contract, no legal obligation, etc.) |
| **25(b)** | Unauthorised processing of SPI | **3–6 years** | **₱500k–₱4M** | Processing SPI without a § 13 basis. The textbook PH case: collecting government IDs (PhilSys / SSS / TIN) without explicit consent. |
| 26(a) | Negligent access (PI) | 1–3 years | ₱500k–₱2M | Access by negligence — weak access controls, mis-configured RLS, leaky API endpoint |
| 26(b) | Negligent access (SPI) | 3–6 years | ₱500k–₱4M | Same, on SPI tables. Compounded with § 25(b) where the access enabled processing |
| 27 | Improper disposal | 6 months–3 years | ₱100k–₱1M | End-of-retention disposal mishandled — paper records discarded without shredding, drives sold without secure wipe, S3 buckets deleted without audit |
| 28 | Processing for unauthorised purposes | 1.5–7 years | up to ₱2M | Function creep — data collected for purpose A used for purpose B without re-notice / re-consent |
| 29 | Unauthorised access or intentional breach | 1–3 years | ₱500k–₱2M | Breaking access controls intentionally. Includes insider threat — staff browsing personal data for non-work reasons |
| **30** | **Concealment of breaches** | **1.5–5 years** | **₱500k–₱1M** | Knowing of a breach, knowing the § 20(f) duty to notify, and failing to do so within 72h. See [06-breach-notification.md](06-breach-notification.md). |
| 31 | Malicious disclosure | 1.5–5 years | ₱500k–₱1M | Disclosure with malice or in bad faith — leaking customer data to a competitor, posting to social media, leaking to journalists for personal motive |
| 32 | Unauthorised disclosure | 1–5 years | ₱500k–₱2M | Disclosure to a recipient not covered by the notice. Includes vendor over-sharing, mis-routed exports, weak DSR identity verification leading to disclosure to the wrong person |

**Implementation layer:** the offences are evidentiary endpoints — they crystallise when the underlying control fails. The proactive engineering work happens in [02 Architecture](../../../layers/02-architecture.md) (security), [04 Controls and processes](../../../layers/04-controls-and-processes.md) (access control, audit logging), and [07 Operational](../../../layers/07-operational.md) (incident response).

## § 33 — Combination or series of acts

**Rule (verbatim):** *"The penalty of imprisonment ranging from three (3) years to six (6) years and a fine of not less than One million pesos (Php1,000,000.00) but not more than Five million pesos (Php5,000,000.00) shall be imposed on persons who, in violation of the rights of the data subjects, commits any of the following acts: (a) Failure to register; or (b) Combination or series of acts as defined in Sections 25 to 32."*

Wait — the actual structure is that § 33 separates two scenarios. The combined-acts scenario carries the highest penalty range below the aggravated maximum. **A single incident with multiple offences** (e.g., unauthorised SPI processing + negligent access + unauthorised disclosure + concealment) is the textbook § 33 case.

## § 34 — Extent of liability (officer / employee personal liability)

**Rule (verbatim):** *"If the offender is a corporation, partnership or any juridical person, the penalty shall be imposed upon the responsible officers, as the case may be, who participated in, or by their gross negligence, allowed the commission of the crime."*

The section then specifies that:
- If the offender is a **juridical person**, the **fine** is paid by the entity AND the **prison terms** are served by the responsible officers.
- If the offender is an **alien**, deportation follows service of sentence.
- If the offender is a **public official or employee**, perpetual or temporary absolute disqualification from public office is imposed.

**Practical effect:** a breach by the company is a breach by the responsible officers. "Responsible officers" includes:
- Directors and corporate officers who participated in the decision-making.
- The DPO who knew of the obligation and did not act.
- **Engineering managers, security leads, and developers with production access** who participated in the act or by gross negligence allowed it.

**Engineering surface:**
- Decision log: every meaningful access-control decision, vendor onboarding decision, retention-rule decision, and incident-response decision should produce a record of who decided and why. This is both the due-diligence defence and the evidence of who is "responsible" if the case turns the wrong way.
- Change management: code changes that affect personal-data handling go through review with named approvers. The reviewer accepts a slice of § 34 exposure when they approve.
- Access provisioning: who has production data access, why, and when was it last reviewed. Inactive accounts with production access are textbook gross-negligence exposure.

## § 35 — Large-scale aggravation

**Rule (verbatim):** *"The maximum penalty in the scale of penalties respectively provided for the preceding offenses shall be imposed when the personal information of at least one hundred (100) persons is harmed, affected or involved as the result of the above mentioned actions."*

**Practical effect:** at ≥ 100 affected data subjects, the penalty for the underlying offence is imposed in its **maximum period** — the top of the range. For § 25(b) SPI processing, that's the top of 6 years and ₱4M per offence.

**Engineering reality:** any consumer-facing PH app with a real user base will exceed 100 in any meaningful breach. § 35 aggravation is the operational baseline, not the exception.

## § 36 — Public officers

**Rule (summary):** when the offender is a public officer, additional disqualification from public office is imposed in addition to the criminal penalty.

Most consumer-app engineering teams will never engage § 36, but where the team includes contractors or secondees from public agencies, the disqualification consequence is in scope.

## § 37 — Restitution

**Rule (summary):** *"In addition to the criminal penalties prescribed in this Act, the courts may impose such restitution to the offended party for damages suffered as a result of the violation."*

**Practical effect:** civil indemnity to the affected data subjects on top of the criminal fines. Combines with the § 16(g) civil right to damages (see [04-access-correction.md](04-access-correction.md)) to give data subjects a meaningful enforcement route independent of the NPC.

## What's at stake — the cumulative picture

A typical breach scenario in a PH consumer app:
- 50,000 users affected, including SPI (PhilSys numbers, health records).
- Root cause: mis-configured RLS allowing one tenant to read another tenant's records.
- Discovery via a customer report; investigation took 5 days; notification delayed past the 72-hour window.

The criminal exposure stack:
- § 25(b) unauthorised SPI processing — engaged by the cross-tenant access.
- § 26(b) negligent access to SPI — engaged by the mis-configured RLS.
- § 30 concealment — engaged by the missed 72-hour clock.
- § 33 combination — engaged by the multiple offences.
- § 35 aggravation — engaged by the 50,000 > 100 threshold; penalties in maximum period.
- § 34 officer liability — engaged for the responsible engineering manager(s), security lead(s), and DPO.
- § 37 restitution — civil indemnity to affected users on top.

The **organisational fines** under §§ 25(b) + 26(b) + 30 + 33 in the maximum period stack to the upper-tens-of-millions of pesos. The **personal prison time** for the responsible officers (combining the § 25(b), § 26(b), § 30 exposures in the maximum period under § 35) reaches the **decade range** in cumulative theoretical maxima — courts ordinarily impose lower combined sentences, but the exposure surface is real.

This is why the engineering invariants matter — least privilege by default, audit-logged SPI access, retention sweeps, vendor due diligence, and a runbook that triggers the 72-hour clock on first credible signal. The criminal regime under PH DPA is not a paperwork concern; it is a personal-liability concern for everyone with production access.

## Defences and mitigation

The Act does not codify a "due diligence" defence in the same way as MY § 133, but in practice:
- The audit trail (consent records, decision logs, access reviews, vendor due-diligence files) is the evidence that supports a "no participation, no gross negligence" position under § 34.
- Prompt notification under § 20(f) / § 38 IRR is a critical mitigation — concealment under § 30 typically attracts heavier court treatment than the underlying breach.
- Cooperation with the NPC during investigation, voluntary remediation, and proactive support to affected data subjects (credit monitoring, identity-restoration assistance) reduce both criminal exposure and civil quantum.

The combination of personal prison time, a wide officer-liability surface, the 100-person aggravation threshold, and a discrete concealment offence makes PH the **single highest-stakes criminal regime among the four SEA jurisdictions covered in this skill**. Plan accordingly.
