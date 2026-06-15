# Codex Execution Profile — codex-approval

Read the sibling base skill `../SKILL.md` before acting. This profile is the
Codex-native execution path for getting independent Fable/Claude-family approval
through ATM/NTM.

## Steps

1. Identify the exact plan, research, diff, `SynthesisPacket`, or
   `PerspectivePlan` paths Fable must review. Use absolute paths when possible;
   do not ask Fable to judge only your summary.
2. Inspect the dedicated validator lane before sending anything:
   `tmux list-sessions`, `tmux list-panes -a`, then `tmux capture-pane -p -t <target> -S -80`.
3. Use only an idle dedicated Fable/Claude-family pane. If the known pane is
   busy, use another idle validator lane or create a fresh ATM/NTM validator.
4. Send a bounded prompt that says the reviewer must not modify files and must
   return `VERDICT: PASS|WARN|FAIL`, `COMMANDS RUN:`, `judge_source:`, and
   `REASONS:`.
5. After the verdict, capture the transcript into
   `.agents/council/ntm-captures/` and write
   `.agents/council/<YYYY-MM-DD>-fable-approval-<slug>.md`.
6. For fanout discovery, write an `ApprovalEdge` under
   `.agents/discovery/<run-id>/approval-edge.yaml` that links the
   `SynthesisPacket`, every `PerspectivePlan`, the Fable artifact, and the tmux
   capture.
7. Gate on the result: PASS continues; WARN requires plan edits or an explicit
   accepted-risk note; FAIL blocks implementation.

## Guardrails

- Never use `claude -p` or `claude --print`; Claude-family approval comes from
  an interactive ATM/NTM pane.
- Never paste into a busy pane.
- Persist both the tmux capture and the normalized council artifact.
- Treat a judge that ran/read nothing as unverified, not approved.
- `WARN is not` a silent pass; unresolved warnings must be explicit in the
  `ApprovalEdge` before work proceeds.
- Reserve the ceremony for one-way doors (architecture forks, cross-agent
  contracts, product decisions); routine runtime/CLI slices take the
  vertical-slice path in `$discovery` instead.
- When the approval gates implementation, mirror the verdict artifact (or a
  compact proof packet) to a tracked durable path before the gated bead/epic
  closes; gitignored `.agents/` state in a temporary worktree is not a proof
  surface.
