# Sections 28–29, 35, 37(1)–(3), 40 — Care of Data (Accuracy, Security, Retention, Cross-Border)

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

## Section 35 — Accuracy obligation

See [04-access-correction.md](04-access-correction.md). Briefly: Personal Data must remain accurate, up-to-date, complete, and not misleading.

## Section 37(1) — Security measures

**Rule:** *"provide appropriate security measures for preventing the unauthorized or unlawful loss, access to, use, alteration, correction or disclosure of Personal Data, and such measures must be reviewed when it is necessary, or when the technology has changed in order to efficiently maintain the appropriate security and safety. It shall also be in accordance with the minimum standard specified and announced by the Committee."*

**Implementation layers:** [02 Architecture](../../../layers/02-architecture.md), [04 Controls](../../../layers/04-controls-and-processes.md), [01 Non-technical](../../../layers/01-non-technical.md).

PDPC Thailand has issued subordinate notifications setting the minimum security standard. **Verify the current text at [pdpc.or.th](https://www.pdpc.or.th)** — it specifies controls at the administrative, physical, and technical level. Common requirements include:
- Access controls (least-privilege, role-based)
- Encryption (in transit and where appropriate at rest)
- Audit logging
- Periodic security review when technology changes
- Documented information security policy

## Section 37(2) — Onward-disclosure protection

**Rule:** when sharing Personal Data with other parties, the Data Controller must take action to **prevent unlawful or unauthorised use / disclosure** by those recipients.

**Implementation layers:** [01 Non-technical](../../../layers/01-non-technical.md) (DPAs), [04 Controls](../../../layers/04-controls-and-processes.md) (sub-processor dispatch sanitisation).

## Section 37(3) — Retention examination system

See [01-accountability.md](01-accountability.md). Briefly: a system to detect and act on Personal Data that should be erased — when retention period ends, when no longer relevant, when consent withdrawn.

## Section 28 — Cross-border transfer

**Rule:** the destination country or international organisation receiving Personal Data must have **adequate Personal Data protection standards** as prescribed by PDPC, EXCEPT in 6 enumerated cases:

1. **Compliance with the law**
2. **Consent** of the data subject — provided the data subject has been informed of the inadequate protection standards of the destination
3. **Contractual necessity** — performance of a contract to which the data subject is a party, or pre-contractual steps at the data subject's request
4. **Contract for the data subject's benefit** — performance of a contract between the Data Controller and other persons / juristic persons, for the interests of the data subject
5. **Vital interests** — preventing or suppressing a danger to life, body, or health, where the data subject is incapable of giving consent at the time
6. **Substantial public interest activities**

PDPC Thailand has not formally designated adequate jurisdictions as of last verification — verify the current list before relying on adequacy. Most engineering teams will rely on the (3) contractual-necessity basis for routine cloud-region or SaaS processing.

**Implementation layers:** [02 Architecture](../../../layers/02-architecture.md), [06 Disclosure](../../../layers/06-disclosure.md).

**Operationalisation:**
- For each sub-processor outside Thailand, identify which s28 basis you rely on
- Where relying on (2) consent: include the inadequate-protection notice in your privacy policy
- List overseas sub-processors in the privacy policy with their region

## Section 29 — Within-affiliate Personal Data Protection Policy

**Rule:** Data Controllers / Processors in Thailand may transfer Personal Data to other group entities abroad **without satisfying s28** if:
- They have a Personal Data Protection Policy covering the transfer, AND
- The Office (PDPC Thailand) has reviewed and certified the policy

This is the Thai equivalent of GDPR's Binding Corporate Rules.

**Operationalisation:**
- For multinational groups: invest in a PDPC-certified Personal Data Protection Policy as a one-time exercise that simplifies all subsequent intra-group transfers
- The Committee specifies the form and certification process — verify current rules

## Section 29 paragraph 3 — Suitable protection measures fallback

**Rule:** in the absence of a PDPC adequacy decision (s28) or a certified Personal Data Protection Policy (s29), the Data Controller / Processor may transfer if **suitable protection measures** are in place that:
- Enable enforcement of data subject rights, AND
- Provide effective legal remedial measures

This is similar to GDPR's "appropriate safeguards" (Standard Contractual Clauses, etc.). PDPC sets the rules and methods.

**Operationalisation:**
- For each cross-border sub-processor without a PDPC adequacy or s29 certification: rely on the vendor's contractual binding clauses (most major vendors offer something equivalent to GDPR SCCs)
- Document which mechanism applies for each transfer

## Section 40 — Data Processor duties (security overlap)

Processor security + breach-flow-down duties are covered in [01-accountability.md](01-accountability.md).

## Cross-border transfer table (planning template)

For each sub-processor:

| Sub-processor | Data categories transferred | Region | s28 / s29 basis | Evidence |
|---|---|---|---|---|
| (e.g.) Cloud DB provider | Account, content, messages | Singapore | s28 — consent OR contractual necessity | Vendor DPA |
| (e.g.) Push notification provider | Push tokens | Global | s28(3) contractual necessity | Vendor DPA |
| (e.g.) Email delivery | Email addresses | Global | s28(3) contractual necessity | Vendor DPA |
| (e.g.) Crash reporting | Stack traces (anonymised) | Global | s28(5) contractual or s29 BCR-equivalent | Vendor DPA / certification |

Maintain this table; update with every new vendor (see [`new-vendor.md`](../../../checklists/new-vendor.md)).

## Penalty exposure (this Part)

| Failure | Maximum administrative fine | Source |
|---|---|---|
| Fails s28 (cross-border without basis), general data | THB 3M | s83 |
| Fails s28 (cross-border without basis), sensitive data (s26) | **THB 5M** | s84 |
| Fails s37 (general security duties) | THB 3M | s83 |
| Fails s37 involving sensitive data | **THB 5M** | s84 |
| Fails s40 (processor duties) without appropriate reasons | THB 3M | s86 |
| Fails s29 paragraph 1 / 3 (intra-group transfer) | THB 3M | s83 / s86 |
| Fails s29 involving sensitive data | **THB 5M** | s84 / s87 |

Plus s81 personal liability for directors / managers responsible.
