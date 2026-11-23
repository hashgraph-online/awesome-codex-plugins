# /start-project intake

## Goal

Bootstrap a **plan with to-dos** from any user payload. This command does **not** mean "start coding."

## When to Use

- First time using Agent Kit
- When there is no active plan or Context Pack  
- When you want to start a **new** project/task

## Hard stops (kit failure if skipped)

These are non-negotiable in manual mode:

1. **Broad Intake Review first.** Before proposing or writing a plan, run the Broad Intake Review (see below) to scan active session, plans, memory, docs, git state, and product version. Use findings for conflict triage.
2. **Plan file before any product edit.** Do not modify agents, skills, rules, app code, registry, or docs-of-record while creating the plan. Allowed writes in the bootstrap turn: the new `.cursor/plans/*.plan.md` and updated HANDOFF reflecting the chosen disposition for any prior active plan (backlog or park).
3. **Goal in the same message is not execute permission.** `/start-project scan the repo and fix X` still goes through the gates below. Never jump to Explore → Edit.
4. **Two gates, two user "yes" answers:**
   - **Gate A (approve plan):** propose phases/to-dos → write the plan file → stop and ask using **Ask questions** tool.
   - **Gate B (approve first unit):** only after Gate A is accepted → run **one** phase or one heavy to-do → update HANDOFF → stop again.
5. **Forbidden phrasing / behavior:** "I'll create a plan and start Phase 1", chaining Gate A+B in one turn, or running the whole plan unless the user explicitly used `/run-plan`.

## Prepared repository contract

Before intake, read `.cursor/agent-kit.config.json` and `.cursor/context/readiness.json`.

**Planning blockers** (stop and point to `/agent-kit-onboard`; do not resolve setup here):

- Derive unresolved essentials from `pillars[].checks[]` where `essential: true` and `status` is not `ready`. Preserve report order.
- Do **not** treat `pendingActions` as an essential-only queue. Non-essential pending items (for example `collaboration.provider` / action `confirm-provider`) are **warnings only**: one-line mention or silence, continue Broad Intake, and do not halt planning. Do **not** Ask on `confirm-provider` / `collaboration.provider`.
- Missing readiness or config files, unsupported snapshot schema, or a fingerprint mismatch that invalidates the snapshot: point to `/agent-kit-onboard`. Do not reconstruct onboarding inside `/start-project`.

**When essentials are ready** (non-essential pending allowed):

- Reuse verified purpose, stack, Git, context, and validation facts. Do not ask the user to confirm them again.
- Ask only for the deliverable goal. Repository purpose is setup context, not the goal of the new plan.
- Gate A and Gate B remain mandatory; readiness does not skip HITL.

## Broad Intake Review (required before plan proposal)

> **Delegation note:** The actual bucket scanning below is performed by a **Task(explore) subagent** dispatched from Step 1. The table defines the specification of what the worker scans. See Step 1 for the delegation pattern. Delegation stays (ADR `decisions/2026-07-26_command-orchestration-delegation-pattern.md`); the Plans bucket is **index + HANDOFF only**.

Before proposing or writing a new plan, **scan** these sources (read/skim; do not deep-dive every file) and use findings for conflict triage:

| Bucket | What to check | How / typical paths |
|--------|---------------|---------------------|
| **Prepared repository** | Verified profile and readiness state | `.cursor/agent-kit.config.json`, `.cursor/context/readiness.json` |
| **Active session** | HANDOFF, Context Pack | `.cursor/HANDOFF.md`, `.cursor/context/current/` |
| **Plans** | Active / backlog / parked / pending | `.cursor/context/plan-index.json` + `.cursor/HANDOFF.md` (named files only). Named single-file reads of a known basename remain OK. |
| **Archived context** | Prior packs for same theme | `.cursor/context/archive/**` (if present; glob by topic) |
| **Decisions** | ADRs that constrain the goal | `.cursor/memory/decisions/`, `_index.md` Decisions table |
| **Memory** | Errors, audits, consolidations, review logs, plan-monitors, findings audits | `.cursor/memory/errors/`, `.cursor/memory/plan-monitor-*.md`, theme-matched `plan-review-*.md`, `_index.md` (Audits + Decisions) |
| **Unprocessed dogfood** | Factory/consumer inbox notes awaiting triage (not sessionStart-only) | `dogfood/README.md` or `.cursor/dogfood/README.md` under `##` or `### Unprocessed Files`; skim titles/summaries only. Missing/empty inbox → no findings. Labels: ignore (owned by open plan), error/include (kit gap), note (inbox evidence only). Never auto-analyze or memory WRITE (ADR `decisions/2026-08-11_dogfood-unprocessed-broad-intake-bucket.md`) |
| **Remote issues and dogfood** | Dogfood/findings filed as remote issues, both lanes | `agent-kit remote-issues --json` (read-only). Factory: origin + public; consumer: own origin only (gh/glab). Filter: provenance label or `[Dogfood]` title (per ADR). Its `notes` (no CLI/auth/offline) → one `note`, never blocks. Same labels; no comment/label/close, no auto-analyze (ADR `decisions/2026-09-28_broad-intake-remote-issues-both-lanes.md`) |
| **Local docs** | SoT / inventories / getting-started that the goal touches | `docs/**`, especially files named in the payload or related SoT |
| **Working tree** | Uncommitted local work that would collide | `git status`, `git diff` (staged + unstaged); do not commit |
| **Recent commits** | What already shipped for this theme | `git log` (short, recent), related PR titles if available |
| **Product version** | Avoid stale version prose | `package.json`, `CHANGELOG.md` `[Unreleased]` / latest |

