---
name: customer-commitment-validation
description: Evaluate whether customer, sales, investor, partner, or product meetings produced real commitment and advancement instead of polite interest. Use when interpreting meeting outcomes, stalled leads, trial requests, letters of intent, preorders, warm intros, case-study offers, unclear next steps, or compliments after a pitch.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.3"
  displayName: Customer Commitment Validation
  category: Marketing
  tags: customer-discovery,sales,validation,startups,commitment
---

# Customer Commitment Validation

Use this skill after a product, sales, partnership, investor, or customer
conversation where the team needs to decide whether the meeting created real
progress. The core test is what the other person gave up: time, reputation, or
money.

## Source Traceability

Primary source: The Mom Test by Rob Fitzpatrick, especially chapters 5 and 8.
Guidance is paraphrased for this MIT repo; authoring notes used converted EPUB
lines 2365-2790 and 3613-4108.

## Commitment Currencies

| Currency | Examples | Signal Strength |
|----------|----------|-----------------|
| Time | Scheduled next meeting with goals, trial setup work, real feedback session | Medium |
| Reputation | Intro to a decision maker, internal championing, public case study | Medium to high |
| Money | Deposit, preorder, paid pilot, purchase order, signed letter of intent | High |

Compliments, vague "keep me posted" replies, and future-tense buying promises
are not commitments.

An advancement must move the real-world funnel to a specific next decision or
action. A next step without an owner, date, or customer-side effort is usually
weak interest.

## Review Workflow

1. Restate the meeting context and what the team hoped would happen next.
2. Classify the outcome as commitment, advancement, rejection, weak interest, or
   bad data.
3. Identify what the other person gave up, if anything.
4. If the outcome is fuzzy, propose a concrete next ask that creates a decision.
5. If there was rejection, preserve the learning and decide whether it changes
   the product, segment, positioning, or sales path.
6. If there was commitment, define the owner, date, success criteria, and follow
   up.

## Outcome Classification

| Outcome | Meaning | Action |
|---------|---------|--------|
| Commitment | They gave up time, reputation, or money | Track and follow through |
| Advancement | They moved the real-world funnel forward | Confirm next step details |
| Rejection | They declined a concrete ask | Learn and update assumptions |
| Weak interest | They were friendly but gave up nothing | Ask for a concrete next step or stop counting it |
| Bad data | Outcome is only compliments or future hypotheticals | Return to evidence or commitment |

## Output Format

```markdown
# Commitment Review

## Meeting
- Person/company:
- Context:
- Stage:

## Outcome
- Classification, evidence, currency given up:

## Interpretation
- What this proves / does not prove:
- Risks, missing decision makers, approval path:

## Next Ask
[A concrete ask that creates advancement or rejection.]

## Follow-Up
- Owner, deadline, success criteria:
```

## Workflow

Use `workflows/classify-meeting-outcome.md` when the user provides notes,
transcripts, CRM entries, or a narrative of how a meeting ended.

## Quality Bar

- Do not call a meeting successful because it felt positive.
- Do not count a lead as real until they had a chance to reject a concrete ask.
- Do not overvalue free trials that cost the customer nothing.
- Do not ignore missing decision makers or approval paths.
- Treat rejection as useful evidence, not as failure.
