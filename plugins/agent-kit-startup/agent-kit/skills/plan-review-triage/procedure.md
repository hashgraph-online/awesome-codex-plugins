# /plan-review-triage procedure

Full Steps 1-6 walk and example flows for `.cursor/commands/plan-review-triage.md` (kept out of the command to fit its size budget; Goal, Usage, Preconditions, Hard stops, and exact Ask labels stay in the command itself).

## What to Do

### Step 1: Read the monitor

When **no paths provided** (select targets; **never** "newest mtime wins" alone):

**Prefer CLI SoT** (deterministic; do not invent selection in the model):

```bash
agent-kit monitors --untriaged --json
```

Use the returned `monitors[].relativePath` list as the walk order. Cite: ADR `2026-07-27_plan-review-triage-untriaged-not-mtime`.

**Selection order** (stop at the first non-empty set; then walk that set like multi-path) — matches the CLI when the binary is unavailable:

1. **Git-fresh:** `git status` / staged / untracked `.cursor/memory/plan-monitor-*.md` that lack a triage heading (`## Triage note` / `## Follow-up plan` / `## Residuals plan`).
2. **HANDOFF-aligned:** monitor paths for plans named in HANDOFF `- **Run queue:**` / queue outcomes / Gaps when those monitors exist and are still untriaged.
3. **Untriaged scan:** all `.cursor/memory/plan-monitor-*.md` without a triage heading. Prefer those with open gaps (numbered Residual items, non-empty Still open, substantive Standing finding; same spirit as Field Report `reportHasOpenReviewGaps`), but still include clean untriaged files so the operator can **Ack and stop**. If several match, walk them (blocking/debt order when obvious; otherwise newest **content** review date, then mtime as a weak tie-break only).
4. **Hard stop:** if every candidate is already triaged, report "no untriaged monitors" and stop. Do **not** Ask on an already-triaged file just because its mtime is newest.

**Gap-aware skip** (empty Still open / no residual items) applies to **explicit multi-path** lists (launcher-printed paths or hand-built lists). Bare-command selection above does **not** skip clean untriaged monitors: they still need a durable triage heading.

**Then read the selected set:**

1. **Delegate to a Task(explore) subagent** using the command-worker-prompt template:
   - Fill the template fields:
     - **Command:** `/plan-review-triage`
     - **Task description:** "Select triage targets under `.cursor/memory/plan-monitor-*.md` using selection order: (1) git-fresh untriaged, (2) HANDOFF-aligned untriaged, (3) all untriaged (prefer open gaps). Do **not** choose solely by mtime. Return structured summaries for each selected path (Current state, Full review, Still open, Standing findings). If none qualify, say so."
     - **read_scope:** `[".cursor/memory/plan-monitor-*.md", ".cursor/HANDOFF.md"]`
     - **worker_contract:** "selected paths + per-monitor structured summary: plan name, closed items, still-open items (with IDs), standing findings, triaged yes/no"
     - **max_ticks:** 1
   - Dispatch Task(explore)
   - Read the worker summary
2. **Fallback:** when Task dispatch is unavailable, perform the same selection order inline (do not glob-sort by mtime and stop on the first file).

When one path is selected, continue with Steps 2-5. When several are selected, use Step 6 (multi-path walk).

When **paths provided**:

1. Treat paths as an ordered list: blocking paths first, debt paths second (Field Report classification order).
2. For each path, apply **Gap-aware skip** (above). Only remaining gap monitors get a Task(explore) dispatch (or batch them in one worker if multiple paths).
3. **Fallback:** when Task dispatch is unavailable, verify each path is an existing file under `.cursor/memory/` matching `plan-monitor-*.md`. Non-existent, non-monitor, already-triaged, or no-open-residual paths are skipped with a one-line note; the walk continues.
4. Read the worker summary for each path that was not skipped.

### Step 2: Summarize for the user

Present a concise summary:
> **Plan monitor findings for `[plan-name]`:**
> 
> **Closed:** [brief list of completed items]
> 
> **Still open:** [numbered list of residuals with IDs from monitor]

### Step 2b: Classify preferred outcome (termination policy)

Before Ask, classify open residuals for **closeout depth** and severity (ADR `decisions/2026-08-11_plan-audit-residuals-termination.md`):

