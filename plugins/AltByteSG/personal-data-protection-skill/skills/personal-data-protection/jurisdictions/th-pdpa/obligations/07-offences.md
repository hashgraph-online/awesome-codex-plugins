# Chapter VII — Penalties (Sections 79–90)

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

Thailand PDPA splits penalties into **criminal** (Part I) and **administrative** (Part II). Personal liability for directors and managers under s81 makes the criminal layer especially important.

## Part I — Criminal Liability (Sections 79–81)

### Section 79 — Sensitive-data misuse (criminal)

**Two-tier criminal offence** for Data Controllers who violate s27 paragraph 1 / 2 (use or disclosure without consent) OR fail to comply with s28 (cross-border transfer rules), **specifically involving s26 sensitive Personal Data**:

| Aggravating factor | Maximum penalty |
|---|---|
| Likely to cause damage, impair reputation, or expose to scorn / hatred / humiliation | **Imprisonment ≤ 6 months + fine ≤ THB 500,000**, or both |
| In order to unlawfully benefit oneself or another person | **Imprisonment ≤ 1 year + fine ≤ THB 1,000,000**, or both |

**Compoundable offences** under this section — the prosecution may be settled.

**Implementation layers:** [01 Non-technical](../../../layers/01-non-technical.md) (staff AUP), [04 Controls](../../../layers/04-controls-and-processes.md) (admin audit log).

### Section 80 — Unauthorised disclosure by duty-holders (criminal)

**Rule:** any person who comes to know Personal Data of another in the course of performing duties under this Act, and discloses it to any other person, is criminally liable.

**Penalty:** imprisonment ≤ 6 months, fine ≤ THB 500,000, or both.

**Exceptions** (disclosure not punishable):
1. Performance of duty
2. Benefit of an investigation or trial
3. Disclosure to a domestic / foreign government agency with legal authority
4. Written consent of the data subject for the specific occasion
5. Open court proceedings

**Practical scenarios:**
- A Competent Official, expert committee member, or staff of the Office disclosing data acquired in their role
- A vendor / sub-processor employee disclosing customer data
- An admin disclosing a user's chat content to a third party

**Implementation layer:** [01 Non-technical](../../../layers/01-non-technical.md) (staff AUP, contractor confidentiality clauses).

### Section 81 — Personal liability for directors / managers

**Rule (paraphrased):** when an offence under this Act is committed by a juristic person AND the offence resulted from the **instructions or acts** of a director / manager / responsible person, OR from that person's **omission to instruct or perform a required act**, **that individual is also punished** with the same penalty as the offence.

**Practical effect:**
- The corporate offence can be stacked with personal criminal liability for the responsible individual
- "Omission" liability is broad — failing to instruct / supervise where one had a duty to do so triggers liability
- The organisation **cannot indemnify** a criminal sanction

**Compared to Singapore PDPA s48D/E/F:** Thai s81 is broader. SG's offences require knowledge or recklessness about a specific act of disclosure / misuse / re-identification. Thai s81 catches negligent failure to supervise.

**Implementation layer:** [01 Non-technical](../../../layers/01-non-technical.md).

**Operationalisation:**
- Directors / managers / DPO must understand they are personally liable for failure to operate the compliance program
- Document compliance decisions (audit trail, training records, policy acknowledgements) so individual responsibility can be evidenced
- Insurance for individual criminal liability is generally not available; behaviour discipline is the only mitigation

## Part II — Administrative Liability (Sections 82–90)

Administrative fines are imposed by the **expert committee** appointed by PDPC. The committee may issue a rectification order or warning **before** imposing a fine (s90). Three tiers based on the nature of the violation:

### THB 1 million tier (Section 82) — procedural

For the Data Controller failing:
- s23 (notification of purpose at collection)
- s30 paragraph 4 (30-day access response)
- s39 paragraph 1 (records)
- s41 paragraph 1 (DPO designation)
- s42 paragraph 2 / 3 (DPO support / non-dismissal)
- s19 paragraph 3 (consent form requirements)
- s19 paragraph 6 (impact-of-withdrawal notice)
- s23 mutatis mutandis under s25 paragraph 2 (notification when collecting from other source)

