# Spec Workflow

Collaborative specification workflow for multi-agent design tasks.
The word "spec" is intentionally used to avoid collision with Claude Code plan mode.

**Core principle**: each agent researches independently first, then both agents discuss and finalize a plan that is presented to the user for approval before implementation.

This is a **skill-managed protocol** that uses standard AMQ primitives (`amq send`, `amq drain`, `amq thread`) with generic kinds + labels.

## DO NOT SKIP PHASES

You MUST follow every phase in order.

**What you MUST NOT do:**
- Research alone and send a finished spec to partner
- Use invalid kinds — only use generic kinds (`question`, `brainstorm`, `review_request`, etc.) with `workflow:spec` labels
- Skip the discussion phase
- Send a draft before both agents exchanged research
- Implement before user approval

## Phase Order (Canonical)

```
1. RESEARCH (parallel) -> 2. DISCUSS (ping-pong) -> 3. DRAFT (main agent drafts) -> 4. REVIEW (partner) -> 5. PRESENT (to user) -> 6. EXECUTE
```

| # | Phase | Who | What happens | Gate to proceed |
|---|---|---|---|---|
| 1 | **Research** | Both agents (parallel) | Initiator sends problem statement. Both do independent research and submit findings. | Both research submissions sent |
| 2 | **Discuss** | Both agents | Read each other's findings and align on architecture/trade-offs/scope. | Alignment reached |
| 3 | **Draft** | Main agent | Main agent sends concrete implementation plan draft. | Partner receives draft |
| 4 | **Review** | Partner agent | Partner reviews draft and sends feedback; main agent revises if needed. | Plan agreed |
| 5 | **Present** | Main agent | Main agent presents final plan to user in chat AND raises a structural `to:user` gate on `gate/<topic>`, then waits for approval. | **User approves on the gate thread** |
| 6 | **Execute** | Per user direction | Implement approved plan. | — |

## Label Convention (Required)

| Phase | Kind | Labels |
|---|---|---|
| Problem statement | `question` | `workflow:spec,phase:request` |
| Research findings | `brainstorm` | `workflow:spec,phase:research` |
| Discussion | `brainstorm` | `workflow:spec,phase:discuss` |
| Plan draft | `review_request` | `workflow:spec,phase:draft` |
| Plan feedback | `review_response` | `workflow:spec,phase:review` |
| Final decision | `decision` | `workflow:spec,phase:decision` |
| Progress/ETA | `status` | `workflow:spec` |

## CRITICAL RULES

### Research Independence (Phase 1)
- **NEVER** read partner research before sending your own.
- Use normal mode with full tool access for research.
- Submit your own findings first, then read partner findings.

### Discussion Is Required (Phase 2)
- Discuss architecture decisions after exchanging findings.
- Expect multiple rounds, not a single message.
- Align on approach, risks, and scope before drafting.