1. **Theme family / closeout_depth:** strip leading `close-`, trailing `-residuals` / `-still-open`, and revision suffixes (`-rN`, `-rN-rM`, `-n2-n3`, `-a-f`, …). Depth includes prior Write-residuals/`close-*` hops for that family; a plan basename that already starts with `close-` is depth ≥ 1. Count those hops from `.cursor/plans/`, `.cursor/plans/archive/`, and HANDOFF `- **Backlog plans:**` (plan files are gitignored; completed `close-*` plans live in archive).
2. **Preferred class:**
   - All open items are nits / docs-cite / process hygiene (Gaps voice, R14/R15, ledger, inherited CI dirt) with **no Blocking product defect** → prefer **Ack and stop** or **Fix nits only**.
   - Monitor is already depth ≥ 1 and no Blocking product finding → prefer **Ack and stop** / **Fix nits only**; do **not** treat Write residuals as the happy path.
   - Blocking product work remains and depth still allows a first residual (depth 0 → first `close-*`) → Write residuals remains eligible.
3. State the preferred class in the Step 2 summary. **Ask still shows all three labels** (HITL preserved). Operator may force Write residuals via Ask **Other** / explicit override when Blocking work remains past depth; record the override in the triage heading.

### Step 3: Ask for triage decision

Use **Ask questions** tool with these exact options:

> "How to handle the open residuals?"

Options: `Write residuals plan` / `Fix nits only` / `Ack and stop`

**Fallback (path 1):** if Ask questions is missing, say so once, print the same three labels as a numbered list, accept number or label, and treat a typed answer as Other. Do not invent a fake tool call.

### Step 4: Persist a durable triage heading (required for every outcome)

After the human chooses, **append** to the monitor file (agent turn writes the file; Mission Control never auto-writes):

```markdown
## Triage note

- **Date:** YYYY-MM-DD
- **Choice:** Write residuals plan | Fix nits only | Ack and stop
- **Summary:** [one line]
```

Rules:

1. **All three outcomes** write this heading (or an equivalent `## Follow-up plan` / `## Residuals plan` heading when a residuals plan is created).
2. **Ack and stop** must write the heading on the monitor. Updating HANDOFF alone is **not** enough: Field Report uses `isReportTriaged`, which looks for a triage heading (or a follow-up plan reference). Without the heading, the row stays untriaged.
3. Keep HITL: do not invent a choice; do not write the heading before the user picks an option.
4. Prefer appending once near the end of the file; do not delete prior review evidence.
5. **Owed-row adoption:** when this monitor's slug has a dead wait-state and an owed Field Report row (see "Owed-row adoption" above), append the adoption fact to the same heading — for example `- **Closes owed:** yes (adoption; earlier exit 3 for this slug stays 3)`. Never narrate this as "the timed-out audit completed"; it is "an independent monitor exists and the operator adopted it." Choice `Ack and stop` on an owed row records the row as **acked**, still **unreviewed** (do not write `reviewed` for an Ack close).
6. **Residuals executors (R15):** when closing Still open items from a residuals plan, **append** a `## Closed by residuals plan` section (ids + evidence). Do **not** rewrite or empty the reviewer's `### Still open` table in place. Prefer the monitor already committed when written so edits have history (ADR `decisions/2026-07-29_plan-monitor-staging-hygiene-r14-r15.md`).

### Step 5: Execute the choice

#### A. `Write residuals plan`

Enqueue residuals in-session via the `/backlog-add` contract (ADR `decisions/2026-07-28_triage-write-residuals-via-backlog.md`). Do **not** end on a clipboard `/start-project` paste as the happy path.

0. **Termination gate (before Broad Intake):** refuse another `close-*` enqueue when (a) closeout_depth ≥ 1 and no Blocking product finding, (b) Still open is only process/monitor hygiene owned by existing ADRs, or (c) the proposal would only restate acceptance / regenerate evidence for already-merged work. Redirect to **Ack and stop** or **Fix nits only** unless the operator explicitly overrides. Default **max closeout depth = 1** (ADR `decisions/2026-08-11_plan-audit-residuals-termination.md`).

1. Persist the triage heading (Step 4) with Choice `Write residuals plan`. After the plan file exists, prefer upgrading or appending `## Residuals plan` / `## Follow-up plan` with the plan basename (durable heading on the monitor still required).

2. **Broad Intake Review** (required before propose): same Broad Intake buckets and triage labels as `/backlog-add` / `/start-project`, including **Unprocessed dogfood** (`dogfood/README.md` or `.cursor/dogfood/README.md` `##` or `### Unprocessed Files`; never auto-analyze) and **Remote issues and dogfood** (`agent-kit remote-issues --json`, read-only; `notes` = note findings, never blocks).
   Reuse the Task(explore) worker contract from `.cursor/commands/backlog-add.md` (template: `.cursor/context/templates/command-worker-prompt.md`; Command may read `/plan-review-triage` Write residuals; include dogfood README paths in `read_scope`). Seed the goal from this monitor's Still open (and include-worthy Standing findings). Fallback: run Broad Intake inline when Task is unavailable. Do not invent a fifth triage label.

