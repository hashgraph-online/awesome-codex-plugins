# Obsidian One-Command Workflow Registry (2026-04-21)

This registry is decision-complete for `obsidian-cli-workflows`.

## Shared note-output foundation

Each entry below retains its domain ownership. Any capture, synthesis/report save, task-log insertion, property repair, or optional `output=note` delegates to the core [authoring/revision contract](../../obsidian-official-cli/SKILL.md) and [procedure](../../obsidian-official-cli/references/authoring-and-revision.md). A destination path alone is insufficient: resolve and retain vault identity/root too. Preview exact content/diff and collision policy; recheck before apply, verify after, and reconcile uncertain completion before retry. Existing-file default is block unless an approved append/revision/replacement policy applies. A note save promotes a read-only workflow to medium risk and requires matching apply authorization. Preview never writes. Matching existing approval is sufficient.

An explicitly selected capture recipe for saving a briefing or a daily workflow draft is a separately previewed create-only note. See [capture recipes](capture-recipes.md).

## Canonical interface

- required: `workflow_id=<command-id>`
- optional: `mode=preview|apply` (default `preview`)
- optional: `vault=<name>`
- optional: `output=inline|note|json` (default `inline`)

Global apply policy:
- medium/high risk workflows require explicit apply confirmation
- apply only runs approved steps that still match preview targets
- ambiguous targets fail closed

## Registered workflows

### 1) `daily.bootstrap`
- `internal_id`: `wf_daily_bootstrap`
- `intent`: initialize the daily note with structured bootstrap context
- `required_inputs`: none
- `optional_inputs`: `date` (defaults to `today`), `template`, `carry_over_from`, `include_metrics`
- `chained_steps`:
  1. `obsidian-official-cli`: `daily:path`, `daily:read`
  2. `obsidian-official-cli`: `tasks daily format=json`
  3. `obsidian-official-cli`: `daily:append`
  4. `obsidian-cli-workspace-and-navigation`: `wordcount`
- `default_output`: inline plan/summary with daily note target and appended sections
- `risk_level`: medium
- `apply_guardrails`: require explicit append block preview and exact daily target before apply

### 2) `daily.review`
- `internal_id`: `wf_daily_review`
- `intent`: produce a concise end-of-day summary from today note and tasks
- `required_inputs`: none
- `optional_inputs`: `date`, `include_backlinks`, `output_note_path`
- `chained_steps`:
  1. `obsidian-official-cli`: `daily:read`
  2. `obsidian-official-cli`: `tasks daily format=json`
  3. `obsidian-official-cli`: `backlinks`
- `default_output`: inline review summary with action buckets
- `risk_level`: low
- `apply_guardrails`: if writing to note output, require explicit target path confirmation

### 3) `inbox.capture`
- `internal_id`: `wf_inbox_capture`
- `intent`: capture an idea into inbox conventions with metadata, or use an explicit [capture recipe](capture-recipes.md) for direct, web, or batch inputs
- `required_inputs`: `title` or `content` for legacy capture. With `recipe=`, use the matching recipe inputs and preview/apply procedure.
- `optional_inputs`: `folder`, `tags`, `properties`, `open_new_tab`, `create_strategy=create|unique`
- `chained_steps`:
  1. `obsidian-official-cli`: `create` (default path-based note creation)
  2. `obsidian-cli-workspace-and-navigation`: `unique` (optional alternative when `create_strategy=unique`)
  3. `obsidian-official-cli`: include approved metadata and body in the create preview when possible. Delegate any separate changes to [controlled authoring](../../obsidian-official-cli/references/authoring-and-revision.md).
  4. `obsidian-official-cli`: `tags` or `properties` verification
  5. `obsidian-cli-workspace-and-navigation`: `open` (optional)
- `default_output`: inline capture result with created path and applied metadata
- `risk_level`: medium
- `apply_guardrails`: require explicit folder/title target and metadata preview before create

A single `recipe=decision` without a requested capture date uses the [undated decision contract](decision-capture.md). Use the [dated recipe contract](capture-recipes.md) for an explicitly dated decision or a batch. Both use one create-only operation per item with properties embedded in the exact preview.

