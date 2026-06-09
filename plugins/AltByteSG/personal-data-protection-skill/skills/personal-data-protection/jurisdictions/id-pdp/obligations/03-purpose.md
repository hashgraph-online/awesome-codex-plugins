# Pasal 16, 21, 27, 28 — Purpose Limitation, Processing Principles, Notification

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

## Pasal 16(2) — Personal Data protection principles

**Rule:** Personal Data processing must observe these principles:

a. **Limited and specific** — collected for limited and specific purposes, lawfully and transparently
b. **Aligned with purpose** — processed in accordance with the notified purpose
c. **Guaranteeing Subject's rights** — processing guarantees the Data Subject's rights
d. **Accurate, complete, not misleading, current, accountable** — quality standard
e. **Secured** — protected from unauthorised access, disclosure, alteration, loss
f. **Transparent** — purpose, processing activities, AND any failure of Personal Data protection are notified
g. **Retained per schedule** — destroyed / erased after retention period or on Data Subject request, unless otherwise provided
h. **Responsible and demonstrable** — accountable + provable

**Implementation layers:** [02 Architecture](../../../layers/02-architecture.md), [04 Controls](../../../layers/04-controls-and-processes.md), [03 Data model](../../../layers/03-data-model.md), [06 Disclosure](../../../layers/06-disclosure.md), [05 Feature/UX](../../../layers/05-feature-ux.md).

This is the foundational principles list — every more specific obligation in BAB VI flows from one of these. When designing a feature, the principles serve as a checklist: which of the 8 does this feature implicate, and does the design satisfy each?

## Pasal 27 — Limited, specific, lawful, transparent

**Rule:** the Controller must process Personal Data in a **limited and specific** manner, **lawfully**, and **transparently**.

This restates Pasal 16(2)(a) as a binding obligation on the Controller specifically. Notable for the **specificity** requirement — generic "we may use your data for various purposes" wording in privacy policies is non-compliant.

**Implementation layer:** [06 Disclosure](../../../layers/06-disclosure.md).

## Pasal 28 — Purpose limitation

**Rule:** the Controller must process Personal Data **in accordance with the purpose of the processing**.

This is the "no re-purposing without fresh consent" rule. New uses of existing data require:
- Either a new consent under Pasal 20(2)(a), OR
- Reliance on a different Pasal 20 lawful basis that covers the new use

**Implementation layer:** [06 Disclosure](../../../layers/06-disclosure.md), [05 Feature/UX](../../../layers/05-feature-ux.md).

**Operationalisation:**
- Maintain a privacy policy purposes table mapping each purpose to the chosen Pasal 20 basis
- New feature → identify whether its data uses fit existing purposes, or require updating the policy + (where relying on consent) re-consenting users
- Document in a lawful-basis register

## Pasal 21 — Notification at consent

See [02-consent.md](02-consent.md). Briefly: when processing is based on consent (Pasal 20(2)(a)), the Controller must inform the Subject of 7 items at the time of consent — covering lawful basis, purpose, data categories, retention, information collected, processing duration, and Subject rights.

**Update on change (Pasal 21(2)):** the Controller must **notify before** any of this information changes. This is a positive obligation — silent change is non-compliant.

## Pasal 17 — Public-area visual processing systems (CCTV-style)

**Rule:** installation of visual data processing systems in public areas / public service facilities is permitted with these conditions:

a. **Only for** security, disaster prevention, **traffic information** collection / analysis / management
b. **Must display information** that the area has visual processing systems (signage)
c. **Not used for personal identification** of individuals

**Exceptions** (Pasal 17(2)): conditions (b) and (c) can be waived for crime prevention and law enforcement.

This is uncommon in privacy statutes — Indonesia explicitly addresses CCTV. **If your application involves any kind of visual capture in public spaces** (smart city sensors, public-facing cameras, etc.), Pasal 17 binds you regardless of consent.

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md), [06 Disclosure](../../../layers/06-disclosure.md) (signage requirement).

## Pasal 18 — Joint Controllers

**Rule:** Personal Data processing may be done by 2 or more Controllers jointly. When so, the Controllers must minimum:

a. Have an **agreement** specifying roles, responsibilities, and the relationship between Controllers
b. Have **interrelated purposes** and jointly determined processing methods
c. Have a **jointly-appointed contact**

**Implementation layer:** [01 Non-technical](../../../layers/01-non-technical.md) (joint-controller agreement).

This is similar to GDPR Article 26. Common scenario: a marketing partner where both your company and the partner determine the processing.

## What this looks like in practice

A canonical privacy policy purposes table for an Indonesia-targeting application:

| Purpose | Lawful basis (Pasal 20) | Categories of data | Retention |
|---|---|---|---|
| Account creation, authentication | (b) Contractual necessity | Email, password hash, name | Until account deletion |
| Service delivery | (b) Contractual necessity | All service-related data | Until account deletion + retention period |
| Country / language detection | (a) Consent at signup, OR (f) Legitimate interests | IP-derived locale | Discarded after detection |
| Notification delivery | (a) Consent | Push token, contact details | Until consent withdrawn |
| Crash reporting | (f) Legitimate interests | Anonymised stack traces | 90 days (typical vendor retention) |
| Sensitive ("specific") data — when applicable | (a) Explicit consent under Pasal 20(2)(a) + Pasal 22 | Per category | Per retention schedule |
| Compliance with legal orders | (c) Legal obligation | As required | As required |
| Security incident investigation | (f) Legitimate interests OR (c) Legal obligation | Logs, account metadata | 30–90 days typical |

**Update discipline:** a layer 03–05 change introduces a new purpose → table updates in the **same PR**. Drift between code and the purposes table is one of the most common audit findings.

## Penalty exposure (this Part)

| Failure | Source |
|---|---|
| Pasal 27 (limited, specific, lawful, transparent) | Pasal 57 administrative sanctions — ceiling 2% revenue |
| Pasal 28 (purpose limitation) | Pasal 57 |
| Pasal 21 (notification at consent) | Pasal 57 |
