# Personal Data Breach Notification — § 20(f) RA 10173 + § 38 IRR + NPC Circular 16-03

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

PH has a **72-hour** breach notification clock that runs to **both NPC and the affected data subjects**, plus an **annual security incident report** every March. The trigger is information-type-driven: SPI or identity-fraud-enabling information acquired by an unauthorised person, with real risk of serious harm. **Concealment is its own offence** under § 30 RA 10173.

## § 20(f) RA 10173 — Statutory basis for breach notification

**Rule (verbatim):** *"The personal information controller shall promptly notify the Commission and affected data subjects when sensitive personal information or other information that may, under the circumstances, be used to enable identity fraud are reasonably believed to have been acquired by an unauthorized person, and the personal information controller or the Commission believes that such unauthorized acquisition is likely to give rise to a real risk of serious harm to any affected data subject."*

**Practical effect:** the statute sets the **trigger conditions** (information type + unauthorised acquisition + real risk of serious harm). The IRR § 38 and NPC Circular 16-03 set the **operational mechanics** (72-hour clock, content of notification, reporting form).

## § 38 IRR + NPC Circular 16-03 — When notification is mandatory

NPC Circular 16-03 § 11 sets the trigger as the **conjunction** of three conditions (all three must be present):

1. The breach involves **sensitive personal information** OR **information that may be used to enable identity fraud** (e.g., government IDs, financial account numbers, credentials).
2. There is reasonable belief that the information has been **acquired by an unauthorised person**.
3. The unauthorised acquisition is **likely to give rise to a real risk of serious harm** to the affected data subject.

**Practical effect:** the trigger is **narrower than ID** ("notify on every breach") and **wider than SG** ("notify on significant scale or significant harm only"). PH sits in the middle, with an information-type filter on top of the harm assessment.

**Where some but not all conditions are present:** the PIC is **not** required to notify, but **must** keep an internal record of the incident and include it in the annual Security Incident Report (see below).

**Implementation layer:** [07 Operational](../../../layers/07-operational.md).

## NPC Circular 16-03 § 12 — The 72-hour clock

**Rule (verbatim from § 12(a)):** *"Notification shall be done within seventy-two (72) hours upon knowledge of, or when there is reasonable belief by the personal information controller or personal information processor that, a personal data breach has occurred."*

**Practical effect:** the clock starts on **knowledge or reasonable belief**, not on confirmation. The first credible signal — an internal alert, a vendor notice, a customer report, a media report — starts the timer. If the PIC spends 36 hours figuring out whether it's real, the PIC has 36 hours left.

**A weekend, public holiday, or staff vacation does not pause the 72-hour clock.**

**Implementation layer:** [07 Operational](../../../layers/07-operational.md).

**Operationalisation:**
- Detection signals that should trigger a triage case: SIEM alerts on data-exfiltration patterns, abnormal access volumes (especially on SPI tables), vendor breach notices, support tickets reporting unauthorised account activity, lost / stolen device reports for devices that handled production data, DLP alerts on egress, public-disclosure / media reports.
- Triage SOP: timer starts on first credible signal. Owner = DPO + on-call security lead. Use a runbook checklist:
  1. Confirm or rule out (eyes-on within first 4 hours; preliminary scope within 12 hours)
  2. Escalate to DPO if signals persist
  3. Pre-fill the NPC notification form
  4. Submit by H+72 even if the assessment is incomplete (preliminary notification with "under investigation" fields)
- The DPO and a backup must both have credentials to submit on the NPC's online incident reporting portal.

## NPC Circular 16-03 § 13 — Content of the NPC notification

The notification to the NPC must include:

| Item | Detail |
|---|---|
| Nature of the breach | Description of how the breach occurred, the chronology, and the vulnerability exploited |
| Personal information possibly involved | Categories and approximate number of records / data subjects affected |
| Measures taken to address the breach | Containment, investigation, remediation in progress |
| Measures taken to reduce the harm | Notifications already sent; offered support (credit monitoring, password resets, etc.) |
| Identity and contact details of the DPO | The named individual and contact channel |

The NPC accepts a **preliminary** notification within the 72-hour window where the full assessment is incomplete, with a follow-up containing the missing details once known.

## NPC Circular 16-03 § 14 — Notification to affected data subjects

Same 72-hour clock. The notification to data subjects must include:

| Item | Detail |
|---|---|
| Nature of the breach | What happened, in plain language |
| Personal information possibly involved | What data of theirs was affected |
| Measures taken to address the breach | What the PIC has done |
| Measures the data subject can take | What the user should do (change password, watch for phishing, monitor accounts) |
| Contact details of the DPO | Where to ask follow-up questions |

