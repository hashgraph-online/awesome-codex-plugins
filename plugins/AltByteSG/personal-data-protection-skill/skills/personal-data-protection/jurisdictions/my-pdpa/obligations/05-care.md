# Care of Data — Security (s9), Retention (s10), Data Integrity (s11), Record (s44), Cross-Border (s129)

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

The "operational backbone" Principles. Three of the seven sit here: Security (s9), Retention (s10), Data Integrity (s11). The 2024 Amendments (Act A1727) made two material changes in this area: data processors are now directly subject to s9 (was indirect), and the cross-border whitelist regime under s129 was deleted in favour of a controller-led safeguards approach.

## s9 — Security Principle

**Rule (verbatim):** *"A data controller and a data processor shall, when processing personal data, take practical steps to protect the personal data from any loss, misuse, modification, unauthorized or accidental access or disclosure, alteration or destruction by having regard — (a) to the nature of the personal data and the harm that would result...; (b) to the place or location where the personal data is stored; (c) to any security measures incorporated into any equipment in which the personal data is stored; (d) to the measures taken for ensuring the reliability, integrity and competence of personnel having access to the personal data; and (e) to the measures taken for ensuring the secure transfer of the personal data."* (s9(1) as amended by A1727 item 5(a))

**A1727 change (1 April 2025):** before the amendment, only the data user (controller) was subject to s9. After: **both controller and processor** are directly bound. The controller still has a parallel duty under s9(2) to ensure the processor *"provides sufficient guarantees... and takes reasonable steps to ensure compliance"*. So you owe the security obligation **as a controller** AND any vendor processing your data owes it **as a processor** — and your DPA should reflect that duality.

**Practical effect:** the s9(1)(a)–(e) factors are the prompt for a defence-in-depth design. Encryption at rest, encryption in transit, key management, RBAC, vendor management, secure transfer of files — all are demanded by the section.

**Implementation layer:** [02 Architecture](../../../layers/02-architecture.md), [04 Controls and processes](../../../layers/04-controls-and-processes.md), [01 Non-technical](../../../layers/01-non-technical.md).

**Operationalisation (developer surface):**
- Encryption at rest: TLS-protected database storage, disk encryption on the host. Provider-managed keys are acceptable; rotate where the provider supports it.
- Encryption in transit: TLS 1.2 minimum; HSTS on web; certificate pinning for high-stakes mobile flows.
- Secrets: dedicated secret store, no secrets in source. Periodic rotation (provider-driven where possible).
- Access control: RBAC at the application layer; row-level security at the DB where the platform supports it (Postgres / Supabase / BigQuery row-access policies). Least privilege for service roles.
- Personnel: staff acceptable-use policy that calls out s9(1)(d) personnel obligations + the s130 personal-offence exposure (see [07-offences.md](07-offences.md)).
- Logging: all access to sensitive personal data (s40 categories incl. **biometric**) audit-logged. Logs themselves are personal data — apply retention to them.
- Sub-processors: contractually flow s9 down. Vendor onboarding checklist captures their s9 posture.
- Backups: encrypted at rest; restore procedure tested; backup retention documented (and squared with s10 retention obligations — backups holding deleted data is the textbook trap, see s10 below).

## s10 — Retention Principle

**Rule (verbatim):** *"(1) The personal data processed for any purpose shall not be kept longer than is necessary for the fulfilment of that purpose. (2) It shall be the duty of a data controller to take all reasonable steps to ensure that all personal data is destroyed or permanently deleted if it is no longer required for the purpose for which it was to be processed."*

**Practical effect:** retention is **purpose-bound**. When the purpose ends (account deleted, contract terminated, statutory retention period elapsed), the data must be destroyed or permanently deleted. "Soft delete" alone is not "permanent deletion".

**Implementation layer:** [03 Data model](../../../layers/03-data-model.md), [04 Controls and processes](../../../layers/04-controls-and-processes.md).

**Operationalisation:**
- Retention policy by data category. Examples:
  - Account profile data: until account deletion + 90-day grace, then hard delete.
  - Transaction records: 7 years (Income Tax Act / accounting record requirements typically govern, riding on s6(2)(c) legal-obligation basis).
  - Audit logs containing personal identifiers: 1–2 years, then either delete or pseudonymise.
- Hard-delete vs soft-delete conventions. A `deleted_at` flag is operationally useful for restore-windows but **must** be paired with a periodic sweep that physically removes after the grace period.
- Backups: a retention sweep that doesn't account for backup tapes / point-in-time recovery is incomplete. Either include backup retention in the same SLA, or document the backup-retention horizon as a known exception in the privacy notice (and don't restore from a backup that includes deleted users to live storage without re-deletion).
- Anonymisation can substitute for deletion if the anonymisation is irreversible (k-anonymity-grade or stronger). Pseudonymisation alone is not — it can be reversed via the key map.

## s11 — Data Integrity Principle

