---
name: codex-approval
description: Use when Codex needs Fable approval through
---
# codex-approval

Ask an always-on ATM/NTM Claude-family validator, usually Fable, to approve or
reject a Codex plan or fanout `SynthesisPacket`. This is the Codex-side bridge
for cross-vendor approval: Codex prepares the packet, an independent
interactive Claude-family pane reviews it, and the verdict is saved as a council
artifact with a tmux capture.

## Critical Constraints

- **Never use print-mode Claude.** Do not run `claude -p` or
  `claude --print`; approval must come from an interactive ATM/NTM pane.
- **Do not hijack a busy pane.** If the known Fable validator pane is working,
  use another idle dedicated validator pane or create a fresh one.
- **Approval is an artifact, not a chat memory.** Save the pane transcript under
  `.agents/council/ntm-captures/` and write a normalized
  `.agents/council/<date>-fable-approval-<slug>.md`.
- **Fable judges the plan, not your summary of it.** Send absolute paths to the
  plan, research, diff, or packet and ask the pane to read them directly.
- **WARN is not a silent pass.** Either update the plan to address the warning,
  or record why the warning is accepted before continuing.
- **Reserve the ceremony for one-way doors.** Routine runtime/CLI slices take
  the MVP vertical-slice path; approval ceremony does not substitute for
  adversarial acceptance tests.
- **Gating approval needs a durable proof surface.** When this approval gates
  implementation, mirror the council artifact (or a compact proof packet:
  verdict, judge source, capture path, required changes) to a **tracked**
  durable location — `docs/` or a tracked `.agents/` path in the canonical
  checkout — before the gated bead/epic closes. `.agents/council/` inside a
  temporary worktree is typically gitignored and is deleted with the worktree;
  approval evidence that lives only there is stranded (finding 6 of the
  2026-06-12 review). Verify with `git check-ignore <path>` — an ignored path
  is not a proof surface.

## Fanout Packet Contract

For open-ended/high-risk discovery, approval consumes the packet contract in
[`docs/contracts/codex-fanout-approval-packet.md`](../../docs/contracts/codex-fanout-approval-packet.md):

- `PerspectivePlan`: one independent planner lens. Fable must receive every
  perspective path, not just the selected one.
- `SynthesisPacket`: the selected or merged candidate plan plus rejected
  alternatives, rationale, risks, and open questions.
- `ApprovalEdge`: the normalized edge proving which Fable lane reviewed which
  packet, where the tmux capture lives, and how PASS/WARN/FAIL was handled.

`WARN is not` approval by omission. If the verdict is WARN, the edge must cite
the updated packet or an explicit accepted-risk note before work proceeds.

## Workflow

### Phase 1: Build the approval packet

Choose a short slug and identify the exact artifacts the validator should read.
Prefer committed or absolute paths:

The request must include:

- role: independent Fable/Claude-family reviewer
- artifacts to read
- decision question
- required output shape
- explicit instruction not to modify files
- for fanout discovery: all `PerspectivePlan` paths and the `SynthesisPacket`

### Phase 2: Find an idle validator pane

List likely panes and inspect the target before sending text:

```bash
tmux list-sessions
tmux list-panes -a -F '#{session_name}:#{window_index}.#{pane_index} cmd=#{pane_current_command} title=#{pane_title}'
tmux capture-pane -p -t agentops--codex-plan-fable-approval:1.1 -S -80
```

Use the pane only when it is idle at a prompt. If it is busy, launch or select a
different dedicated validator lane through ATM/NTM. Keep the lane single-purpose:
one approval request at a time.

**Boot race — wait for input-ready before Phase 3.** A *freshly launched* validator
lane (Claude or codex) returns from `spawn` before the agent has booted to its input
box; a request sent in the first few seconds is silently dropped and you wait forever
on a verdict that was never requested. Confirm the pane is at a real input prompt
first: `tmux capture-pane -p` should show the `❯`/input box (not a splash or booting
screen). If the validator lane is a **codex** pane, `tmux capture-pane`/`atm save` can
return ANSI-only/empty — read readiness with `atm codex preflight --json` (proceed only
on `codex-live`/`goal-completed`) instead. See `using-atm` (Observing lanes / OC-047).

### Phase 3: Send the request