**Exception (§ 14(c)):** notification to the data subject may be **delayed** at the NPC's instruction in cases where notification would impede a criminal investigation, or where the PIC can demonstrate that the personal information has been **rendered unintelligible** to unauthorised persons (e.g., strong end-to-end encryption with the keys not compromised).

**Implementation layer:** [07 Operational](../../../layers/07-operational.md), [05 Feature/UX](../../../layers/05-feature-ux.md).

**Operationalisation:**
- Channels for subject notification: email (primary); in-app banner on next launch; SMS where the breach involves an authentication credential and the user must act immediately.
- Plain-language template: what happened, when, what data, what the PIC has done, what the user should do, how to contact the DPO.
- Pre-stage templates so the comms team isn't drafting under time pressure. NPC Circular 16-03 doesn't allow "we'll figure out the wording" as a reason to miss the 72-hour clock.
- "Real risk of serious harm" categories that almost always trigger subject notification: government identifier disclosure (PhilSys / SSS / TIN / passport), payment / financial data, account credentials, health information, sensitive personal information per § 3(l).

## NPC Circular 16-03 § 17 — Annual Security Incident Report

**Rule (summary):** every PIC and PIP must submit an **Annual Security Incident Report** to the NPC by **31 March** each year, covering all security incidents and personal data breaches from the preceding calendar year — **including those that did not meet the mandatory notification trigger**.

**Practical effect:** the annual report captures the long tail of incidents that didn't require individual notification — small breaches, near-misses, incidents where the safe-harbour applied. The internal incident log is the source of truth for the report.

**Implementation layer:** [04 Controls and processes](../../../layers/04-controls-and-processes.md), [07 Operational](../../../layers/07-operational.md).

**Operationalisation:**
- Maintain an incident register: every incident (notifiable or not) gets a record with date, nature, scope, action taken, lessons learned.
- The register is the engineering input to the annual report. Build it as a structured table (database, ticketing-system queue, spreadsheet — whatever survives staff turnover) with the schema NPC expects.
- The annual report is filed via the NPC's online incident reporting portal.

## § 30 RA 10173 — Concealment of security breaches involving sensitive personal information

**Rule (verbatim):** *"The penalty of imprisonment of one (1) year and six (6) months to five (5) years and a fine of not less than Five hundred thousand pesos (Php500,000.00) but not more than One million pesos (Php1,000,000.00) shall be imposed on persons who, after having knowledge of a security breach and of the obligation to notify the Commission pursuant to Section 20(f), intentionally or by omission conceals the fact of such security breach."*

**Practical effect:** **concealment is its own offence.** The textbook trap is "we'll notify after we figure out what happened" — the clock starts on knowledge / reasonable belief, not confirmation, and the failure to notify within the 72-hour window can be charged as concealment under § 30 in addition to the underlying breach offence.

**Implementation layer:** [07 Operational](../../../layers/07-operational.md), with knock-on to [01 Non-technical](../../../layers/01-non-technical.md) (DPO / management awareness training).

**Operationalisation:**
- The runbook (see `templates/INCIDENT_RESPONSE.md.template`) must explicitly call out the § 30 risk so triage owners understand that delay-to-investigate is itself the offence.
- Decision log: every triage case records who decided to notify or not notify, with reasoning. This is the audit trail for any later prosecution.
- Director / officer / engineering manager awareness: § 30 + § 34 means the personal-prison-time risk runs up the chain. A breach that the engineering manager knew about and didn't escalate is the textbook scenario.

## What's at stake

- **§ 20(f) / § 38 IRR notification failure**: surfaces under multiple offence sections — § 25 / § 26 (the underlying processing failure), § 30 (concealment), § 32 (unauthorised disclosure if the breach was caused by misdirected disclosure), § 33 (combination or series).
- **§ 30 — concealment**: 1.5 to 5 years + ₱500k–₱1M per offence.
- **§ 35 — large-scale aggravation**: where ≥ 100 persons are affected, the penalty is in the maximum period of the underlying offence.
- **§ 34 — officer liability**: where the corporate offence engages, the responsible officers face the prison terms personally. The DPO and the management chain who knew about the breach are the natural § 34 targets.

The runbook (see `templates/INCIDENT_RESPONSE.md.template`) is the single most important artefact for § 20(f) / § 38 IRR. The template should be adapted to encode the **PH 72-hour clock to NPC AND to data subjects**, the **31 March annual incident report**, and the **§ 30 concealment risk** before any incident occurs.
