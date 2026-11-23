---
name: hitl-gates
description: Agent Kit HITL contract, exact Ask questions labels, and numbered-list fallback as path 1. Use when running /start-project, /run-plan, /run-plan-all, /continue-plan, /git-prod, backlog CRUD, /hotfix, /qa, /plan-review-triage, install, or onboard, or when Ask questions is missing. Factory landing wraps /kit-staging and /kit-prod keep their own command-file Asks; they are not consumer default-path inventory. Invoke via the command's own link; do not auto-load.
version: 0.1.3
category: core
disable-model-invocation: true
---

# HITL gates

Kit-wide human-in-the-loop. Commands stay Goal + five hard stops + Ask labels + a link here. Per-command procedures, one hop each: [run-plan-tick-contract.md](./run-plan-tick-contract.md), [start-project-intake.md](./start-project-intake.md), [run-plan-all-queue.md](./run-plan-all-queue.md), [pending-ticket.md](./pending-ticket.md); `/continue-plan` is inline in its own command file. Always-applied short rule: `.cursor/rules/hitl-ask-questions.mdc`.

## Contract

1. Any confirmation, choice, or clarification before acting uses **Ask questions** (`AskQuestion` / ACP `cursor/ask_question`). Do not ask the user to type yes.
2. Prefer one question at a time.
3. Options are concrete labels (tables below). Do not invent a fake tool call.
4. **Numbered-list fallback is path 1** when the tool is not in the session toolset. Say the tool is missing once, print one `HITL_GATE: <ask-id> | <labels>` line and the same labels as a numbered list (block below), accept number or label, and treat a typed answer as Other. Matrix: `.cursor/memory/decisions/2026-07-20_ask-questions-model-availability.md`.
5. Skipped or cancelled answers mean **stop** (same as no yes).
6. Do not fabricate HITL in HANDOFF. Parked / approved / deferred / confirmed / stopped-by-operator need Ask id, operator reply, or `agent-inferred`. In a headless run the operator reply arrives as a `HITL_REPLY: <ask-id> | operator reply <n> | <label>` line; cite that line.
7. CLI `agent-kit init` keeps `@clack/prompts`. Do not call IDE Ask questions from the CLI.
8. **Check in** before each Ask and plan write: `agent-kit queue lease`; `Queue lease held:` means stop and report it ([tick contract](./run-plan-tick-contract.md)).

## Default-path Ask inventory

Each main command has **exactly one Ask at entry** on the default path. Inbox, owed-close, and landing Asks are opt-in or post-default. They are never pre-Ask blockers. Empty Unprocessed inbox: silent skip (mention count only if non-empty, after the entry Ask or not at all). A pending operator ticket is the one preflight Ask before it.

| Command | Default-path Ask (one at entry) | Off default path |
|---------|--------------------------------|------------------|
| `/start-project` | Gate A (vague-goal Ask first only if the goal is missing) | Gate B after a second yes. `confirm-provider` never |
| `/run-plan` | Risk Ask only when PII, secrets, or scope is ambiguous; otherwise the run starts with no entry Ask | Inbox, exhaustion, owed-close |
| `/run-plan-all` | Start-vs-resume (stored queue + Backlog appeared after last confirm) **or** queue confirm (fresh synthesis) | Inbox, owed-close, landing, context checkpoint at plan boundaries, novel error / expired wait. No mid-queue triage Ask |
| `/continue-plan` | Next unit: `Start [to-do-id]` / `Edit plan first` / `Switch to different plan` / `Stop here`. Multi-plan picker first when needed | Inbox |
| `/backlog-add` | `Write plan to backlog` / `Modify proposal first` / `Cancel` | Inbox. `confirm-provider` never |
| `/git-prod` | `Proceed with production deploy` / `Review changes first` / `Cancel` | none |
| `/hotfix` | `Write mini plan and run` / `Write mini plan only (stop)` / `Modify proposal first` / `Cancel` | none |
| `/qa` | Mode Ask only when the invocation is ambiguous (`QA this release` / `Repro this bug` / `Claims only` / `Cancel`); otherwise start | Scratch install: `Use a scratch git repo` / `QA this checkout only` / `Cancel` |
| `/handoff` | `Automatic handoff` / `Manual handoff` (first time or when offering a choice) | none |

## Exact Ask labels

### /start-project

**Gate A, active plan** (id `gate-a`)**:** `Write plan and add to backlog (keep current active)` / `Park current plan, write plan and activate new` / `Modify proposal first` / `Cancel`

**Gate A, no active plan** (id `gate-a`)**:** `Write plan file` / `Write plan and add to backlog` / `Modify proposal first` / `Cancel`

**Gate B** (id `gate-b`)**:** `Start first unit` / `Switch to /run-plan` / `Edit plan first` / `Add to backlog` / `Stop here`

Vague goal: ask for a 1-2 sentence goal before Gate A. Confirm-provider / `collaboration.provider` is advisory only; do not Ask it.

### /run-plan

