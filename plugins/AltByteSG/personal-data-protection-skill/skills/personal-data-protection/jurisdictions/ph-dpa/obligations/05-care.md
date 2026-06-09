# Security, Retention, and Cross-Border Accountability — § 20, § 21 RA 10173 + §§ 25–29 IRR + § 50 IRR + NPC Circular 16-01

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

§ 20 sets the security obligation; the IRR §§ 25–29 break it into **organisational, physical, and technical measures**. § 21 establishes accountability for transfers — including cross-border — and § 50 IRR operationalises it. Together these define the "care" engineering owes the personal information under its control.

## § 20(a) — General security duty

**Rule (verbatim):** *"The personal information controller must implement reasonable and appropriate organizational, physical and technical measures intended for the protection of personal information against any accidental or unlawful destruction, alteration and disclosure, as well as against any other unlawful processing."*

**Practical effect:** "reasonable and appropriate" is a sliding scale calibrated to the **nature of the information, the likelihood and severity of risk, and the cost of implementation**. SPI processing requires more than plain PI; high-volume processing requires more than low-volume; consumer-facing apps with weak authentication infrastructure require more compensating controls.

**Implementation layer:** [02 Architecture](../../../layers/02-architecture.md), [04 Controls and processes](../../../layers/04-controls-and-processes.md).

## § 20(b) — Determining "reasonable and appropriate"

**Rule (verbatim):** the determination shall take into account *"the nature of the personal information to be protected"*; *"the risks represented by the processing"*; *"the size of the organization and complexity of its operations"*; *"current data privacy best practices"*; and *"the cost of security implementation."*

**Practical effect:** the Act adopts a **risk-based** standard. A small startup is not held to the same baseline as a large bank, but both must demonstrate the controls are proportionate to the risk. NPC Circular 16-01 (Security in Government Agencies), although addressed to the public sector, is widely treated as a **reference baseline for private-sector practice**.

## §§ 25–28 IRR — Organisational, physical, and technical measures

The IRR breaks § 20 into three pillars. Each pillar has prescribed minimum content.

### Organisational (§ 26 IRR)

- Compliance officers (DPO + Compliance Officers for Privacy where appointed).
- Privacy management policies and procedures, in writing.
- Records of processing activities (the operational equivalent of the EU ROPA).
- Recordkeeping for data subject requests, security incidents, and breach notifications.
- Capacity-building and training for personnel handling personal information.
- Personnel confidentiality agreements / NDAs.

**Engineering touch-point:** the Records of Processing Activities is the artefact engineering supports — every system that processes personal information appears in the inventory, with its purpose, lawful basis, recipients, and retention rule.

### Physical (§ 27 IRR)

- Secure physical workspaces; controlled access.
- Secure storage of physical media (paper records, backup tapes, hardware).
- Procedures for transfers of physical media.
- Procedures for the disposal of physical media (shredding, secure wipe before resale / recycling).

**Engineering touch-point:** mostly relevant to data-centre physical security (handled by hosting providers under their certifications) and any office-premises records. For a SaaS / mobile / web app, physical security is largely inherited from the cloud provider; the engineering action is documenting the inheritance.

### Technical (§ 28 IRR) — engineering core

The IRR specifies technical safeguards that the PIC / PIP must consider. Not all are mandatory in every case but each must be evaluated:

| Measure | What it means in code |
|---|---|
| Safeguards to protect computer network against accidental, unlawful or unauthorized usage / interference / hindering of functioning / availability | Firewalls, WAF, rate limiting, DDoS protection, network segmentation |
| Ability to ensure and maintain the confidentiality, integrity, availability and resilience of processing systems | Encryption, integrity checks, replication, backup / restore tested |
| **Regular monitoring for security breaches** and a process for **identifying and accessing reasonably foreseeable vulnerabilities** | SIEM, logging, IDS, vulnerability scanning, dependency-scan in CI |
| **Process for regularly testing, assessing and evaluating the effectiveness of security measures** | Pen test cadence, tabletop exercises, internal audit |
| **Encryption of personal data during storage and transmission**, authentication processes, and other technical security measures that control and limit access | TLS 1.2+ in transit, AES-256 (or equivalent) at rest; per-user / per-tenant keys where SPI is processed |

**Implementation layer:** [02 Architecture](../../../layers/02-architecture.md), [04 Controls and processes](../../../layers/04-controls-and-processes.md).

**Operationalisation:**
- **Encryption in transit:** TLS 1.2+ enforced on all endpoints; HSTS for web; certificate pinning for native apps where the threat model warrants.
- **Encryption at rest:** AES-256 (or equivalent) on every personal-data store. Disk-level encryption is the floor; field-level / column-level encryption for SPI (especially government identifiers).
- **Authentication:** MFA for staff with access to production data; service-to-service authentication via short-lived tokens, not long-lived static credentials; rotated secrets.
- **Authorisation:** principle of least privilege; default deny; row-level security where the data model supports it. SPI columns gated separately from plain PI.
- **Logging and monitoring:** immutable audit logs of read / write / delete on personal-data tables (especially SPI). Logs themselves are personal data — retention rules apply, see § 11(e).
- **Vulnerability management:** dependency scanning in CI; periodic penetration testing (annual is the practical floor; quarterly for high-risk apps); incident response runbook tested.
- **Backup and recovery:** backups encrypted; restore tested; backup retention bounded (do not extend the retention rule indirectly through unbounded backup retention).

### § 29 IRR — Personnel safeguards

- Personnel must be **bound by confidentiality**.
- Background checks where appropriate to the role.
- Written acknowledgement of the personal-information policies.
- Termination procedures: revoke access on day of separation; recover devices and credentials.

