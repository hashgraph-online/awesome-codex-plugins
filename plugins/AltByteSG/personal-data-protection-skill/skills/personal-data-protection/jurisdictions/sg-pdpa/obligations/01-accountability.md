# Part 3 — Accountability (s11–12)

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

## s11(2) — Responsibility for personal data in possession or under control

**Rule:** the organisation is responsible for personal data it holds — including data held by data intermediaries (sub-processors) on its behalf.

**Implementation layer:** [01 Non-technical](../../../layers/01-non-technical.md) (vendor contracts), [02 Architecture](../../../layers/02-architecture.md) (sub-processor selection).

**Evidence to maintain:** signed DPAs with each sub-processor; written sub-processor register naming each vendor and what they do.

## s11(3)–(5) — DPO designation

**Rule:** the organisation **must designate at least one individual** responsible for ensuring compliance, and must make their business contact information available to the public.

**Implementation layer:** [01 Non-technical](../../../layers/01-non-technical.md).

**Operationalisation:**
- Designate a primary DPO and a backup contact (the breach clock doesn't pause if the primary is unreachable).
- Publish the DPO email in the privacy policy, in-app help, and any public website.
- Keep a written appointment record on file.

For solo founders: you are the DPO. Document this explicitly — "the DPO is [your name], reachable at [email]".

## s12(a) — Develop and implement policies and practices

**Rule:** the organisation **must develop and implement policies and practices** necessary to meet its obligations under the Act.

**Implementation layer:** [01 Non-technical](../../../layers/01-non-technical.md), [06 Disclosure](../../../layers/06-disclosure.md).

**Operationalisation:**
- Public privacy policy + T&C
- Internal incident-response runbook (see [`templates/INCIDENT_RESPONSE.md.template`](../../../templates/INCIDENT_RESPONSE.md.template))
- Internal SOPs for: complaint handling, access requests, correction requests, retention sweeps, consent withdrawal
- Internal staff AUP if more than one person has data access

## s12(b) — Complaint-handling process

**Rule:** must develop a process to receive and respond to complaints regarding application of the Act.

**Implementation layer:** [01 Non-technical](../../../layers/01-non-technical.md).

**Operationalisation:**
- Stable channel (e.g. `privacy@yourdomain` or DPO email)
- Surfaced in the privacy policy and in-app help
- Target SLA: 30 calendar days (PDPC guidance)
- Tracking: at minimum, an issue tracker tag

## s12(c)–(d) — Communicate to staff; make information available on request

**Rule:** must communicate policies and practices to staff, and make information available on request.

**Implementation layer:** [01 Non-technical](../../../layers/01-non-technical.md).

**Operationalisation:**
- Internal onboarding material covering the Act and the staff AUP
- Acknowledgement records for staff who've read the AUP
- Public privacy policy already satisfies the public-facing portion of "available on request"

## Penalty exposure (this Part)

Contravention of Part 3 can carry the s48J(3) financial penalty — see [07-offences.md](07-offences.md) for the cap calculation. PDPC also typically issues a written direction requiring remediation alongside (or instead of) a financial penalty.

## What "demonstrable compliance" looks like in practice

If a PDPC inspector visited tomorrow morning, they would expect to see:

- A named DPO, with contact details published
- A privacy policy that matches what the application actually does
- An incident-response runbook that's been read by anyone who would need to act on it
- A vendor register with current DPAs
- A retention schedule that matches the cleanup jobs actually running
- Training / acknowledgement records if multi-person team

Not all of this needs to be elaborate — for a small team, it can fit in a single internal wiki page. The point is that the documents exist, are current, and someone can find them.
