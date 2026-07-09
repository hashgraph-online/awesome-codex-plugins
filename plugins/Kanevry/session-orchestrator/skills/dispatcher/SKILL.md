---
name: dispatcher
description: Use when you want the orchestrator to pick the next repo to work on across your whole portfolio — it enumerates candidate repos below the confinement root, resolves free/busy from each repo's session.lock lease, ranks the FREE ones by backlog priority × staleness × readiness, recommends the single most worthwhile one via AskUserQuestion, atomically claims it, and routes you to the chosen entry command. Triggers: "what should I work on next", "dispatch me to a repo", "pick the next project", "run /dispatcher". <example>Context: operator finished a session and wants the next-best repo across the portfolio. user: "/dispatcher" assistant: "Ranked 18 free repos — top recommendation: Pencil-Designs (score 4.50, 90d stale). Confirm via the picker, I'll claim its lease atomically, then route you to /session deep."</example>
model: sonnet
---

# Dispatcher Skill

> Cross-repo autopilot front-door — enumerate → rank → owner-AUQ → atomic claim → route. Read-only until the operator confirms; the only mutating step is the atomic `session.lock` claim, and it happens BEFORE any launch.

## Soul

The dispatcher answers one question: *"of all my repos, which is the most worthwhile to work on right now, and is it free?"* It scans the confinement-root children, resolves each repo's free/busy status from its `session.lock` v2 lease (same lease semantics as the vault-status board), ranks only the FREE ones by `priority × staleness × readiness`, and recommends the single best one. You confirm via a picker, it claims the lease atomically (winning the race or excluding-and-re-ranking on a loss), then routes you to the entry command for that repo. Busy repos are listed-as-such, never selected.

## When to use

- You just finished a session and want the orchestrator to pick the next-best repo across your whole portfolio.
- You want a ranked, free/busy-aware view of every candidate repo before committing to one.
- You want the atomic claim handled for you so two parallel sessions never both grab the same repo.

## When NOT to use

- Single-repo work where you already know the target — just run `/session`, `/plan`, or `/discovery` directly in that repo.
- A cross-repo *read-only health dashboard* (open issues/MRs/CI per repo) — that is `/portfolio` (gitlab-portfolio), not the dispatcher.
- Writing issues/MRs back to GitLab/GitHub — use `gitlab-ops`.
- Inside a subagent — the dispatcher is coordinator-only because Phase 2 uses `AskUserQuestion` (unavailable in dispatched agents; see `.claude/rules/ask-via-tool.md` AUQ-004).

## Phase 1: Enumerate + Rank

Run the read path (non-mutating). Either invoke the CLI directly or call `runDispatch` from the module:

```bash
node scripts/lib/dispatcher/cli.mjs --json
```

The JSON object has keys `{ candidates, free, ranked, warnings, recommended }`:

- `candidates` — every repo found below the confinement root (busy ones LISTED, not dropped).
- `free` — the subset with no live lease (`free === true`).
- `ranked` — the free candidates sorted DESC by score; `ranked[0]` is the recommendation.
- `recommended` — `ranked[0]` or `null` (no free candidates).
- `warnings` — human-readable degradation notes (glab/gh missing, host probe failed). **Surface every warning to the operator** — they explain why a repo was ranked on partial signals.

Ranking combines three signals per repo (implementation: `scripts/lib/dispatcher/rank.mjs`): backlog **priority** (critical/high counts), **staleness** (days since the last completed session — older = more worthwhile, capped at 90d), and **readiness** (CI status × host resource verdict — only ever dampens). A null priority (glab/gh missing) is ranked on staleness × readiness alone with a warning; the dispatcher NEVER blocks on a missing CLI.

## Phase 1.5: Verdict gate (autonomy-gated launch) — #682

> Decides ONE thing for the recommended repo **R** (`ranked[0]`): may the dispatcher launch WITHOUT per-selection confirmation, or must it inform-and-ask? This sits BETWEEN ranking (Phase 1) and the Owner-AUQ (Phase 2). It is a **pre-launch** decision, NOT a per-iteration kill-switch — the autopilot loop's 10 kill-switches are reused unchanged once a session is running (see `skills/autopilot/SKILL.md § Pre-Loop Verdict Gate`).