### 4) `project.kickoff`
- `internal_id`: `wf_project_kickoff_note`
- `intent`: create a project kickoff note with starter structure and metadata. Explicit `recipe=kickoff` uses [capture recipes](capture-recipes.md) instead of the legacy steps below.
- `required_inputs`: `project_name`, `target_path` for legacy kickoff. Recipe mode uses the recipe inputs.
- `optional_inputs`: `template`, `owner`, `status`, `starter_tasks`
- `chained_steps`:
  1. `obsidian-official-cli`: exact-path `create`, optionally with a verified template
  2. `obsidian-official-cli`: preview metadata in the candidate or follow [metadata revision](../../obsidian-official-cli/references/authoring-and-revision.md#revise-metadata)
  3. `obsidian-official-cli`: `append` task scaffold
  4. `obsidian-official-cli`: `links` verification
- `default_output`: note-ready kickoff artifact summary
- `risk_level`: medium
- `apply_guardrails`: confirm target path and template presence/readability before mutation

### 5) `project.status_digest`
- `internal_id`: `wf_status_digest`
- `intent`: build a cited project briefing or explicit handoff
- `required_inputs`: `project_path`, project name, or selected notes identifying the project
- `optional_inputs`: `view=briefing|handoff` (default `briefing`), `query`, `status_property`, shared [retrieval inputs](cited-retrieval.md#inputs-and-scope). Keep `project_path` as the folder alias and `write_digest_note` / `digest_note_path` as save aliases.
- `chained_steps`: workspace/navigation resolves vault identity; core skill retrieves and verifies sources with [shared cited retrieval](cited-retrieval.md), using tasks/properties on selected notes where useful; workflow skill synthesizes the briefing or handoff.
- `default_output`: inline scope, current state, decisions, blockers, next actions and cited sources
- `risk_level`: low for retrieval, medium for note output
- `apply_guardrails`: recheck evidence and delegate any requested save to shared authoring after matching approval

### 6) `tasks.rollup`
- `internal_id`: `wf_task_rollup`
- `intent`: aggregate open tasks across selected scope with prioritization
- `required_inputs`: none
- `optional_inputs`: `path`, `tag`, `assignee`, `bucket_rules`
- `chained_steps`:
  1. `obsidian-official-cli`: `tasks todo verbose format=json`
  2. `obsidian-official-cli`: `search:context` for blocker signals
- `default_output`: prioritized rollup report (inline/json/note)
- `risk_level`: low
- `apply_guardrails`: note output mode requires explicit output path

### 7) `tasks.close_and_log`
- `internal_id`: `wf_task_closure_sync`
- `intent`: close a specific task and log completion in daily note
- `required_inputs`: `task_ref`
- `optional_inputs`: `completion_note`, `daily_date`
- `chained_steps`:
  1. `obsidian-official-cli`: `task ref=... done`
  2. `obsidian-official-cli`: `daily:append`
  3. `obsidian-official-cli`: `tasks daily`
- `default_output`: completion audit with closed task and daily log status
- `risk_level`: medium
- `apply_guardrails`: require explicit `task_ref` and explicit daily target/date confirmation

### 8) `research.pack`
- `internal_id`: `wf_research_pack`
- `intent`: answer a vault question, build a topic evidence pack, or explain related notes
- `required_inputs`: `query`; for related notes, selected notes may supply the anchor instead
- `optional_inputs`: `view=answer|pack|related` (default `pack` for named calls), shared [retrieval inputs](cited-retrieval.md#inputs-and-scope). Keep `scope_path` as the folder alias and `write_pack_note` / `pack_note_path` as save aliases.
- `chained_steps`: workspace/navigation resolves vault identity; core skill retrieves and verifies sources with [shared cited retrieval](cited-retrieval.md); workflow skill answers, builds the pack, or explains the recommendations.
- `default_output`: inline cited findings with conflicts and gaps, or explained related notes with excerpts
- `risk_level`: low for retrieval, medium for note output
- `apply_guardrails`: recheck evidence and delegate any requested save to shared authoring after matching approval

### 9) `graph.repair_plan`
- `internal_id`: `wf_link_repair_plan`
- `intent`: diagnose unresolved links in an exact scope and preview selected repairs
- `required_inputs`: exact folder or note paths in a pinned vault
- `optional_inputs`: `scope_path` (exact folder or note), exclusions, budgets, `apply_mode=plan_only|guided_apply`
- `chained_steps`: scope through workspace/navigation, then core `unresolved`, `links`, bounded candidate verification, and approved exact revision
- `default_output`: structured findings, exact source occurrences, verified candidates and ambiguity
- `risk_level`: low for diagnosis, medium for apply
- `apply_guardrails`: follow [vault audits](vault-audit.md) and require matching per-link approval

### 10) `graph.orphan_reduction`
- `internal_id`: `wf_orphan_reduction`
- `intent`: review orphan/dead-end candidates with context and optional link suggestions
- `required_inputs`: exact folder or note paths in a pinned vault
- `optional_inputs`: `scope_path` (exact folder or note), exclusions, budgets, `suggest_backlink_seed`, `apply_backlink_seed`
- `chained_steps`: intersect core `orphans` and `deadends` with scope, verify exact-path context, optionally preview an explicit append
- `default_output`: explained review candidates and exact optional link proposals
- `risk_level`: low for review, medium for approved append
- `apply_guardrails`: follow [vault audits](vault-audit.md), require explicit per-note apply list and exact link approval, verify occurrence counts

### 11) `base.snapshot`
- `internal_id`: `wf_base_view_snapshot`
- `intent`: snapshot base view output for reporting and downstream analysis
- `required_inputs`: `base`, `view`
- `optional_inputs`: `format=json|csv`, `output_note_path`
- `chained_steps`:
  1. `obsidian-cli-bases-and-bookmarks`: discover exact path with `bases` and use `base:views` only if the intended base is already confirmed active
  2. `obsidian-cli-bases-and-bookmarks`: `base:query`
- `default_output`: structured snapshot plus quick summary metrics
- `risk_level`: low
- `apply_guardrails`: output note write requires explicit destination path

### 12) `base.intake_create`
- `internal_id`: `wf_base_intake_create`
- `intent`: create a new tracked item through a base workflow
- `required_inputs`: `base`, `view`, `item_data`
- `optional_inputs`: `open_after_create`, `target_path`
- `chained_steps`:
  1. `obsidian-cli-bases-and-bookmarks`: validate the named view with pinned `base:query path=... view=...`
  2. `obsidian-cli-bases-and-bookmarks`: `base:create`
  3. `obsidian-cli-workspace-and-navigation`: `open` or `tab:open` (optional)
- `default_output`: created-item summary with resulting file/path identifiers
- `risk_level`: high
- `apply_guardrails`: require explicit base/view confirmation and field-level create preview

### 13) `bookmark.curate`
- `internal_id`: `wf_bookmark_curator`
- `intent`: curate bookmarks for an active context
- `required_inputs`: none
- `optional_inputs`: `folder`, `search`, `file`, `target_collection`
- `chained_steps`:
  1. `obsidian-cli-bases-and-bookmarks`: `bookmarks verbose`
  2. `obsidian-cli-bases-and-bookmarks`: `bookmark file|search|folder`
  3. `obsidian-cli-bases-and-bookmarks`: `bookmarks` post-check
- `default_output`: bookmark diff summary (before/after)
- `risk_level`: medium
- `apply_guardrails`: require explicit bookmark target scope and add list before apply

### 14) `workspace.focus_mode`
- `internal_id`: `wf_focus_mode_switch`
- `intent`: switch into a named focus workspace and open priority notes
- `required_inputs`: `workspace_name`
- `optional_inputs`: `priority_paths`, `verify_recents`
- `chained_steps`:
  1. `obsidian-cli-workspace-and-navigation`: `workspace:load`
  2. `obsidian-cli-workspace-and-navigation`: `tabs`
  3. `obsidian-cli-workspace-and-navigation`: `open path=... newtab`
  4. `obsidian-cli-workspace-and-navigation`: `recents`
- `default_output`: workspace switch summary with opened-tab list
- `risk_level`: high
- `apply_guardrails`: require explicit workspace name and note-open list confirmation

### 15) `recents.triage`
- `internal_id`: `wf_recent_triage`
- `intent`: triage recent notes into actionable next steps
- `required_inputs`: none
- `optional_inputs`: `recent_limit`, `write_summary_note`, `summary_note_path`
- `chained_steps`:
  1. `obsidian-cli-workspace-and-navigation`: `recents`
  2. `obsidian-cli-workspace-and-navigation`: `wordcount`
  3. `obsidian-official-cli`: `tasks` on selected notes
- `default_output`: ranked triage summary
- `risk_level`: low
- `apply_guardrails`: summary-note writes require explicit destination path

### 16) `runtime.debug_snapshot`
- `internal_id`: `wf_plugin_debug_snapshot`
- `intent`: capture runtime/plugin debug evidence in one pass
- `required_inputs`: `plugin_id`
- `optional_inputs`: `screenshot_path`, `include_dom`, `include_css`
- `chained_steps`:
  1. `obsidian-cli-runtime-admin`: `plugin:reload`
  2. `obsidian-cli-devtools`: `dev:errors`, `dev:console`
  3. `obsidian-cli-devtools`: `dev:screenshot`
  4. `obsidian-official-cli`: optional report-note append
- `default_output`: debug snapshot artifact summary
- `risk_level`: medium
- `apply_guardrails`: require explicit plugin target and artifact paths; do not use `eval` unless explicitly requested

### 17) `sync.health_check`
- `internal_id`: `wf_sync_health_check`
- `intent`: assess sync health and potential restore/deletion risk indicators
- `required_inputs`: none
- `optional_inputs`: `path`, `include_history`
- `chained_steps`:
  1. `obsidian-cli-sync-and-publish`: `sync:status`
  2. `obsidian-cli-sync-and-publish`: `sync:deleted`
  3. `obsidian-cli-sync-and-publish`: `sync:history` (optional)
- `default_output`: health summary with risk flags and suggested follow-up
- `risk_level`: low
- `apply_guardrails`: no mutation in default path; restore actions must be delegated and explicitly confirmed

### 18) `publish.release_gate`
- `internal_id`: `wf_publish_release_gate`
- `intent`: gate publish actions behind capability + readiness checks
- `required_inputs`: none
- `optional_inputs`: `path`, `publish_scope=changed|path|file`, `dry_run`
- `chained_steps`:
  1. `obsidian-cli-sync-and-publish`: `help publish:status` capability probe
  2. if supported: `publish:status`, `publish:list`
  3. if supported and approved: `publish:add` or `publish:remove`
- `default_output`: capability gate verdict + publish readiness report
- `risk_level`: high
- `apply_guardrails`: if probe unsupported, block with explicit reason and run no `publish:*` commands

### 19) `base.dashboard`
- `internal_id`: `wf_base_dashboard`
- `intent`: author or revise a table definition and verify representative dashboard results
- `required_inputs`: exact `.base` destination, explicit collection scope, table specification, and expected result checks. Edits also require an exact existing view.
- `optional_inputs`: view filters, sort, grouping, supported formulas and summaries, and bounded row limit
- `chained_steps`:
  1. `obsidian-cli-workspace-and-navigation`: pin vault identity and canonical root
  2. `obsidian-official-cli`: inspect representative note properties and check exact target
  3. `obsidian-bases-authoring`: validate and preview definition or scoped diff
  4. `obsidian-official-cli`: after matching approval, apply and verify exact `.base` bytes through the shared authoring safeguards
  5. `obsidian-cli-bases-and-bookmarks`: query exact path and named view and compare with expected results
- `default_output`: structural, write and live result status with exact target, candidate or diff, and any metadata or capability gaps
- `risk_level`: medium
- `apply_guardrails`: follow the [Bases authoring contract](../../obsidian-bases-authoring/SKILL.md), verify CLI suffix/content capability, require exact create-only absence or approved scoped overwrite, and preserve collection notes

### 20) `canvas.map`
- `internal_id`: `wf_canvas_map`
- `intent`: author or revise a source-linked research map, project overview or process flow
- `required_inputs`: exact `.canvas` destination, purpose, layout and source or process scope. Edits require exact record IDs.
- `optional_inputs`: selected notes, verified subpaths, relationship labels and explicit URLs
- `chained_steps`:
  1. `obsidian-cli-workspace-and-navigation`: pin vault and canonical root
  2. `obsidian-official-cli`: verify exact source and target paths, using cited retrieval when needed
  3. `obsidian-canvas-authoring`: validate source links and layout, preview exact content or scoped diff
  4. `obsidian-official-cli`: apply the approved artifact through verified exact-path CLI transport and verify bytes
  5. `obsidian-cli-workspace-and-navigation`: open the exact map for visual inspection when authorized
- `default_output`: source and relationship evidence, layout warnings, candidate or diff, write and visual status
- `risk_level`: medium
- `apply_guardrails`: follow the [Canvas authoring contract](../../obsidian-canvas-authoring/SKILL.md), preserve unrelated records and source notes, and never silently overwrite

### 21) `vault.audit`
- `internal_id`: `wf_vault_audit`
- `intent`: audit explicit metadata conventions and unresolved links, with selected verified corrections
- `required_inputs`: exact folder or note paths in a pinned vault
- `optional_inputs`: exclusions, note/read budgets, conventions, orphan/dead-end review
- `chained_steps`: resolve scope, compare core CLI evidence with conventions, preview exact selected repairs, delegate approved writes and verify findings
- `default_output`: coverage, structured findings, exact repair diffs, remaining issues and per-item outcomes
- `risk_level`: low for diagnosis, medium for apply
- `apply_guardrails`: follow [vault audits](vault-audit.md), honor per-link/per-note approval and stop on uncertain dispatch
