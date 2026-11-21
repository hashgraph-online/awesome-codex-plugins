# RFC and Post-Mortem Templates

The stationery for the two documents this skill occasionally asks a lane to write.
The rules that decide *whether* to write one (the RFC-required list, the
`accepted`-before-any-builder gate, the P0-P3 severity definitions, and the
required/optional/skip rule for post-mortems) stay in the `suede-agent-teams`
SKILL.md next to their triggers. Read this file when you are about to author one of
the two documents, and fill every section.

## RFC template

```
RFC: [Title]
Date: [date]
Status: draft | accepted | superseded | withdrawn
Deciders: [who has final say]

## Problem Statement
One paragraph: what is broken, missing, or suboptimal? Include the user or system impact.

## Proposed Solution
What we will build or change. Be specific about interfaces, data shapes, and behavioral contracts.

## Alternatives Considered
2–3 alternatives with the reason each was not chosen.

## Risks
What could go wrong with the proposed solution? How is each risk mitigated?

## Success Criteria
How will we know this worked? Observable, measurable signals.

## Decision Record
[filled in after consensus] Accept / Modify / Reject + reason.
```

## Post-mortem template

Keep it blameless: focus on systems, not individuals.

```
Post-Mortem: [Brief title]
Date of incident:
Duration:
Severity: P0 (total outage) / P1 (primary path broken) / P2 (degraded) / P3 (cosmetic)
Author(s):

## Timeline
[time]: [event]
[time]: [detection]
[time]: [first response]
[time]: [resolution]

## Impact
Users affected:
Revenue impact (if known):
Data integrity: affected / not affected

## Root Cause
One sentence: the direct technical cause.

## Contributing Factors
The systemic conditions that made this possible. (What allowed the root cause to reach production?)

## What Went Well
Things that helped detect or contain the incident faster.

## Action Items
| Action | Owner | Due |
|---|---|---|
| ... | ... | ... |

Status: open / closed
```