**Engineering touch-point:** access provisioning and deprovisioning is in scope. SCIM integration with the HR system, automated offboarding, and a recurring access-review cycle are the realistic implementations.

## § 20(c) — Vendor selection

**Rule (verbatim):** *"The personal information controller shall promptly notify the Commission and affected data subjects when sensitive personal information or other information that may, under the circumstances, be used to enable identity fraud are reasonably believed to have been acquired by an unauthorized person... [and shall] ensure that third parties processing personal information on its behalf shall implement the security measures required by this provision."*

**Practical effect:** vendor selection is a § 20 obligation, not just a contract obligation. The PIC must verify (and re-verify) that processors meet the security baseline.

**Operationalisation:**
- Vendor onboarding gate: documented review of the vendor's controls (ISO 27001 / SOC 2 / equivalent attestation; NPC seal of registration where applicable; sectoral certifications where relevant).
- Annual re-baseline of every active vendor processing personal information.
- DPA must contractually require the vendor to maintain the security baseline and to allow audit.

## § 11(e) — Retention

**Rule (verbatim from § 11(e)):** personal information shall be *"retained only for as long as necessary for the fulfilment of the purposes for which the data was obtained or for the establishment, exercise or defence of legal claims, or for legitimate business purposes, or as provided by law."*

**Practical effect:** every persistent personal-data field has a retention rule. The rule is **purpose lifetime + grace period for legal claims / regulatory windows**.

**Implementation layer:** [03 Data model](../../../layers/03-data-model.md), [04 Controls and processes](../../../layers/04-controls-and-processes.md).

**Operationalisation:**
- Retention schedule documented per field / table — purpose, lifetime, sweep cadence, hard-delete or anonymisation outcome.
- Sweep job runs on schedule (daily / weekly), processes records past their retention period, and produces an audit-trail entry per disposal.
- Backups: backup retention should not silently extend the live retention. If backups retain data for 90 days, the retention rule must contemplate that — typically by stating that hard-deletion completes within X days of the live deletion (covering backup expiry).
- Tax / AML / sectoral retention windows override the default — keep the legal-obligation basis documented per retention rule.

## § 21 — Cross-border accountability

**Rule (verbatim from § 21):** *"Each personal information controller is responsible for personal information under its control or custody, including information that have been transferred to a third party for processing, whether domestically or internationally, subject to cross-border arrangement and cooperation."*

**Practical effect:** PH does **not** have an adequacy regime, an SCC mechanism, or a cross-border whitelist. The PIC is **accountable for personal information regardless of where it is processed** — domestic or international — and must use *"contractual or other reasonable means"* to provide a comparable level of protection.

**Implementation layer:** [02 Architecture](../../../layers/02-architecture.md) (where the data lands), [01 Non-technical](../../../layers/01-non-technical.md) (the contractual machinery). Also see [01-accountability.md](01-accountability.md) for vendor flow-down.

**Operationalisation:**
- **Cloud-region choice:** PH does not require region-pinning by default (sectoral rules like BSP banking rules may differ). Foreign-region processing is permissible with a written DPA + due diligence.
- **Vendor inventory** records the processing region per vendor — useful both for compliance and for incident response.
- **Outsourcing Agreement / Data Sharing Agreement** is the contractual mechanism. NPC Circular 2020-03 (Data Sharing Agreements in the Private Sector) sets the operative content for data-sharing scenarios; § 44 IRR sets the operative content for processor outsourcing.
- **Group company transfers** (HR systems, customer-data sharing within an MNC) need their own DSA, not just the master vendor DPA. A Group Data Sharing Agreement or Binding Corporate Rules-equivalent is the typical pattern.
- The PIC remains accountable even where the foreign processor breaches its own local law — there is no "the vendor's jurisdiction's data protection authority handled it" defence under PH § 21.

## § 50 IRR — Operational rules for transfers

**Rule (summary):** § 50 IRR reinforces § 21 — the PIC must use *"contractual or other reasonable means to provide a comparable level of protection while the information is being processed by a third party."* The IRR does not prescribe a fixed contractual template, leaving the PIC discretion to use the appropriate instrument (outsourcing agreement, data-sharing agreement, intra-group binding rules) given the scenario.

**Operationalisation:**
- Transfer documentation lives in a vendor file: the agreement, the due-diligence record, the sub-processor list, the most-recent attestation.
- Material change in the processing location (vendor migrates to a new region, sub-processor change) triggers re-documentation.

## What's at stake

- **§ 25 / § 26 — unauthorised processing or negligent access**: where a security failure exposes personal information, the underlying offence engages. SPI: 3 to 6 years + ₱500k–₱4M. PI: 1 to 3 years + ₱500k–₱2M.
- **§ 27 — improper disposal**: where end-of-retention disposal is mishandled. Up to 3 years + ₱500k.
- **§ 32 — unauthorised disclosure**: where a transferred-out dataset is mishandled by a vendor. 1 to 5 years + ₱500k–₱2M (and the PIC remains accountable under § 21).
- **§ 33 — combination or series**: 3 to 6 years + ₱1M–₱5M. A multi-record breach with retention violations and inadequate vendor controls is the textbook § 33 case.
- **§ 35 — large-scale aggravation**: where ≥ 100 persons are affected, the penalty is in the maximum period.
- **§ 34 — officer liability**: where the corporate offence engages, the responsible officers face the prison terms personally. Vendor onboarding, encryption design decisions, and access-grant approvals are the engineering touch-points where § 34 attaches.

The technical-measures evidence pack (architecture diagrams, encryption configuration, access logs, vulnerability scan history, pen test reports, vendor due-diligence files) is the single most useful artefact in any NPC inspection. Build it as you build the system.
