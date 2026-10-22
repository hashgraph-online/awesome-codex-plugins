---
name: sdlc-design
description: Turn an accepted .sdlc/feature-slug/intent.md into a policy-constrained, reviewer-approved spec.md when asked to design or specify an approved feature. Do NOT use for raw idea discovery, coding, test execution, PR review, deployment, or production monitoring.
---

# SDLC Design

Run Stage 2 of 6 in the AI-Native SDLC playbook described in `docs/PLAYBOOK.md`.

## Purpose

Generate a testable specification from accepted intent while making policy
collisions and unresolved decisions visible.

The primary value of this stage is the **Flagged concerns** section. Never solve
or hide a concern silently.

## Entry gate

Locate `.sdlc/<slug>/intent.md`.

Proceed only if it exists and declares `Status: accepted`.

If the artifact is missing, still draft, or lacks explicit acceptance, route the
work back to `sdlc-plan` and stop.

Read the entire accepted intent before generating requirements or a design.

## Discover governing policy

Discover available organization skills and relevant project instructions before
designing. Look specifically for brand, security, compliance, and data-handling
skills or policies.

List each discovered skill or policy that constrains the design.

If none are found, log that no organization skills were available. Do not pretend
that an undiscovered policy has been applied.

Read the applicable guidance and constrain the proposed design by it.

## Procedure

1. Read the accepted `intent.md` in full.
2. Discover and read applicable organization skills and project policies.
3. Log the skills or policies found, or log that none were found.
4. Convert desired outcomes into numbered requirements that can be verified.
5. State clear non-goals to protect the accepted scope.
6. Design the architecture, flow, data model, and interfaces within policy.
7. Describe API, schema, persistence, and contract changes when applicable.
8. Identify every collision among intent, policy, constraints, and open questions.
9. Mark every concern as `blocking` or `non-blocking` and explain why.
10. Describe how the final implementation will be verified.
11. Write `.sdlc/<slug>/spec.md` and show the complete draft to the user.

Use plain language. Do not replace a requirement with an implementation preference.

## Required artifact

Start with this contract structure. Add `Status: draft` directly below the title
while the document awaits review, then change it to `Status: accepted` only after
explicit approval.

```markdown
# Spec: [feature name] (from intent.md [date])

## Source intent
[one-line link to or quote from the accepted intent.md]

## Requirements
1. [testable requirement]
2. [testable requirement]
[etc.]

## Non-goals
[explicitly what this change does NOT do]

## Design
[architecture, flow, data model, interfaces]

## Data and interfaces
[API/schema changes, persistence, contracts]

## Flagged concerns
[CRITICAL: each blocking/non-blocking issue, never silently resolved]
- [concern]: [why it matters], [blocking|non-blocking]

## Verification strategy
[how we'll prove the spec worked]
```

Keep the contract headings and the concern format unchanged.

## Flagged concerns rules

A concern is blocking when the specification cannot safely proceed without a
decision or approval. Example: a new database table requires operations approval.

A concern is non-blocking when it is valuable to resolve but the scoped change can
ship without it. Example: the first release does not cover every locale.

Flag both kinds. Do not downgrade a blocker because a workaround seems likely.

Do not silently resolve an open question, policy collision, exception, or risk.

When a concern needs a decision, state the decision needed and its owner if known.

## Exit gate

Show the entire spec, including every flagged concern, then stop and ask exactly:

> Reviewer, do you accept this scope and the flagged concerns?

Accept only explicit human approval. Do not code, reinterpret approval, or proceed
from an implied response.

After explicit approval, change the status to `accepted` in `spec.md` and commit
with `Status: accepted` in the commit message.

If the reviewer requests changes, revise the draft, preserve or update concerns,
and repeat the exit gate.

## Handoff

Hand off the accepted `.sdlc/<slug>/spec.md` to `sdlc-build`.

Include the policy sources consulted and every unresolved non-blocking concern.

Do not decide a blocker on behalf of the reviewer or organization.
