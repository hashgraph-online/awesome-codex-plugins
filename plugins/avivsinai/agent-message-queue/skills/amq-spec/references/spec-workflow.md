# Spec workflow

Each agent researches independently, then both discuss and agree on a plan
that the user approves before implementation. The workflow uses ordinary AMQ
commands (`amq send`, `amq drain`, `amq thread`) with the kinds and labels in
[the skill's label table](../SKILL.md#labels). Only the generic AMQ kinds
(`question`, `brainstorm`, `review_request`, `review_response`, `decision`,
`status`) with `workflow:spec` labels are valid spec messages. "Spec" avoids a
collision with Claude Code plan mode.

## Phases

```
1. RESEARCH (parallel) -> 2. DISCUSS (ping-pong) -> 3. DRAFT (main agent drafts) -> 4. REVIEW (partner) -> 5. PRESENT (to user) -> 6. EXECUTE
```

| # | Phase | Who | What happens | Gate to proceed |
|---|---|---|---|---|
| 1 | **Research** | Both agents (parallel) | Initiator sends problem statement. Both do independent research and submit findings. | Both research submissions sent |
| 2 | **Discuss** | Both agents | Read each other's findings and align on architecture, trade-offs, and scope over several rounds. | Alignment reached |
| 3 | **Draft** | Main agent | Main agent sends concrete implementation plan draft. | Partner receives draft |
| 4 | **Review** | Partner agent | Partner reviews draft and sends feedback; main agent revises if needed. | Plan agreed |
| 5 | **Present** | Main agent | Main agent presents the plan and raises the approval gate. | **User approves on the gate thread** |
| 6 | **Execute** | Per user direction | Implement approved plan. | — |

Do not send a finished spec without the research and discussion phases, and do
not send a draft before both agents exchanged research.

All spec messages use thread `spec/<topic>` (example: `spec/auth-redesign`).
Read it at any time with `amq thread --id "spec/<topic>" --include-body`; the
labels show the phase:

- `phase:request` -> kickoff/problem statement
- `phase:research` -> research submissions
- `phase:discuss` -> discussion rounds
- `phase:draft` -> plan draft
- `phase:review` -> plan review feedback
- `phase:decision` -> final agreed plan

## Phase 1: Research (parallel)

**Initiating agent:**
```bash
# 1) Send the problem statement (no findings yet)
amq send --to "<partner>" --kind question \
  --labels workflow:spec,phase:request \
  --thread "spec/<topic>" --subject "Spec: <topic>" \
  --body "Problem: <what needs to be designed>"

# 2) Research the codebase, constraints, and external docs

# 3) Submit your findings
amq send --to "<partner>" --kind brainstorm \
  --labels workflow:spec,phase:research \
  --thread "spec/<topic>" --subject "Research: <topic>" \
  --body "<your findings using template below>"

# 4) With a live injecting wake, yield; drain when its doorbell arrives.
# Only without an injecting wake: amq watch --timeout 120s
```

**Receiving agent:**
```bash
# 1) Research first; do not read partner research from the thread yet

# 2) Submit your findings
amq send --to "<partner>" --kind brainstorm \
  --labels workflow:spec,phase:research \
  --thread "spec/<topic>" --subject "Research: <topic>" \
  --body "<your findings>"

# 3) Then read the full thread
amq thread --id "spec/<topic>" --include-body
```

## Phase 2: Discuss (ping-pong)

```bash
amq thread --id "spec/<topic>" --include-body

amq send --to "<partner>" --kind brainstorm \
  --labels workflow:spec,phase:discuss \
  --thread "spec/<topic>" --subject "Discussion: <topic>" \
  --body "<analysis + open questions>"

# Continue rounds until aligned; drain on each wake doorbell.
amq drain --include-body
```

## Phase 3: Draft (main agent)

```bash
amq send --to "<partner>" --kind review_request \
  --labels workflow:spec,phase:draft \
  --thread "spec/<topic>" --subject "Plan: <topic>" \
  --body "<plan using template below>"
```

## Phase 4: Review (partner)

```bash
amq send --to "<partner>" --kind review_response \
  --labels workflow:spec,phase:review \
  --thread "spec/<topic>" --subject "Review: <topic>" \
  --body "<review feedback>"
```

The main agent revises and re-sends the draft if needed. An optional
`phase:decision` message then records the agreed plan for the partner:

```bash
amq send --to "<partner>" --kind decision \
  --labels workflow:spec,phase:decision \
  --thread "spec/<topic>" --subject "Final: <topic>" \
  --body "<final agreed plan>"
```

## Phase 5: Present to the user

The main agent synthesizes the final plan, presents it in chat, and sends the
approval request to the human handle on a `gate/<topic>` thread. That gate, not
the `phase:decision` message, is the approval: nobody implements until the human
answers on it. Human-handle seeding and guardrails are in
[operator gates](https://github.com/avivsinai/agent-message-queue/blob/main/skills/amq-cli/references/operations.md#operator-gates).

```bash
amq send --to user --thread "gate/<topic>" --kind question \
  --subject "APPROVAL: <decision>" \
  --body "<final plan summary; what you need the human to approve>"
```

## Phase 6: Execute

Implement the approved plan, following the user's direction on scope and
rollout.

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
