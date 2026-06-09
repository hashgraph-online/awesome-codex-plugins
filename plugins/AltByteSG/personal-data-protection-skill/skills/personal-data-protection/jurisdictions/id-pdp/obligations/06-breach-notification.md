# Pasal 46 — Breach Notification (72 hours, dual-recipient)

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

UU PDP's breach notification obligation is in a single dense paragraph of Pasal 46. The 72-hour clock is non-negotiable, and unlike Singapore (PDPC only) or Thailand (regulator only), **Indonesia requires notification to BOTH the Data Subject AND the regulator**.

## Pasal 46 — The rule

**Pasal 46(1):** *"In the event of a Personal Data protection failure, the Personal Data Controller must provide a written notification within 3 × 24 hours to: (a) the Data Subject; and (b) the regulator (lembaga)."*

**Pasal 46(2):** the written notification must include at minimum:
a. The Personal Data that was disclosed
b. When and how the Personal Data was disclosed
c. Handling and recovery efforts undertaken by the Controller

**Pasal 46(3):** under certain circumstances, the Controller must also notify the **public**.

## Three-tier notification

| Tier | Recipient | Trigger | Timing |
|---|---|---|---|
| 1 | The regulator (lembaga) | Any breach | Within 72 hours (3 × 24 jam) |
| 2 | Affected Data Subjects | Any breach | Within 72 hours (3 × 24 jam) |
| 3 | The public | "Certain circumstances" — likely large-scale or serious | Per implementing PP |

**Critical:** the clock starts at **awareness of the breach**, not at notifiability assessment. Indonesia does not have an explicit assessment window before the 72-hour clock starts (unlike Singapore where the clock starts at "assessment-as-notifiable").

## What constitutes a "Personal Data protection failure"

The Act uses the phrase *"kegagalan Pelindungan Data Pribadi"* (Personal Data protection failure) without a separate definition. Practical reading: any breach of the Pasal 35–39 security obligations, including:

- Unauthorised access (intrusion, leaked credentials, RLS / IAM bypass)
- Unauthorised disclosure (mistaken email, public-bucket misconfiguration)
- Unauthorised alteration (data tampering)
- Loss of Personal Data (lost device with active credentials, deleted records)
- Vendor / sub-processor breach affecting your data

**Implementation layer:** [07 Operational](../../../layers/07-operational.md) (incident-response runbook).

**Examples that should be triaged as breaches and assessed for the 72-hour clock:**
- Leaked secret (database credential, API key, OAuth key) — once it's leaked, unauthorised access is "likely to occur"
- Access-control bypass discovered in production
- Stolen / lost device with active prod credentials
- Misdirected email containing Personal Data
- Admin / staff accessing data outside their role
- Anomalous traffic exfiltrating data
- A user reports their account was accessed by someone else
- Vendor / sub-processor notifies you of a breach on their side

When in doubt, treat as an incident. The cost of opening a triage case is low; the cost of missing the 72-hour clock is high.

## Notification content (Pasal 46(2))

The written notification must contain:

a. **Personal Data that was disclosed** — types, categories, scale (estimate is fine if exact unknown — update later)
b. **When and how the Personal Data was disclosed** — timeline of awareness, occurrence (if known), and the mechanism of disclosure
c. **Handling and recovery efforts** — containment actions, remediation, and steps taken to prevent recurrence

This is the minimum. The implementing PP may require additional fields — verify current text.

## Channels for notifying Data Subjects

UU PDP doesn't prescribe channels. Practical sequence:

1. **Email** to the address on file
2. **In-app banner** on next launch
3. **Push notification** (only if email + in-app aren't reaching them)

## Sample notification template (drop-in to your runbook)

```
Subject: Important: a security incident affecting your account

Hi [first name],

On [date], we discovered that [one-line description of what happened].
We notified the Indonesian regulator on [date].

What data was involved: [bullet list — types of Personal Data]
What we have done: [containment + remediation steps]
What you should do: [specific user actions, e.g. reset password, log out everywhere]

We are sorry this happened. Reply to this email for any questions
and it will reach me directly.

[DPO name]
Data Protection Officer, [Legal Entity]
[DPO email]
```

Save the send log (recipient count, send timestamp) in the incident log.

## Public notification (Pasal 46(3))

The Controller must notify the public *"under certain circumstances"* — the Act doesn't enumerate, deferring to implementing PP. Reasonable read: large-scale breaches, breaches involving "specific" (sensitive) data at scale, breaches with public safety implications.

Common channels: a notice on your public website, a press release, posts on official social channels.

## Vendor / sub-processor breaches

When a Processor (your sub-processor) experiences a breach affecting your data:

- Pasal 51 establishes the Processor's obligation to act on Controller's instructions and report issues
- Your DPA with the processor should require notification of breaches **without undue delay** — best practice: contractually require ≤24 hours so you have time to assess
- The 72-hour clock starts when **you (as Controller) become aware** — typically when the processor notifies you

Document this chain in your incident log: when the processor became aware → when they notified you → when you assessed.

## Records and audit

Pasal 31 requires the Controller to keep records of all Personal Data processing activities. After a breach, **add the post-incident remediation** to those records — this is part of the demonstrable accountability principle (Pasal 47) and likely to be reviewed by the regulator if they investigate.

## Penalty exposure

Failure to notify per Pasal 46(1) or Pasal 46(3) carries administrative sanctions per Pasal 57:

| Sanction | Source |
|---|---|
| Written warning | Pasal 57(2)(a) |
| Temporary suspension of processing activities | Pasal 57(2)(b) |
| Deletion or destruction of Personal Data | Pasal 57(2)(c) |
| Administrative fine — up to **2% of annual revenue** | Pasal 57(2)(d) + 57(3) |

Plus potential criminal liability (Pasal 67) if the breach involved unauthorised obtaining or disclosure carried out for personal benefit.

## Operational checklist (incorporate into the runbook)

- [ ] Pre-stage the notification template in **Bahasa Indonesia** for Indonesian Data Subjects
- [ ] Pre-fill the regulator notification (verify current submission method — Komdigi / appointed regulator)
- [ ] DPO + backup contact both have submission access
- [ ] Documented incident log location with awareness-timestamp pattern
- [ ] Annual review of the runbook
- [ ] Vendor DPAs require breach notification ≤24 hours

See `templates/INCIDENT_RESPONSE.md.template` for a starting runbook.

## Quick reference

| Obligation | Singapore PDPA | Thailand PDPA | Indonesia UU PDP |
|---|---|---|---|
| Notify regulator | 3 calendar days from assessment | 72 hours from awareness | **72 hours from awareness** (Pasal 46(1)(b)) |
| Notify affected individuals | If significant harm likely (s26D(2)) | If high risk (s37(4)) | **Always** (Pasal 46(1)(a)) — distinctive |
| Notify public | Not required | Not required | "Under certain circumstances" (Pasal 46(3)) |

Indonesia's "always notify the Data Subject" requirement is broader than Singapore's significant-harm test or Thailand's high-risk test — making the 72-hour cycle operationally heavier.