| Gate | Id | Labels |
|------|----|--------|
| Risk (PII, secrets, ambiguous scope) | `risk` | `Continue with risk` / `Modify approach` / `Stop run` |
| Inbox (post-default; Unprocessed non-empty; skip inside a `/run-plan-all` per-plan Task) | `inbox` | `Analyze inbox now` / `Enqueue Fix now` / `Not now` |
| Exhaustion (post-default; after Final HANDOFF; `offerOnExhausted`) | `exhaustion` | `Run review now` / `Always enable automatic` / `Not now` |
| Owed-close (post-default; dead wait-state + genuine later monitor) | `owed-close` | `Adopt existing monitor` / `Ack owed without review` / `Not now` |

Never steal `/git-prod`. Exhaustion Ask/arm is after Final HANDOFF and the prod suggestion.

### /run-plan-all

| Gate | Id | Labels |
|------|----|--------|
| Inbox (post-default) | `inbox` | `Analyze inbox now` / `Enqueue Fix now` / `Not now` |
| Start vs resume (Backlog appeared after last confirm) | `queue-drift` | `Resume frozen queue` / `Insert new backlog` / `Re-synthesize` |
| Confirm queue | `queue-confirm` | `Run as proposed` / `Run plans only` / `Edit order` / `Apply merges & drops only` / `Keep all plans as-is` / `Include Gate-B plans` / `Cancel` |
| Context checkpoint (plan boundary, ~50% window) | `context-checkpoint` | `Continue queue` / `Stop and prepare handoff` / `Change queue` |
| Novel error / expired wait | `novel-failure` | `Retry recovery once` / `Hold and document` / `Stop the queue` |
| Queue end, deferred rows (after Final HANDOFF) | `queue-end-gates` | `Resolve gates now` / `Print resolution prompt` / `Later` |
| Promote PR merge wait cap | `promote-merge-wait` | `Keep waiting` / `Show the merge box reason` / `Stop and hand off` |
| Malformed Task summary | `malformed-summary` | Ask before advancing the cursor |

Asks only at these rows (ADR `2026-09-25_run-plan-all-three-hitl-points.md`, Amend 2026-10-26). Drift only for Backlog new since `- **Confirmed backlog:**`. No mid-queue triage Ask. Queue end: `queue-end-gates`, `/plan-review-triage`, `/git-prod` suggestion, separately.

### Other surfaces

| Surface | Labels |
|---------|--------|
| `/continue-plan` | Default-path (id `next-unit`): `Start [to-do-id]` / `Edit plan first` / `Switch to different plan` / `Stop here`. Multi-plan picker (index + HANDOFF only): `[plan-name.plan.md]` / `Create new plan instead`. Inbox (id `inbox`) same three labels, post-default, when Unprocessed is non-empty |
| `/backlog-add` | Default-path write (id `backlog-write`): `Write plan to backlog` / `Modify proposal first` / `Cancel`. Inbox (id `inbox`) same three labels, post-default, when Unprocessed is non-empty. Never park, activate, or Gate B. Never Ask confirm-provider |
| `/backlog-edit` | `Edit [plan-file]` / `Cancel` |
| `/backlog-delete` | `Delete [plan-file] from backlog` / `Cancel` |
| `/backlog-cancel` | `Cancel [plan-file] on backlog` / `Keep on backlog` |
| `/cancel-plan` | Id `cancel-plan`: `Cancel active plan [plan-file]` / `Keep the active plan` |
| `/git-prod` | `Proceed with production deploy` / `Review changes first` / `Cancel`. Claude lane (or recorded classifier denial): `I pushed main` / `Open staging→main PR instead` / `Cancel` |
| `/hotfix` | `Write mini plan and run` / `Write mini plan only (stop)` / `Modify proposal first` / `Cancel` |
| `/qa` | Mode (when ambiguous): `QA this release` / `Repro this bug` / `Claims only` / `Cancel`. Scratch install: `Use a scratch git repo` / `QA this checkout only` / `Cancel`. Playbook: `.cursor/skills/core/qa/SKILL.md` |
| `/plan-review-triage` | Write residuals / Fix nits only / Ack and stop. Residuals write uses backlog-add labels. Multi-path: one Ask when remaining monitors share a uniform class |
| `/field-report-resolve` | Cadence id, per owed plan (id `plan-verdict`): `Delivered nothing` / `Superseded` / `Keep owed` |
| `/handoff` / guardian | `Automatic handoff` / `Manual handoff` (first time) |
| `install.md` | Registry URL/ref; migrate nested `agent-kit/`; optional git-hooks |
| `/agent-kit-onboard` | One unresolved essential at a time. Domain skills: `Scaffold domain skills` / `Defer (record reason)` / `Skip` |
| Pending ticket (preflight, only while `.cursor/context/gate-exit.json` has a pending entry) | Id `ticket`: `Read the ticket` / `Accept` / `Discard` / `Later`. Unattended: list stamps, no Ask. Commands and effects: [pending-ticket.md](./pending-ticket.md) |