### THB 3 million tier (Section 83) — substantive

For the Data Controller violating:
- s21 (purpose limitation)
- s22 (data minimization)
- s24 (lawful basis for collection)
- s25 paragraph 1 (collection from other source)
- s27 paragraph 1 / 2 (use or disclosure without consent — general data)
- s28 (cross-border transfer — general data)
- s32 paragraph 2 (immediate cessation on objection)
- s37 (Data Controller duties — general)
- Obtaining consent by deceiving / misleading about purpose
- s21 mutatis mutandis under s25 paragraph 2
- s29 paragraph 1 / 3 (intra-group transfer — general data)

### THB 5 million tier (Section 84) — sensitive data

For the Data Controller violating, **involving s26 sensitive Personal Data**:
- s26 paragraph 1 / 3 (sensitive data without explicit consent or per exceptions)
- s27 paragraph 1 / 2 (use or disclosure without consent)
- s28 (cross-border transfer)
- s29 paragraph 1 / 3 (intra-group transfer)

### Sections 85–87 — Data Processor fines

Same three-tier structure for Data Processors:
- s85 (THB 1M): fails s41 paragraph 1 (DPO) or s42 paragraph 2 / 3 (DPO support)
- s86 (THB 3M): fails s40 (processor duties) without appropriate reasons; fails s29 paragraph 1 / 3; fails s37(5) representative
- s87 (THB 5M): fails s29 paragraph 1 / 3 involving sensitive data (s26)

### Section 88 — Representative fines

Fines apply to a representative of the Data Controller / Processor (THB 1M for failing record-keeping or DPO requirements applied mutatis mutandis).

### Section 89 — Procedural / cooperation fines

THB 500,000 for:
- Failing to comply with an order from the expert committee
- Failing to provide a statement of facts under s75
- Failing to comply with s76(1) (cooperation with the Office)
- Failing to facilitate Competent Officials under s76 paragraph 4

### Section 90 — Penalty calculation factors

The expert committee considers:
- **Severity of the offence** (nature, gravity)
- **Size of the business** of the Data Controller / Processor
- Other circumstances per Committee rules

The committee **may issue a rectification order or warning first** before imposing a fine. This means demonstrable cooperation and rapid remediation can avoid or reduce the fine.

## Penalty cap calculation in practice

Compared to Singapore PDPA's single-tier cap (SGD 1M / 10% turnover), Thailand's tiered structure aligns penalty severity with violation severity. Key implications:

- **Sensitive-data violations (THB 5M cap)** carry the highest risk and warrant the strongest controls — admin audit, explicit consent, stricter access patterns
- **Procedural failures (THB 1M cap)** are still meaningful but the lower tier reflects that record-keeping / DPO failures are typically symptoms of broader gaps
- **No turnover-based cap** — the absolute fine cap is the same regardless of organisation size, but s90 explicitly considers organisation size in the calculation, so smaller orgs typically face proportionally smaller fines

## Mental model

Three concepts to internalise:

1. **Civil + administrative + criminal layers stack.** s77–78 (civil), s82–90 (administrative), s79–81 (criminal). The same incident can trigger all three.

2. **Personal liability is broader than Singapore's** — s81 catches omissions, not just active misuse. Directors and managers must demonstrably operate the compliance program, not just delegate it.

3. **Sensitive data triples the fine cap** — auditing your data inventory for s26 sensitive categories is the single highest-leverage compliance investment under Thai law.

## Cross-references

- [02-consent.md](02-consent.md) — sensitive data (s26) and explicit consent
- [05-care.md](05-care.md) — security measures and cross-border transfer
- [01-accountability.md](01-accountability.md) — DPO designation, records
- [01 Non-technical](../../../layers/01-non-technical.md) — staff AUP and director / manager responsibilities
