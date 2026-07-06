---
name: customer-segment-slicing
description: Narrow broad customer categories into specific, reachable who-where segments for customer discovery, positioning, traction tests, sales outreach, or SEO personas. Use when feedback is inconsistent, the market is too broad, personas are vague, users request too many different features, or the team does not know where to find target customers.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.3"
  displayName: Customer Segment Slicing
  category: Marketing
  tags: customer-discovery,segmentation,startups,positioning,research
---

# Customer Segment Slicing

Use this skill before customer conversations, traction tests, sales outreach, or
persona work when the target customer is too broad to produce consistent
evidence. A useful segment is a who-where pair: who has the problem and where
the team can find them.

## Source Traceability

Primary source: The Mom Test by Rob Fitzpatrick, especially chapters 6-7.
Guidance is paraphrased for this MIT repo; authoring notes used converted EPUB
lines 2791-3610.

## Slicing Workflow

1. Start with the broad audience or market.
2. Split by demographics, role, use case, behavior, buying context, urgency, or
   current workaround.
3. For each slice, state the motivation or problem that makes them care.
4. Keep slicing any group that still produces mixed goals or feature requests.
5. Add where to find each group: communities, events, tools, platforms, job
   titles, search queries, partners, directories, or physical locations.
6. Score the slices by reachability, expected value, urgency, consistency, and
   team fit.
7. Pick one starting segment for the next discovery or traction pass.

## Useful Segment Tests

Ask:

- Would most people in this slice share the same problem or goal?
- Can we find at least five of them this week?
- Do they already spend time, money, attention, or reputation on this problem?
- Would their feedback point toward one product direction rather than many?
- Are there hidden stakeholders, buyers, users, or partners?
- Is this slice narrow enough to learn from but valuable enough to matter?

## Output Format

```markdown
# Customer Segment Slicing

## Broad Segment
[Starting audience.]

## Candidate Slices
| Segment | Problem or Goal | Where To Find Them | Current Behavior | Reachability | Value | Urgency | Consistency | Fit |
|---------|-----------------|--------------------|------------------|--------------|-------|---------|-------------|-----|

## Recommended Starting Segment
[One who-where pair.]

## Why This Segment
- Strong shared motivation:
- Easy access path:
- Evidence to gather:
- Risks:

## Next Conversations
1. [Person/source]
2. [Person/source]
3. [Person/source]
```

## Workflow

Use `workflows/slice-customer-segment.md` for a full segmentation pass.

## Quality Bar

- Do not accept categories like "students", "businesses", or "creators" without
  further slicing.
- Do not optimize positioning or features from mixed-segment feedback.
- Do not choose a segment that cannot be found.
- Do not talk only to impressive people if they are not representative users,
  buyers, or stakeholders.
