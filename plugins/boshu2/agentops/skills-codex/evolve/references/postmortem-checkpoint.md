# Mandatory checkpoint: session-PR threshold (soc-n75z)

> Stop reason #6 of `$evolve`. NOT terminal — gates the next cycle, not the loop's existence. Derivation: the 2026-05-19 and 2026-05-20 sessions both shipped 5-6 PRs while the agent self-graded "HEALTHY" without running a real council; STOP got written as if it were post-mortem completion. This procedure closes that gap.

## When this fires

At Step 7 boundary, after a cycle whose result is `improved` or `regressed`
(`$session_pr_count` is the canonical count from `scripts/session-pr-scope.sh --count`):

```bash
if [ "$session_pr_count" -ge "${SESSION_PR_THRESHOLD:-5}" ] \
   && [ "$session_pr_count_at_last_checkpoint" -lt "${SESSION_PR_THRESHOLD:-5}" ]; then
  # checkpoint fires once per crossing — not repeatedly at every cycle past 5
  run_postmortem_checkpoint
fi
```

The check is **edge-triggered** (fires when the counter first crosses the threshold), not level-triggered. After PASS/WARN, the loop continues until either another stop reason fires OR another threshold crossing — e.g., at `2 × SESSION_PR_THRESHOLD = 10`, the checkpoint re-fires for a second post-mortem.

## What it MUST do

1. **Invoke `$post-mortem --deep`** on the cycles since the last checkpoint (or session start). `--deep` runs 3 same-vendor judges in adversarial posture.

   - Do NOT use `--mixed`. Cross-vendor (Codex availability) is an infrastructure dependency that should not block the loop gate. Reserve `--mixed` for strategic architecture decisions (e.g., the DUEL.md precedent), not per-session health checks.
   - Do NOT use single-judge mode. Single-judge sweeps are too weak for a gate that enables continued autonomous work — the whole point of the checkpoint is adversarial counter-balance against the author who just wrote the cycles.

2. **Wait for the verdict file** at `.agents/council/<date>-<scope>-postmortem/verdict.md`. The verdict file's first non-blank line must start with `## Council Verdict: <PASS|WARN|FAIL>`.

3. **Branch on verdict:**

   | Verdict | Action |
   |---|---|
   | `PASS` | Continue the ladder. Next cycle's `notes` field MUST record the verdict path. |
   | `WARN` | Continue the ladder. Next cycle's `notes` field MUST emit the council's caveats verbatim — they need to trace through `cycle-history.jsonl` so the loop's recorded behavior reflects what was acknowledged. |
   | `FAIL` | Write `.agents/evolve/STOP` with the verdict path embedded. Do NOT clear. Surface the council's required-follow-up list to the operator. |

4. **Treat non-convergence as FAIL.** If after 600 seconds the verdict file is missing, malformed, or the council's judges disagreed irreconcilably after a second pass, default to FAIL. **Absence of evidence is NOT evidence of pass.** The 2026-05-20 failure mode was an empty 2-minute cron pass treated as council completion; this rule is the corrective.

## What it MUST NOT do

- **Never self-grade.** The agent who ran the cycles is the same agent doing the post-mortem. Self-attestation is definitionally invalid for the gate; council enforcement is the structural requirement.
- **Never write `.agents/evolve/STOP` without a council verdict file.** STOP without a verdict is the 2026-05-20 anti-pattern — the file becomes a self-imposed pause that the same agent (or operator) clears without rigor. Every STOP written by this checkpoint must cite a verdict path that resolves to a FAIL verdict.
- **Never run `$post-mortem` without `--deep` from this checkpoint.** A light-touch cron-fire pass that writes learnings but skips Phase 1 council does not satisfy the gate. The 2026-05-20 cron `$post-mortem` was insufficient by design.

## Pre-creation signal (opt-in, not shipped)

The pre-creation counterpart to this post-merge checkpoint — `hooks/session-pr-counter.sh` (PR #362, soc-1aou), which fired on `gh pr create` at `count >= threshold - 1` — was **removed** in the 3.0 hookless teardown (#511). AgentOps ships no hook. The reusable session-PR count it provided now lives in `scripts/session-pr-scope.sh` (the canonical `$session_pr_count` source — `scripts/session-pr-scope.sh --count`). Re-author the always-on pre-creation signal as an **opt-in** hook via the hooks-authoring skill if you want it.

This checkpoint is the *post-merge* gate — it fires after PR #N+1 has merged, before cycle N+1 enters Step 1. It is **mandatory** and cannot be bypassed (the loop genuinely waits on the verdict file), unlike the advisory pre-creation signal:

| Layer | Trigger | Default | Status |
|---|---|---|---|
| `scripts/session-pr-scope.sh` (wrap as an opt-in hook via hooks-authoring) | `gh pr create` at `count >= threshold-1` | Advisory | Reusable count; not shipped as a hook (removed in #511) |
| `evolve` checkpoint #6 | Cycle boundary after `count >= threshold` | Mandatory | Structural council enforcement before the next cycle starts |

## Configuration

| Variable | Default | Effect |
|---|---|---|
| `SESSION_PR_THRESHOLD` | `5` | Matches soc-waxr documentation default. The 2026-05-19 session (6 PRs, 3 self-corrections) and 2026-05-20 session (5 PRs, 1 self-correction + 1 confirmation-bias verdict) are the two derivation points. Do not change without a third data point. |
| `EVOLVE_POSTMORTEM_TIMEOUT_SEC` | `600` | Max wait for verdict file. Past this, treat as FAIL. |
| `EVOLVE_POSTMORTEM_COUNCIL_FLAG` | `--deep` | Override only with operator sign-off in a follow-up PR; reverting to single-judge or `--mixed` requires a council justifying the change. |

## Failure modes this closes

The 2026-05-20 post-mortem (`.agents/council/2026-05-20-evolve-204-208-postmortem/verdict.md`) found WARN with Q4 FAIL:

> The "post-mortem" that "cleared" cycle 208 was a cron-fire that wrote 5 learning files and appended a harvest entry. No Phase 1 (council) ran. No Phase 2 extraction with adversarial review. No Phase 3 backlog processing. No verdict file was produced.
>
> Cycle 208's notes contain the string "HEALTHY verdict from $post-mortem cron" — a verdict that does not exist in any file the council directory contains.

That cycle-history entry transformed an absence (no council ran) into a positive claim (clearance exists) in an append-only ledger. Stop reason #6 prevents that pattern by requiring a real verdict file path before continuing.

## Cross-references

- `skills/post-mortem/SKILL.md` — the post-mortem skill this checkpoint invokes
- `skills/council/SKILL.md` — the council skill `--deep` runs against
- `skills/ship-loop/SKILL.md` — the soc-waxr session-scope doctrine source
- `scripts/session-pr-scope.sh` — canonical session-PR count source (the pre-creation hook was **removed** in #511; re-author as an opt-in hook via hooks-authoring)
- `CLAUDE.md` § "Autonomous-session scope" — top-level doctrine reference
- `.agents/council/2026-05-20-evolve-204-208-postmortem/verdict.md` — the derivation council (local; gitignored)
