---
name: amq-spec
version: 0.34.1
description: >-
  Parallel-research-then-converge design workflow between two agents. Use this
  skill when the user wants two agents to independently think through a design
  problem before aligning on a solution — "spec X with codex", "design X
  together", "both agents think through X", "brainstorm architecture together",
  "parallel research then joint proposal", "think through separately then
  align", "careful thought from both sides before coding", or any variation
  where the user wants collaborative design rather than just splitting
  implementation work. Also use this when you receive a message labeled
  workflow:spec and need to know the correct receiver-side protocol. Not for
  sending simple messages or reviews (use /amq-cli), implementing completed
  designs, or creating document templates.
argument-hint: "<description of what to design> [with <partner>]"
metadata:
  short-description: Multi-agent collaborative spec workflow
  compatibility: claude-code, codex-cli
---

# /amq-spec — Collaborative Specification Workflow

This skill defines a structured two-agent specification flow.

Use canonical phases in order:
`Research -> Discuss -> Draft -> Review -> Present -> Execute`

Detailed step-by-step protocol lives in `references/spec-workflow.md`.
This file is the concise operational entrypoint.

## Parse Input

From the user prompt, extract:
- **topic**: short kebab-case spec name (e.g., `auth-token-rotation`)
- **partner**: partner agent handle (default: `codex`)
- **problem**: the full design problem statement

If topic/problem are unclear, ask for clarification.

## Pre-flight

1. Verify AMQ is available: `which amq`
2. Verify the AMQ root is discoverable (`.amqrc`, AMQ env vars, or the default `.agent-mail` layout); otherwise run: `amq coop init`
3. Use thread name: `spec/<topic>`

## First Action: Send problem to partner IMMEDIATELY

The entire point of the spec workflow is parallel research — both agents
exploring the problem independently, then comparing notes. Every second you
spend researching before sending is a second your partner sits idle waiting
for the problem statement. That's why the send comes first, even though your
instinct might be to "research first to give better context."

```bash
amq send --to <partner> --kind question \
  --labels workflow:spec,phase:request \
  --thread spec/<topic> --subject "Spec: <topic>" --body "<problem>"
```

Send the user's problem description verbatim — your own analysis goes in the
research phase, not the kickoff. If you pre-analyze, you bias the partner's
independent research, which defeats the purpose of having two perspectives.

## Label Convention

Labels are how both agents and the receiver-side protocol table know which phase the conversation is in. Use existing AMQ kinds plus labels to express spec workflow semantics:

| Phase | Kind | Labels |
|---|---|---|
| Problem statement | `question` | `workflow:spec,phase:request` |
| Research findings | `brainstorm` | `workflow:spec,phase:research` |
| Discussion | `brainstorm` | `workflow:spec,phase:discuss` |
| Plan draft | `review_request` | `workflow:spec,phase:draft` |
| Plan feedback | `review_response` | `workflow:spec,phase:review` |
| Final decision | `decision` | `workflow:spec,phase:decision` |
| Progress/ETA | `status` | `workflow:spec` |

## Quick Command Skeleton

```bash
# Initiate spec with problem statement
amq send --to <partner> --kind question \
  --labels workflow:spec,phase:request \
  --thread spec/<topic> --subject "Spec: <topic>" --body "<problem>"

# Submit independent research
amq send --to <partner> --kind brainstorm \
  --labels workflow:spec,phase:research \
  --thread spec/<topic> --subject "Research: <topic>" --body "<findings>"

# Discuss and align
amq send --to <partner> --kind brainstorm \
  --labels workflow:spec,phase:discuss \
  --thread spec/<topic> --subject "Discussion: <topic>" --body "<analysis>"

# Draft plan
amq send --to <partner> --kind review_request \
  --labels workflow:spec,phase:draft \
  --thread spec/<topic> --subject "Plan: <topic>" --body "<plan>"

# Review plan
amq send --to <partner> --kind review_response \
  --labels workflow:spec,phase:review \
  --thread spec/<topic> --subject "Review: <topic>" --body "<feedback>"

# Optional final decision message
amq send --to <partner> --kind decision \
  --labels workflow:spec,phase:decision \
  --thread spec/<topic> --subject "Final: <topic>" --body "<final plan>"
```

## When You RECEIVE a Spec Message

If you receive a message labeled `workflow:spec`, your action depends on the phase:

| Label | Your action |
|---|---|
| `phase:request` | Read the problem statement, do your **own independent research first**, then submit findings as `brainstorm` + `phase:research` |
| `phase:research` | **Before reading**: check if you've already submitted your own research on this thread. If not, do your own research and submit it first. This preserves research independence — reading the partner's findings before forming your own view contaminates your perspective. Once your research is submitted, read the thread and start discussion as `brainstorm` + `phase:discuss`. |
| `phase:discuss` | Reply with your analysis, continue discussion until aligned |
| `phase:draft` | Review the plan and send feedback as `review_response` + `phase:review`. Your job here is review, not implementation — the plan needs to survive scrutiny before anyone builds it. |
| `phase:review` | Revise plan if needed, or confirm alignment |
| `phase:decision` | Stop. Only the user can authorize implementation. The initiator presents the plan to the user; you wait until the initiator confirms approval and assigns you work. |

**Why the partner doesn't implement**: The spec workflow is a design process.
The initiator owns the relationship with the user and presents the final plan.
If the partner implements without approval, the user loses control over what
gets built. Implementation starts only after the initiator explicitly tells
you the user approved and assigns work.

## Protocol Discipline

These rules exist because violations silently break the workflow's value proposition:

- **Send before researching** — parallel research is the whole point. Pre-researching wastes your partner's time and biases the outcome toward your initial framing.
- **Submit your own research before reading partner's** — reading first contaminates your independent perspective. Two agents who read the same code and reach the same conclusion is less valuable than two agents who explore independently and then compare notes.
- **Don't skip phases** — each phase builds on the previous. Collapsing directly to a finished spec skips the discussion where misunderstandings surface.
- **Use `spec/<topic>` threads and the label convention** — this is how both agents (and the tooling) know which phase the conversation is in. Without consistent labels, the receiver-side protocol table above breaks.
- **Don't enter plan mode during research** if it blocks tool usage — you need tools to explore the codebase.
- **Present the final plan to the user before executing** — the initiator owns the user relationship. After the decision phase, present the plan in chat and wait for explicit approval. Only then assign implementation work to agents.

## Reference

For full protocol details, templates, and phase gates, see:
- [references/spec-workflow.md](references/spec-workflow.md)
