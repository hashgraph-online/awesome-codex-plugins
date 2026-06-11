# Codex Execution Profile — Operating Loop Skill

Run the assured operating loop on Codex: drive one ready bead through **claim → work → independent-validate → close → persist**. This profile is the Codex realization of the loop. The canonical methodology, output spec, quality rubric, examples, and troubleshooting live in the sibling `SKILL.md` (and its full form `../SKILL.md`) — read it for anything not spelled out here.

Codex fan-out mapping:
- **Orchestrator** = this main Codex session + `tick.sh`.
- **Worker (fresh context)** = a separate `codex exec` invocation (or NTM pane).
- **Validator (fresh context)** = a *different* `codex exec` invocation (or NTM pane) — never the worker's.

Pick the tracker first: use `br` where `.beads/` is beads_rust, `bd` where it is beads. Check the repo's `AGENTS.md`/`CLAUDE.md` for which wins. If `tick.sh` is present, use its subcommands (`next`, `claim`, `verdict-gate`, `council-gate`, `close`); otherwise use the raw `br`/`bd` + git equivalents shown.

## Steps

1. **Pick + claim (orchestrator).** Read state first, then take the next undone increment:
   ```
   id=$(./tick.sh next)          # or: br ready --json | first unblocked, highest-priority (bd ready / br ready)
   [ -z "$id" ] && echo NO_READY && exit 0
   ./tick.sh claim "$id"          # or: br update "$id" --claim  /  bd update "$id" --claim
   ```
   Read the bead's ACCEPTANCE verbatim — it is the contract for both worker and validator. Confirm `id` is non-empty and now in-progress before dispatching.

2. **Work (worker — fresh `codex exec`, PROPOSES only).** Dispatch a fresh worker context with the bead id, title, and ACCEPTANCE verbatim. The worker: (a) does exactly what ACCEPTANCE requires — no scope creep, no files outside the bead's concern; (b) writes `evidence/<id>.md` with WHAT changed (file:line per change), PROOF (commands run + output, greps, tests), ACCEPTANCE MAP (one line per acceptance point → how met); (c) returns the evidence path + a 3-line summary. It does NOT close, status-set, or self-grade. Confirm `evidence/<id>.md` exists and maps every acceptance point before validating.

3. **Independent validate (validator — different fresh `codex exec`, JUDGES only).** Dispatch a validator in a context that is NOT the worker's. Tell it: you did not author this; author ≠ judge. It reads `evidence/<id>.md` AND the real artifacts it cites (re-runs the commands / opens the files — does not trust the claims), judges each acceptance point strictly, and returns EXACTLY:
   ```
   VERDICT: PASS | FAIL
   COMMANDS RUN: <commands executed + a snippet of each one's output>   # mandatory
   REASONS: 2-4 bullets, each pointing at one of the COMMANDS RUN above
   ```
   Default to FAIL on genuine uncertainty (fail-closed). For higher assurance, run two independent validators in two different `codex exec` contexts.

4. **Gate the verdict.** Run `./tick.sh verdict-gate evidence/<id>.v1.md` (or manually confirm a non-empty COMMANDS RUN). A verdict with no cited commands is **rejected as unverified** — route to a fresh tie-break validator; never act on it. With two validators, run `./tick.sh council-gate evidence/<id>.v1.md evidence/<id>.v2.md`.

5. **Close (orchestrator — sole writer) or reopen.**
   - **PASS** (or council PASS = unanimous + all verified):
     ```
     ./tick.sh close "$id" "<conventional commit msg>" "evidence/<id>.md" <scoped paths...>
     # raw: br close "$id" --reason "...evidence/<id>.md" && git commit
     ```
     The close reason carries the evidence ref; the commit is the durable ledger.
   - **Verified FAIL:** reopen with the validator's REASONS injected → informed fresh-worker retry. Budget **2 retries**, then **ESCALATE**.
   - **Contested/unverified FAIL, or mixed council verdicts:** dispatch a fresh tie-break validator; majority of *verified* verdicts decides; fail-closed if no majority. Record both verdicts; never self-overrule.

6. **Persist + repeat.** `br sync` (or `bd sync`) — JSONL export; git IS the provenance. Loop back to step 1 until `next` is empty.

7. **Emit the precise state word:**
   - **NO_READY** — no schedulable bead right now (blocked/in-progress may remain).
   - **CONVERGED** — no open OR in-progress beads remain.
   - **ESCALATE** — a bead exhausted its retry budget; hand to a human/quorum.

## Guardrails

- **Single writer.** ONLY the orchestrator runs `close`. Workers and validators NEVER close, set status, or self-grade.
- **Author ≠ judge.** The worker `codex exec` and the validator `codex exec` MUST be different invocations — a context grading its own output is biased toward PASS.
- **Evidence or it didn't happen.** Every close cites a real proof surface in `evidence/<id>.md` (commands run + output, greps, test results), not chat memory.
- **Verdict must carry COMMANDS RUN.** A PASS or FAIL with no cited commands is rejected as unverified and routed to a tie-break — never acted on.
- **No `claude -p` / `claude --print` for workers.** This is the Codex profile — use `codex exec` (Pro sub) or NTM panes for worker/validator dispatch. `claude -p` bills the API per-token and is banned.
- **Idempotent.** Each tick reads state first (`next`) and does only the next undone increment — re-running a tick must never double-work or re-pull a closed bead.
- **No Dolt for this loop.** `br`/`bd` (SQLite + JSONL) + git IS the entire state/persistence story.
- **Fail-closed.** Default to FAIL on genuine uncertainty; on no verified majority, do not close.

See the sibling `SKILL.md` (and `../SKILL.md`) for the full output specification, quality rubric, worked examples, and troubleshooting table. Reference implementation (proven n=1): `~/dev/control-plane/{ARCHITECTURE,ORCHESTRATOR,WORKER,VALIDATOR}.md` + `tick.sh`.
