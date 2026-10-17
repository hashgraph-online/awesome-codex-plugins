---
name: customer-discovery-conversations
description: Plan and audit customer discovery conversations that produce concrete evidence instead of compliments, opinions, hypotheticals, or feature-request noise. Use when planning customer interviews, rewriting interview scripts, validating startup ideas before building, avoiding biased questions, or applying Mom Test-style customer learning.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.3"
  displayName: Customer Discovery Conversations
  category: Marketing
  tags: customer-discovery,customer-interviews,startups,validation,research
---

# Customer Discovery Conversations

Use this skill to turn customer conversations into decision-quality evidence.
The goal is not approval for an idea. The goal is to learn concrete facts about
customers' lives, current behavior, constraints, costs, workarounds, and risks.

## Source Traceability

Primary source: The Mom Test by Rob Fitzpatrick, especially chapters 1-4 and 8.
Guidance is paraphrased for this MIT repo; authoring notes used converted EPUB
lines 236-2362 and 3613-4108.

## Workflow Routing

| Need | Use |
|------|-----|
| Rewrite an interview script | `workflows/rewrite-interview-questions.md` |
| Run a batch of conversations | `workflows/run-conversation-batch.md` |
| Recover from compliments, hypotheticals, or ideas | `workflows/recover-bad-data.md` |
| Segment is too broad | `customer-segment-slicing` |
| Product or sales meeting needs a real next step | `customer-commitment-validation` |
| Raw notes need synthesis | `customer-learning-notes` |

## Conversation Workflow

1. State the decision the conversations should improve.
2. Name the riskiest assumptions, including at least one uncomfortable question.
3. Choose the narrow customer or stakeholder type. If the segment is fuzzy, use
   `customer-segment-slicing` first.
4. Prepare up to three learning goals for this type of person.
5. Rewrite questions toward current behavior and specific past examples.
6. Keep the conversation about the customer until there is enough evidence to
   discuss a solution.
7. During the conversation, anchor vague claims to recent examples and dig into
   current costs, workarounds, constraints, and goals.
8. Capture notes, signals, and follow-up tasks for review.

## Question Rules

- Talk about the customer's life, work, tools, constraints, and recent past.
- Ask scary questions early enough that the answer can still change the plan.
- Turn opinions, compliments, and hypotheticals into requests for examples.
- Ask what already costs them time, money, reputation, or operational pain.
- Save the pitch until the customer evidence justifies discussing a solution.

## Good Evidence

Prefer recent examples, current workarounds, money/time/reputation already
spent, existing tools and budgets, named stakeholders, decision paths, and strong
emotion backed by a concrete story.

Treat compliments, opinions, future promises, generic claims, and feature
requests without motivation as weak evidence.

## Output Format

```markdown
# Customer Discovery Plan

## Context
- Decision:
- Segment:
- Risk questions:

## Conversation Guide
| Goal | Ask About | Avoid | Follow-Up |
|------|-----------|-------|-----------|

## Evidence To Capture
- Current behavior, past examples, workarounds:
- Costs, budget, constraints, stakeholders:
- Strong emotion, follow-up, commitment:

## Review Criteria
- What changed in our beliefs?
- What is still unknown?
- What are the next three questions?
```

## Quality Bar

- Do not help users collect approval or compliments.
- Do not ask customers to design the product for the team.
- Do not treat "I would buy this" as validation without commitment.
- Do not run conversations without a decision, segment, and learning goals.
- Prefer fewer high-value conversations over many generic interviews.