Use `atm send` when available; `tmux send-keys` is acceptable for a known pane —
but only after the pane is confirmed input-ready (see Phase 2 boot-race note).
**Then verify the request actually engaged before Phase 4:** after sending, confirm
the pane LEFT its idle prompt and is reviewing (a working/thinking indicator, or for
a codex lane `atm codex wait-goal-engaged --json`, non-zero = it did not take). Do not
capture a "verdict" from a pane that never received the request — a blank/idle pane is
not a PASS. If the validator is a codex pane driven through the goal flow, dispatch
with `atm send --codex-goal --pane N --file <packet>` (a bare send may not fire), or
the `asend` readiness-gated helper. Keep the prompt bounded and auditable:

```text
You are an independent Fable Claude-family reviewer. Do not modify files.
Review <PLAN or SYNTHESIS_PACKET> and its supporting artifacts. Judge whether
the plan is implementable, correctly scoped, and safe with respect to Law 0 and
Codex subscription auth.
Return exactly:
VERDICT: PASS|WARN|FAIL

COMMANDS RUN:
judge_source: fable-claude-code
<commands/read operations>

REASONS:
- concise bullets
If WARN or FAIL, name required plan changes.
```

### Phase 4: Capture and normalize the verdict

After the pane returns a final answer, capture the transcript:

```bash
STAMP="$(date -u +%Y%m%d_%H%M%S)"
CAPTURE=".agents/council/ntm-captures/${SESSION}_${PANE}_${STAMP}.txt"
tmux capture-pane -p -t "$TARGET" -S -2000 > "$CAPTURE"
```

Then write:

```text
.agents/council/<YYYY-MM-DD>-fable-approval-<slug>.md
```

The artifact must contain:

- YAML frontmatter with `verdict`, `judge_source`, `model`, `plan`, optional
  `research`, and `capture`
- `# Fable Approval: <title>`
- `## Council Verdict`
- `## Commands Run`
- `## Reasons`
- `## Required Changes` when verdict is WARN or FAIL

For fanout discovery also write:

```text
.agents/discovery/<run-id>/approval-edge.yaml
```

The `ApprovalEdge` records the source `SynthesisPacket`, every
`PerspectivePlan`, the validator pane, tmux capture, verdict artifact, verdict,
required changes, and accepted risks.

### Phase 5: Gate on the result

- `PASS`: continue.
- `WARN`: apply the required plan edits or record an explicit accepted-risk note.
- `FAIL`: stop implementation and fix the plan before trying again.

### Phase 6: Closeout — make the proof durable

Before the bead/epic this approval gated is closed, mirror the evidence out of
ephemeral state:

```bash
# In the CANONICAL checkout (not the temp worktree):
git check-ignore .agents/council/<date>-fable-approval-<slug>.md \
  && echo "IGNORED — mirror to a tracked path" || echo "tracked — OK"
```

If the artifact path is ignored (or lives in a worktree that will be removed),
copy the council artifact — or write a compact proof packet (verdict,
judge_source, capture path, required changes/accepted risks) — to a tracked
durable location and commit it with the arc. The tmux capture may stay local;
the normalized verdict artifact may not.

## Quality Rubric

- [ ] Validator is Claude-family/Fable and independent from the Codex author.
- [ ] Request named exact artifacts, not a lossy prose summary.
- [ ] Pane was checked idle before text was sent.
- [ ] No print-mode Claude command was used.
- [ ] tmux capture exists under `.agents/council/ntm-captures/`.
- [ ] Council artifact includes verdict, judge source, commands/read operations,
  reasons, and capture path.
- [ ] WARN/FAIL has required changes and blocks or updates the next step.
- [ ] The work actually warranted the ceremony (one-way door / cross-agent /
  product decision) — routine slices were routed to the vertical-slice path.
- [ ] When the approval gated implementation, the verdict artifact (or compact
  proof packet) is mirrored to a tracked durable path before the gated
  bead/epic closes — not stranded in an ignored worktree `.agents/` dir.

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Pane is busy | A prior validation is still running | Do not send; use another idle validator or spawn a fresh lane |
| No verdict shape | Prompt was too loose | Re-prompt the same pane with the exact output contract |
| Capture is empty | Wrong pane target or scrollback | Re-check `tmux list-panes`; capture with a larger `-S` |
| Artifact path mismatch | Filename was guessed later | Put the capture path in frontmatter immediately |
| Approval cannot be reproduced | Validator read a summary only | Re-run against the real plan/research paths |

## See Also

- `using-atm` for the ATM/NTM substrate contract.
- `agent-mail` for cross-pane coordination and file reservations.
- `codex-exec` for Codex worker auth and subscription billing guardrails.
