# Serialized Multi-Lane Land Protocol

> **The land-phase contract for landing N beads on a hot, multi-lane `main` with zero clobbers.**
> This is the by-hand discipline behind the [Land Loop](../SKILL.md)
> when the automated `scripts/pawl-land.sh` auto-bind path does not apply — it decays like ungated
> docs unless it lives here, gated. It **consolidates, does not duplicate**, three existing surfaces:
> the rebase-on-reject rule in [`AGENTS-WORKFLOW.md`](../../../AGENTS-WORKFLOW.md) (git serializes
> concurrent pushers), the pawl-before-merge / bead-acceptance rule in
> [`failure-recovery.md`](failure-recovery.md) "Final Batched Validation" +
> [`docs/contracts/pawls.md`](../../../docs/contracts/pawls.md), and the rebase+restamp automation in
> [`scripts/pawl-land.sh`](../../../scripts/pawl-land.sh). Read those for the WHY behind each; this
> doc is the ordered command sequence + the failure playbook.

## Land-token serialization (the core rule)

**One land at a time across lanes — a single serialized land-token.** Implement beads in parallel
worktrees, but **land them serially**: only one lane may be between `git fetch origin main` and a
confirmed-ancestor push at any moment. Parallel *implementation* is fine; parallel *landing* races
the tip and clobbers. `git` itself serializes concurrent pushers (rebase-on-reject); the land-token
is the discipline that keeps you from fighting it — take the token, land one bead end-to-end, release
it, then the next lane takes it.

## The land sequence (verified working, 2026-07-07/08)

Real worked example — a clean `[feat, #trivial-bind]` pair landed on hot `main`:
feat `f93e98478b09d070c6d4dedd1622a916bd999fd8` (age-gascity-port-slate-irye.6) + bind
`42e08037eeff5dfb10a08a5921f0f1f1d2222ed0` (the `#trivial` provenance commit whose parent IS the
feat and which touches only `docs/provenance/ledger.jsonl`, +1 line). The verdict binds the **feat**,
not the bind.

1. **Commit the feat.** `git commit -m "feat(<scope>): <subject> (<bead>)"`
   — WHY: the subject must cite the bead id; the gate and the pawl resolve the bead from the HEAD subject.

2. **Review — FOREGROUND.** `ao pawl review <bead> --scope head`
   — WHY: the codex refuter writes a CONFIRMED verdict to `.agents/pawl-verdicts/<bead>.json`; run it in the FOREGROUND (~3–5 min) because backgrounding reaps the codex subprocess mid-review.
   - **NOTE:** `ao pawl review` runs from a temp script copy and sets `PAWL_UNTRUSTED_REPO=1`, which **SKIPS auto-bind** — so you must do steps 3–4 by hand. (`bash scripts/pawl-review.sh` from the live checkout auto-binds instead; see the [Land Loop](../SKILL.md).)

3. **Emit the sealed verdict.** `ao provenance emit-verdict --file .agents/pawl-verdicts/<bead>.json`
   — WHY: this is the SEALED, hash-chained emit. NEVER hand-append the ledger — a `git add` of a raw edge breaks the hash chain (payload_hash mismatch) and every downstream `provenance.chain` check fails.

4. **Bind commit.** `git commit -m "chore(provenance): bind pawl CONFIRMED verdict for <bead> #trivial"`
   — WHY: the land shape is `[feat, #trivial-bind]` — the verdict binds the FEAT commit, and the `#trivial` tip is waived by the pre-push gate (the ledger append is provenance-only).

5. **Fast-forward or land-script.** `git fetch origin main`
   — WHY: if `HEAD~2 == origin/main` it is a clean fast-forward → `git push origin HEAD:main`. If origin moved, use `scripts/pawl-land.sh <bead>` — it rebases onto the new tip AND **restamps the CONFIRMED verdict onto the post-rebase feat** (the catch-22 fix: rebase changes the feat sha the verdict was bound to).

6. **Prove the landing before close.** `git merge-base --is-ancestor <feat-sha> origin/main`
   — WHY: a push can be REFUSED (lost the race) while the surrounding compound command keeps going; check the push RC AND ancestry. Never read `origin/main`'s tip and assume it is yours. Only after ancestry passes: `ao beads exec close <bead>`.

## Stale-bind drop + re-pawl on tip change

- **STALE-BIND DROP.** A verdict whose sha a rebase invalidated must be **dropped and re-created**
  (re-run step 3, `ao provenance emit-verdict`), **never rebound by hand**. `scripts/pawl-land.sh`
  does this restamp for you; a manual land must re-emit, not edit the ledger.
- **RE-PAWL on tip change.** If the reviewed tree changed after CONFIRMED (a rebase brought in
  conflicting content, or you amended the feat), the verdict no longer describes the pushed tree —
  re-run `ao pawl review <bead> --scope head` before landing. `head_sha` must equal the pushed commit.

## Failure playbook

| Failure | Recovery command | Why |
|---|---|---|
| **non-fast-forward** on push | `scripts/pawl-land.sh <bead>` | rebases onto the moved `origin/main` AND restamps the verdict onto the post-rebase feat — the one command that survives a raced tip. |
| **`provenance.chain` FAIL at an old line** while `ao provenance verify` reports intact | `cd cli && go build -o bin/ao ./cmd/ao` | a STALE `cli/bin/ao` is the cause — the gate prefers `cli/bin/ao`. Confirm the true state: only the appended line should differ from `git show origin/main:docs/provenance/ledger.jsonl`. |
| **race-suite flake** (the `-shuffle=on` tmux/session isolation test) | retry the push | the shuffle-order suite is a late backstop, not a real regression here; a clean retry lands. |
| **codex stall / reaped** mid-review | re-run the pawl FOREGROUND: `timeout 450 ao pawl review <bead> --scope head` | the reviewer needs the full budget in the foreground; a reaped subprocess produces no verdict. |
| **NO-VERDICT** (push refused, no CONFIRMED verdict) | run the pawl first: `ao pawl review <bead> --scope head` | the pre-push pawl-gate is fail-closed — no CONFIRMED verdict = push refused (no verdict = not done). |
| **false-REFUTE with deterministic ground truth** | `ao pawl review <bead> --scope head --smoke "<the deterministic check that proves it>"` | re-review attaching the runnable ground-truth check; a green live smoke overrides a diff-read REFUTE (a red runtime still REFUTES fail-first). |

## Anti-patterns (do NOT)

- Do NOT `git add docs/provenance/ledger.jsonl` a hand-edited edge — use `ao provenance emit-verdict` (breaks the hash chain otherwise).
- Do NOT rebind a stale verdict by editing the ledger — drop and re-emit.
- Do NOT close a bead on a push success line or a `git log` line — prove `git merge-base --is-ancestor` first ([`ship-loop-anti-patterns.md`](ship-loop-anti-patterns.md) #9).
- Do NOT land two lanes concurrently — take the land-token, land one bead, release it.
