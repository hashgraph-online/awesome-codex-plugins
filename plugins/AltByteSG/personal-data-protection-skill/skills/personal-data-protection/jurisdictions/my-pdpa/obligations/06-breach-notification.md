# Data Breach Notification — s12B (new 2024)

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

s12B was inserted by Act A1727 (effective **1 June 2025**) and is the first time MY PDPA has had a statutory breach-notification obligation. The statute sets the standard (*"as soon as practicable"*) and the JPDP **Personal Data Protection Guideline on Data Breach Notification** (issued 25 February 2025, effective 1 June 2025) operationalises it as a **72-hour Commissioner notification** + **7-day affected-individual notification**. The Guideline is binding for compliance assessment.

## s4 — Definition of "personal data breach" (new 2024)

**Rule (verbatim):** *"'personal data breach' means any breach of personal data, loss of personal data, misuse of personal data or unauthorized access of personal data"* (s4 as amended by A1727 item 3(d)).

**Practical effect:** the definition is **broad**. A lost / stolen device, a leaked credential, a misconfigured S3 bucket, a row-level-security bypass, a phishing-driven account takeover, a social-engineered support ticket — all qualify, **before** any actual exfiltration is confirmed.

**Implementation layer:** [07 Operational](../../../layers/07-operational.md).

**Operationalisation:** the runbook (see `templates/INCIDENT_RESPONSE.md.template`) must define "incident" broadly enough to capture all of those. When in doubt, treat as an incident — the cost of opening triage is low; the cost of missing the clock is high.

## s12B(1) — Notify the Commissioner [CRITICAL — 72 hours]

**Rule (verbatim):** *"Where a data controller has reason to believe that a personal data breach has occurred, the data controller shall, as soon as practicable, notify the Commissioner in the manner and form as determined by the Commissioner."*

**Operationalisation per the JPDP Guideline (25 Feb 2025):** notify the Commissioner **within 72 hours** from when the personal data breach is **discovered** (whether by detection or by external notification). If the controller cannot complete the assessment within 72 hours, an **initial / preliminary notification** is filed within the window and supplemented later.

**Practical effect:** **72 hours from discovery, not from confirmation.** The clock starts on the first credible signal that a breach has occurred — an alert, a customer report, a vendor notice, a media report. If you spent 36 hours figuring out whether it's real, you have 36 hours left.

**Implementation layer:** [07 Operational](../../../layers/07-operational.md).

**Operationalisation:**
- Detection signals that should trigger a triage case: SIEM alerts on data-exfiltration patterns, abnormal access volumes, vendor breach notices, support-ticket reports of unauthorised account activity, lost / stolen device reports for devices that handled production data, DLP alerts on egress.
- Triage SOP: timer starts on first credible signal. Owner = DPO + on-call security lead. Use a runbook checklist:
  1. Confirm or rule out (eyes-on within first 4 hours; preliminary scope within 12 hours)
  2. Escalate to DPO if signals persist
  3. Pre-fill the JPDP notification form
  4. Submit by H+72 even if the assessment is incomplete (preliminary notification with "under investigation" fields)
- DPO and a backup must both have credentials to submit on the Personal Data Protection System portal.
- A weekend / public holiday does not pause the 72-hour clock.
- s12B(3) penalty for non-notification: **RM 250,000 / 2 years**. This is in addition to any underlying s9 / s40 penalty.

## s12B(2) — Notify affected individuals [significant harm]

**Rule (verbatim):** *"Where the personal data breach under subsection (1) causes or likely to cause any significant harm to the data subject, the data controller shall notify the personal data breach to the data subject in the manner and form as determined by the Commissioner without unnecessary delay."*

**Operationalisation per the JPDP Guideline:** subject notification must be made within **7 days** after the initial notification to the Commissioner.

**Practical effect:** the trigger is **"significant harm"**. The Guideline indicates this is assessed against criteria including: nature and sensitivity of the personal data; number of affected subjects; identifiability; likelihood of identity theft or financial loss; severity of consequences; existing safeguards (e.g., strong encryption may reduce the assessed harm).

**Implementation layer:** [07 Operational](../../../layers/07-operational.md), [05 Feature/UX](../../../layers/05-feature-ux.md).

**Operationalisation:**
- Channels: email (primary); in-app banner on next launch; push notification (only if email + in-app aren't reaching them).
- Plain-language template: what happened, when, what data, what you've done, what they should do, how to contact the DPO. Pre-stage templates so the comms team isn't drafting under time pressure.
- "Significant harm" categories that almost always trigger subject notification: identity-credential disclosure (ID number, passport), payment / financial data, account credentials, sensitive personal data per s40 (incl. **biometric data**, post-2024).
- 7 days is short. Stage user-comms drafts in advance during the assessment phase, not after submission to the Commissioner.

## s12B(3) — Penalty for failure

**Rule (verbatim):** *"A data controller who contravenes subsection (1) commits an offence and shall, on conviction, be liable to a fine not exceeding two hundred and fifty thousand ringgit or imprisonment for a term not exceeding two years or to both."*

**Practical effect:** the discrete s12B(3) penalty is moderate (RM 250,000), but a missed notification typically also indicates s9 (Security) failure, attracting the s5(2) cap of **RM 1,000,000 / 3 years** in parallel, plus director-liability under s133.

## Operational guidance from JPDP

The JPDP Guideline (25 Feb 2025) sets out the detailed expectations. As of last verification:

- **Notification form:** submitted via the JPDP Personal Data Protection System (online portal). Pre-register and onboard before you need it.
- **Content of notification (Commissioner):** nature of the breach, categories and approximate number of affected subjects, categories and approximate volume of records, likely consequences, mitigation measures taken or proposed, DPO contact.
- **Content of notification (subject):** nature of the breach, likely consequences, mitigation, DPO contact, recommended steps the subject should take.
- **Records:** the controller is expected to maintain a register of all breaches (including those not notifiable), with assessment reasoning. This is an evidence trail for any inspection.
- **Vendor breaches:** if your processor has a breach affecting your data, **you** are the controller-of-record for s12B purposes. Your vendor DPA must require timely flow-down (typically ≤ 24 hours from vendor's discovery) so you can still hit your 72-hour clock.

## What's at stake

- **s12B(3) penalty**: RM 250,000 / 2 years per discrete failure.
- **Co-occurring s9 (Security Principle) breach**: RM 1,000,000 / 3 years under s5(2).
- **Director liability under s133**: notification failure with a known breach is precisely the scenario where the "no knowledge / due diligence" defence collapses.

The runbook (see `templates/INCIDENT_RESPONSE.md.template`) is the single most important artefact for s12B. The template includes the MY-specific 72-hour Commissioner clock and 7-day subject clock — adapt the placeholders before any incident occurs.
