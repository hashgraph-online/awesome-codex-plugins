# Optional Multi-Agent Extension

Use this extension only when independent roles would materially improve the
artifact. Default to the single-agent loop for normal writing tasks.

## When To Use

Use multi-agent when at least one condition is true:

- High-stakes artifact: legal, executive, investor, public launch, safety, policy
- Long artifact: multiple sections, chapters, or audiences
- Ambiguous artifact: uncertain thesis, structure, evidence, or audience fit
- Multi-domain artifact: needs technical, factual, style, and stakeholder review
- User explicitly asks for multiple agents, independent reviewers, or parallel critique

Do not use multi-agent when:

- The task is a short draft, small edit, or simple rewrite
- The user wants speed over review depth
- Roles would duplicate the same work
- Context is too sensitive to spread across agents
- The platform cannot actually dispatch subagents and role simulation would be misleading

## Roles

- **Controller**: owns the user relationship, constraints, decisions, merge policy, and final answer.
- **Planner**: proposes structure, argument, section order, or scene sequence.
- **Drafter**: writes from the approved or best-current plan without inventing preferences.
- **Critic**: reviews against artifact-specific rubrics; split into parallel critics when useful.
- **Editor**: applies accepted changes while preserving constraints and user intent.
- **Preference Distiller**: records only user decisions, not raw agent suggestions.

## Workflow

1. Controller frames the artifact and decides if multi-agent is justified.
2. Controller states the multi-agent plan and why single-agent is insufficient.
3. Planner receives only task-local context and produces a plan.
4. Controller checks the plan, outputs a mandatory `PLAN CHECKPOINT`, and waits unless the user explicitly requested the fast-draft path.
5. If rejected, revise only criticized elements, reissue the full plan, and checkpoint again.
6. If approved, Drafter writes from the plan.
7. Critics review independently. Use parallel critics only when their scopes differ.
8. Controller merges critique into targeted revision proposals.
9. User accepts, rejects, or adjusts meaningful proposals.
10. Editor applies accepted changes only.
11. Preference Distiller records reusable rules only from user decisions.

## Parallel Critic Pattern

Use distinct critic scopes to avoid duplicate work:

- Structure critic: flow, section order, thesis, pacing
- Evidence critic: factual support, caveats, missing data, citations
- Audience critic: reader needs, tone, actionability
- Style critic: clarity, voice, concision, prose rhythm
- Risk critic: legal, safety, reputational, operational, continuity issues

Give each critic a narrow prompt:

```text
Role: Evidence Critic
Artifact type: [type]
Audience: [audience]
Goal: [goal]
Constraints: [constraints]
Task: Find evidence gaps, unsupported claims, and caveats only.
Return: top issues, severity, and proposed fixes. Do not rewrite the draft.
```

## Merge Policy

The Controller resolves conflicts:

- User constraints beat agent recommendations.
- Artifact-specific rubric beats generic taste.
- Higher-risk issues beat style preferences.
- Multiple independent critics flagging the same issue increases priority.
- Conflicting critiques become options for the user, not hidden unilateral edits.
- Rejected critic suggestions must not be applied later.

## Context Isolation

When actual subagents are available:

- Give each agent the minimum task-local context needed.
- Do not pass private preference journals unless the user opted in.
- Do not pass other agents' conclusions to independent critics before they review.
- Ask agents for findings and proposed fixes, not final authority.
- Keep the Controller responsible for final synthesis.

When actual subagents are not available, do not claim that multiple agents ran.
Instead say "I can simulate role-based passes" and keep the output clearly
labeled as single-agent role simulation.

## Preference Learning

Agents do not create preferences. Only the Controller may record preference
signals, and only from:

- User-approved plans
- User-rejected plans with reasons
- Accepted, rejected, adjusted, or undone edits
- Explicit standing preferences
- Repeated user corrections

Agent critiques, draft variants, or internal role votes are non-signals until
the user decides.

## Output Shape

Before approval, output only the mode, plan, and checkpoint:

```text
Multi-Agent Mode
Reason: [why optional multi-agent is justified]
Roles: [Planner, Drafter, Critics, Editor, Preference Distiller]

Plan
[controller-checked plan]

PLAN CHECKPOINT
Reply "approve" to draft from this plan, or describe what to change.
```

After the plan checkpoint passes, or when the user explicitly requested the
fast-draft path, use this compact form unless the user asks for a full trace:

```text
Multi-Agent Mode
Reason: [why optional multi-agent is justified]
Roles: [Planner, Drafter, Critics, Editor, Preference Distiller]

Plan
[controller-approved plan]

Draft
[draft]

Critique Synthesis
- [issue, source role, severity]

Proposed Changes
- [change, scope, reason, risk]

Decision Log
- [accepted/rejected/adjusted/unresolved]

Learned Preferences
[None unless user decisions support them]
```
