---
name: lead-magnet-ideas
description: "Turn a content topic, campaign, or existing piece into 3-5 named, briefable lead-magnet ideas cut from the brand's real assets and expertise, each graded on lead-gen power × build effort, with funnel-fit and delivery notes plus a not-recommended list that pre-empts the obvious-but-weak options. Triggers on \"/digital-marketing-pro:lead-magnet-ideas\", \"lead magnet for this\", \"what should we give away\", \"opt-in ideas\", \"freebie for this campaign\", \"turn this into a lead magnet\". Reads the brand profile for audience, expertise, and existing IP; routes onward to /digital-marketing-pro:email-sequence for the post-capture nurture or /digital-marketing-pro:funnel-architect when there is nowhere to send the lead yet."
argument-hint: "[brand-name] [--topic <topic or piece>] [--max-effort low|medium|high]"
user-invocable: true
---

# /digital-marketing-pro:lead-magnet-ideas

The bridge between content that earns attention and a funnel that captures it.
A good lead magnet is not "an ebook" — it is the specific artifact this
audience would trade an email for, on this topic, from this brand, buildable
with what the brand already has.

## Inputs

- **The topic** — a subject, a campaign, or an existing piece the magnet
  should extend.
- **The brand profile** — audience, expertise, existing assets, funnel stage
  from `~/.claude-marketing/brands/{slug}/`. The best magnets are cut from IP
  the brand already owns: the internal checklist, the template they use on
  every engagement, the dataset nobody else has.
- `--max-effort` — cap suggestions at what the team can actually build.

## The grading matrix

Every idea is graded on two axes, stated with reasons — ungraded idea lists
outsource the real decision back to the user:

| Grade | Lead-gen power | Build effort |
|---|---|---|
| **A** | Audience actively searches for this; clear next step toward the offer | Assembled from existing assets in hours |
| **B** | Wanted once seen; adjacent to the buying decision | Days; some new material |
| **C** | Nice-to-have; collects curiosity, not intent | A real project |

The sweet spot is power-A × effort-A: the artifact the brand already uses
internally, packaged. Flag any power-C × effort-C idea as not worth building.

## Output structure

```
# Lead magnets — [topic], {brand}

## 1. [Specific name — "The 23-point pre-launch QA checklist", never "a checklist"]
**What it is:** [2-3 sentences — contents, format, length]
**Cut from:** [the existing brand asset or expertise it is built from]
**Power: A/B/C** — [why: search demand, intent proximity, offer fit]
**Effort: A/B/C** — [why: what exists vs what must be made]
**Funnel fit:** [what it qualifies the lead FOR — the next step it sets up]
**Delivery:** [landing page + email / in-content unlock / webinar follow-up]

[... 3-5 ideas, best power-to-effort ratio first ...]

## Not recommended
[Ideas that look obvious for this topic but grade badly here, with the grade —
pre-empting the "what about an ebook?" conversation]

## Next steps
[Route onward: /digital-marketing-pro:email-sequence for the nurture that
follows capture; /digital-marketing-pro:funnel-architect if there is nowhere
to send the lead yet]
```

## Critical rules

- **Specific, or it does not ship.** Every idea carries a name a designer
  could brief from. "A template" is a category; "the client-onboarding email
  sequence template with the 6 send-day rules annotated" is an idea.
- **Tied to existing IP first.** An idea requiring expertise the brand does
  not demonstrably have is graded effort-C and flagged — a magnet the brand
  cannot credibly deliver damages the exact trust it exists to build.
- **Grade honestly, both axes, with reasons.** The grades are the deliverable;
  the ideas are commodity.
- **A magnet must lead somewhere.** Each idea names what it qualifies the lead
  for. Capture with no next step is a list nobody emails.
- **Compliance applies.** Gated content in regulated industries carries the
  same disclaimer and claims rules as published content — a magnet is not a
  compliance side door.