`/git-prod` and factory `/kit-prod`: one `Proceed with production deploy` is one ship (one SemVer close, one annotated `v*` tag, one promote). A red or unfinished post-prod verification (tag CI, or the wrapper's release checks) is a STOP. The next patch needs a new Ask. A `/run-plan-all` queue confirm that sets Ship auth `per-plan-release` is that yes for one ship per completed plan. It does not open this Ask again, and a red post-prod verification still stops the queue.

### Wrapper commands (not consumer L0)

A project may wrap `/git-staging` / `/git-prod` (the kit factory keeps `/kit-staging` and `/kit-prod`, omitted from consumer L0, public-sync, and the `agent-kit run` catalog). A wrapper keeps the native Ask first and owns any extra post-ship Asks and their labels in its own command file.

## Numbered fallback (path 1)

When Ask questions is absent, the numbered list is **mandatory** (path 1). Print the `HITL_GATE:` sentinel line immediately before the list, in the same message: it is how a headless run (`agent-kit run`, `run-plan`, `run-plan-all`) detects the gate and relays the operator's answer (ADR `2026-09-19_headless-hitl-transport-and-live-tui.md`).

```text
Ask questions is not available in this session. Reply with the number or the label. You can also type your own answer (Other).

HITL_GATE: <ask-id> | <label-a> | <label-b> | <label-c>
1. <label-a>
2. <label-b>
3. <label-c>
```

One numbered list per message.

Sentinel rules: one line, column 0, `HITL_GATE: <ask-id> | <label 1> | ... | <label n>`.
`<ask-id>` is the kebab-case id from the tables above (`gate-a`, `gate-b`, `risk`, `inbox`, `exhaustion`, `owed-close`, `queue-drift`, `queue-confirm`, `context-checkpoint`, `novel-failure`, `queue-end-gates`, `promote-merge-wait`, `malformed-summary`, `next-unit`, `plan-verdict`, `backlog-write`, `cancel-plan`, `ticket`); labels are the exact table labels, in list order, separated by ` | ` (no label contains `|`).
Surfaces without a listed id keep the numbered list without a sentinel (the headless runner detects them by the wording above as a prose fallback). `git-prod` and `kit-prod` are never relayed headless: the run stops and points at the operator slash.
The operator's answer comes back as one line, `HITL_REPLY: <ask-id> | operator reply <n> | <label>` (or `operator reply other | <typed text>`); cite it as the Ask provenance in HANDOFF. Never assume a reply: no answer means stop.

## /run-plan compressed tick

Strategy (announce, do not ask): Task available → orchestrated (inline-first only when every lightweight check passes); else in-session; headless → `agent-kit run-plan`.

1. Read HANDOFF, plan, config. Refuse auto-reschedule on a recorded API/usage-limit stop until the operator confirms recovery. Audits preflight `off`/`warn`/`block`. Unsatisfiable `enabled: true` + reviewer `claude` on a Claude implementer: warn or block per preflight. Session-pile warn/cap before arm.
2. Next pending to-do, frontmatter order. `force_task: true` → Task. Findings contract → Task. Else lightweight docs-only → inline-first. Mark `in_progress` before work.
3. Execute only that to-do. Findings-only for `review-*`. `autoRemediate` default false: fix-agent or residuals plan, no silent product apply.
4. Close: `completed`, HANDOFF `Mode: run-plan (<strategy>)`, cadence bump, `/git-staging` on a commitable diff. **Staging ready: yes** needs lint evidence (or `none applicable`). Dashboard HTML: `none applicable (dashboard-CSS)` covered by plugin-ux-validation. Contract string alone without that evidence is invalid.
5. Reschedule or stop. Exit `3` is **timeout-only** and does **not** retroactively convert, upgrade, or rewrite a later monitor into success. Never `/git-prod`.

Inline-first allowlist, findings authorship, worker prompt, headless runner, and audit wait: [run-plan-tick-contract.md](./run-plan-tick-contract.md).

## /continue-plan compressed

Read HANDOFF first. Plans inventory is index + HANDOFF only. Default-path Ask: next-unit confirm (multi-plan picker first when several plans resume). Persona chrome after the entry Ask. One unit per chat unless `/run-plan`. Procedure: `.cursor/commands/continue-plan.md`.

## /start-project compressed

Broad Intake (index + HANDOFF only; no `.cursor/plans/*.plan.md` glob) → Gate A (plan file only) → stop → Gate B (one unit) only after a second yes. Host Plan Mode does not replace Gate A/B: copy a native plan into `.cursor/plans/` then run Gate A (ADR `2026-09-15_kit-plans-sot-over-host-plan-mode.md`). Goal in the same message is not execute permission. Backlog paths skip Gate B. Details: [start-project-intake.md](./start-project-intake.md).

## /run-plan-all compressed

Pure orchestrator. PO synthesis (Task explore) → start-vs-resume or queue confirm (write `- **Confirmed backlog:**`) → one Task per plan. Checkpoint (~50%+ window), novel error / expired wait, promote merge wait cap: labels above.
When Ship auth is `per-plan-release`, one release per completed plan before the next. `Run plans only` does not promote. Mid-batch audits wait, no triage Ask. Queue-end wait then `/plan-review-triage`. Details: [run-plan-all-queue.md](./run-plan-all-queue.md).
