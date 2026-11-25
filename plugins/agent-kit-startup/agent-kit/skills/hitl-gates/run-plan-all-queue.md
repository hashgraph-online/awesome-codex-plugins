# /run-plan-all queue

## Goal

Orchestrate multiple plans as an ordered, deduplicated execution queue. The agent first acts as a **product owner**: it reads the recent code state (latest merges/commits), the changelog, and every eligible plan, then synthesizes a proposed execution order with overlap/dependency annotations and consolidation suggestions. After the user approves the queue, the main window **dispatches one Task per plan**; each Task runs `/run-plan`'s tick contract. One active plan at a time; the queue persists so a resume in a fresh chat does not re-synthesize from scratch.

**Never** `/git-prod` from this command (remains separate HITL).

## When to Use

- Multiple Gate-A backlog plans have accumulated, with overlapping scope, implicit ordering, or consolidation opportunities.
- You want one command that orders, deduplicates, and runs plans end-to-end without manual activation per plan.
- A workspace has been running `/run-plan` per plan individually and the operator wants batch throughput.

## Precondition

- A set of eligible plans exists in the pending-only index (`.cursor/context/plan-index.json`) plus HANDOFF  -  at least one with `pending` or `in_progress` to-dos. Do not glob `.cursor/plans/*.plan.md`.
- The eligibility contract is defined by `.cursor/memory/decisions/2026-07-26_run-plan-all-queue-contract.md`:
  - **Included by default:** active plan with implementable to-dos; backlog plans with pending to-dos and Gate A done (or no Gate pending).
  - **Excluded by default:** exhausted/all-completed, cancelled, closed plans; plans awaiting Gate B without opt-in.
  - **Opt-in:** Gate-B-awaiting plans may be included via the `Include Gate-B plans` option at confirm time.
- No eligible plans: report and stop. Suggest `/start-project` for a new plan.

## Strategy

This command runs in the **main window** as a **pure orchestrator**. It synthesizes, asks, applies user-approved consolidations, then **dispatches one Task subagent per queued plan**. Each subagent runs the existing `/run-plan` tick contract in its own context. The orchestrator does **not** implement to-dos, fork a second tick engine, fan out plans in parallel, or replace `/run-plan` behavior. See `.cursor/memory/decisions/2026-07-26_run-plan-all-pure-orchestration.md`.

**Persona:** reuse `agentPersona.modes.run-plan` / night-shift (no new persona id required; documented in registry).

## PO Synthesis (read-only proposal step)

