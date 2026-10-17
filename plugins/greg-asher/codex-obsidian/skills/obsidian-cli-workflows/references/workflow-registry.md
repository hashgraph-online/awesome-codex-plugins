# Obsidian One-Command Workflow Registry (2026-04-21)

This registry is decision-complete for `obsidian-cli-workflows`.

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
- `intent`: capture an idea into inbox conventions with metadata
- `required_inputs`: `title` or `content`
- `optional_inputs`: `folder`, `tags`, `properties`, `open_new_tab`, `create_strategy=create|unique`
- `chained_steps`:
  1. `obsidian-official-cli`: `create` (default path-based note creation)
  2. `obsidian-cli-workspace-and-navigation`: `unique` (optional alternative when `create_strategy=unique`)
  3. `obsidian-official-cli`: `property:set`, `append`
  4. `obsidian-official-cli`: `tags` or `properties` verification
  5. `obsidian-cli-workspace-and-navigation`: `open` (optional)
- `default_output`: inline capture result with created path and applied metadata
- `risk_level`: medium
- `apply_guardrails`: require explicit folder/title target and metadata preview before create

### 4) `project.kickoff`
- `internal_id`: `wf_project_kickoff_note`
- `intent`: create a project kickoff note with starter structure and metadata
- `required_inputs`: `project_name`, `target_path`
- `optional_inputs`: `template`, `owner`, `status`, `starter_tasks`
- `chained_steps`:
  1. `obsidian-official-cli`: `create` or `template:insert`
  2. `obsidian-official-cli`: `property:set`
  3. `obsidian-official-cli`: `append` task scaffold
  4. `obsidian-official-cli`: `links` verification
- `default_output`: note-ready kickoff artifact summary
- `risk_level`: medium
- `apply_guardrails`: confirm target path and template presence/readability before mutation

### 5) `project.status_digest`
- `internal_id`: `wf_status_digest`
- `intent`: summarize project status from folder-level tasks and metadata
- `required_inputs`: `project_path`
- `optional_inputs`: `status_property`, `write_digest_note`, `digest_note_path`
- `chained_steps`:
  1. `obsidian-official-cli`: `search path=...`
  2. `obsidian-official-cli`: `tasks path=... format=json`
  3. `obsidian-official-cli`: `properties` / `property:read`
- `default_output`: status digest grouped by state and blockers
- `risk_level`: low
- `apply_guardrails`: writing digest note requires explicit destination path

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
- `intent`: build topic-focused research pack from related vault notes
- `required_inputs`: `query`
- `optional_inputs`: `scope_path`, `max_notes`, `write_pack_note`, `pack_note_path`
- `chained_steps`:
  1. `obsidian-official-cli`: `search:context query=...`
  2. `obsidian-official-cli`: `outline` on selected notes
  3. `obsidian-official-cli`: `backlinks`, `links`
- `default_output`: synthesized topic pack with source note references
- `risk_level`: low
- `apply_guardrails`: write mode requires explicit output note path

### 9) `graph.repair_plan`
- `internal_id`: `wf_link_repair_plan`
- `intent`: produce unresolved-link repair plan with candidate mappings
- `required_inputs`: none
- `optional_inputs`: `scope_path`, `apply_mode=plan_only|guided_apply`
- `chained_steps`:
  1. `obsidian-official-cli`: `unresolved verbose format=json`
  2. `obsidian-official-cli`: `search` candidate targets
- `default_output`: repair plan with confidence-ranked suggestions
- `risk_level`: low
- `apply_guardrails`: any mutation path requires per-link confirmation and exact path matching

### 10) `graph.orphan_reduction`
- `internal_id`: `wf_orphan_reduction`
- `intent`: reduce orphan/dead-end notes with prioritized actions
- `required_inputs`: none
- `optional_inputs`: `scope_path`, `suggest_backlink_seed`, `apply_backlink_seed`
- `chained_steps`:
  1. `obsidian-official-cli`: `orphans`, `deadends`
  2. `obsidian-official-cli`: `tags`, `properties`
  3. `obsidian-official-cli`: `append` (optional backlink seed)
- `default_output`: actionable orphan reduction report
- `risk_level`: low (preview/report), medium (apply backlink seeds)
- `apply_guardrails`: require explicit per-note apply list before any append actions

### 11) `base.snapshot`
- `internal_id`: `wf_base_view_snapshot`
- `intent`: snapshot base view output for reporting and downstream analysis
- `required_inputs`: `base`, `view`
- `optional_inputs`: `format=json|csv`, `output_note_path`
- `chained_steps`:
  1. `obsidian-cli-bases-and-bookmarks`: `bases`, `base:views`
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
  1. `obsidian-cli-bases-and-bookmarks`: `base:views` validation
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