**Rule (verbatim):** *"A data controller shall take reasonable steps to ensure that the personal data is accurate, complete, not misleading and kept up-to-date by having regard to the purpose, including any directly related purpose, for which the personal data was collected and further processed."*

**Practical effect:** integrity is a process obligation as much as a technical one. The user's correction right under s34 is one mechanism; periodic verification (re-confirm email annually, periodic prompts to update profile) is another.

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md), [04 Controls and processes](../../../layers/04-controls-and-processes.md).

**Operationalisation:**
- Self-service correction (covered in [04-access-correction.md](04-access-correction.md)).
- Periodic re-verification for high-stakes fields — KYC re-confirmation, address validation for delivery, email verification on change.
- Don't propagate manifest errors silently. A bounce on a transactional email should flag the email as suspect, not silently discard.

## s44 — Record to be kept by the data controller

**Rule (summary):** the controller must maintain and regularly update *"a list of personal data disclosed to third parties"* (s44(1)(a)) and *"the categories of personal data and the categories of recipients to whom such personal data is or has been disclosed"* (s44(1)(b)), and produce these records on the Commissioner's request.

**Practical effect:** a regulator-facing record-of-processing inventory. Less detailed than GDPR Article 30, but real.

**Implementation layer:** [03 Data model](../../../layers/03-data-model.md), [04 Controls and processes](../../../layers/04-controls-and-processes.md), [01 Non-technical](../../../layers/01-non-technical.md).

**Operationalisation:**
- A simple recipients table or spreadsheet maintained by the DPO: vendor / processor name, categories of data sent, purpose, contract-DPA reference, whether cross-border (s129 cross-reference).
- Update on every new vendor onboarding. Review annually.
- This artefact is also what you reach for in a breach assessment — categories of data + categories of recipients are precisely the breach-impact inputs.

## s129 — Transfer of personal data outside Malaysia (amended 2024)

**Rule, post-A1727 item 12 (1 April 2025):** s129(1) (the Ministerial whitelist of approved destinations) is **deleted**. s129(2) is rephrased: *"A data controller may transfer any personal data of a data subject to a place outside Malaysia"* — i.e., the default rule is now that transfer is permitted, conditional on the s129(3) safeguards. s129(3) preserves the original list of bases:

(a) data subject's consent;
(b) transfer necessary for performance of a contract between subject and controller;
(c) transfer necessary for conclusion / performance of a contract between controller and a third party at the subject's request or in the subject's interests;
(d) for legal proceedings / legal advice / establishing-exercising-defending legal rights;
(e) reasonable belief that the transfer is for avoidance / mitigation of adverse action against the subject and consent isn't practicable;
**(f) the controller has taken all reasonable precautions and exercised all due diligence to ensure that the personal data will not in that place be processed in any manner which, if that place is Malaysia, would be a contravention of this Act**;
(g) vital interests of the subject.

(Paragraph (h) — Minister-determined public interest — was deleted by A1727 item 12(c)(iv).)

**Practical effect:** the realistic engineering basis for routine cloud-region or SaaS-vendor processing is now **s129(3)(f) due diligence**. You no longer need to wait for the Minister to gazette an "approved" destination. You take the burden of proof: vendor DPAs, security certifications (ISO 27001, SOC 2), data-flow assessments, periodic audits.

**Implementation layer:** [02 Architecture](../../../layers/02-architecture.md), [06 Disclosure](../../../layers/06-disclosure.md), [01 Non-technical](../../../layers/01-non-technical.md).

**Operationalisation:**
- Disclose cross-border destinations in the privacy notice — categories of recipients (s7(1)(e)) plus the destination country if material to the user's expectations.
- Vendor DPA must include: vendor's commitment to comply with controls equivalent to MY PDPA's Principles; breach-notification flow-down (so you can hit s12B); restrictions on sub-processors and onward transfers; audit / inspection rights where commercially feasible.
- Document the s129(3)(f) basis: which vendors / regions, what evidence of due diligence (cert audits + DPA + risk assessment).
- Sensitive data (s40 incl. biometric) crossing borders is a higher-stakes assessment — explicit consent under s40(1)(a) is the safer overlay even if s129(3)(f) is otherwise satisfied.
- s129(5) penalty: RM 300,000 / 2 years — note this is **lower** than the s5(2) principle penalty, reflecting the original 2010 calibration.

## What's at stake

- **Security Principle breach (s9 → s5(2))**: RM 1,000,000 / 3 years.
- **Retention Principle breach (s10 → s5(2))**: RM 1,000,000 / 3 years.
- **Data Integrity Principle breach (s11 → s5(2))**: RM 1,000,000 / 3 years.
- **Cross-border breach (s129(5))**: RM 300,000 / 2 years (separately calibrated, lower than principle breach).
- **Record obligation (s44)**: surfaces under s5(2) for the General Principle / Notice & Choice; non-production of the record on regulator demand is itself an enforcement signal.

This layer is where most actual enforcement risk lives — the principles here generate the headline-grabbing breaches. The audit trail (security controls evidence, retention sweep run logs, recipients list) is what an inspection looks for first.