> **Delegation note:** The actual scanning below is performed by a **Task(explore) subagent** dispatched from the delegation pattern. The tables define the specification of what the worker scans. The main window reviews the structured report and runs the queue confirm Ask only. See the [Delegation pattern](#delegation-pattern) subsection below.

Before asking the user for confirmation, the agent performs a **read-only** synthesis. It edits no plan files and changes no HANDOFF state during this step.

### Inputs (reads)

| Source | What is read | Purpose |
|--------|-------------|---------|
| **Recent merges** | `git log --first-parent --merges -20` for merge commits on the active branch | Identify scope already shipped; prune candidate plans whose to-dos have already landed |
| **Recent commits** | `git log --first-parent --no-merges -10`; `git diff staging...HEAD --stat` | Catch work-in-progress that overlaps with candidate plans; flag conflicts |
| **CHANGELOG** | `CHANGELOG.md` `[Unreleased]` section + latest release notes | Catch scope already delivered or contradicted in releases |
| **HANDOFF** | `.cursor/HANDOFF.md` active plan, queue cursor (if resuming), backlog/parked lists | Preserve current execution position; the active HANDOFF plan keeps priority unless reordered |
| **Candidate plans** | Pending-only index + named plan files from HANDOFF | `.cursor/context/plan-index.json` and `.cursor/HANDOFF.md`; then named single-file reads of those basenames. ADR `decisions/2026-07-26_command-orchestration-delegation-pattern.md` |
| **In-flight vs Gate-A Backlog** | On **start and resume**, compare current Gate-A Backlog basenames to `- **Confirmed backlog:**` (set at last queue confirm). Flag adjustment-class only for **new-since-confirm** Backlog | Drift Ask fires only when a Backlog plan appeared after confirm, or a queued file is invalid |

### Outputs (surfaced at the confirm Ask only)

| Output | Detail |
|--------|--------|
| **Logical execution order** | A flat ordered list of plan basenames. Dependency prerequisites first; shipped-scope sections pruned; smaller/unblocking before large when dependencies are equal |
| **Overlap / dependency map** | Per-pair annotations: `A blocks B`, `A touches same files as B` (sequential-only), `B is subset of A` (merge), `A contradicts B` (user decides) |
| **Consolidation proposals** | **Merge** / **Split** / **Simplify** / **Drop** (scope shipped → archive) |
| **Ship expectations** | Per queued plan: public notes yes/no, landing touched, expected transient rows, known recoveries. Persist via `serializeIntakeShipRunbook` (`run-plan-all-intake-runbook.ts`). Ship lane consults before Ask. |
| **Coherence notes** | Shared ADRs, acceptance diffs, ordering notes |

### Ordering heuristics (locked)

1. **Shipped-scope-first pruning**  -  scan merge history and CHANGELOG; fully shipped → propose drop; partially shipped → reorder to skip delivered sections.
2. **Dependency edges before siblings**  -  A plan that explicitly depends on another's output runs after that plan.
3. **Smaller/unblocking before large**  -  among no-dependency plans, fewer to-dos or narrower `read_scope` runs first.
4. **Active HANDOFF priority**  -  the plan referenced by `.cursor/HANDOFF.md` as active runs first, unless reordered at confirm.
5. **Backlog list fallback**  -  tie-breaking: HANDOFF Backlog plans order (top-to-bottom as listed).
6. **Basename tiebreaker**  -  alphabetical if still tied.

### Overlap / dependency map rules

- **Same-file collision:** two plans list the same path or glob → collision flag; run sequentially, user may merge or reorder.
- **Scope subset:** plan B's goal fully covered by plan A → `B is subset of A`; merge B's unique to-dos into A, archive B.
- **Explicit dependency:** plan B says "depends on A" in `Constraints` or `Why` → edge `A → B` is hard-wired.
- **Contradiction:** plan A assumes architecture state X, plan B changes X → conflict; user decides order.
- **Independent default:** no collisions or edges → independent; order by remaining heuristics.

### Adjustment-class hard drift (start and resume)

On **start** and **resume**, compare current Gate-A Backlog basenames to `- **Confirmed backlog:**`. A Backlog plan that was already present at the last queue confirm is **not** drift, even if it is eligible-not-queued. When a basename is **new since confirm**, read its body against the in-flight plan (same files/ADRs, reads this plan, subset/overlap, blocks current HITL). Same-theme adjustment wins over freeze. Also treat a missing or status-invalidated queued plan as drift. Exact Ask labels: [Start vs resume](#start-vs-resume-stored-queue). Helpers: `decideQueueDriftAsk` in `run-plan-all-orchestrator.ts`.

### Delegation pattern

This step is delegated to a **Task(explore) subagent** using `.cursor/context/templates/command-worker-prompt.md` (same pattern as `/start-project` Step 1).

1. **Fill the template**  -  set:
   - **Repo:** `[absolute repo path]`
   - **Command:** `/run-plan-all`
   - **Task description:** "Scan recent merges (git log --first-parent --merges -20), recent commits (git log --first-parent --no-merges -10; git diff staging...HEAD --stat), CHANGELOG.md [Unreleased] + latest release, then read `.cursor/context/plan-index.json` and `.cursor/HANDOFF.md`. Candidate plans are the HANDOFF-named set; named single-file reads OK. Do not glob `.cursor/plans/*.plan.md`. On start/resume, list Gate-A Backlog basenames vs `- **Confirmed backlog:**`; flag only new-since-confirm Backlog (and read those bodies for adjustment-class). Do not return kind: resume. Return PO report: order, overlaps, consolidations, coherence notes, per-plan ship expectations."
   - **read_scope:** `[".cursor/context/plan-index.json", ".cursor/HANDOFF.md", "CHANGELOG.md", ".cursor/memory/decisions/"]` (plus workspace git log/diff). Dogfood is Confirm Queue preflight; not on this explore worker.
   - **worker_contract:** "PO report: ordered plans, overlaps, consolidations, coherence notes, per-plan ship expectations, staging-ready (lint)"
   - **max_ticks:** 2
   - **worker_type:** explore

2. **Dispatch** a Task subagent with `subagent_type: explore`.

3. **Read the worker summary**  -  use it for the queue confirm Ask on a fresh queue, or the 3-way start/resume Ask when a Backlog plan appeared after confirm (see [Start vs resume](#start-vs-resume-stored-queue)). Do not dump raw diffs. If the worker returns `kind: resume` or omits new-since-confirm Backlog, treat as incomplete: re-dispatch once or run PO inline.

**Fallback:** If Task dispatch is unavailable or the worker template is missing, run the PO synthesis inline.

**References:** `.cursor/context/templates/command-worker-prompt.md`; `autogit/plan-routine.md` section 9.

## Start vs resume (stored queue)

When the operator runs `/run-plan-all` and HANDOFF already has `Mode: run-plan-all` plus a non-empty `- **Run queue:**`:

1. Run the same Unprocessed / audit preflights as a fresh start (Confirm Queue preflight). **Queue owner lease** (ADR `2026-07-26_run-plan-all-queue-contract.md`, Amend 2026-11-16): the headless `agent-kit run-plan-all` holds `.cursor/context/run-plan-all.lock` (pids, session id, 30 s heartbeat), refuses to start (exit 1) while another dispatcher or its agent lives, and takes over a stale lease (both gone, or heartbeat older than 120 s with no live agent) with one HANDOFF bullet. Before writing `Run queue`, `Queue cursor`, `Queue status` or `Queue outcomes`, and before an interactive session dispatches, run `agent-kit queue lease`: output starting `Queue lease held:` (exit 1) means another live owner holds the queue, so stop and report that line (no write, no dispatch); `Queue lease: free`, `stale` or `held by this session` (`AGENT_KIT_QUEUE_LEASE_SESSION`) is exit 0. An engine without the subcommand prints the `queue` usage (also exit 1): skip the check.
2. Compare current Gate-A Backlog basenames to `- **Confirmed backlog:**` ([Adjustment-class hard drift](#adjustment-class-hard-drift-start-and-resume)). Missing Confirmed backlog on an older HANDOFF: treat current Backlog as unconfirmed and Ask (safe default).
3. **No new Backlog since confirm** and queued files valid: resume the frozen queue. Re-probe `deferred-operator` rows first (gate open: re-dispatch that plan), then dispatch the next plan as a Task. Do not re-synthesize. Do not scramble the approved order. Do not auto-append Backlog into Run queue. A stable eligible-not-queued Backlog that was already listed at confirm is **not** drift.
4. **New Backlog since confirm** (or invalid queued item): do not silently resume. **Ask questions** (one question; chat numbered-list fallback) with labels exactly:

| Option | Behavior |
|--------|----------|
| `Resume frozen queue` | Keep stored Run queue, cursor, status, outcomes, and Confirmed backlog. Leave new-since-confirm Backlog off the queue. Dispatch the next queued Task only when Queue status still allows execution. A stored `blocked` on an operator gate converts to `deferred-operator` (agent-inferred, no operator unblock); dispatch the next non-deferred plan. |
| `Insert new backlog` | Revise the proposal to include new-since-confirm Backlog. Do not silent-append a default slot. Show the revised order, then continue into the queue confirm (rewrites Confirmed backlog). |
| `Re-synthesize` | Ignore freeze. Run full PO synthesis and the queue confirm as a fresh queue. |

Skipped or cancelled Ask means **stop**. No CLI `eligiblePlans` scanner. No silent auto-append. **Explore / PO workers:** `kind: resume` is **not** a supported worker contract.

This 3-way Ask is in addition to the queue confirm on a true fresh synthesis (no stored queue, or after `Re-synthesize`).

## Confirm Queue (Ask questions)

**Unprocessed dogfood preflight (off the default path):** same mechanic as `/run-plan`'s tick contract (see [Unprocessed dogfood preflight](./run-plan-tick-contract.md#1-read-state)): skim `##`/`### Unprocessed Files`, opt-in inbox Ask (`Analyze inbox now` / `Enqueue Fix now` / `Not now`, numbered-list fallback path 1), never auto-analyze, never invent Field Reports, never refuse solely because the inbox is non-empty. Runs **once here, before start-vs-resume or the queue confirm** (not per to-do). The orchestrator owns this skim and any later inbox Ask for the whole batch: per-plan `/run-plan` workers must not re-recite the same inbox and must not Ask again. sessionStart tip remains complementary (ADRs `2026-08-11_dogfood-unprocessed-broad-intake-bucket.md`, `2026-08-14_main-command-dogfood-audit-routing.md`).

**Audit session-pile preflight (before the confirm Ask):** same check as `/run-plan`'s tick contract (see [Audit session-pile preflight](./run-plan-tick-contract.md#1-read-state)): count detached `agent-kit-audit-*` sessions via `.cursor/scripts/plan-external-review.sh --reap-audit-sessions --dry-run`; warn prints the dispose command (or offers `--reap-audit-sessions`) and continues; at cap, do not arm and surface the cap in the Ask/preflight body, not only launcher stderr. Attached sessions are operator work and are never counted. This orchestrator check runs **once, at queue confirm**; per-arm protection is the launcher's own session-cap refusal (exit 4), which the mid-batch and queue-end arms already honour, so no second orchestrator call site is wired.

**Audits unsatisfiable-config preflight (before the confirm Ask):** same check as `/run-plan`'s tick contract (see [Audits pre-flight / unsatisfiable-config check](./run-plan-tick-contract.md#1-read-state)): `enabled: true` with `backend` pinned `"claude"` against a Claude implementer can only end owed (`CLAUDE.md` non-goal; implementer≠reviewer same-model skip, ADR `decisions/2026-08-13_audits-atomic-wait-reviewer-fallback.md` point 4); `"auto"`, `"cursor"`, and `"cloud"` stay satisfiable; `warn`/`block` behave the same as the tick contract's version. **Queue-specific:** `midBatchAudits: true` multiplies the cost — every completed plan arms, every arm same-model-skips, every plan in the queue ends owed. This runs before the confirm Ask because that is the one place an operator can still change config cheaply, ahead of a multi-plan run. A growing owed pile is not an acceptable substitute for surfacing this (`.cursor/memory/errors/2026-08-14_audit-owed-ledger-no-close-path.md`).

After synthesis, present the proposal using **Ask questions** tool. Include the ordered list, key overlaps/consolidations, and coherence notes in the question body. Fallback to chat numbered list if the tool is unavailable.

> "Plans synthesized. Proposal: [N] plans in order, [M] consolidations, [K] overlaps. Here is the proposed execution queue..."

Options:

| Option | Behavior |
|--------|----------|
| `Run as proposed` | Accept the full PO synthesis: apply approved merges/drops, set the queue order, activate the first plan, begin execution. Ship auth `per-plan-release`. |
| `Run plans only` | Same execution as `Run as proposed`. Ship auth `plans-only` (no promote). |
| `Edit order` | Accept consolidation proposals but reorder the queue. The user specifies the new order (typed or pasted). Ship auth `per-plan-release`. |
| `Apply merges & drops only` | Accept consolidation proposals but keep the default per-heuristic order for the remaining queue. Ship auth `per-plan-release`. |
| `Keep all plans as-is` | Run the queue without any consolidation; use the proposed order only (no plan files are changed). Ship auth `per-plan-release`. |
| `Include Gate-B plans` | Re-run the synthesis with Gate-B-awaiting plans included; show a new confirm Ask. Only offered when Gate-B plans exist. |
| `Cancel` | Abort `/run-plan-all`. No plans reordered, merged, or dropped. HANDOFF unchanged. |

### After confirmation

- **Run as proposed / Apply merges & drops only / Run plans only:** apply consolidation mutations (merge, split, drop, rename) to plan files and/or archive directory. Write the resolved queue order to HANDOFF. `Run plans only` sets `- **Ship auth:** plans-only`. The other two set `per-plan-release`. Write `- **Confirmed backlog:**` with Gate-A Backlog basenames visible at confirm (including eligible-not-queued).
- **Edit order:** apply consolidation mutations, then update the queue order per user input. Write `- **Ship auth:** per-plan-release` and Confirmed backlog.
- **Keep all plans as-is:** preserve all plan files exactly; write only the queue order, Ship auth `per-plan-release`, and Confirmed backlog.
- **Include Gate-B plans:** re-run synthesis with Gate-B plans included, then present a new confirm Ask.
- **Cancel:** stop immediately. Report that no state was changed.

Rejected consolidation proposals leave plans untouched. If the user rejects all consolidations but approves the order, the queue runs in the proposed order without mutating plan files.

### Consolidation apply

Use the safe helper after the confirm Ask grants consolidations. Canonical launcher: `.cursor/scripts/run-plan-all-consolidate.sh` (wrapper: `scripts/run-plan-all-consolidate.sh`). Default is `--dry-run`; real mutations need `--apply --approved`.

**Pre-flight (always):**

1. Confirm Ask already granted for the consolidations being applied (script refuses `--apply` without `--approved`).
2. Target plan files exist under `.cursor/plans/` (not already archived unless intentional).
3. Do not change active HANDOFF `- **Plan:**` unless activating the first queued plan via `--activate` / `--rewrite-queue`.
4. **In-flight queue guard:** `/backlog-add`, `/backlog-edit`, `/backlog-delete`, and `/backlog-cancel` must **not** call this script, and must **not** rewrite `- **Run queue:**`, `- **Queue cursor:**`, `- **Queue status:**`, or `- **Queue outcomes:**` (ADR `2026-07-26_backlog-crud-commands-contract`). The script with `--caller backlog-crud` refuses those paths when a `/run-plan-all` queue is in flight.

**Checklist (after confirm):**

| Step | Command / action |
|------|------------------|
| Preflight | `.cursor/scripts/run-plan-all-consolidate.sh --preflight` |
| Merge (frontmatter) | `.cursor/scripts/run-plan-all-consolidate.sh --merge-checklist SOURCE.plan.md TARGET.plan.md` then agent-edit TARGET (script never auto-merges YAML); archive SOURCE with `--drop` |
| Drop / archive | `.cursor/scripts/run-plan-all-consolidate.sh --drop PLAN.plan.md --apply --approved` (refuse overwrite unless `--force-overwrite`) |
| HANDOFF queue rewrite | `.cursor/scripts/run-plan-all-consolidate.sh --rewrite-queue --queue "a.plan.md,b.plan.md" --cursor 0 --status running --activate a.plan.md --apply --approved` |

`--rewrite-queue` validates and normalizes `--outcomes` (including multiline) **before** any HANDOFF mutation, then applies Plan/Mode/queue/cursor/status/outcomes as one atomic rewrite. Invalid outcomes (for example a line that looks like a HANDOFF machine field) refuse with the file untouched. Backlog CRUD callers still cannot rewrite the queue.

Queue field shape aligns with `serializeRunPlanAllQueueFields` in `packages/cli/src/plan-loop/run-plan-all-orchestrator.ts` (machine-field bullets only). This path does not promote.

## Execute the Queue

After confirmation, the main window is a **pure orchestrator**. For each plan in the approved queue **in order** (one at a time; no parallel plan Tasks):

### Orchestrator must not

The orchestrator **must not** implement to-dos, edit product code, run tests, write changelogs, or edit plan files except **user-approved consolidation mutations** applied after the confirm Ask. The PO synthesis Task(explore) delegation (see [Delegation pattern](#delegation-pattern)) is a read-only analysis step and does **not** satisfy the execute-queue contract. Mandatory execution Task is **per queued plan** after confirmation.

### Per-plan flow

1. **Activate the plan**  -  update `.cursor/HANDOFF.md`: `Mode: run-plan-all`, active plan basename, full `Run queue`, `Queue cursor`, `Queue status: running`. HITL fields that assert a human decision (Queue status stopped, Parked, approved, deferred, confirmed) must record Ask id, operator reply, or `agent-inferred`. Do not write Parked / Queue status stopped as operator action unless an Ask id and operator reply exist.
2. **Dispatch Task**  -  launch one Task subagent with a self-contained prompt (template below) that includes:
   - Absolute path to the plan file under `.cursor/plans/`
   - HANDOFF snapshot (active plan, cursor, outcomes so far, queue order)
   - Instruction to run the `/run-plan` tick contract for that plan until exhausted or blocked
   - Structured return contract (required)
3. **Background wait**  -  prefer `run_in_background: true`. Wait for the **end-of-turn completion notification**. Do **not** poll the Task (no AwaitShell loops on subagent status). **No co-pack:** do not start the next plan Task, `/git-staging`, or other parallel heavy work in the same turn as an in-flight plan Task; sequential queue only (ADR `decisions/2026-07-27_auto-run-no-regression-invariants.md`).
4. **Validate the summary**  -  require a structured return of the form:

```text
{ outcome: "completed"|"blocked"|"partial", lastTodoId, filesTouched[], failures?[] }
```

   Missing or malformed summary: **Ask the user** before advancing the cursor. Do not invent an outcome.
5. **Record the outcome**  -  write HANDOFF `Queue outcomes` (plan basename, `outcome`, `lastTodoId`, optional notes from `failures`). When `outcome` is `completed`: Remove the plan basename from `- **Backlog plans:**` (empty -> none); file stays, no Ask.
6. **Ship lane, then advance**  -  when outcome is `completed`, run the [ship lane](#ship-lane-after-each-completed-plan) before incrementing `Queue cursor`. Advance only on a benign skip (`plans_only`, `staging_not_ahead`, `no_product_diff`) or a Done ship. `blocked` / `partial` goes through `decideBlockedPlanDisposition`: an operator gate (and its PO-map `A blocks B` dependents) records `deferred-operator (gate: <what>)` agent-inferred, skips the ship lane, and advances with Queue status `running`; any other blocker hits [Stop conditions](#stop-conditions). Then repeat from step 1 until a stop condition.

### Ship lane (after each completed plan)

Main window only, after a valid `completed` summary, before the next plan Task. A stored queue with no `- **Ship auth:**` field is `plans-only`.

| State | Action |
| --- | --- |
| `plans-only`, outcome not `completed`, or `staging` not ahead of `main` | Skip. `plans-only` suggests `/git-prod` only at queue end. |
| Completed plan, no versionable product diff (`Staging ready: no-diff`, `no` with an empty product diff, or an `[Unreleased]` public CHANGELOG extract that is empty: `publicUnreleasedNotes` null) | Skip (`no_product_diff`). Advance the cursor. Do not cut a tag. Commits already on `staging` stay for the next plan that has a diff. |
| `Staging ready: no` and a product diff exists | Stop (`staging_not_ready`). Do not start the next plan. |
| Previous ship in this queue is not Done | Stop. Do not start the next plan. |
| Staging CI pending | Wait for that SHA. |
| Staging CI red, no fix yet | One Task fixes that CI and runs `/git-staging`. Not an in-window product edit. |
| Staging CI still red, or subjects unreadable | Stop. |
| `BREAKING CHANGE` or a `type!:` subject | Stop. No automatic major. |
| Any `feat` subject | One minor. Otherwise one patch. |

Use `/kit-prod` when present, else `/git-prod` (no second prod Ask; queue confirm is the yes). One tag. Done = that command's Done. Before the promote, run the advisory `agent-kit promote rules --base main` and copy any advisory line into HANDOFF. A promote PR that waits for the operator merge uses `agent-kit promote wait --pr <N>` (bounded by `promoteMergeWaitMs`, default 60 min); exit 3 is the `promote-merge-wait` Ask ([promote-merge-wait.md](./promote-merge-wait.md)). That Ask holds the cursor; it is not a red stop and not a license to merge. Subjects: `git log origin/main..origin/staging --format=%s%n%b`. Helpers: `run-plan-all-ship-lane.ts` + `consultAfterShipLane` in `run-plan-all-intake-runbook.ts` (known recoveries before Ask; novel Asks once with `Retry recovery once` / `Hold and document` / `Stop the queue`; red stays stop). After Done/skip, run the [context checkpoint](#context-checkpoint-plan-boundaries) before the next plan Task.

Subagent ownership (inside the Task): mark to-dos `in_progress` → implement → `completed`; plan-level HANDOFF updates; per-to-do risk gates (`max_ticks`, PII/secrets Ask, staging-on-diff); never `/git-prod`.

### Audits (mid-batch + queue end)

**Default path when audits are enabled:** this command arms, waits, rearms leftover wait budget on exit 3, and continues into `/plan-review-triage` at queue end (explicit path list). Operators stay on `/run-plan-all`; specialist `/plan-external-review` and `/plan-review-triage` stay SoT and are invoked from this path. Do not reimplement exit-3 resume (`dogfood-ingest-fix-now`) or a Cloud Agents reviewer (`cursor-cloud-agents-sdk`). ADR `2026-08-14_main-command-dogfood-audit-routing.md`.

Read `externalPlanReview` before the queue confirm Ask and at each advance:

| Config | Behavior |
|--------|----------|
| Audits **pre-flight** (`preflight`: `off` \| `warn` \| `block`) | Before the confirm Ask and before each mid-queue advance: same owed/untriaged check as `/run-plan`, plus the unsatisfiable-config check (`enabled: true` + pinned `backend: "claude"` in this lane can only end owed; see "Audits unsatisfiable-config preflight" above). `block` arms or stops; never steals `/git-prod`. |
| `midBatchAudits: true` and audits enabled | After the ship lane for that plan returns skip or Done, the **orchestrator** arms **one** full audit for that plan with `--force --autonomous --wait-monitor` (or one `--batch` + wait_all when batching is intentional) **before** advancing the cursor. No paste Ask between plans. Soft-fail → Field Report owed; still advance. AwaitShell until exit `0|3|4` (chat slice ~90s; remaining budget in `.cursor/context/audit-wait/<slug>.json`). **Exit 3 with remaining `waitTimeoutSeconds`:** do not treat as arm-done. Same orchestrator session resumes wait-state polling (re-arm `--wait-monitor` against leftover budget) before advancing the cursor or skipping triage. Exit 3 with zero leftover budget, or exit 4: Field Report owed, then advance. Wait success requires a **fresh** monitor after arm start. Reviewer cascade: `backend: "auto"` uses Claude (Haiku) when usable, else Cursor Agent. Same-model implementer/reviewer is an honest skip. Do **not** fan out N background sessions without wait. Do **not** insert a mid-queue triage Ask (operator non-stop preserved; record ready path for queue-end). Mid-batch stays findings-only: **never** auto-Write residuals or rewrite the Run queue between plans. |
| `midBatchAudits` false/missing | **Non-stop** mid-queue: do **not** pause for audit Ask/paste between plans. Mid-queue completed plans stay Field Report **owed** until reviewed. |
| Queue exhausted | Final HANDOFF; cadence `batch-complete`; then queue-end audit arm covering remaining owed/unreviewed targets (enabled → `--force --autonomous --wait-monitor` or paste per `mode`; else `offerOnExhausted` Ask). Prefer one launcher `--batch` + wait_all when multiple basenames. After wait exit `0`: run `/plan-review-triage` Ask with an **explicit path list** of fresh monitors (batch uniform Ask when outcomes match; sequential fallback when mixed; durable heading per file). **Batch exhaust without conveyor:** when remaining monitors are process-only / depth-capped, prefer uniform **Ack and stop** or **Fix nits only**; do not spawn unbounded `close-*` backlog from Write residuals (ADR `decisions/2026-08-11_plan-audit-residuals-termination.md`). `plans-only` then suggests `/git-prod` if staging is ahead of `main`. `per-plan-release` does not ship again here. |

Never steal `/git-prod` confirmation. Chat never runs silent headless `--force` / `claude -p` in the agent shell. Spawn-only exit 0 without `--wait-monitor` is **not** review done. Never stop at Final HANDOFF "when monitors exist, run triage" after arming: wait (freshness) then continue (mid-batch waits for file only; queue-end waits then triage Ask with explicit paths). ADR: `2026-07-27_audits-autonomous-plan-review-contract.md` (supersedes queue-end-only); wait freshness: `2026-07-27_audits-wait-freshness-enforce.md`.

**Exit 3 stays timeout-only across the queue.** A mid-queue or queue-end arm that returns `3` reviewed nothing: leave that plan Field Report **owed**, keep its path out of the queue-end triage list, and never narrate it as reviewed. **Same-session resume:** when leftover `waitTimeoutSeconds` remains in `.cursor/context/audit-wait/<slug>.json`, the same orchestrator session must keep polling (re-arm `--wait-monitor`) before advancing the cursor or skipping `/plan-review-triage`. A later session may poll leftover budget; that is fallback, not the default while this session is still open. Do not treat a first-slice exit `3` as "arm done, continue the queue." Monitors that show up later, including monitors written by a different arm or a later queue position, do **not** retroactively upgrade an earlier `3`  -  the `3` stays `3` even when a later genuine monitor exists. Exit `4` covers the launcher soft-fails: no usable reviewer (`backend: "auto"` tried Claude then Cursor; pinned `claude` still tips when Claude is missing), same-model refuse, background spawn unavailable, a **silent PTY** early abort (spawn succeeded but produced no scrollback in the grace window), and a **session-cap refusal** (detached `agent-kit-audit-*` pile at the cap, so nothing spawned). Advance the queue on exit 4 or on exit 3 with zero leftover budget, but record the target as owed, never as reviewed. **Leftover budget is `deadline` vs wall clock, never `status: "armed"` alone:** the launcher expires a wait-state file left `armed` past its `deadline` on contact (to `status: "timeout"`, `remainingBudgetSeconds: 0`), so a stale arm from an earlier queue run is never resumed as live budget; sweep all slugs with `.cursor/scripts/plan-external-review.sh --gc-wait-state [--dry-run]`. **Owed close (separate, later event, not an upgrade of the `3`):** once the wait-state for that slug is terminal-and-dead (`status: "timeout"`/`"soft-fail"`, or `"armed"` with `now >= deadline`) and a genuine post-hoc monitor for the slug exists, `/run-plan`'s owed-close HITL applies  -  `Adopt existing monitor` (into `/plan-review-triage`, closes as reviewed-by-adoption) or `Ack owed without review` (closes as acked/unreviewed); a duplicate re-arm against already-merged work is not the only route. Queue-end triage lists still exclude dead-timeout rows by default; adoption is operator-initiated per row. ADR: `2026-07-30_audits-pty-progress-gate-zombie-policy.md`; wait resume: `2026-08-13_audits-atomic-wait-reviewer-fallback.md`; owed-close: `.cursor/memory/errors/2026-08-14_audit-owed-ledger-no-close-path.md`.

### External plan review (legacy heading)

Same table as **Audits (mid-batch + queue end)** above. Keep Field Report owed rows (`buildOwedReviewItems`). Mid-batch: one arm+wait (or one batch wait_all) before advance; no unwatched multi-Terminal fan-out; triage via `/plan-review-triage` at queue-end with explicit path list. Queue-end chat path: wait then triage Ask.

### Subagent prompt template

Self-contained; the subagent does **not** inherit the orchestrator transcript.

```text
You are an Agent Kit worker running one queued plan for /run-plan-all. Execute the plan via the /run-plan tick contract and stop when the plan is exhausted or blocked.

Repo: <absolute repo root>
Plan: .cursor/plans/<plan-basename>.plan.md
HANDOFF snapshot:
- Mode: run-plan-all
- Active plan: <plan-basename>.plan.md
- Queue cursor: <N> (of <total>)
- Run queue: [<ordered basenames>]
- Queue outcomes so far: <list or none>
- Instruction from HANDOFF: <1-3 sentences if present>

Rules:
- Read `.cursor/HANDOFF.md` and the plan file first. Resume from the next pending/in_progress to-do.
- Follow `/run-plan` (`.cursor/commands/run-plan.md`): tick contract, risk gates, staging-on-diff when there is a diff.
- Findings-only: review workers (`review-*` / findings contracts) return structured findings (severity, path, evidence) and must not auto-fix product code. After findings, the in-plan `/run-plan` orchestrator applies `externalPlanReview.autoRemediate` (default false): fix-agent Task (small) or residuals backlog plan (large). Do not silent-apply.
- Unprocessed dogfood already skimmed by the orchestrator at queue-confirm  -  do not re-recite.
- When this plan is exhausted (`outcome: completed`), **skip** chat exhaustion Ask/paste in the worker (parent orchestrator owns mid-batch + queue-end audits). Return the structured summary and stop.
- Never `/git-prod` (the parent owns the ship lane). Never ask the user for `/continue-plan` as the default path.
- A refused command (permission classifier, never /git-prod class) is terminal in this worker: do not retry it.
- Do not fabricate HITL: do not write Parked / Queue status stopped as operator action unless an Ask id and operator reply exist.
- Do not start the next queued plan; this Task owns only this plan.
- Pending operator ticket (`.cursor/context/gate-exit.json` has a pending entry): never Ask `ticket` in this Task and do not block; list the stamps in Notes as `Pending tickets: <stamp>, ...` ([pending-ticket.md](./pending-ticket.md)).
- Prefer orchestrated /run-plan strategy inside this Task when Task nesting is available; otherwise in-session loop for this plan only.
- Update plan frontmatter todo statuses and HANDOFF for this plan as you go.
- Before "Staging ready: yes": run repository-appropriate formatter/linter on touched files.
- `Staging ready: no-diff` when the plan completed and there is no versionable product diff. The parent skips the release and advances.
- `Staging ready: no` only when a product diff exists and did not land on staging. The parent stops the queue.

Return ONLY a structured summary (no diff/log dump):
## Worker summary
- outcome: completed | blocked | partial
- lastTodoId: <id>
- filesTouched: [<paths>]
- failures: [<optional short notes>]
- Staging ready: yes | no | no-diff
- Notes: <1-2 sentences>
```

### Stop conditions

Do not dispatch the next plan when:

| Condition | Action |
|-----------|--------|
| Worker `blocked` / `partial` on an operator-only gate (account checkout, host panel, credential, billing) | Defer, not stop: outcome `deferred-operator (gate: <what>)` agent-inferred, plan stays in Run queue, no ship, cursor advances, Queue status stays `running`. Dependents via PO-map `A blocks B` defer with gate = blocking plan. No mid-queue Ask; the gates come back at queue end ([Queue-end gates Ask](#queue-end-gates-ask)) |
| Next plan depends on a prior plan's unfinished deliverable (not an operator gate) | HANDOFF with blocked status; stop. `/git-staging` only if there is a diff (orchestrator may stage queue-meta only; product staging belongs to the subagent tick) |
| Next plan requires Gate B (was opted in) | HANDOFF + stop (Gate B not yet granted; manual `/start-project` or re-run with explicit opt-in) |
| User asked to stop | Do not reschedule; HANDOFF with current queue position |
| API / usage hit limit (quota, rate-limit signal, Task dispatch failure, auto model switch) | Hard stop: revert to-do to `pending`; HANDOFF with stop reason + cursor + queue position; operator message to wait for reset or switch off Auto to a named model (Claude Opus / Sonnet 4.6 / Composer 2.5 Fast); do not advance queue cursor; do not dispatch the next plan |
| Prior HANDOFF still records an API/usage limit hard stop and operator has not confirmed recovery | Refuse auto-reschedule and refuse next-plan Task dispatch until named-model switch and/or quota wait; same pre-flight as `/run-plan` (HANDOFF stop-reason check only; no remaining-quota API) |
| Queue exhausted (all plans completed or deferred) | Final HANDOFF; with deferred rows Queue status is `exhausted (deferred: <plan> -> <gate>; ...)` (`formatQueueEndStatus`) and the report lists each gate, then the [Queue-end gates Ask](#queue-end-gates-ask) (last, after the audits and triage below); the next `/run-plan-all` re-probes those gates first; run `.cursor/scripts/field-report-cadence-bump.sh batch-complete`; queue-end audits arm (autonomous or paste per config; not a mid-queue paste Ask); `plans-only` suggests `/git-prod` if staging is ahead of `main` (separate HITL). `per-plan-release` does not ship again |
| Subagent summary missing/malformed and user does not authorize advance | HANDOFF with blocked/partial marker; stop or re-dispatch after Ask |

### Queue-end gates Ask

A queue that ends with `deferred-operator` rows does not end silently. After Final HANDOFF (so nothing is lost when nobody answers), after the queue-end audits / triage and the `plans-only` `/git-prod` suggestion, the orchestrator Asks once, id `queue-end-gates`, labels exactly `Resolve gates now` / `Print resolution prompt` / `Later`. The question lists one line per deferred plan: the gate, who owns it, and the exact step or command that unblocks it. Helpers: `decideQueueEndGatesAsk` and `formatQueueEndResolutionPrompt` in `run-plan-all-orchestrator.ts` (ADR `2026-09-28_run-plan-all-defer-operator-gates.md`, Amend 2026-10-26).

`Resolve gates now`: in order, open each Ask the gates name (`asks`, one per message, labels as stored in the plan/ADR) and cite the reply as that Ask's provenance; for an operator action (merge, account step, dogfood) print the step and wait for the reply; then re-probe, one `/run-plan` Task per plan whose gate is now open, with the normal ship lane; plans still gated stay deferred and, when any remain, Ask `queue-end-gates` again. Never performs or skips the operator step. `Print resolution prompt`: print `formatQueueEndResolutionPrompt` (re-run command + one line per gate) for a fresh session or the driver client, then stop. `Later`, skip or cancel: stop; HANDOFF already holds the deferred rows and the next `/run-plan-all` re-probes them first. Headless runs relay this gate as `hitl_gate`; a backend with no relay ends at the gate with HANDOFF already final.

### Context checkpoint (plan boundaries)

At each plan boundary (after ship lane Done/skip, before the next plan Task), if the orchestrator self-estimates about **50% or more** of its window is used: persist the queue, then **Ask questions** with labels exactly `Continue queue` / `Stop and prepare handoff` / `Change queue`. Claude Code has no `preCompact` signal; the orchestrator self-estimates (message count, tool calls, token heuristic). Helpers: `decideContextCheckpointAsk` in `run-plan-all-orchestrator.ts`.

| Option | Behavior |
|--------|----------|
| `Continue queue` | Keep going; dispatch the next plan Task. |
| `Stop and prepare handoff` | Persist queue + outcomes; tell the operator to open a new conversation and paste `/run-plan-all`. |
| `Change queue` | Stop execution; return to PO / confirm path (do not scramble the frozen order silently). |

Skipped or cancelled means **stop**. Do not Ask this mid-plan inside a Task. On resume after handoff, compare Backlog to Confirmed backlog (see [Start vs resume](#start-vs-resume-stored-queue)). **Policy pre-answer (driver mode only):** the reply may be `HITL_REPLY: context-checkpoint | policy pre-answer 1 | Continue queue` instead of an operator reply. That means the operator turned on the driving app's pre-answer setting (ADR `2026-10-26_driver-chat-side-agent-programmatic-resolver.md`, Amend 2026-10-28; the only pre-answerable gate). Act on it as `Continue queue`. Cite that line as a policy pre-answer in HANDOFF, never as an operator reply. No other Ask ever gets this stamp.

## HANDOFF Persistence

Every queue mutation updates `.cursor/HANDOFF.md` with these fields:

```
Mode: run-plan-all
Run queue: [plan-a.plan.md, plan-b.plan.md, plan-c.plan.md]
Queue cursor: 1 (current: plan-b.plan.md)
Queue status: running | paused | blocked | exhausted | exhausted (deferred: plan-b.plan.md -> <gate>)
Confirmed backlog: [plan-a.plan.md, plan-b.plan.md, plan-c.plan.md, eligible-not-queued.plan.md]
Queue outcomes:
  plan-a.plan.md: completed (to-dos: id-1, id-2, id-3)
```

HITL claims on these fields (especially `Queue status: stopped` or a Parked row as operator action) must record Ask id, operator reply, or `agent-inferred`. An inferred stop must not look identical to an operator stop.

`- **Confirmed backlog:**` is the Gate-A Backlog basename set at the last queue confirm. Resume compares current Backlog to this set. See ADR `2026-09-25_run-plan-all-three-hitl-points.md` and `2026-07-26_run-plan-all-queue-contract.md`.

**Gaps voice:** keep `- **Gaps:**` short and operator-facing (exact `none` when only mid-batch / cadence / monitor plumbing changed; never `none. Residuals…` as an OK debit). Do not dump queue-outcome tables, mid-batch monitor paths, or `/git-prod` boilerplate into Gaps. Full say/avoid pattern: handoff template + ADR `2026-07-27_mc-flight-log-panel.md`.

## Guidance for long runs

- **Cooldown between plans (`interTickCooldownMs`):** when `.cursor/context/config.json` has a value `> 0`, the orchestrator waits that many ms between queued plan Tasks. **Default remains `0`** so named-model / fast queues are not silently slowed. Set via Mission Control **Config** or `config.json` (see `config.example.json`).
- **Auto continuous queues:** if the operator stays on **Auto**, strongly recommend a non-zero cooldown before starting (documented recommend: **15000** ms). After a quota hard stop, next successful resume should use cooldown ≥ that recommend (bounded adaptive backoff, prose only; no fake Cursor quota API).
- **First-queue Auto surface (when cooldown is `0`):** before dispatching the first plan Task (or on resume after an API-limit stop), if `interTickCooldownMs` is missing or `0` and the operator appears to be on **Auto**, briefly surface the 15000 ms recommend. Do **not** change the global default. Named-model queues need no nag.
- **Prefer a named model** (Claude Opus, Sonnet 4.6, or Composer 2.5 Fast) over **Auto** for long queues. Named models typically use a **separate quota bucket** from Auto and expose Ask questions for HITL. Auto fallback after a limit (e.g. to Grok 4.5) loses Ask questions and is not a successful tick.
- **Do not** throttle Mission Control SSE/poll as a Cursor Agent quota fix (local-only; see enforcement audit).
- **Parallel plan Tasks are not used.** The sequential orchestration (one Task per plan, one plan at a time) is already a mitigation against API hit-rate. This is locked by the pure-orchestration ADR.

## Stop

User: "stop" / "stop the run" → do not schedule the next plan; HANDOFF with current queue position (cursor index + outcomes so far).

## HITL (invariants)

- Asks only at (1) queue confirm, (2) context checkpoint at plan boundaries when estimated window use is about 50%+, (3) novel error or expired wait. Labels: see command Ask table. Novel failure: `Retry recovery once` / `Hold and document` / `Stop the queue` (no fourth label)
- Plan Tasks never `/git-prod`. The ship lane promotes only when `- **Ship auth:**` is `per-plan-release`
- The confirm queue Ask is a mandatory HITL gate (no silent default); write `- **Confirmed backlog:**` at confirm
- Stored-queue start/resume uses the 3-way Ask only when a Backlog plan appeared after confirm (or a queued item is invalid); stable Backlog already present at confirm is not drift
- After confirmation, each plan runs in a **Task** subagent; the orchestrator does not implement to-dos in-window
- Missing/malformed Task summary requires an Ask before advancing the cursor
- Risk gates (PII, secrets, ambiguous scope) remain per-plan within `/run-plan`'s own tick contract (inside the Task)
- External plan review Ask/paste runs **once at queue end** only for HITL; mid-queue arms one wait per plan (or one `--batch` + wait_all) without triage Ask; queue-end waits then `/plan-review-triage` Ask with explicit paths; must not open a second prod Ask or cut another tag
- Rejected consolidation proposals leave plan files untouched

## Typical flow

```
User: /run-plan-all
Agent: [PO synthesis] Read merges (20), commits (10), CHANGELOG, 4 plans...
       Proposal: 4 plans in order. Overlap: plan-b touches same files as plan-c (collision).
       Consolidation: merge plan-d into plan-a (scope subset).
       [Ask questions: confirm labels]
User: [clicks Run as proposed]
Agent: [Merges plan-d into plan-a, archives plan-d]
       HANDOFF: Mode run-plan-all, Ship auth per-plan-release, Run queue [plan-a, plan-b, plan-c], Queue cursor 0
       [Activate plan-a → Task dispatch (run_in_background) with plan + HANDOFF + return contract]
       [End-of-turn: Worker summary outcome=completed]
       [Ship lane: one release for plan-a, wait until Done, then Queue cursor 1]
       [Activate plan-b → Task dispatch ...]
       ...
       [All plans exhausted → Final HANDOFF, queue-end audits arm; plans-only may suggest /git-prod]
```

**Context checkpoint / pause flow:**

```
...plan boundary...
Agent: Window ~50%+. Ask Continue queue / Stop and prepare handoff / Change queue.
User: [Stop and prepare handoff]
Agent: HANDOFF persisted (cursor, outcomes, Confirmed backlog). Open a new conversation and paste '/run-plan-all'.
```

## Troubleshooting

- **"No eligible plans found"**  -  check that at least one plan has `pending`/`in_progress` to-dos. Gate-B-only plans require `Include Gate-B plans` opt-in at confirm time.
- **"Queue file missing on resume"**  -  a plan was deleted outside the queue. That is drift (`queued_plan_invalid`); Ask start-vs-resume or run a new synthesis.
- **"Blocked queue plus Backlog"**  -  Ask only when a Backlog basename is new since `- **Confirmed backlog:**`. Stable eligible-not-queued Backlog from confirm time is not drift. Do not auto-append. Do not accept explore `kind: resume` that omits new-since-confirm plans.
- **"Consolidation proposal rejected"**  -  no state is changed. The queue runs in the proposed order with all original plan files intact.
- **"HANDOFF Mode is run-plan-all but queue is empty"**  -  the queue finished and no new synthesis was requested. Suggest `/run-plan-all` again if there are new eligible plans.