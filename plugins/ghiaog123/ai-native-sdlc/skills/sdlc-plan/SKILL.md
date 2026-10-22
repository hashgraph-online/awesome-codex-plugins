---
name: sdlc-plan
description: Turn a raw feature idea, problem statement, or request such as “plan this feature” into a human-approved .sdlc/feature-slug/intent.md by interviewing the originator before design begins. Do NOT use for architecture design, implementation, testing, review, deployment, or monitoring work.
---

# SDLC Plan

Run Stage 1 of 6 in the AI-Native SDLC playbook described in `docs/PLAYBOOK.md`.

## Purpose

Transform a raw idea into an accepted intent artifact.

Interview the originator. Establish the problem and desired outcome.

Do not choose architecture, implementation details, tools, or solutions in this stage.

## Entry gate

Proceed only when the user has supplied a problem statement, even if it is rough.

If there is no problem statement, ask for one and stop.

If the originator declares the change low-risk — a copy fix, a documentation
correction, a change behind a flag that is off — check the **Sensitive paths** list in
`REVIEW.md` against the files the change would touch. When nothing matches, hand the
change to `sdlc-build` to enter on the fast path, and stop: an interview about a typo
spends the originator's attention on a decision they have already made. When something
matches, say which path it is and run this stage normally. The declaration is theirs to
make; the path check is not negotiable, and the artifact gate enforces it either way.

Derive a short, filesystem-safe kebab-case `<slug>` only after the originator has
identified the feature well enough to name it. Confirm the name when it could be
ambiguous.

## Procedure

1. Read the problem statement carefully before proposing any wording.
2. Restate the problem neutrally to confirm your understanding.
3. Interview the originator about what users cannot do today.
4. Ask why that inability matters to customers, operators, or the business.
5. Ask what breaks, remains costly, or becomes risky if the work is skipped.
6. Ask which users, systems, integrations, and teams are affected.
7. Ask for known limitations, requirements, deadlines, compatibility needs, and
   regulatory or operational constraints.
8. Ask follow-up questions whenever an answer is vague, contradictory, or lacks
   a concrete consequence.
9. Do not turn a requested solution into an assumed problem statement. Ask for
   the underlying user problem and outcome first.
10. Capture unresolved facts as open questions rather than inventing answers.
11. Synthesize the answers into `.sdlc/<slug>/intent.md` using the exact template
    below.
12. Show the full draft to the user, including every open question.

## Required artifact

Write this initial artifact verbatim in structure and labels. Replace only the
bracketed content with confirmed information.

```markdown
# Intent: [feature name]
Author: [name]. Status: draft.

## Problem
[what customers cannot do today]

## Proposed outcome
[what better looks like]

## Affected users and systems
[who and what is impacted]

## Constraints
[limitations or requirements]

## Open questions
[unresolved items]
```

Use the originator's name for `[name]` when it is known. Ask rather than infer it.

Keep the artifact about intent, not a proposed technical solution.

Describe the outcome in observable terms without prescribing how to build it.

## Quality loop

Push on vague answers. For example, “make it better” does not state what a user
cannot do now or what success looks like.

Treat an empty section as a prompt to investigate, not a field to quietly omit.

If constraints are empty while the request clearly has limits, ask about those
limits and revise the draft after receiving an answer.

If the originator cannot answer yet, place the issue in **Open questions**.

Open questions are better than guesses. Never present an inference as a confirmed
fact.

Do not proceed to design merely because the prose sounds complete. The originator
must explicitly approve the intent.

## Exit gate

After showing the draft, stop and ask exactly:

> Does this intent match what you meant?

Accept only an explicit human approval. Do not treat silence, a new request, a
reaction, or a request to continue as approval.

When the human explicitly approves, update the artifact status from `draft` to
`accepted` so the next stage can verify its entry gate. Commit the accepted
artifact with `Status: accepted` in the commit message.

If approval includes corrections, revise the draft and repeat the exit question.

Do not start Stage 2 before this gate is satisfied.

## Handoff

Hand off the accepted `.sdlc/<slug>/intent.md` to `sdlc-design`.

State the artifact path and any remaining open questions in the handoff.

Do not answer those questions on the originator's behalf.
