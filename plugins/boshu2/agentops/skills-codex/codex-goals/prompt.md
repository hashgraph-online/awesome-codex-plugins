# Codex Execution Profile — codex-goals

Read the sibling base skill `../SKILL.md` (full overview, critical constraints,
output spec, quality rubric, examples, troubleshooting) before acting. This
profile is the Codex-native, step-ordered execution path; the base SKILL.md is
the source of truth. The one inviolable rule: **a goal MUST have a
machine-checkable done-condition, or it loops forever.**

## Steps

1. **Confirm the feature is live.** Run `codex features list | grep '^goals'` —
   expect `goals    stable    true`. Run `codex doctor | grep -i 'goals DB'` —
   expect `integrity ok`. Never assume the shape from memory; the base is
   verified against `codex-cli 0.137.0`. If disabled, `codex features enable
   goals` (persists to `~/.codex/config.toml`) or pass `-c goals=true` per run.
2. **Write the objective + done-condition.** Draft ONE testable objective. State
   the loop contract inline: the **objective** (one sentence — what "done"
   produces), the **done-condition** (a machine-checkable gate: `bd ready` empty,
   `pytest -q` exit 0, file present, lint clean), and **guardrails** (paths in
   scope, what not to touch). If you cannot name a verifying command, STOP and
   tighten the objective — a vibe is not a done-condition.
3. **Pick the launch form.** Interactive/supervised: `codex -C <repo> -a never`,
   then inside the TUI, use the goals slash command to state the objective and done-condition (interactive
   `codex` DOES take `-a`/`--ask-for-approval`). Unattended worker: `codex exec
   -C <repo> -s workspace-write -o /tmp/codex-goal-result.md "GOAL: <objective>.
   ITERATE UNTIL DONE. Done-condition: <gate>. Guardrails: only touch <paths>. On
   convergence: commit + close beads + write summary."`
4. **Set sandbox + policy correctly for `exec`.** `codex exec` is already
   non-interactive — it returns command failures to the model rather than
   prompting, so **no approval flag is needed**, and `-a`/`--ask-for-approval` is
   REJECTED by `exec` (`unexpected argument '-a' found`). Use `-s
   workspace-write` for editing workers; pin policy explicitly with `-c
   approval_policy=never` if required; use
   `--dangerously-bypass-approvals-and-sandbox` ONLY inside an already-sandboxed
   host. Add `--json` for a JSONL event stream and `-o FILE` for the final report.
5. **Monitor + resume.** Tail `--json` or the pane for the iterate → check →
   continue cycle; confirm each tick re-runs the gate (contact with the
   done-condition, not just motion). Resume an interrupted goal on the SAME host:
   `codex exec resume --last "continue toward the goal"` — Goals state is durable
   in host-local SQLite, so the objective is preserved.
6. **Converge + publish.** When the done-condition passes, re-run the gate
   YOURSELF (do not trust Codex's self-report), then publish to shared state:
   `git commit`, `bd close`, and an Agent Mail / `.agents` summary.
7. **Report.** Return exactly three things — the **Goal** (objective +
   done-condition as launched), the **Status** (`converged` | `iterating` |
   `stalled` | `failed` + the resolved session/goal id), and the **Artifact**
   (commit SHA / closed bead ids / the green gate command + its passing output).

## Guardrails

- **A goal without a done-condition loops forever and burns budget.** Define the
  machine-checkable termination before launch (step 2). No gate → no goal.
- **Never `claude -p` to spawn the worker.** Goals is a *Codex* loop; drive it
  with `codex exec` (Pro sub) or an interactive `codex` NTM pane (OAuth). `claude
  -p` bills per-token against the API, not the Max sub — banned for worker
  dispatch.
- **`-a` is interactive-only; do NOT pass it to `codex exec`.** It aborts the
  launch outright. Pin policy in `exec` with `-c approval_policy=never` instead.
- **Set the sandbox explicitly for unattended runs.** An over-broad sandbox on an
  unsandboxed host is destructive; `--dangerously-bypass-approvals-and-sandbox`
  is for externally-sandboxed boxes only.
- **Goals state is host-local SQLite (`~/.codex/goals_1.sqlite`).** It does not
  sync across the fleet — a goal set on Mac is invisible on bushido. Treat the
  worker host as the source of truth and resume on the same host.
- **Verify before acting.** No remembered flag shapes — `codex features list` /
  `--help` first (step 1).
- **Publish on convergence.** A live Codex session is unreadable to other agents;
  only the committed/announced compression makes the work visible (step 6).
- **Multi-account lanes go through `caam`.** `caam exec codex <profile> --` keeps
  each Pro lane isolated; don't hand-juggle `CODEX_HOME`.
- **Backstage only.** Never surface Codex / Goals / AUTODEV / loop framing in
  client-facing AI Partner content.
