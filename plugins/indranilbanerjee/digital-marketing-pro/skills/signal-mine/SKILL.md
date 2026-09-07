---
name: signal-mine
description: "Triage a raw dump of external material — news, social threads, community discussions, competitor moves, sales-call notes — into content angles the brand has authority to make, each mapped to a pillar with a format and timeliness window, plus an explicit dropped-signals list recording why the rest were rejected. Triggers on \"/digital-marketing-pro:signal-mine\", \"mine this\", \"what content is in here\", \"turn this industry news into ideas\", \"any angles for us in this thread\". Requires the brand profile (pillars, audience, competitors) and stops without one; unverified claims route to /digital-marketing-pro:verify-claims before anything cites them; surviving angles feed /digital-marketing-pro:content-engine."
argument-hint: "[brand-name] [--signals <pasted material>]"
user-invocable: true
---

# /digital-marketing-pro:signal-mine

The intelligence layer between "interesting" and "ours to say". Raw input comes
from anywhere — a newsletter, a Reddit thread, three competitor posts, notes
from yesterday's sales calls. The output is only the angles this brand has
standing to make, each mapped to a pillar, with everything else explicitly
dropped.

The mapping is the value. Any model can turn news into generic content ideas;
the discipline is refusing the ideas that do not serve this brand's authority.

## Inputs

- **The dump** — pasted material, in any shape. More is fine; this skill's job
  is triage.
- **The brand profile** — pillars, audience, positioning, competitors from
  `~/.claude-marketing/brands/{slug}/`. **No profile → stop**: signal-mining
  without pillars produces trend-chasing, which is the exact failure mode this
  skill exists to prevent. Run /digital-marketing-pro:brand-setup first.

## Process

1. Split the dump into discrete signals (a claim, an event, a sentiment, a
   number, a competitor move).
2. For each signal, ask the standing question: *does this brand have something
   to say here that its audience would rather hear from it than from anyone
   else?* Pillar fit is necessary but not sufficient — authority fit decides.
3. For signals that pass: name the angle (the brand's specific take, not a
   summary of the signal), the pillar, a format, and a timeliness window.
4. For signals that fail: list them as dropped, with the reason. This list is
   half the deliverable — it is the record of discipline, and the user may
   overrule it with context you lack.

## Output structure

```
# Signal mine — {brand}, {date}

## Angles ({n})
### A1. [The angle — the take, not the topic]
**From signal:** [one-line source reference]
**Pillar:** [brand pillar]  **Timeliness:** [act this week / evergreen / expires ~date]
**Format:** [post / article / newsletter section / campaign hook]
**Why this brand:** [one sentence of standing — why this take is credibly ours]

## Dropped ({n})
- [signal] — [why: off-pillar / no standing / competitor's story to tell /
  stale by the time we publish / compliance risk]

## Sourcing note
[Which signals carry claims that need verification before anything cites them —
route those through /digital-marketing-pro:verify-claims before drafting]
```

## Critical rules

- **An angle is a take, not a topic.** "AI regulation is changing" is a topic.
  "The new rules reward exactly the disclosure work our clients already do" is
  an angle. Return angles.
- **Authority beats relevance.** A signal can be perfectly on-pillar and still
  be dropped because the brand has nothing distinctive to add. Say that
  plainly.
- **Timeliness is honest.** A "react this week" label on something that takes
  three weeks to produce is a plan to be late. Match the window to the brand's
  real production speed.
- **Claims from pasted material are unverified by definition.** Nothing cites
  a pasted number until it has been through verification — pasted text carries
  no provenance, and provenance is the house rule.
- **The dropped list always ships.** An output with ten angles and no
  rejections means the triage did not happen.