**Triage labels** (every relevant finding gets one):

- **ignore**: already a future/pending to-do on an active or parked plan; leave for `/continue-plan`. For plan-monitors: owned by another open plan, or already triaged clean (`## Triage note` / follow-up / residuals-plan heading)
- **error**: completed work that overreached, contradicted HITL, or left a verifiable residual → **include** in the new plan. For plan-monitors: GAP or regression vs claimed-complete work
- **include**: new scope from the user payload, or residual not owned by another plan. For plan-monitors: open residual not owned by an active/backlog plan
- **note**: operational gap (e.g. monitor misses tags); record in plan Constraints / Acceptance or memory, no code unless asked. For plan-monitors: outdated vs HEAD, freshness caveat, or staging-hygiene risk (dirty untracked monitors)

Do not invent a fifth triage label. Field Report and `/plan-review-triage` remain attention/HITL SoT; Broad Intake consults monitors as evidence only (ADR `decisions/2026-07-27_plan-monitor-consumer-awareness.md`).

### Product-context reasoning (when source mixes personal and product)

When the operator payload (attachment, cited document, or inline text) mixes personal operations with product intent, run the **product-context reasoning stage** (see `.cursor/context/templates/plan.md`) as part of Broad Intake, before proposing the plan:

1. Single-scan the source: split product facts from personal/PII.
2. Persist a hygiene-stripped extract to `docs/product-context/` (tracked, inheritable project voice, no PII or chat metalanguage).
3. Point the plan at the extract. Later ticks read the extract, not the session origin.
4. Do not commit raw operator attachments. Do not graft an interview loop onto intake.

Skip when no mixed source exists. Do not treat autonomous scheduled mode as intake.

## What to Do

### Step 1: Broad Intake Review (delegated)

The actual scanning and triage is delegated to a **Task(explore) subagent** using the worker prompt template at `.cursor/context/templates/command-worker-prompt.md`.

1. **Fill the template**  -  set these parameters:
   - **Repo:** `[absolute repo path]`
   - **Command:** `/start-project`
   - **Task description:** "Scan the Broad Intake buckets listed in this command (prepared repository, active session, plans from index + HANDOFF only, archived context, decisions, memory, Unprocessed dogfood, local docs, working tree, recent commits, product version) and return a structured triage report with findings per bucket, each labeled ignore/error/include/note. For Plans: read `.cursor/context/plan-index.json` and `.cursor/HANDOFF.md`; do not glob `.cursor/plans/*.plan.md`. For Unprocessed dogfood: skim `dogfood/README.md` or `.cursor/dogfood/README.md` `### Unprocessed Files` only; never auto-analyze. Remote issues: `agent-kit remote-issues --json` (read-only)."
   - **read_scope:** `[".cursor/agent-kit.config.json", ".cursor/context/readiness.json", ".cursor/HANDOFF.md", ".cursor/context/current/", ".cursor/context/plan-index.json", ".cursor/context/archive/**", ".cursor/memory/decisions/", ".cursor/memory/errors/", ".cursor/memory/plan-monitor-*.md", ".cursor/memory/plan-review-*.md", ".cursor/memory/_index.md", "dogfood/README.md", ".cursor/dogfood/README.md", "docs/**", "package.json", "CHANGELOG.md"]`
   - **worker_contract:** "structured triage report: list of findings per bucket with triage labels (ignore/error/include/note)"
   - **max_ticks:** 2

2. **Dispatch** a Task subagent with `subagent_type: explore`.

3. **Read the worker summary**  -  the main window uses the triage findings for conflict triage in Step 2 (vague goals) and Step 3 (Gate A).

**Fallback:** If Task dispatch is unavailable, run the Broad Intake Review inline (same as pre-delegation behavior).

### Step 2: Handle vague goals

If the goal is missing or vague, use **Ask questions** tool (fallback to chat if tool unavailable):
> "What's the goal of your project? (1-2 sentences)"

Wait for answer before proceeding.

### Step 3: Gate A (design only)

1. **Propose phases and to-dos** based on the goal and Broad Intake findings. If the host already has a native Cursor Plan Mode plan, copy it into `.cursor/plans/` first, then run this Gate A (host Plan Mode does not replace Gate A/B; ADR `2026-09-15_kit-plans-sot-over-host-plan-mode.md`). Align with `autogit/plan-routine.md` and `.cursor/context/templates/plan.md`.

