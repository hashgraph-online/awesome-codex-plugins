# Section 37(4) — Breach Notification (72 hours)

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

Thailand PDPA's breach notification obligation lives in a single dense paragraph of s37. The 72-hour clock makes preparation in advance non-negotiable.

## Section 37(4) — The rule

**Rule (verbatim):** *"notify the Office of any Personal Data breach without delay and, where feasible, within 72 hours after having become aware of it, unless such Personal Data breach is unlikely to result in a risk to the rights and freedoms of the Persons. If the Personal Data breach is likely to result in a high risk to the rights and freedoms of the Persons, the Data Controller shall also notify the Personal Data breach and the remedial measures to the data subject without delay. The notification and the exemption to the notification shall be made in accordance with the rules and procedures set forth by the Committee."*

**Three tiers:**

| Risk level | PDPC notification required? | Data subject notification required? |
|---|---|---|
| **Unlikely** to result in risk to rights and freedoms | No | No |
| **Likely** to result in risk (but not high risk) | Yes — within 72 hours | No |
| **High risk** to rights and freedoms | Yes — within 72 hours | Yes — without delay |

**Critical:** the clock starts at **awareness**, not at occurrence. The Data Controller must be able to demonstrate when awareness occurred (assessment-complete timestamp, ticket creation, etc.).

**"Where feasible, within 72 hours"** — Thai PDPA permits exceeding 72 hours where infeasible, but the burden of justifying the delay falls on the Data Controller. Plan to meet 72 hours; treat any longer window as exceptional.

## What constitutes a breach

The Act doesn't define "Personal Data breach" as a separate term — but s37(1) defines the security obligation in terms of *"unauthorized or unlawful loss, access to, use, alteration, correction or disclosure of Personal Data."* A breach is a failure of any of these.

**Examples that should be triaged as breaches:**
- A leaked secret (database credential, API key, OAuth key, encryption key) where it could enable unauthorised access
- An access-control bypass discovered to return data the caller shouldn't see
- A stolen / lost device with active prod credentials
- A misdirected email with Personal Data
- An admin / developer accessing data outside their role
- A scraper or anomalous traffic exfiltrating data
- A user reports their account was accessed by someone else
- A vendor / sub-processor notifies you of a breach on their side

**Internal-only access** (curious admin, no external disclosure) is still a breach under s37(1) and may require notification depending on the risk assessment. (Thai PDPA does not have an explicit "internal-only is not notifiable" carve-out like Singapore's s26B(4).)

**Implementation layer:** [07 Operational](../../../layers/07-operational.md) (incident-response runbook).

## Risk-to-rights-and-freedoms assessment

**High-risk indicators (data subject notification required):**

- Sensitive data (s26) leaked at any scale
- Authentication credentials leaked in a form usable for account takeover
- Health / medical data leaked
- Children's data leaked
- Financial data leaked
- Data enabling identity theft (national ID, government ID, etc.)

Other inputs to the assessment: volume of affected subjects, identifiability (easily-reversible pseudonymisation does not reduce risk), vulnerability of the cohort (minors, patients), and the realistic misuse path (identity theft, financial fraud, physical safety).

When in doubt, notify both PDPC and affected individuals. Over-notification is recoverable; under-notification is a strict-liability breach.

## What to file with PDPC

PDPC Thailand provides a notification form. Verify the current form and submission method at [pdpc.or.th](https://www.pdpc.or.th). At minimum, expect to provide:

- Nature of the breach (one paragraph)
- When discovered, when it occurred (or "unknown — under investigation")
- Number of affected individuals (estimate is fine if exact unknown — update later)
- Types of Personal Data involved (general + whether s26 sensitive categories)
- Cause (root cause if known; "under investigation" otherwise)
- Likely consequences for individuals
- Containment + remediation actions taken (or planned)
- Steps individuals can take to protect themselves
- DPO contact details

## Notifying affected data subjects (high-risk breach)

**Channels (in order of preference):**
1. Email to the address on file
2. In-app banner on next launch
3. Push notification (only if email + in-app aren't reaching them)

**Content** — explain in plain Thai (or the data subject's language of communication):
- What happened
- When
- What Personal Data was involved
- What you've done about it
- What the data subject should do
- How to contact the DPO

## Tech-measure exception?

Thai PDPA does **not** have an explicit "tech measure renders harm unlikely" exception equivalent to Singapore's s26D(5) or GDPR Article 34(3)(a). However, the **risk-to-rights-and-freedoms** assessment naturally takes into account whether data was encrypted, hashed, or otherwise rendered useless to an attacker. Document the assessment basis.

## Vendor / sub-processor breaches

When a Data Processor (your sub-processor) experiences a breach affecting your data:

- s40(2) requires the Data Processor to **notify the Data Controller** of the breach
- Your DPA with the processor should require this without undue delay (best practice: contractually require ≤24 hours so you have time to assess)
- The 72-hour clock starts when **you (as Data Controller) become aware** — typically when the processor notifies you

Document this chain in your incident log (when the processor became aware → when they notified you → when you assessed).

## Records and audit

s39(8) requires the Data Controller to maintain records of security measures. After any breach, **add the post-incident remediation** to those records — this is part of the demonstrable accountability principle and likely to be reviewed by PDPC if they investigate.

## Penalty exposure

| Failure | Maximum administrative fine | Source |
|---|---|---|
| Fails s37 (including breach notification) generally | THB 3M | s83 |
| Fails s37 involving sensitive data | **THB 5M** | s84 |

Plus s81 personal liability for directors / managers responsible — and potential s79 criminal liability if the underlying breach involves sensitive-data misuse.

## Operational checklist (incorporate into the runbook)

- [ ] Pre-fill the PDPC breach notification form (latest version) before any incident occurs
- [ ] DPO + backup contact both have access to submit
- [ ] Pre-staged data-subject notification email template in Thai (and English if applicable)
- [ ] Documented incident log location with the awareness-timestamp pattern
- [ ] Annual review of the runbook
- [ ] Vendor DPAs include breach-notification clauses requiring notice without undue delay

See `templates/INCIDENT_RESPONSE.md.template` for a starting runbook.