3. **Propose** a residuals plan from Still open + Broad Intake `include` / `error` findings (respect `ignore` / `note`). Prefer a single combined residuals plan; do not invent a basename that continues an unbounded `close-*-still-open` chain when depth is already capped.

4. **Ask write confirm** with Ask questions (chat numbered-list fallback). Exact options:
   - `Write plan to backlog`
   - `Modify proposal first`
   - `Cancel`

5. **Cancel / skipped answer:** stop. Triage heading already written; no plan file or Backlog HANDOFF edit.

6. **Modify:** revise the proposal, ask again.

7. **Write plan to backlog:**
   1. Create `.cursor/plans/<name>.plan.md` with frontmatter to-dos (template: `.cursor/context/templates/plan.md`).
   2. Append the basename under HANDOFF `- **Backlog plans:**` (bullet field only; never a bare `## Backlog plans` heading).
   3. **Never** park, activate, offer Gate B, invent Field Report cards for routine enqueue, or rewrite `- **Run queue:**` / queue cursor / status / outcomes.
   4. Stop. Tell the operator the plan path; resume later via `/continue-plan` or queue inclusion (`/run-plan-all`), not Gate B.

8. **Escape hatch only:** if the operator explicitly wants activate + Gate B, they may run `/start-project` themselves. That is optional; it is **not** the default close after Write residuals plan.

#### B. `Fix nits only`

1. Persist the triage heading (Step 4) with Choice `Fix nits only`.

2. **Confirm scope** with specific item list from monitor:
   > "Fixing these nits only: [list]. Proceed?"

3. **On confirmation:** implement only the small fixes listed as "nits" 
   - Typically: typos, formatting, small doc updates, obvious omissions
   - **Never:** architecture changes, new features, or multi-file refactors

4. **After fixes:** suggest `/git-staging` if there are changes

5. **Warn about multi-phase:** if fixes look substantial, stop and redirect to "Write residuals plan" instead

#### C. `Ack and stop`

1. Persist the triage heading (Step 4) with Choice `Ack and stop` so the Field Report row clears.

2. **Optionally update HANDOFF** with a short note. Keep `- **Gaps:**` natural (exact `none` or one residual); do **not** dump monitor paths, cadence ids, or mid-batch audit plumbing into Gaps, and do **not** write `none. Residuals…` when the intent is OK (Flight Log voice; ADR `2026-07-27_mc-flight-log-panel.md`). Example Instruction (not Gaps body):
   ```
   Monitor reviewed; residuals acknowledged. No immediate action.
   ```

3. **No product edits** beyond the monitor heading (and optional HANDOFF note)

4. **Confirm status:** monitor findings noted; triage heading written

### Step 6: Multi-path walk (paths provided **or** Step 1 selected a set)

When multiple report paths are in scope (explicit args **or** bare-command selection), the agent applies Steps 2-5 after gap-aware skip. Rules:

1. **Uniform batch HITL** - after skip, if **two or more** monitors still need a triage decision and their open residuals share the **same outcome class** (all Ack-and-stop, or all write-one-residuals / fix-nits for the shared set), present **one** Ask questions gate for the whole set. Do **not** require N identical replies. ADR: `decisions/2026-07-27_plan-review-triage-batch-uniform-hitl.md`. When the uniform class is process-only or depth-capped, prefer batch **Ack and stop** / **Fix nits only** (still Ask; never silent-Ack).
2. **Mixed → sequential fallback** - if outcome classes differ, or the operator chooses a per-file path, Ask **per** monitor (legacy walk).
3. **No silent Ack** - every triage decision (batch or per-file) requires Ask questions (or chat numbered-list fallback). Never invent Ack without HITL. Never silent-Ack **Blocking** findings that still need real product work when depth allows a first residual (or the operator overrides).
4. **Durable heading on every target** - after the chosen outcome, write `## Triage note` (or Follow-up / Residuals) on **each** monitor in the decided set before finishing. Batch Ack that updates only the first file is invalid.
5. **Batch Write residuals** - when the uniform (or operator-expanded) choice is Write residuals plan:
   - **Default (shared theme):** one Broad Intake for the set → one combined residuals plan → one backlog write-confirm Ask. On write, enqueue once; each monitor's Residuals / Triage heading references that path.
   - **Per-monitor (operator asks for one plan per monitor, or residuals do not share a coherent theme):** one Broad Intake seed per monitor (may share a skim pass), then **one residuals plan file per monitor**. Prefer this when the operator says e.g. `Write residuals for all` / `1 and write all the other` / `one plan per monitor`.
   - **Write-confirm collapse:** after the first Write residuals choice in a multi-path walk, if the operator also authorizes the remaining untriaged targets in the same reply (e.g. `1 and write all the other`), treat that as write-confirm for the whole remaining set. Do **not** re-Ask write-confirm per monitor. Still write a durable triage heading on every target before enqueue.
   - Never require a second `/start-project` paste after backlog write. Never park, activate, Gate B, or rewrite Run queue.
