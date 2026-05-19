# Sections 21–23, 25 — Purpose Limitation, Data Minimization, Notification of Purpose

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

## Section 21 — Purpose limitation

**Rule:** *"The Data Controller shall collect, use, or disclose Personal Data according to the purpose notified to the data subject prior to or at the time of such collection."*

**No new purpose** without:
1. Informing the data subject of the new purpose AND obtaining consent prior to the new use, OR
2. Permission under the Act or other law.

**Implementation layer:** [06 Disclosure](../../../layers/06-disclosure.md) (privacy policy purposes table).

**Operationalisation:**
- Maintain a privacy policy purposes table with one row per purpose and the lawful basis (s24 reference) for each
- Every new feature touching Personal Data: map its uses to existing purposes, OR update the policy to add a new purpose **before** launching
- No re-purposing of existing data without fresh consent

## Section 22 — Data minimization

**Rule (verbatim):** *"The collection of Personal Data shall be limited to the extent necessary in relation to the lawful purpose of the Data Controller."*

**Implementation layer:** [03 Data model](../../../layers/03-data-model.md), [05 Feature/UX](../../../layers/05-feature-ux.md).

**Operationalisation:**
- For each new field collected: justify against a stated purpose. If you can't articulate why you need it, you probably can't lawfully collect it.
- Periodic data-inventory audits to identify fields collected but not actually used — these should be removed
- Default to less: short retention, shorter precision (city instead of GPS coordinates), aggregate instead of identifying where possible

## Section 23 — Notification of purpose

**Rule:** the Data Controller must inform the data subject **prior to or at the time of collection** of:

1. **Purpose** of the collection / use / disclosure (including any s24 exception relied on)
2. **Notification** of cases where the data subject must provide the data for compliance with a law / contract, with the **possible effect** of not providing
3. **Categories of Personal Data** collected and the **retention period** (or expected retention if exact period not possible)
4. **Categories of recipients** to whom data may be disclosed
5. **Contact details** of the Data Controller (and representative / DPO where applicable)
6. **Rights of the data subject** under s19 paragraph 5, s30, s31, s32, s33, s34, s36, s73 paragraph 1

**Implementation layer:** [06 Disclosure](../../../layers/06-disclosure.md).

**Operationalisation:**
- Privacy policy covers all six items
- Per-feature contextual notices when new data is collected (camera permission, location access, etc.)
- The DPO contact must be exposed proactively (publishing satisfies "on request")

**Exception:** notice not required where the data subject already knows the details.

## Section 25 — Notice when collecting from other sources

See [02-consent.md](02-consent.md) for the consent / lawful basis aspect. The s23 notification requirement applies mutatis mutandis to data collected from third-party sources, with the **30-day window** for notification (and exceptions for impossibility, urgency, professional confidentiality).

## What this looks like in practice

The privacy policy purposes table is the canonical artifact. A typical Thai-PDPA-aligned table:

| Purpose | Lawful basis (s24) | Categories of data |
|---|---|---|
| Account creation and authentication | (3) Contractual necessity | Email, password hash, name |
| Providing the service | (3) Contractual necessity | All service-related data |
| Country / language detection | (1) Consent at signup OR (5) Legitimate interests | IP-derived locale |
| Notification delivery | (1) Consent | Push token, contact details |
| Crash reporting / performance | (5) Legitimate interests | Anonymised crash data |
| Abuse moderation | (5) Legitimate interests | Reports, content metadata |
| Compliance with law (court orders, regulatory requests) | (6) Legal obligation | As required |
| Sensitive data (health, biometrics, etc.) | (1) Explicit consent under s26 | Per-category |

**Update discipline:** when a layer 03–05 change introduces a new purpose, the table updates in the **same PR**. Drift between code and the purposes table is one of the most common audit findings.

## Penalty exposure (this Part)

| Failure | Maximum administrative fine | Source |
|---|---|---|
| Fails s23 notification | THB 1M | s82 |
| Violates s21 (purpose limitation) | THB 3M | s83 |
| Violates s22 (data minimization) | THB 3M | s83 |
| Violates s25 paragraph 1 (collection from other source without notification / consent) | THB 3M | s83 |
| Obtains consent by deceiving about purpose | THB 3M | s83 |
