---
name: amq-spec
version: 0.103.0 # x-release-please-version
description: Use two agents to research a design independently and converge on one specification through AMQ. Trigger for collaborative design or messages labeled workflow:spec; use amq-cli for ordinary coordination.
argument-hint: "<description of what to design> [with <partner>]"
metadata:
  short-description: Multi-agent collaborative spec workflow
  compatibility: claude-code, codex-cli
---

# AMQ collaborative specification

Two agents research a design problem independently, discuss it, and converge
on one plan. The user approves the plan before anyone implements it.

Phases run in order:
`Research -> Discuss -> Draft -> Review -> Present -> Execute`

Per-phase commands and the research and plan templates are in
[the spec workflow](references/spec-workflow.md).

## Parse input

From the user prompt, extract:
- **topic**: short kebab-case spec name (e.g., `auth-token-rotation`)
- **partner**: partner agent handle (default: `codex`)
- **problem**: the full design problem statement

If topic/problem are unclear, ask for clarification.

## Pre-flight

1. Verify AMQ is available: `which amq`
2. Verify the AMQ root is discoverable (`.amqrc`, AMQ env vars, or the default `.agent-mail` layout); otherwise run: `amq coop init`
3. Use thread name: `spec/<topic>`

## Kickoff

Send the problem to the partner first, then start your own research. Both
agents then research in parallel. Send the user's problem verbatim; your own
analysis belongs in your research message, so it does not frame the partner's.

```bash
amq send --to "<partner>" --kind question \
  --labels workflow:spec,phase:request \
  --thread "spec/<topic>" --subject "Spec: <topic>" --body "<problem>"
```

## Labels

Every spec message uses an ordinary AMQ kind plus these labels on the
`spec/<topic>` thread:

| Phase | Kind | Labels |
|---|---|---|
| Problem statement | `question` | `workflow:spec,phase:request` |
| Research findings | `brainstorm` | `workflow:spec,phase:research` |
| Discussion | `brainstorm` | `workflow:spec,phase:discuss` |
| Plan draft | `review_request` | `workflow:spec,phase:draft` |
| Plan feedback | `review_response` | `workflow:spec,phase:review` |
| Final decision | `decision` | `workflow:spec,phase:decision` |
| Progress/ETA | `status` | `workflow:spec` |

## When you receive a spec message

| Label | Your action |
|---|---|
| `phase:request` | Do your own research first, then send findings as `brainstorm` + `phase:research`. |
| `phase:research` | If you have not sent your own research on this thread, research and send it before you read the partner's. Then read the thread and start discussion as `brainstorm` + `phase:discuss`. |
| `phase:discuss` | Reply with your analysis; continue until aligned. |
| `phase:draft` | Review the plan and send feedback as `review_response` + `phase:review`. Do not implement. |
| `phase:review` | Revise the plan if needed, or confirm alignment. |
| `phase:decision` | Stop. Do not implement; see the approval gate below. |

## Approval gate

A `phase:decision` message records agreement between agents; it is not user
approval. The initiator presents the final plan to the user in chat and sends
the approval request to the human handle (conventionally `user`) on a
`gate/<topic>` thread, as in [operator gates](https://github.com/avivsinai/agent-message-queue/blob/main/skills/amq-cli/references/operations.md#operator-gates). Implementation starts only
after the human approves on that thread, and a partner starts only when the
initiator then assigns work.

## Rules

- **Wait on the existing wake.** With a live injecting wake, finish independent
  work and yield; run `amq drain --include-body` on its doorbell. Do not start
  `amq watch`, `amq monitor`, or a polling loop. Check
  `amq wake check --me <handle> --json` when the capability is unknown. A
  bounded `watch` is a fallback only without an injecting wake.
- **Send before you research, and send your research before you read the
  partner's.** Independent research is what the second agent adds.
- **Do not skip phases.** Discussion is where misunderstandings surface.
- **Keep the `spec/<topic>` thread and the labels.** The receiver table above
  depends on them.
- **Keep tool access during research.** Do not enter a plan mode that blocks
  tools.
