# /backlog-add Broad Intake Review detail

Full Broad Intake bucket table, triage labels, product-context reasoning, Task(explore) delegation fields, and the post-write inbox Ask for `.cursor/commands/backlog-add.md` (kept out of the command to fit its size budget; Goal, Hard stops, and the write-confirm Ask stay in the command itself).

### 1. Broad Intake Review (required before plan proposal)

> **Delegation note:** The actual bucket scanning below is performed by a **Task(explore) subagent** dispatched from this step. The table defines the specification of what the worker scans. See below for the delegation pattern. Delegation stays (ADR `decisions/2026-07-26_command-orchestration-delegation-pattern.md`); the Plans bucket is **index + HANDOFF only**.

Before enqueueing a new plan, **scan** these sources (read/skim; do not deep-dive every file) and use findings for conflict triage:

| Bucket | What to check | How / typical paths |
|--------|---------------|---------------------|
| **Prepared repository** | Verified profile and readiness state | `.cursor/agent-kit.config.json`, `.cursor/context/readiness.json` |
| **Active session** | HANDOFF, Context Pack | `.cursor/HANDOFF.md`, `.cursor/context/current/` |
| **Plans** | Active / backlog / parked / pending | `.cursor/context/plan-index.json` + `.cursor/HANDOFF.md` (named files only). Named single-file reads of a known basename remain OK. |
| **Archived context** | Prior packs for same theme | `.cursor/context/archive/**` (if present; glob by topic) |
| **Decisions** | ADRs that constrain the goal | `.cursor/memory/decisions/`, `_index.md` Decisions table |
| **Memory** | Errors, audits, consolidations, review logs, plan-monitors, findings audits | `.cursor/memory/errors/`, `.cursor/memory/plan-monitor-*.md`, theme-matched `plan-review-*.md`, `_index.md` (Audits + Decisions) |
| **Unprocessed dogfood** | Factory/consumer inbox notes awaiting triage (not sessionStart-only) | `dogfood/README.md` or `.cursor/dogfood/README.md` under `##` or `### Unprocessed Files`; skim titles/summaries only. Missing/empty inbox → no findings. Labels: ignore (owned by open plan), error/include (kit gap), note (inbox evidence only). Never auto-analyze or memory WRITE (ADRs `decisions/2026-08-11_dogfood-unprocessed-broad-intake-bucket.md`, `decisions/2026-08-14_main-command-dogfood-audit-routing.md`) |
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

When the operator payload mixes personal operations with product intent, run the **product-context reasoning stage** (see `.cursor/context/templates/plan.md`) as part of Broad Intake: single-scan the source, split product from personal/PII, persist a hygiene-stripped extract to `docs/product-context/` (tracked, inheritable project voice), and point the plan at the extract. Do not commit raw attachments. Skip when no mixed source exists.

The actual scanning and triage is delegated to a **Task(explore) subagent** using the worker prompt template at `.cursor/context/templates/command-worker-prompt.md`.

1. **Fill the template** — set these parameters:
   - **Repo:** `[absolute repo path]`
   - **Command:** `/backlog-add`
   - **Task description:** "Scan the Broad Intake buckets listed in this command (prepared repository, active session, plans from index + HANDOFF only, archived context, decisions, memory, Unprocessed dogfood, local docs, working tree, recent commits, product version) and return a structured triage report with findings per bucket, each labeled ignore/error/include/note. For Plans: read `.cursor/context/plan-index.json` and `.cursor/HANDOFF.md`; do not glob `.cursor/plans/*.plan.md`. For Unprocessed dogfood: skim `dogfood/README.md` or `.cursor/dogfood/README.md` `### Unprocessed Files` only; never auto-analyze. Remote issues: `agent-kit remote-issues --json` (read-only)."
   - **read_scope:** `[".cursor/agent-kit.config.json", ".cursor/context/readiness.json", ".cursor/HANDOFF.md", ".cursor/context/current/", ".cursor/context/plan-index.json", ".cursor/context/archive/**", ".cursor/memory/decisions/", ".cursor/memory/errors/", ".cursor/memory/plan-monitor-*.md", ".cursor/memory/plan-review-*.md", ".cursor/memory/_index.md", "dogfood/README.md", ".cursor/dogfood/README.md", "docs/**", "package.json", "CHANGELOG.md"]`
   - **worker_contract:** "structured triage report: list of findings per bucket with triage labels (ignore/error/include/note)"
   - **max_ticks:** 2

2. **Dispatch** a Task subagent with `subagent_type: explore`.

3. **Read the worker summary** — the main window uses the triage findings for conflict triage in Step 2 (vague goals) and Step 3 (propose and confirm write).

**Fallback:** If Task dispatch is unavailable or the worker template is missing, run the Broad Intake Review inline (same as pre-delegation behavior).

**Unprocessed inbox Ask (post-default, when non-empty):** after the write Ask, if Unprocessed has rows, **Ask questions** (one question; numbered-list fallback is path 1) with labels exactly:
- `Analyze inbox now` — start the ingest ritual (analyze → memory WRITE → triage). Notes become plans/memory after HITL, never `plan-monitor-*.md`. Then continue this enqueue.
- `Enqueue Fix now` — fold include/error Unprocessed rows into this proposal (already in Broad Intake). Do not start a nested `/backlog-add`.
- `Not now` — treat remaining inbox rows as `note` only.

Never auto-analyze. Never Ask inbox before the write confirm. Empty or missing inbox: skip this Ask.
