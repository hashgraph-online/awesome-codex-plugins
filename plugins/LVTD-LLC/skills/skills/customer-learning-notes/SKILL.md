---
name: customer-learning-notes
description: Turn customer conversation notes, interview transcripts, call summaries, CRM snippets, or research notes into shared team learning and next questions. Use when synthesizing raw customer notes, avoiding founder interpretation bottlenecks, extracting quotes and signals, updating beliefs, or deciding what to ask next.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.3"
  displayName: Customer Learning Notes
  category: Marketing
  tags: customer-discovery,research,notes,synthesis,startups
---

# Customer Learning Notes

Use this skill after customer conversations to turn raw notes into team-readable
evidence. Good notes make it harder to misremember, overfit, or let one founder
become the sole source of customer truth.

## Source Traceability

Primary source: The Mom Test by Rob Fitzpatrick, especially chapter 8 and the
conclusion. Guidance is paraphrased for this MIT repo; authoring notes used
converted EPUB lines 3613-4445.

## Signal Taxonomy

Use these labels when synthesizing notes:

| Label | Meaning |
|-------|---------|
| Pain | Problem, obstacle, annoyance, risk, or cost |
| Goal | Desired outcome, job to be done, or priority |
| Workaround | Current manual process, tool stack, hack, or substitute |
| Money | Budget, cost, value, purchase process, or decision owner |
| Person | Specific stakeholder, competitor, team, buyer, or intro lead |
| Feature | Request, buying criterion, integration need, or implementation clue |
| Emotion | Strong excitement, anger, embarrassment, fear, or skepticism |
| Follow-up | Promise, task, intro, research item, or next step |

## Synthesis Workflow

1. Preserve concrete facts separately from interpretation.
2. Pull out short, useful quotes only when they are needed for traceability,
   positioning, or internal alignment.
3. Tag signals using the taxonomy above.
4. Group evidence by segment, problem, workaround, budget, and commitment.
5. Identify contradictions and mixed-segment noise.
6. Update beliefs, risks, and the next three questions.
7. Recommend whether to continue, narrow the segment, ask for commitments, or
   move to building/testing.

## Confidence Levels

| Level | Use When |
|-------|----------|
| High | Repeated behavior from a focused segment, with concrete cost or commitment. |
| Medium | Specific evidence from a few good-fit conversations. |
| Low | One-off quotes, mixed segments, opinions, or weakly anchored claims. |

## Output Format

```markdown
# Customer Learning Synthesis

## Source Notes
- Conversations:
- Segment:
- Date range:

## Evidence
| Signal | Evidence | Segment | Confidence | Implication |
|--------|----------|---------|------------|-------------|

## Belief Updates
- Stronger / weaker / new / rejected:

## Decisions
- Product, segment, positioning, sales or access:

## Next 3 Questions
1. [Question]
2. [Question]
3. [Question]
```

## Workflow

Use `workflows/synthesize-conversation-notes.md` when the user provides raw
notes, transcripts, call summaries, or interview excerpts.

## Quality Bar

- Do not summarize notes into vibes.
- Do not let one loud quote outweigh repeated behavior from a focused segment.
- Do not mix segments without labeling them.
- Do not treat notes as useful until they have been reviewed and turned into
  updated beliefs or decisions.