### User Approval Gate (Phase 5)
- Final plan must be presented to the user in chat.
- ALSO raise a **structural** gate: send the approval request to the initialized human handle (conventionally `user`) on a stable `gate/<topic>` thread. See the Operator Gates section in /amq-cli for canonical mechanics, seeding, and guardrails. An agent-to-agent `phase:decision` message is NOT the approval.
- Wait for explicit user approval (the human's reply on the gate thread) before execution. Partner agents do not implement from a spec decision alone.

## Thread Convention

All spec messages use thread `spec/<topic>` (example: `spec/auth-redesign`).

## Agent Protocol (Step by Step)

### Phase 1: Research (parallel)

**Initiating agent (starts the spec):**
```bash
# 1) Send problem statement request (no findings yet)
amq send --to <partner> --kind question \
  --labels workflow:spec,phase:request \
  --thread spec/<topic> --subject "Spec: <topic>" \
  --body "Problem: <what needs to be designed>"

# 2) Do your own independent research immediately
#    - Explore codebase/files/patterns/constraints
#    - Check external docs if relevant

# 3) Submit your findings
amq send --to <partner> --kind brainstorm \
  --labels workflow:spec,phase:research \
  --thread spec/<topic> --subject "Research: <topic>" \
  --body "<your findings using template below>"

# 4) Wait for partner findings
amq watch --timeout 120s
```

**Receiving agent (got the kickoff request):**
```bash
# 1) Do your own independent research FIRST
#    - Read the kickoff problem statement
#    - Do not read partner research from the thread yet

# 2) Submit your findings
amq send --to <partner> --kind brainstorm \
  --labels workflow:spec,phase:research \
  --thread spec/<topic> --subject "Research: <topic>" \
  --body "<your findings>"

# 3) Then read full thread
amq thread --id spec/<topic> --include-body
```

### Phase 2: Discuss (ping-pong)

```bash
# Read both research submissions
amq thread --id spec/<topic> --include-body

# Discuss differences, trade-offs, and decisions
amq send --to <partner> --kind brainstorm \
  --labels workflow:spec,phase:discuss \
  --thread spec/<topic> --subject "Discussion: <topic>" \
  --body "<analysis + open questions>"

# Continue rounds until aligned
amq watch --timeout 120s
amq drain --include-body
```

### Phase 3: Draft (main agent)

```bash
amq send --to <partner> --kind review_request \
  --labels workflow:spec,phase:draft \
  --thread spec/<topic> --subject "Plan: <topic>" \
  --body "<plan using template below>"
```

### Phase 4: Review (partner)

```bash
amq send --to <partner> --kind review_response \
  --labels workflow:spec,phase:review \
  --thread spec/<topic> --subject "Review: <topic>" \
  --body "<review feedback>"

# If needed: main agent revises and re-sends draft
```

### Phase 5: Present to User

Main agent must:
1. Synthesize final plan from discussion + review
2. Present it directly to user in chat
3. Raise a **structural gate**: address the approval request to the initialized
   human handle (conventionally `user`) on a stable `gate/<topic>` thread:
   ```bash
   # See the Operator Gates section in /amq-cli for human-handle seeding and guardrails.
   amq send --to user --thread gate/<topic> --kind question \
     --subject "APPROVAL: <decision>" \
     --body "<final plan summary; what you need the human to approve>"
   ```
4. Wait for explicit approval (the human's reply on the `gate/<topic>` thread)
5. Not implement before approval; partner agents must NOT implement from the
   agent-to-agent `phase:decision` message alone

The `phase:decision` message below is an **optional partner alignment marker**,
not the user approval. See /amq-cli's Operator Gates section for the canonical
mechanics and guardrails.

Optional partner notification after alignment:
```bash
amq send --to <partner> --kind decision \
  --labels workflow:spec,phase:decision \
  --thread spec/<topic> --subject "Final: <topic>" \
  --body "<final agreed plan>"
```

### Phase 6: Execute

Only after user approval. Follow user direction on scope and rollout.

## Tracking Progress

Use the thread to inspect current phase:
```bash
amq thread --id spec/<topic> --include-body
```

Phase indicators:
- `labels=workflow:spec,phase:request` -> kickoff/problem statement
- `labels=workflow:spec,phase:research` -> research submissions
- `labels=workflow:spec,phase:discuss` -> discussion rounds
- `labels=workflow:spec,phase:draft` -> plan draft
- `labels=workflow:spec,phase:review` -> plan review feedback
- `labels=workflow:spec,phase:decision` -> final agreed plan

## Research Summary Template

```markdown
## Problem Understanding
<your interpretation in your own words>

## Codebase Findings
- <relevant files/patterns/constraints>
- <existing implementations>
- <integration points>

## Proposed Approach
<high-level direction>

## Open Questions
- <questions for discuss phase>

## Risks
- <key risks>
```

## Spec Draft Template (Plan)

```markdown
## Problem Statement
<clear problem definition>

## Proposed Solution
<concrete solution>

## Architecture
<design/components/interactions>

## File Changes
- `path/to/file.ext` — what changes and why

## Decisions Made
- <decision>: <chosen option> because <rationale>

## Trade-offs Considered
- <option A vs B> — why chosen

## Edge Cases
- <case> — handling

## Testing Strategy
- <verification approach>

## Risks
- <risk> — mitigation
```