2. **Ask one composite Gate A question** using **Ask questions** tool (fallback to chat if tool unavailable  -  render one numbered list per message). If an active plan exists, the options merge disposition and write into a single pick:

   > "Write this plan to `.cursor/plans/[name].plan.md` (to-dos in frontmatter, no coding yet)?"

   **With active plan**  -  composite options:
   | Option | Disposition | Action | Gate B |
   |--------|-------------|--------|--------|
   | `Write plan and add to backlog (keep current active)` | backlog | write plan file | skipped |
   | `Park current plan, write plan and activate new` | park | write plan file | follows |
   | `Modify proposal first` |  -  |  -  |  -  |
   | `Cancel` |  -  | abort |  -  |

   **No active plan**  -  options:
   | Option | Action | Gate B |
   |--------|--------|--------|
   | `Write plan file` | write plan file and activate | follows |
   | `Write plan and add to backlog` | write plan file; list under Backlog plans; Mode STOPPED | skipped |
   | `Modify proposal first` |  -  |  -  |
   | `Cancel` | abort |  -  |

3. **On approval:** create the plan file. Update HANDOFF per the chosen disposition (park, backlog, or activate). Backlog path (with active plan, or no-active-plan `Write plan and add to backlog`): plan listed under "Backlog plans", Mode STOPPED (or current plan stays active when disposing a prior active plan), skip Gate B. Park path: new plan active, phase none / awaiting Gate B. Activate path (`Write plan file` with no prior active plan): new plan active, then Gate B.

4. **Stop and ask for Gate B** (park path or no-active-plan activate path only) using **Ask questions** tool (fallback to chat if tool unavailable, one list per message):
   > "Plan ready: `[path]`. First unit would be `[to-do-id]` only (manual = one phase per chat)."
   
   Options: `Start first unit` / `Switch to /run-plan` / `Edit plan first` / `Add to backlog` / `Stop here`

   | Option | Effect |
   |--------|--------|
   | `Start first unit` | run one unit (Gate B proceed) |
   | `Switch to /run-plan` | continuous mode for this plan |
   | `Edit plan first` | revise plan; re-ask Gate B later |
   | `Add to backlog` | list under Backlog plans; Mode STOPPED; unit not started |
   | `Stop here` | plan stays **active**; unit not started (not backlog) |

   On any backlog path (Gate A or Gate B `Add to backlog`), skip or exit Gate B: report the plan location and stop (resume via `/continue-plan` or activate later). `Add to backlog` is distinct from `Stop here`.
### Step 4: Gate B (first unit only, after explicit approval)

1. Mark the to-do `in_progress`, do **only** that unit.
2. Mark it `completed`, update HANDOFF, suggest `/git-staging` if there is a diff.
3. Stop. Do not start the next phase in this chat (manual mode).

### Step 5: Footer (informational only)

After proposing the plan, list any in-progress or parked plans in one short block:

> **Other plans:** [plan names and status]: Use `/continue-plan` to resume.

## Ask questions requirement

**Active-plan disposition, Gate A, Gate B, and vague-goal clarification MUST use Ask questions tool** (`AskQuestion` / ACP `cursor/ask_question`) instead of chat prompts like "type yes to continue." This opens clickable options in the IDE UI.

**Requirements:**
1. Use **Ask questions** for any confirmation, choice among options, or clarification before acting
2. Prefer one question at a time (or small coherent set if the product allows multi-question)  
3. Options must be concrete labels (e.g. `Write plan file`, `Start first unit`, `Skip for now`)
4. **Fallback:** if the tool is not available in the current session, say so once and ask the same options in chat

**Note:** Kit-wide contract: always-applied L0 rule [`.cursor/rules/hitl-ask-questions.mdc`](https://github.com/agent-kit-startup/agent-kit/blob/main/.cursor/rules/hitl-ask-questions.mdc).

## Onboarding flow (correct)

```
User: /start-project Build an authentication API with JWT  
Agent: [Broad Intake Review] No conflicts found.
       Proposed plan:
       0. Project setup
       1. Login/register  
       2. JWT access + refresh
       3. Auth middleware
       4. Tests
       [Ask questions: Write plan? Options: Write plan file / Write plan and add to backlog / Modify first / Cancel]
User: [clicks Write plan file]
Agent: [Writes plan + HANDOFF only] Plan ready.
       [Ask questions: Start "phase0-setup" only? Options: Start first unit / Switch to run-plan / Edit first / Add to backlog / Stop here]
User: [clicks Start first unit]  
Agent: [Does phase0 only] -> HANDOFF -> stops; suggests /git-staging if diff
```

Backlog path (Gate A or Gate B): plan file exists under `.cursor/plans/`, listed on HANDOFF Backlog, Mode STOPPED; no first-unit execution until the operator activates it later.

Wrong (do not do this):

```
User: /start-project ainda tem PT no repo, deixe EN
Agent: Scanning... creating plan and starting Phase 1... [edits files]
```

## Tip

If the user is unsure:
> "Not sure yet? Tell me a bit about what you want to build and we'll figure it out together."

Manual mode default: one phase per chat after Gate B. Multi-phase in one window requires `/run-plan`.