Compute the suitability verdict for **R** via the pure four-gate engine `computeSuitabilityVerdict(deps)` from `scripts/lib/autonomy/suitability.mjs`. The engine is pure + DI: the dispatcher gathers every signal and passes it in.

**Source each verdict input as follows** (the dispatcher already has most in hand from Phase 1):

| `deps` field | Source | Notes |
|---|---|---|
| `autonomy` | `resolveDispatcherAutonomy({ committed, env, ownerConfig })` from `scripts/lib/config/dispatcher-autonomy.mjs` | The effective dial. Defaults to `'off'` when unset (fail-closed). |
| `confidenceFloor` | the `confidence-floor` from the parsed `dispatcher-autonomy:` block (default 0.5) | Same source object as `autonomy`. |
| `confidence` | mode-selector `selectMode(signals).confidence` (0..1 float) for the recommended session-type | The same mode-selector the Phase-2 heuristic and autopilot use. |
| `ci` | `checkCiStatus({ repoRoot: R })` → `{ status }` \| `null` | **CRITICAL (NICE-b):** Phase-1 `rank.mjs` exposes only the BARE status string (`readiness.ciStatus`). The engine's G3 gate expects an OBJECT `{ status }` — wrap it as `{ status: ciStatus }` when you HAVE a status; on a CI-fetch FAILURE pass `ci = null` (checkCiStatus already returns `null` on failure — pass it straight through). **Do NOT synthesize `{ status: undefined }`** (or `{}`): that present-but-unusable object hits the engine's MALFORMED branch (`'CI signal malformed — treated as absent'`) instead of the clean ABSENT branch (`'CI signal absent'`). Both pass G3 + warn, but `null` is the honest "no signal" — reserve the malformed branch for a genuinely unexpected shape. A bare string ALSO hits the malformed branch — always wrap or null. |
| `resourceVerdict` | the host resource verdict string (`'green'\|'warn'\|'degraded'\|'critical'`) from `rank.mjs` (`readiness.resourceVerdict`) or a fresh `evaluate(probe(), thresholds).verdict` | Host-level — already fetched once in Phase 1. **NICE-b:** on a genuine probe FAILURE (no signal), prefer `resourceVerdict = null` over synthesizing `'green'`. `null` = "no signal" ⇒ G4 passes + warns (`'resource signal absent'`) — honest. Synthesizing `'green'` fabricates a positive signal the host never reported and can let an autonomous launch proceed against an unknown host state. Pass the real verdict string when you have one; `null` when you do not. |
| `recentRuns` | `readRecentAutopilotRuns({ repoRoot: R })` from `scripts/lib/autopilot/recent-runs.mjs` | NEW reader. Reads `<R>/.orchestrator/metrics/autopilot.jsonl`, returns the most-recent records (newest-last), never throws (`[]` on missing/unreadable). Pass the TRUE count — the engine's G2 gate omits-with-warn below 5 runs and otherwise checks `fired/N < 0.2`. |

**The launch decision (FAIL-CLOSED invariant):**

```
verdict = computeSuitabilityVerdict({ autonomy, confidenceFloor, confidence, ci, resourceVerdict, recentRuns })

IF autonomy === 'autonomous-gated' AND verdict.suitable === true:
    # MAY launch WITHOUT per-selection confirmation:
    # skip the Phase-2 AUQ and proceed straight to Phase 3 (atomic claim) → Phase 4 (route).
ELSE:
    # INFORM the operator of verdict.rationale + verdict.warnings,
    # then run the Phase-2 AUQ (ask before launch). NEVER auto-launch.
```

