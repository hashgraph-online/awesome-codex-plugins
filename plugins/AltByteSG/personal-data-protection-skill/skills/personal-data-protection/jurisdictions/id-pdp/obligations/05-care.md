# Pasal 29, 35–39, 42, 55–56 — Care of Data (Accuracy, Security, Retention, Cross-Border)

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

## Pasal 29 — Accuracy

**Rule:** the Controller must ensure **accuracy, completeness, and consistency** of Personal Data, including through verification (Pasal 29(2)).

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md) (self-service edit), [04 Controls](../../../layers/04-controls-and-processes.md) (verification flows).

## Pasal 35 — Security obligations

**Rule:** the Controller must protect and ensure the security of Personal Data by:

a. **Composing and implementing technical operational measures** to protect Personal Data from processing disturbances that conflict with law
b. **Determining the security level** with attention to the **nature and risk** of the Personal Data being protected

**Implementation layers:** [02 Architecture](../../../layers/02-architecture.md), [04 Controls](../../../layers/04-controls-and-processes.md).

The Act is high-level here; implementing PP provides specific technical standards. **Verify current PP text at [peraturan.go.id](https://peraturan.go.id).** Common requirements expected:

- Access controls (least-privilege, role-based)
- Encryption (in transit; at rest where appropriate to data sensitivity)
- Audit logging
- Periodic security review
- Documented information security policy
- Incident response plan

## Pasal 36 — Confidentiality

**Rule:** the Controller must **maintain confidentiality** of Personal Data during processing.

Operationalised via:
- Staff confidentiality agreements
- Logging hygiene (no plaintext PII in logs)
- Encryption at rest

## Pasal 37 — Supervise all parties involved

**Engineering surface:** maintain a vendor / sub-processor register with current DPAs and technical scoping. Each processor's access must be limited to the data categories and purposes documented in the DPA — enforce at the platform level (separate API keys, scoped service accounts, per-vendor row filters) so the supervision is real-time, not paper. Conduct vendor-compliance audits annually at minimum.

**Statute basis:** the Controller must supervise every party involved in Personal Data processing under the Controller's control.

**Implementation layer:** [01 Non-technical](../../../layers/01-non-technical.md) (vendor governance), [04 Controls](../../../layers/04-controls-and-processes.md) (sub-processor dispatch oversight).

## Pasal 38 — Protect from unlawful processing

**Rule:** the Controller must protect Personal Data from **unlawful processing**.

Counterpart to Pasal 37 — focuses on the data itself rather than the actors.

## Pasal 39 — Prevent unauthorized access

**Rule:** the Controller must **prevent Personal Data from being accessed without authorization** (Pasal 39(1)). Prevention is achieved through:
- A reliable security system over the processed data
- Reliable, secure, accountable electronic system processing

**Implementation layer:** [02 Architecture](../../../layers/02-architecture.md) (access controls).

## Pasal 42 — End processing when triggered

The Controller must end processing when:
a. Retention period reached
b. Purpose achieved
c. Subject requests it

**Implementation layer:** [04 Controls](../../../layers/04-controls-and-processes.md) (retention sweep, withdrawal handler).

## BAB VII — Personal Data Transfer

### Pasal 55 — Domestic transfer

**Rule:** the Controller may transfer Personal Data to other Controllers within Indonesia. **Both** the transferring and receiving Controller must comply with PDP protection requirements.

**Implementation layer:** [01 Non-technical](../../../layers/01-non-technical.md) (controller-to-controller agreements).

**Operationalisation:** when sharing data with another Indonesian organisation (B2B integration, partnership), execute a written agreement governing the receiving party's PDP compliance.

### Pasal 56 — Cross-border transfer (3-tier hierarchy)

**Rule:** the Controller may transfer Personal Data to Controllers / Processors outside Indonesia, satisfying **one of three tiers** in order:

**Tier 1 — Adequacy (Pasal 56(2)):** the destination country has Personal Data protection level **equal to or higher than** UU PDP.

**Tier 2 — Adequate and binding safeguards (Pasal 56(3)):** if Tier 1 is not satisfied, ensure **adequate and binding** Personal Data protection. This is the SCC / BCR / certification-equivalent path.

**Tier 3 — Subject consent (Pasal 56(4)):** if neither Tier 1 nor Tier 2 is satisfied, obtain the **explicit consent of the Data Subject** for the transfer.

**Implementation layers:** [02 Architecture](../../../layers/02-architecture.md), [06 Disclosure](../../../layers/06-disclosure.md), [01 Non-technical](../../../layers/01-non-technical.md).

**Compared to other jurisdictions:**
- Singapore PDPA s26: comparable-protection-via-contract (single tier, simpler)
- Thailand PDPA s28: adequacy / 6 enumerated exceptions (consent + 5 others) — closer to Indonesia's structure but more exceptions enumerated
- Indonesia: cleanest hierarchy — adequacy → safeguards → consent

**Operationalisation:**
- For each cross-border sub-processor, identify the tier you rely on
- Tier 1 (adequacy) requires the regulator to have published a list — verify current state
- Tier 2 (binding safeguards) — most realistic path; rely on vendor DPAs that include SCC-equivalent commitments
- Tier 3 (consent) — disclosed in privacy policy AND obtained at signup if relied upon

**Cross-border transfer planning template:**

| Sub-processor | Region | Categories transferred | Tier relied on | Evidence |
|---|---|---|---|---|
| (e.g.) Major cloud provider | Singapore / Global | Account, content, messages | Tier 2 — vendor DPA with SCC-equivalent | DPA copy on file |
| (e.g.) Push notifications | Global | Push tokens | Tier 2 — vendor DPA | DPA copy |
| (e.g.) Email delivery | Global | Email addresses, transactional content | Tier 2 — vendor DPA | DPA copy |
| (e.g.) Crash reporting | Global | Stack traces (anonymised) | Tier 2 — vendor DPA | DPA copy |

Document this register; update with every new vendor (see [`new-vendor.md`](../../../checklists/new-vendor.md)).

## Penalty exposure (this Part)

| Failure | Source |
|---|---|
| Pasal 29 (accuracy), 35 (security), 36 (confidentiality), 37 (supervision), 38 (unlawful processing), 39(1) (unauthorized access prevention) | Pasal 57 — ceiling 2% revenue |
| Pasal 42 (end processing) | Pasal 57 |
| Pasal 55(2), 56(2)–(4) (transfer) | Pasal 57 |

Plus potential criminal liability (Pasal 67) where unauthorized access leads to disclosure or use, and corporate criminal liability (Pasal 70).