6. **Paced Task dispatch (API/usage hygiene)** - when writing **more than one** residuals plan via Task subagents:
   - Dispatch **at most 2** plan-author Tasks in parallel (wave size 2). Do **not** fan out one Task per monitor in a single turn when N ≥ 3.
   - After each wave returns, the parent consolidates (plan paths, HANDOFF Backlog bullets, `## Residuals plan` headings), then starts the next wave. Optional short pause between waves when the session is on Auto (same spirit as `interTickCooldownMs` ≥ 15000 after quota risk; see context-guardian).
   - Each Task writes **only** its `.cursor/plans/<name>.plan.md` (unique path). The **parent** appends all HANDOFF `- **Backlog plans:**` rows and monitor Residuals headings (avoids HANDOFF merge races).
   - Shared cross-monitor debt (e.g. one stale ledger) must be **owned once**: first plan that includes it, or an explicit companion plan; later plans label that item `note` with a pointer. Do not enqueue N identical ledger-regen to-dos.
   - Fallback: if Task dispatch is unavailable or quota-blocked, author plans inline one at a time (same pacing: finish one file before the next). Hard-stop on API/usage limit per context-guardian; do not keep dispatching.
7. **Stopping contract** - if the human stops mid-walk (disagrees, changes mind, or says stop), the walk stops at that point. Completed monitors keep their triage headings; remaining monitors stay untriaged.
8. **Path skipping** - non-existent or non-monitor paths are skipped with a one-line note. The walk continues to the next valid path.

## Example flow - Bare command (untriaged selection)

```
User: /plan-review-triage
Agent: Selection: git-fresh untriaged → plan-monitor-auth-api.md
       (skipped plan-monitor-run-plan-all.md: already triaged; mtime newer but ineligible)

       Plan monitor findings for auth-api plan:
       
       Closed: JWT middleware, refresh tokens, basic tests
       
       Still open:
       A. Rate limiting missing from login endpoint
       B. Password strength validation not implemented  
       C. API docs missing error response formats
       
       [Ask questions: How to handle residuals? Options: Write residuals plan / Fix nits only / Ack and stop]
User: [clicks Write residuals plan]
Agent: Appends ## Triage note to the monitor, runs Broad Intake (same as /backlog-add),
       proposes a residuals plan from Still open + intake, then Ask:
       Write plan to backlog / Modify proposal first / Cancel.
User: [clicks Write plan to backlog]
Agent: Writes `.cursor/plans/auth-api-residuals.plan.md`, appends it under HANDOFF
       `- **Backlog plans:**`, upgrades monitor heading with the plan path, and stops.
       Plan is on Backlog (no Gate B). Resume later with `/continue-plan` or queue inclusion.
       (Optional escape hatch: operator may still run `/start-project` for activate + Gate B.)
```

## Example flow - Multi-path walk

```
User: /plan-review-triage .cursor/memory/plan-monitor-auth.md .cursor/memory/plan-monitor-ui.md
Agent: Both monitors share Write-residuals outcome class → one batch Ask.
User: [clicks Write residuals plan]
Agent: One Broad Intake for the set → one combined residuals proposal →
       Ask Write plan to backlog / Modify / Cancel.
User: [clicks Write plan to backlog]
Agent: Writes one plan file + Backlog row; ## Residuals plan (or Triage note) on each monitor
       referencing that path. No `/start-project` paste. Mixed outcomes stay sequential.
```

## Example flow - Per-monitor Write residuals (paced Tasks)

```
User: /plan-review-triage
Agent: Six git-fresh untriaged monitors; mixed classes → sequential Ask starting at 1/6.
User: 1 and write all the other with a subagent for each
Agent: Treats as Write residuals + write-confirm for remaining set.
       Appends ## Triage note on each target.
       Dispatches plan-author Tasks in waves of 2 (not 5 at once).
       Each Task writes one .cursor/plans/*.plan.md; parent updates HANDOFF
       Backlog + ## Residuals plan on every monitor. Shared ledger owned once.
```