- **Gate on BOTH conditions.** The launch wiring MUST check `autonomy === 'autonomous-gated'` **AND** `verdict.suitable === true`. Keying only on `verdict.suitable` is a **fail-OPEN bug** — it would auto-launch even in `advisory`/`off` mode. The `autonomy` field inside `deps` is ADVISORY-ONLY inside the engine (it pushes a warning but never flips `suitable`); the CALLER is responsible for the `autonomy === 'autonomous-gated'` half of the AND. `resolveDispatcherAutonomy` defaults to `'off'` when no `dispatcher-autonomy:` config is present, so an absent config forces the inform-and-ask ELSE branch.
- **`null` is "no signal", not a failure (NICE-b).** Passing `ci = null` or `resourceVerdict = null` on a fetch/probe failure is the CORRECT honest wiring: the engine treats each `null` as absent ⇒ the corresponding gate (G3 / G4) PASSES and a warning is recorded (`'CI signal absent'` / `'resource signal absent'`). A `null` signal does NOT by itself block an autonomous launch — it just surfaces a warning the operator sees. Reserve synthesized objects/strings for real signals; never fabricate a positive (`'green'` / `{ status: 'green' }`) to paper over a missing probe.
- **forcedFail path is reachable end-to-end (NICE-c).** When CI is red OR the resource verdict is critical, the engine sets `verdict.suitable === false` **REGARDLESS of confidence** — the four-gate AND fails on G3/G4, and the engine words the rationale `FORCED: CI red` / `FORCED: resource critical` / `FORCED: CI red + resource critical`. For this branch to be reachable, the wiring MUST actually pass the live signals through: `ci` wrapped as `{ status: ciStatus }` (a bare string or a synthesized-absent object would hit the malformed-PASS branch and mask a real red) and the real `resourceVerdict` string (`'critical'` must arrive lowercase-or-normalizable, NOT replaced by a fabricated `'green'`). With the signals wired through, a CI-red / resource-critical repo in `autonomous-gated` mode falls to the ELSE branch: the gate INFORMS the operator (rationale + warnings) and ASKS via the Phase-2 AUQ — it NEVER auto-launches. (Wave 4 covers this with an integration test; this prose is the wiring contract.)
- **Why fail-closed is the default.** `resolveDispatcherAutonomy` returns `'off'` when no config is present, so an unconfigured repo correctly takes the ELSE branch (inform + ask). A CI-red or resource-critical repo also fails the engine's G3/G4 gate (the rationale words it `FORCED: CI red` / `FORCED: resource critical`), so even in `autonomous-gated` mode it falls to inform + ask. **The dispatcher never auto-launches against a non-green verdict.**
- **Inform-branch content.** When taking the ELSE branch under `autonomous-gated` (verdict not suitable), surface `verdict.rationale` (the one-line gate breakdown) and every entry in `verdict.warnings` to the operator BEFORE the AUQ, so they understand WHY confirmation is still required.

## Phase 2: Owner-AUQ

