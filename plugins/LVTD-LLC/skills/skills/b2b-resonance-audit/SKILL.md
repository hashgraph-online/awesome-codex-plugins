---
name: b2b-resonance-audit
description: Audit and rewrite B2B sales messaging so the right buyers quickly understand the painful problem, concrete outcome, and mechanism behind the offer. Use when buyers see the company but do not remember it, cannot explain what it does, do not connect it to a trigger, or messaging sounds clever, vague, over-complex, generic, or too simplified for the buyer's world.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: B2B Resonance Audit
  category: Marketing
  tags: b2b-sales,sales,messaging,positioning,copywriting
---

# B2B Resonance Audit

Use this skill when reach exists but the message does not stick. The goal is to
make the offer obvious to the right buyer: who it is for, what painful problem
it solves, what outcome it creates, and how it gets there.

## Source Traceability

Primary source: Unf*ck Your Sales by Jakob Greenfeld, especially the
"Resonance", "Diagnostics", "The Cleverness Fallacy", "The Category-Creation
Fallacy", "The Complexity Fallacy", "The Fifth-Grade Fallacy", "The Shortlist
Law", and "Engineering Resonance" sections.

## Diagnostic Signals

Resonance is likely the constraint when:

- Target buyers have seen the company but cannot recall it when the problem or
  category comes up.
- Buyers cannot plainly explain what the company does.
- The message is clever, abstract, category-creating, over-explained, or packed
  with seller language.
- The offer gets impressions or opens but does not create memory, replies, or
  qualified pull.
- The team keeps rewriting taglines instead of anchoring to a painful trigger.

## Resonance Test

Ask a small sample of target buyers:

- When you think of this problem or category, who comes to mind?
- What do you think this company does?
- What problem do you associate with this company?
- What outcome do you think it creates?

If the company is not recalled, not understood, or not linked to a specific
pain and outcome, treat resonance as the constraint.

## Workflow

### 1. Start With The Pain

Write the problem in the buyer's language. Use terms that would sound natural in
their team chat, CRM notes, internal deck, or Slack thread.

### 2. Make The Outcome Concrete

State the result the buyer gets. Replace abstractions with visible business
effects such as cycle time, risk reduction, revenue quality, saved labor, fewer
failed reviews, or clearer decisions.

### 3. Name The Mechanism

Explain how the result happens without burying the point. The mechanism should
make the claim believable, not turn the message into a product tour.

### 4. Compress The Message

Build one direct sentence or short block:

```text
We help [buyer] fix [pain] by [mechanism], so [outcome].
```

Then cut anything that does not make the message clearer, more specific, or more
credible.

### 5. Repeat It Consistently

Use the same core message across website, outbound, profiles, sales deck, ads,
and founder content until the market can finish the sentence.

## Output Format

```markdown
# B2B Resonance Audit

## Current Message
- Buyer:
- Current wording:
- Main concern:

## Pain, Outcome, Mechanism
| Element | Draft | Evidence / Buyer Language |
|---------|-------|---------------------------|
| Pain | | |
| Outcome | | |
| Mechanism | | |

## Revised Core Message
[One clear version.]

## Consistency Plan
- Website:
- Outbound:
- Sales calls:
- Social/content:
```

## Quality Bar

- Do not reward cleverness if the buyer has to decode the message.
- Do not create a new category when a familiar problem frame would work.
- Do not simplify by removing the buyer's professional language.
- Do not add detail that slows comprehension.
- Optimize for being remembered by the right buyer, not admired by everyone.
