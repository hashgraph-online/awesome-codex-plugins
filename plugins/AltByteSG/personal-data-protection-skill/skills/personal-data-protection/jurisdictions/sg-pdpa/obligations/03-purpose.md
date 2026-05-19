# Part 4 Division 2 — Purpose Limitation + Notification of Purpose (s18–20)

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

## s18 — Purpose limitation

**Rule (verbatim):** an organisation *"may collect, use or disclose personal data only for purposes — (a) that a reasonable person would consider appropriate in the circumstances; and (b) that the individual has been informed of under section 20."*

**Practical effect:** every collection, use, and disclosure must map to a declared purpose. New features cannot quietly repurpose existing data.

**Implementation layers:** [06 Disclosure](../../../layers/06-disclosure.md) (privacy policy purposes table), [05 Feature/UX](../../../layers/05-feature-ux.md) (feature design).

**Operationalisation:**
- Maintain a purposes table in the privacy policy (typically section 3) with one row per purpose and the lawful basis for each
- For every new feature touching personal data, map its data uses to existing purposes — or update the policy to add a new purpose **before** launching the feature
- No re-purposing of existing data without either fresh consent or notification under s15A (see [02-consent.md](02-consent.md))

## s20(1) — Notify purpose at or before collection

**Rule (verbatim):** an organisation *"must inform the individual of — (a) the purposes for the collection, use or disclosure of the personal data, as the case may be, on or before collecting the personal data; (b) any other purpose of the use or disclosure of the personal data of which the individual has not been informed... before the use or disclosure of the personal data for that purpose; and (c) on request by the individual, the business contact information of a person who is able... to answer the individual's questions about the collection, use or disclosure of the personal data."*

**Practical effect:**
- Pre-collection notice: privacy policy + in-app permission rationales must be available before the user is asked to provide data
- Pre-new-use notice: when extending an existing data collection to a new purpose, notify before the new use begins
- DPO contact: must be exposed on request (in practice, publish proactively)

**Implementation layer:** [06 Disclosure](../../../layers/06-disclosure.md).

**Operationalisation:**
- Privacy policy lists all current purposes by category (account, content, technical, location, etc.)
- OS permission usage strings (`Info.plist`, Android rationales) plainly state the purpose for each permission
- Just-in-time UX explains the purpose at the moment of collection
- DPO contact (or equivalent) exposed in privacy policy and in-app help

## s20(2) — Inform other organisation when collecting from them without consent

**Rule:** when collecting personal data from another organisation without the individual's consent, you must provide the other organisation with sufficient information about the purpose of the collection to allow them to determine whether the disclosure complies with the Act.

**When relevant:** receiving user data from a B2B partner, data broker, or identity provider in a flow where the user hasn't directly consented to your collection.

**Operationalisation:**
- For any partner-ingest integration: document in the integration MOU or data-sharing agreement what your purposes are
- Most consumer apps don't trigger this (they collect directly from the user); flag it if a B2B integration is added later

## What this looks like in practice

The privacy policy purposes table is the canonical artefact for this Part. A typical table:

| Purpose | Lawful basis |
|---|---|
| Account creation and authentication | Contractual necessity |
| Providing the service (chat, content, events, etc.) | Contractual necessity |
| Country detection for content relevance | Consent (at signup) |
| Notification delivery | Consent |
| Crash reporting and performance monitoring | Reasonable business purpose / s17 1st Sch Pt 5 |
| Enforcing T&C (abuse moderation) | s17 1st Sch Pt 3 §1 (Legitimate Interests) |
| Compliance with legal obligations (court orders, regulatory requests) | s17 |

**Update discipline:** when a layer 03–05 change introduces a new purpose, the table updates in the same PR. Drift between code and the purposes table is one of the most common audit findings.