> **Conditional (#682):** SKIP this phase when Phase 1.5 green-lit an autonomous launch (`autonomy === 'autonomous-gated'` AND `verdict.suitable === true`) — in that branch proceed straight to Phase 3. In EVERY other case (any non-`autonomous-gated` dial, OR a non-suitable verdict) this phase RUNS: inform the operator of the verdict first, then ask. The dispatcher NEVER auto-launches outside the green-verdict autonomous-gated branch.

Present the decision to the operator via the **`AskUserQuestion` tool** — never inline prose (`.claude/rules/ask-via-tool.md` AUQ-001..005, enforced).

- `AskUserQuestion` is a **deferred tool**. Call `ToolSearch` with `"select:AskUserQuestion"` ONCE per session before the first use to load its schema.
- **Option 1 is always the recommendation**, labelled `(Recommended)`: the top-ranked free repo paired with a recommended session-type. Options 2–4 are overrides (other high-ranked free repos, or other session-types for the same repo). 2–4 options total, each with a one-line `description` explaining the trade-off.
- This skill runs at coordinator level. **Never** call `AskUserQuestion` from inside a subagent — if a sub-step needs the decision, bubble it back to the coordinator (AUQ-004).

Recommended session-type heuristic for option 1: high critical/high backlog ⇒ `/session deep`; stale-but-clean (no backlog signal, high staleness) ⇒ `/discovery` or `/session housekeeping`; unscoped/new work ⇒ `/plan`. Offer the alternatives as the other options.

## Phase 3: Atomic claim

Claim the lease for repo **R** **BEFORE** launching anything. This runs in BOTH branches — the operator-confirmed Phase-2 path AND the autonomous-gated green-verdict path that skipped Phase 2 (#682). The claim ALWAYS precedes the Phase-4 route: an autonomous launch does not bypass the atomic claim, it only bypasses the per-selection AUQ.

```js
// via the module (preferred — returns the acquire() result verbatim)
import { claimRepo } from 'scripts/lib/dispatcher/cli.mjs';
const res = claimRepo({ repoRoot: R, sessionId, mode, ttlHours, semanticSessionId });
```

Or reuse the primitive directly: `acquire({ sessionId, mode, ttlHours, repoRoot, semanticSessionId })` from `scripts/lib/session-lock.mjs`. The claim is a `linkSync` create-or-fail = **atomic**.

- **`ok: true`** → the claim is held. Proceed to Phase 4.
- **`ok: false`** (race lost / busy — reasons: `active`, `stale-pid-alive`, `stale-pid-dead`, `fs-error`, …) → **exclude R**, re-rank the remaining free candidates (drop R from `free`, re-run Phase 1's rank step), and re-present Phase 2. Loop until a claim succeeds or no free candidate remains (then Phase 5).

Do NOT reinvent the claim — always go through `claimRepo`/`acquire`. The `ok:false` path is the load-bearing concurrency guard: two parallel dispatchers can both recommend R, but only one wins the `linkSync`; the loser must re-rank, never force.

## Phase 4: Route

With the lease held, the **coordinator** invokes the chosen entry slash-command for repo R:

- `/session housekeeping` or `/session deep` — execution modes.
- `/plan` — read-only planning precursor (produces a wave plan; does not execute).
- `/discovery` — read-only investigation precursor (maps scope; does not execute).

`/plan` and `/discovery` are **read-only precursors**, NOT execution modes — the menu may route to them, but they only produce artifacts for a later execution session. The full mode taxonomy lives in the mode-selector surface (P2 of this epic); the dispatcher only routes to the entry command the operator picked.

## Phase 5: Edge cases

- **No free candidate** (`recommended === null` / `free` empty) → report "all repos busy", and offer `resume` (an in-progress session) or `wait` via AUQ. **Never force a selection** of a busy repo.
- **vault off / glab missing** → degrade per the `warnings` array: rank on staleness × readiness only, surface the warning, continue. A missing CLI is never fatal.
- **Host resource probe failed** → readiness is scored without resource dampening (a warning says so); ranking still completes.
- **Bad `--start-dir`** → CLI exits 1 (user/input error); fix the path and re-run.

## CLI

```bash
node scripts/lib/dispatcher/cli.mjs [--json] [--dry-run] [--repo <name>] [--start-dir <path>] [--help] [--version]
```

| Flag | Description |
|---|---|
| `--json` | Emit `{ candidates, free, ranked, warnings, recommended }` as a single JSON object to stdout. |
| `--dry-run` | Explicit non-mutating rank (the read path is already non-mutating; documents intent). |
| `--repo <name>` | Filter the human-readable table to one `repoName` (informational; does not change ranking). |
| `--start-dir <path>` | Override the scan root (defaults to the confinement root). |
| `--help` / `--version` | Print usage / version and exit 0. |

Data → stdout, warnings/errors → stderr (never mixed). Exit codes follow `.claude/rules/cli-design.md`:

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | User/input error (e.g. bad `--start-dir`) |
| `2` | System error (unexpected dispatch failure) |

## Anti-Patterns

- **Inline prose for the Phase-2 decision** — always `AskUserQuestion` (AUQ-001). A numbered markdown list of repos is a bug.
- **Launching before claiming** — Phase 3's `acquire` MUST succeed before Phase 4. Launching then claiming re-opens the race the lease exists to close.
- **Forcing a busy repo** when none are free — report and offer resume/wait; never select a `free === false` candidate.
- **Treating a missing glab/gh as fatal** — null priority degrades to staleness × readiness with a warning; never block.
- **Re-implementing the claim** — go through `claimRepo`/`acquire`; do not hand-roll a lockfile.
- **Ignoring `ok:false`** — on a lost race you MUST exclude-and-re-rank, not retry the same repo or proceed without the lease.
- **Running this from a subagent** — coordinator-only (AUQ is unavailable in subagents).
- **Fail-OPEN verdict gate (#682)** — keying the autonomous launch on `verdict.suitable` alone (ignoring `autonomy === 'autonomous-gated'`) auto-launches in `advisory`/`off` mode. ALWAYS gate on BOTH.
- **Feeding the bare CI string into the engine** — `rank.mjs` exposes `ciStatus` as a bare string; `computeSuitabilityVerdict` wants `{ status }`. Wrap it (`{ status: ciStatus }`) or pass `null` — a bare string silently hits the malformed-absent branch. A red CI fed as a bare string would PASS G3 (masked as malformed) instead of forcing the FORCED-fail branch (NICE-c).
- **Synthesizing an absent signal instead of passing `null` (NICE-b)** — on a CI-fetch or resource-probe failure, pass `ci = null` / `resourceVerdict = null` (honest "no signal" ⇒ gate passes + warns). Do NOT synthesize `{ status: undefined }` (hits the malformed branch) and do NOT fabricate `'green'` / `{ status: 'green' }` (invents a positive signal the host never reported and can green-light an autonomous launch against an unknown state).
- **Pre-truncating `recentRuns` below 5** — passing fewer than the true on-disk count when ≥ 5 runs exist falsely triggers the engine's <5-run omission branch and skips the kill-switch gate. Pass the TRUE count; never call `readRecentAutopilotRuns` with `limit < 5` on the launch-gate read (the reader honours a small `limit` literally and will not clamp it upward).
- **Auto-launching against a non-green verdict** — a CI-red / resource-critical / low-confidence verdict ALWAYS falls to inform + ask, even under `autonomous-gated`. Never proceed straight to claim on a non-suitable verdict.

## Critical Rules

- The read path (`runDispatch` / `cli.mjs` without a claim) is NON-MUTATING. The ONLY mutating step is the Phase-3 atomic claim.
- The atomic claim is `linkSync` create-or-fail via `acquire(...)`. `ok:false` ⇒ exclude the repo and re-rank — this is the concurrency guard, not an error to swallow.
- Phase 2 uses `AskUserQuestion` with option 1 = recommendation `(Recommended)`; coordinator-only.
- Busy repos are LISTED, never selected (PRD: "busy repos listed as such, not selected").
- glab/gh/host-probe degradation is surfaced as a warning and never blocks ranking.
- **Phase 1.5 verdict gate (#682)** is FAIL-CLOSED: `MAY launch without per-selection confirmation` requires `autonomy === 'autonomous-gated'` **AND** `verdict.suitable === true`. Every other case informs the operator (rationale + warnings) and asks via Phase-2 AUQ. The dispatcher NEVER auto-launches outside that single green branch. The 10 autopilot kill-switches are reused unchanged once a session is running — the verdict gate is a pre-launch decision, not a kill-switch.
- Implementation files: `scripts/lib/dispatcher/cli.mjs` (orchestration: `runDispatch`, `claimRepo`) · `scripts/lib/dispatcher/enumerate.mjs` (enumeration + free/busy) · `scripts/lib/dispatcher/rank.mjs` (scoring) · `scripts/lib/session-lock.mjs` (`acquire` atomic claim) · `scripts/lib/autonomy/suitability.mjs` (`computeSuitabilityVerdict` four-gate engine, #682) · `scripts/lib/config/dispatcher-autonomy.mjs` (`resolveDispatcherAutonomy` effective dial, #682) · `scripts/lib/autopilot/recent-runs.mjs` (`readRecentAutopilotRuns` kill-switch-history reader, #682).
