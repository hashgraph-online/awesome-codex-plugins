# Tending the ATM swarm — operator loop, convergence, close

> **Provenance / ownership.** Extracted verbatim from `skills/using-atm/SKILL.md`
> (payload-diet, age-verification-economics-ebec.8 / age-skills-audit-fable-l6ic.8).
> Swarm-**tending doctrine** — the nudge / restart / stop / converged ladder,
> the "meter LIES" discipline, and the two-tick stall rule — is **owned by the
> `ntm` skill** ([`../../ntm/SKILL.md`](../../ntm/SKILL.md)). What lives here is
> the **ATM-runner view**: the operator-loop tick order and the ATM-substrate
> convergence/close discipline. These are ATM-specific deltas over the `ntm`
> tending doctrine, not a second source of truth.

## Tending the swarm (operator loop)

Run one tick at a time; take the first action whose trigger fires:

- **A peer says `ACTION NEEDED`, `Hey! Listen!`, `merge gate`,
  `unblock-condition`, or asks for a verdict/dry-run before merge/close** →
  interrupt broad watching and answer that gate first. Run the named verifier,
  then surface the result in a channel the peer can read. If Agent Mail reads are
  degraded, use a bead note, PR comment, or raw tmux relay with `C-m` plus
  capture evidence. A mail send alone is not proof the peer was answered.
- **A pane is rate-limited or auth-expired** → rotate the account / relaunch the
  pane, then re-send its in-flight bead. Do not let a dead pane look idle.
- **A pane is wedged** (no output, not at a prompt) → nudge it once; if still
  wedged, kill + relaunch and re-dispatch its bead.
- **A pane is context-saturated** (forgetting earlier instructions, repeating
  itself) → have it write a handoff, then relaunch fresh and re-dispatch.
- **A worker finished its bead** (PR merged, bead closed) → dispatch the next
  `br ready` bead to it.
- **Many review beads open, few closing** → flip the swarm to review-only and
  drain the backlog before taking new feature work.
- **Otherwise** → observe; do not nudge a healthy working pane.

> **The wedged-vs-working judgment depends entirely on reading the pane CORRECTLY — see [`continuity-and-meter.md`](continuity-and-meter.md). The `atm` meter lies.**

## Convergence + shutdown

The swarm is done when: `br ready` is empty, no pane has an in-flight bead, and
the last few CI runs are green. Confirm with `atm activity` (all panes idle) and
`br ready` (empty) before tearing down with `atm kill <session>`. Don't shut down
on a transient quiet patch — a rate-limited pane also looks idle.

## Single-writer + merged-before-close (cards 17–18, cp-4gj6; POLICY → gate cp-hxp6)

For assurance-close contexts, the gate cp-hxp6 enforces: a bead is durable only
when its branch is **merged to trunk** and the commit is visible on the canonical
store. A pane that closes a bead before merging puts protection OFF — the split-brain
incident of 2026-06-09 was caused by an unmerged trio. The fix is not behavioral:
the gate enforces it structurally.

**Read canonical, not shared main.** Every reader of bead/verdict state must target
the canonical store (the bead's worktree branch or the trunk after merge). `main`
in a shared checkout is stale relative to in-flight worktree branches. A reader that
declares "stuck" or "closed" based on a stale `main` read is reporting on phantom
state. Verify bead state on the bead's branch or via `br show` against the live
server; do not declare convergence from a stale checkout.
