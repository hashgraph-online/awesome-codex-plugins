---
name: session-plan
user-invocable: false
tags: [orchestration, planning, waves, agents]
model: opus
model-preference: opus
model-preference-codex: gpt-5.4
model-preference-cursor: claude-opus-4-6
description: >
  Creates a structured wave execution plan with role-based assignment after user alignment.
  Decomposes agreed tasks into configurable waves (default 5) with optimal agent assignment,
  dependency ordering, and inter-wave checkpoints. Activated by session-start after Q&A phase completes.
---

> **Platform Note:** Project agents live in `<state-dir>/agents/` where `<state-dir>` is `.claude/` (Claude Code), `.codex/` (Codex CLI), or `.cursor/` (Cursor IDE). On Cursor IDE, parallel agent dispatch is not available — present wave tasks as a sequential execution list instead. See `skills/_shared/platform-tools.md`.

# Session Plan Skill

> Project-instruction file resolution: `CLAUDE.md` and `AGENTS.md` (Codex CLI) are transparent aliases — see [skills/_shared/instruction-file-resolution.md](../_shared/instruction-file-resolution.md). Wherever this skill mentions `CLAUDE.md`, the alias rule applies.

## Purpose

Transform the agreed session scope (from session-start Q&A) into an executable wave plan (using role-based assignment) with specific agent assignments, file scopes, and acceptance criteria per task.

## Input: Session Scope

This skill receives the agreed session scope from session-start. The scope includes:
- **Issue list**: VCS issue numbers and titles selected by the user
- **Session type**: housekeeping, feature, or deep
- **Recommended focus**: the option the user selected in session-start Phase 7
- **Session Config**: parsed JSON from `parse-config.mjs`
- **Express-path signal** (optional): session-start Phase 8.5 may set `EXPRESS_PATH=true` in the handoff context when the activation conditions are met.

These are passed via the conversation context (not a file). Parse the preceding session-start output to extract the agreed scope.

## Express Path Short-Circuit (#214)

> Check this **before Step 0**. If the express path is active, this skill emits a minimal 1-wave plan and exits — no role decomposition, no wave splitting, no agent count computation.

**Detect express-path activation:** Search the conversation context for the banner line:

```
Express path activated — <N> tasks, coordinator-direct, no inter-wave checks.
```

If found AND `express-path.enabled` is `true` in Session Config (read via Step 0 below — skip only that field check if config read is needed):

Emit this 1-wave plan and exit the skill immediately (do not continue to Step 1 or beyond):

```
## Wave Plan (Session: housekeeping, 1 wave, isolation: none) [Express Path]

### Wave 1: Coordinator-Direct (<N> tasks)
- All agreed tasks executed sequentially by the coordinator — no subagents dispatched.
- Tasks: [list agreed issues/tasks]
- Isolation: none (coord-direct)
- Max-turns: N/A (coordinator executes directly)

### Execution Config
- Waves: 1 | Agents-per-wave: 0 (coordinator-direct) | Isolation: none
- Express path: active (housekeeping + scope ≤ 3 + no parallel agents needed)
- Total agents planned: 0

Express path — no inter-wave checks. Use /go to begin.
```

**When express-path banner is absent or `express-path.enabled: false`:** Proceed to Step 0 and the full planning flow as normal.

## Step 0: Read Session Config

Read and parse Session Config per `skills/_shared/config-reading.md`. Store result as `$CONFIG`.

Extract these fields for planning:
- `waves` (default: 5) — number of execution waves
- `agents-per-wave` (default: 6, may have session-type overrides per `config-reading.md`) — max parallel agents per wave
- `isolation` (default: auto) — `worktree` / `none` / `auto` (auto = worktree for feature/deep, none for housekeeping)
- `enforcement` (default: warn) — `strict` / `warn` / `off`
- `max-turns` (default: auto) — agent turn budget (auto = housekeeping: 8, feature: 15, deep: 25)
- `agent-mapping` (optional) — explicit role-to-agent bindings
- `persistence` (default: true) — whether to use STATE.md and learnings

> **Fallback:** If session-start already output a `## Session Config (active)` block in the conversation context, extract values from there to avoid a redundant parse. If not present in context, parse independently.

## Step 1: Task Decomposition

0. **Check for resume context**: > Skip if `persistence` is `false` in Session Config.
   If `<state-dir>/STATE.md` exists with `status: active` or `status: paused`, read it to understand:
   - Which waves were completed in the prior session
   - Which agents completed, which were partial/failed
   - What deviations were logged
   - Use this to avoid re-doing completed work and to prioritize carryover tasks
   If no STATE.md or `status: completed`, proceed with fresh planning.

0.5. **Read project intelligence**: > Skip if `persistence` is `false` in Session Config.
   If `.orchestrator/metrics/learnings.jsonl` exists, read active learnings (confidence > 0.3, not expired). Sort by `confidence` DESC (tiebreaker: `created_at` DESC) and slice to the first `learnings-surface-top-n` entries (default 15) before applying the four categories below. If the top-N slice is empty, skip the categories.
   - **Fragile files**: if any planned task touches a known fragile file, note it as a warning in the agent spec
   - **Effective sizing**: use historical sizing data to inform Step 3 complexity scoring
   - **Recurring issues**: pre-populate risk mitigation with known issue patterns
   - **Scope guidance**: validate planned scope against historical session capacity

For each agreed task/issue:
1. Read the VCS issue description and acceptance criteria
2. Identify affected files by searching the codebase (Grep/Glob — don't guess)
3. Map dependencies: which tasks must complete before others can start
4. Estimate complexity: small (1 agent), medium (2-3 agents), large (dedicated wave)
5. Identify synergies: tasks that touch the same files → same wave, same agent

## Step 1.5: Agent Discovery

Before assigning tasks to waves, discover available agents for this session:

1. **Scan for project-level agents**: Glob `<state-dir>/agents/*.md` (`.claude/agents/*.md` for Claude Code, `.codex/agents/*.md` for Codex CLI, `.cursor/agents/*.md` for Cursor IDE)
   - Read each file's YAML frontmatter: extract `name` and `description`
   - Filter out non-agent reference files (skip files with `description` containing "Reference documentation" or "NOT an executable agent")
   - Build a list of available project agents with their names and capabilities

2. **Read agent-mapping from Session Config** (optional):
   - Field: `agent-mapping` — a JSON object mapping role keys to agent names
   - Role keys: `impl`, `test`, `db`, `ui`, `security`, `compliance`, `docs`, `perf`
   - Example: `agent-mapping: { impl: code-editor, test: test-specialist, db: database-architect }`
   - If present, these explicit mappings take priority over auto-matching

   **Validation:** If `agent-mapping` specifies an agent name, verify the agent exists:
   - For project agents: check `<state-dir>/agents/<name>.md` exists
   - For plugin agents: check the agent is registered (contains `:` separator)
   - If the agent doesn't exist: warn the user and fall back to auto-discovery for that role

3. **Build Agent Registry** (resolution priority):
   - **Priority 1**: Project agents (from `<state-dir>/agents/` — see Platform Note) — matched by name
   - **Priority 2**: Plugin agents (`session-orchestrator:code-implementer`, `session-orchestrator:test-writer`, `session-orchestrator:ui-developer`, `session-orchestrator:db-specialist`, `session-orchestrator:security-reviewer`)
   - **Priority 3**: `general-purpose` (fallback)

4. **Match tasks to agents**: For each task from Step 1:
   - If `agent-mapping` config specifies a mapping for the task's domain → use that agent. For Docs-role tasks specifically, check `agent-mapping.docs` first; if set, use that agent name instead of the default below.
   - **Docs-role fast path (high-priority — runs before keyword matching):** If the task's role is classified as `Docs` (per Step 1.8) AND `docs-orchestrator.enabled: true` in Session Config → resolve `subagent_type: "docs-writer"`. The `docs-writer` project agent is discovered at `<state-dir>/agents/docs-writer.md` during the Priority 1 scan above. No colon prefix — it is a project agent, not a plugin agent. If `agent-mapping.docs` is set, use that name instead of `"docs-writer"`.
   - Else, match task description against agent descriptions using the content-based routing table below. Match any keyword from the pattern column (case-insensitive) against the task title and description. Use the first matching row; rows are checked top to bottom.

     | Keyword pattern | Resolved agent |
     |---|---|
     | `migration`, `schema`, `RLS`, `index`, `query`, `ORM`, `supabase`, `postgres`, `database`, `db` | `session-orchestrator:db-specialist` |
     | `component`, `tsx`, `css`, `tailwind`, `page`, `layout`, `a11y`, `wcag`, `responsive`, `UI`, `frontend`, `style` | `session-orchestrator:ui-developer` |
     | `security`, `auth`, `csrf`, `csp`, `injection`, `XSS`, `sanitize`, `OWASP`, `vulnerability`, `pen test` | `session-orchestrator:security-reviewer` |
     | `test`, `coverage`, `vitest`, `jest`, `playwright`, `spec`, `fixture`, `assertion` | `session-orchestrator:test-writer` |
     | (none of the above match) | `session-orchestrator:code-implementer` |
   - Else, use role-based default: Impl-Core/Impl-Polish → `code-implementer`, Quality → `test-writer`
   - Record the resolved `subagent_type` for each task

> **No agents found?** If no project agents exist and plugin agents are available, use plugin agents. If neither, fall back to `general-purpose` for all tasks. The system works at every level.

## Step 1.8: Task-to-Role Classification

For each task from Step 1, assign exactly one role. Use these signal-to-role mappings:

| Signal in task | Role | Examples |
|---|---|---|
| Needs codebase understanding before changes; audit, explore, verify assumptions, check existing coverage | **Discovery** | "Audit auth flow", "Check test coverage for module X", "Identify affected modules" |
| New feature code, new API endpoints, DB schema changes, primary UI components, new modules | **Impl-Core** | "Add /api/users endpoint", "Create migration for invoices table", "Implement auth middleware" |
| Bug fixes from prior waves, secondary features, integration work, edge cases, polish of existing code | **Impl-Polish** | "Fix pagination edge case", "Integrate payment with billing", "Handle error states in form" |
| Documentation updates — new/changed README sections, CLAUDE.md (or AGENTS.md on Codex CLI) updates, vault context.md/decisions.md narratives, ADR edits. Audience-aware (User/Dev/Vault). Gated on `docs-orchestrator.enabled` | **Docs** | "Update README for new --no-vault flag", "Write CLAUDE.md section for new hook (or AGENTS.md on Codex CLI)", "Append vault decisions.md entry for architecture change" |
| Write/update tests, lint fixes, security review, code simplification, type errors | **Quality** | "Add tests for auth module", "Fix TypeScript errors", "Security audit of new API" |
| Documentation updates, issue cleanup, commit preparation, SSOT refresh, changelog | **Finalization** | "Update README", "Close resolved issues", "Write session handover notes" |

**Disambiguation rules:**
- If a task involves BOTH exploration AND implementation → split it: Discovery agent reads/validates, Impl-Core agent implements. Create two separate task entries.
- If a task is "fix something from a previous session" (not from this session's Impl-Core) → classify as **Impl-Core** (it is new work for this session).
- If a task is "write tests for new feature code being built this session" → classify as **Quality** (not Impl-Core). Tests run after implementation.
- If unsure between Impl-Core and Impl-Polish → if the task is on the critical path (other tasks depend on it), it is **Impl-Core**. If independent polish, it is **Impl-Polish**.
- **Docs role** is only active when `docs-orchestrator.enabled: true` in Session Config. When disabled (default), documentation-update tasks fall into **Impl-Polish** (inline doc changes alongside code) or **Finalization** (standalone doc/SSOT updates) as today.

#### Step 1.8 Docs-role: Consuming the Phase 2.5 Emission Block

When `docs-orchestrator.enabled: true`, session-start Phase 2.5 emits a delimited block in the conversation context. Read and parse it before synthesizing Docs-role tasks:

**Locating the block:** Search the conversation context for the header `### Docs Planning Result (Phase 2.5)`. If the header is absent, Phase 2.5 was skipped — emit **0 Docs tasks** and do not fabricate any.

**Parsing rules (apply in document order):**
- `Audiences:` — comma-separated list of active audience identifiers (e.g., `user, dev`). Trim whitespace around each value.
- `Mode:` — single enum value: `warn`, `strict`, or `off`. Store as `$docs_mode`.
- `Docs-tasks-seed:` — multi-entry bullet list. Each top-level `- audience:` bullet is **one seed task**. Parse in document order; do not merge entries. Each seed task has:
  - `audience:` — target audience (`user`, `dev`, or `vault`)
  - `rationale:` — free-text description of what needs documenting

**Synthesizing Docs-role tasks:** For each seed task entry (in document order):
1. Set `role: Docs`.
2. Set `description` derived from the `rationale` field (paraphrase as an actionable imperative, e.g., "Document the new `--no-vault` flag in user-facing README").
3. Set `audience` from the `audience` field.
4. Set `target-pattern` by looking up the audience in the `Audiences & File Patterns` table in `skills/docs-orchestrator/audience-mapping.md`. Use the glob pattern listed there for the matched audience row.
5. Resolve `subagent_type` per the Docs-role fast path in Step 1.5 point 4 above.

**If the block is absent:** Do not fabricate Docs tasks. The Docs role remains empty; apply the empty-role rule from Step 2.

- Housekeeping sessions: skip Steps 1.8, 2, and 3 — all tasks go into a single consolidated wave:
  - No role classification — all tasks treated as generic housekeeping work
  - Agent count: fixed at 1-2 per task (from wave-template.md housekeeping row), capped by `agents-per-wave`
  - File-scope deconfliction (Step 3.5) still applies within the single wave
  - Wave plan output uses: `### Wave 1: Housekeeping ([N agents])`

Record the assigned role next to each task before proceeding to Step 2.

### Docs-tasks persistence (for session-end Phase 3.2)

When `docs-orchestrator.enabled: true` AND the plan contains 1+ Docs tasks, session-plan MUST emit a machine-readable block **at the end of its plan output** (after the wave plan, before `Ready to execute?`). This block is the single source of truth (SSOT) consumed downstream:

- **wave-executor Pre-Wave 1b (STATE.md init):** reads this block and persists `docs-tasks: [...]` into STATE.md frontmatter.
- **session-end Phase 3.2 (docs verification):** reads `docs-tasks` back from STATE.md to verify each task produced a diff.

**Emit format:**

```yaml
### Docs Tasks (machine-readable)
docs-tasks:
  - id: docs-1
    audience: <user|dev|vault>
    target-pattern: <glob from skills/docs-orchestrator/audience-mapping.md>
    rationale: <verbatim rationale from Phase 2.5 seed>
    wave: <wave number where this docs-writer agent is dispatched>
    status: planned
  - id: docs-2
    ...
```

**Field rules:**
- `id`: sequential index-based identifier (`docs-1`, `docs-2`, …). No UUID generation required.
- `audience`: one of `user`, `dev`, `vault`.
- `target-pattern`: the glob from `skills/docs-orchestrator/audience-mapping.md` for this audience row — do not invent patterns.
- `rationale`: copy the `rationale` text from the Phase 2.5 seed entry verbatim (do not paraphrase here).
- `wave`: the actual wave number assigned in Step 2 where the `docs-writer` agent for this task is dispatched.
- `status`: always `planned` at plan time. Terminal values are set by session-end Phase 3.2 per-task verification loop: `ok` (diff substantive), `partial` (diff has `<!-- REVIEW: source needed -->` markers), or `gap` (no matching diff). wave-executor does NOT perform intermediate status updates — `status: planned` remains until session-end writes the terminal value.

**Omission rule:** When `docs-orchestrator.enabled: false` OR there are 0 Docs tasks, do NOT emit the `### Docs Tasks (machine-readable)` block. Absence of the block signals to wave-executor and session-end that no docs verification is needed for this session.

### Wave-Plan Mission Status (machine-readable)

When the wave plan contains 1 or more wave-plan items (i.e., for all non-empty plans), session-plan MUST emit a machine-readable mission-status block **at the end of its plan output** (after the Docs Tasks block if present, before `Ready to execute?`). This block is the SSOT consumed by wave-executor (for STATE.md persistence) and session-end Phase 1.9 (for enum-based classification).

- **wave-executor Pre-Wave 1b (STATE.md init):** reads this block and persists `mission-status: [...]` into STATE.md frontmatter via `writeMissionStatus` from `scripts/lib/state-md.mjs`.
- **session-end Phase 1.9:** reads `mission-status` back from STATE.md frontmatter via `parseMissionStatus` to classify items into the 1.1–1.4 buckets using enum values.

**Emit format:**

```yaml
### Wave-Plan Mission Status (machine-readable)
mission-status:
  - id: m-1
    task: <task description from wave-plan item>
    wave: <N>
    status: brainstormed
  - id: m-2
    task: <task description from wave-plan item>
    wave: <N>
    status: brainstormed
```

**Field rules:**
- `id`: sequential `m-N` identifier. No UUID generation required.
- `task`: verbatim task description from the wave-plan item (do not paraphrase).
- `wave`: the wave number where this task is dispatched.
- `status`: always `brainstormed` at plan emission. Terminal values are updated at gate transitions by wave-executor: `brainstormed` → `validated` (user confirms via `/go`) → `in-dev` (agent dispatched) → `testing` (Quality wave) → `completed` (Quality gate green). session-end Phase 1.9 reads the current value to classify the item.

**Transition gates (summary):**
At plan time, all items start at `brainstormed`. When the user runs `/go` to approve the plan, wave-executor updates each item to `validated`. When an agent for a wave-plan item is dispatched, wave-executor updates that item to `in-dev`. When the Quality wave begins, items from prior waves move to `testing`. When the Quality gate passes, items finalize at `completed`. Rollback to `brainstormed` is permitted from any state. All transitions are validated against the schema in `scripts/lib/mission-status-schema.mjs`.

**Omission rule:** When the plan has 0 wave-plan items (e.g., pure express-path coord-direct with no sub-agent tasks), do NOT emit the `### Wave-Plan Mission Status (machine-readable)` block.

### Mission-Status Enum (#340)

Every wave-plan item carries a `status` field drawn from a 5-value enum. The field is always present on items emitted in the `### Wave-Plan Mission Status (machine-readable)` block (see below). It is also the value persisted in STATE.md frontmatter and read back by session-end Phase 1.9 for enum-based classification.

#### Enum values

| Status | Meaning | Set when |
|---|---|---|
| `brainstormed` | Draft item from `/plan`, not yet user-confirmed | Plan emitted by session-plan (all items start here) |
| `validated` | User confirmed via AUQ in session-plan (`/go` approval) | wave-executor: user runs `/go` to approve the wave plan |
| `in-dev` | Agent picked up the task this wave | wave-executor: agent dispatched for this item |
| `testing` | Implementation done, tests passing for this task | wave-executor: Quality wave begins for this item's work |
| `completed` | Quality-Lite green for this task's wave | wave-executor: Quality gate passes for this item |

#### Default and transitions

- **Default at plan creation:** `brainstormed` — all items start here.
- **Transitions are coordinator-level orchestration** (not inside individual agent prompts). See `skills/wave-executor/SKILL.md` "Mission-Status Updates (#340)" for when each transition fires.
- **Rollback:** any item may return to `brainstormed` from any state (e.g. if work is discarded or re-planned).
- **Schema validation:** transitions are validated against `scripts/lib/mission-status-schema.mjs` before being written to STATE.md.

#### Status field in wave-plan items

Every item in the wave plan output carries an implicit `status: brainstormed` at plan time. The `### Wave-Plan Mission Status (machine-readable)` block below (emitted at the end of the plan output) is the machine-readable form that wave-executor and session-end Phase 1.9 consume. session-plan does NOT write STATUS transitions — it only emits the initial `brainstormed` values.

## Step 2: Wave Assignment

Distribute tasks across waves using 5 named roles. Read `waves` from Session Config (default: 5) and map roles to wave numbers.

### Wave Roles

| Role | Purpose | Agents modify code? |
|------|---------|---------------------|
| **Discovery** | Understand the current state before changing anything | No (read-only) |
| **Impl-Core** | Primary implementation — core feature code, APIs, DB changes | Yes |
| **Impl-Polish** | Fix issues from Impl-Core, secondary tasks, integration, edge cases | Yes |
| **Quality** | Tests, typecheck, lint, security review | Yes (tests only) |
| **Finalization** | Documentation, issue cleanup, commit preparation | Minimal |

### Role-to-Wave Mapping

Map roles to the configured wave count:

| `waves` | Mapping |
|---------|---------|
| 3 | W1=Discovery+Impl-Core, W2=Impl-Polish+Quality, W3=Finalization |
| 4 | W1=Discovery, W2=Impl-Core+Impl-Polish, W3=Quality, W4=Finalization |
| 5 | W1=Discovery, W2=Impl-Core, W3=Impl-Polish, W4=Quality, W5=Finalization |
| 6+ | W1=Discovery, W2-W3=Impl-Core (split), W4-W5=Impl-Polish (split), W6=Quality+Finalization |

When roles are combined into a single wave, agents from both roles execute in that wave. The combined wave inherits the more restrictive verification level.

**Docs role dispatch rule (conditional — `docs-orchestrator.enabled: true` only):**

When `docs-orchestrator.enabled: true`, apply the following concrete dispatch rule based on the count of synthesized Docs tasks from Step 1.8:

- `len(docs-tasks) == 0` → **skip Docs role entirely**. Apply the empty-role rule: do not create a Docs wave slot, do not dispatch any `docs-writer` agent.
- `len(docs-tasks) == 1` → **inline with Finalization wave**. Dispatch one `docs-writer` agent alongside the Finalization agent in the Finalization wave. The `docs-writer` agent's file scope must not overlap the Finalization agent's files (deconflict per Step 3.5).
- `len(docs-tasks) >= 2` → **dedicated Impl-Polish sub-slot or dedicated wave slot**. Options in priority order:
  1. If Impl-Polish wave has remaining agent capacity (below `agents-per-wave`): add `docs-writer` agents to the Impl-Polish wave as a sub-slot. The `docs-writer` agents MUST NOT share file scopes with any `code-implementer` agents in the same wave — verify via Step 3.5 deconfliction.
  2. If Impl-Polish is at capacity: add a dedicated Docs slot within the closest wave with capacity (prefer the wave immediately before Finalization).
- **NEVER add a 6th wave** for Docs. Docs always occupies an existing wave slot.
- When `docs-orchestrator.enabled` is `false` (default), this rule has no effect — the Docs role does not exist.

**Cross-role constraint in combined waves:** Tasks from different roles within a combined wave CANNOT be merged into a single agent (different scope permissions — e.g., Discovery is read-only, Impl-Core has write access). If the combined wave exceeds `agents-per-wave`, defer the lower-priority role's tasks: in W1=Discovery+Impl-Core, defer Impl-Core tasks to the next applicable wave. In W2=Impl-Polish+Quality, defer Quality tasks to a separate phase within the same wave.

> Example: When Discovery+Impl-Core are combined (3-wave config), the wave runs Incremental quality checks (Impl-Core's level) rather than no verification (Discovery's level).

**Splitting criteria for 6+ waves**: When Impl-Core or Impl-Polish span multiple waves, split by module or dependency boundary. Tasks with shared file dependencies go in the same wave; tasks touching independent modules go in separate waves. If no clear boundary exists, split by task count (distribute evenly).

**Empty roles:** If a role has 0 tasks, skip its wave entirely. Do NOT dispatch an empty wave. Remaining waves retain their original role names but are renumbered sequentially (e.g., if Discovery has 0 tasks and waves=5: W1=Impl-Core, W2=Impl-Polish, W3=Quality, W4=Finalization). Update `total-waves` in the plan output to reflect the actual wave count.

### Role Details

**Discovery**
- Explore-type subagents (read-only, fast)
- Tasks: Audit affected code paths, verify assumptions, check test coverage, identify edge cases
- Output: Validated understanding, updated task scope if discoveries warrant it
- Tools: Read, Grep, Glob, Bash (read-only commands only) — do NOT use Edit or Write
- Scope enforcement: set `allowedPaths` to `[]` (empty) for Discovery waves. Include in agent prompts: "You are READ-ONLY. Do NOT use Edit or Write tools."

**Impl-Core**
- Full implementation agents with Write/Edit/Bash access
- Tasks: Core feature code, database changes, API endpoints, primary UI components
- Output: Working implementation (may have rough edges)

**Impl-Polish**
- Targeted fix agents + new implementation agents
- Tasks: Bug fixes from Impl-Core, secondary features, integration, edge cases
- Output: Complete implementation with integrations working

**Quality**
- Simplification agents + test writers + quality reviewers
- Tasks: Simplify AI-generated code patterns (using slop-patterns.md from discovery skill), write/update tests (test files only — `**/*.test.*`, `**/*.spec.*`, `**/__tests__/**`), run full quality checks per quality-gates skill, security review
- Scope restriction: Simplification agents may edit production files changed in this session. Test/review agents restricted to test file patterns and test configuration.
- Output: Simplified code, all tests passing, 0 TypeScript errors, no lint violations

**Finalization**
- 1-2 specialized agents
- Tasks: Update SSOT files, close issues, write session handover, prepare commits
- Output: Clean git state, updated documentation, issues resolved

## Step 3: Complexity Assessment

Score the session scope to determine optimal agent counts per wave. Skip for housekeeping sessions (use fixed counts from Step 4).

### Scoring Formula

| Factor | 0 points | 1 point | 2 points |
|--------|----------|---------|----------|
| Files to change | 1-5 | 6-15 | 16+ |
| Cross-module scope | 1 directory | 2-3 directories | 4+ directories |
| Issue count | 1 issue | 2-3 issues | 4+ issues |

**Total score** = sum of all factors (0-6 range).

> **Cross-module scope** counts top-level source directories (e.g., `src/auth/`, `src/api/`, `lib/utils/`). Nested subdirectories under the same parent count as one directory. Non-source directories (docs, config, scripts) don't count unless they contain modified production code.

### Complexity Tiers

| Tier | Score | Description |
|------|-------|-------------|
| Simple | 0-1 | Small scope, few files, single module |
| Moderate | 2-3 | Medium scope, multiple modules |
| Complex | 4-6 | Large scope, many modules and issues |

### Agent Count by Tier

| Session Type | Tier | Discovery | Impl-Core | Impl-Polish | Quality | Finalization |
|-------------|------|-----------|-----------|-------------|---------|-------------|
| feature | simple | 2-3 | 3-4 | 2-3 | 2 | 1 |
| feature | moderate | 4-5 | 5-6 | 4-5 | 3-4 | 2 |
| feature | complex | 5-6 | 6 | 5-6 | 4 | 2 |
| deep | simple | 3-4 | 4-6 | 3-4 | 3 | 2 |
| deep | moderate | 5-6 | 6-8 | 5-6 | 4-5 | 2-3 |
| deep | complex | 6-8 | 8-10 | 6-8 | 6 | 3-4 |
| housekeeping | (fixed) | — | 2 | 1 | 1 | 1 |

> Housekeeping sessions skip Discovery (tasks are predefined) and use fixed agent counts regardless of complexity.

The `agents-per-wave` Session Config value caps the maximum regardless of tier.

If project intelligence (learnings) suggests different sizing based on historical data, prefer the historical recommendation over the formula.

## Step 3.5: Task-to-Agent Distribution

For each role's wave, distribute its classified tasks across the allocated agent count from Step 3:

**Distribution algorithm:**
1. **Group by file affinity**: Tasks touching the same files or the same directory MUST go to the same agent (prevents parallel merge conflicts).
2. **One task per agent** (preferred): If task count ≤ agent count, assign one task per agent. Leave unused agent slots empty — do not invent tasks to fill them.
3. **Merge small tasks**: If task count > agent count, merge the smallest tasks (by file count) that share a directory. Never merge tasks that touch different top-level modules.
4. **Split large tasks**: If a single task touches 6+ files across 3+ directories, split it by **immediate parent directory** boundary into sub-tasks for separate agents. Each parent directory becomes a separate sub-task scope, even if all parents fall under a single top-level source directory. Each sub-agent gets a clear file-boundary scope with no overlap.
5. **File-scope deconfliction**: After assignment, verify that NO two agents in the same wave modify the same file. If overlap exists, apply this resolution:
  - If both tasks share >50% of their file scope → merge them into one agent
  - If the overlapping task is NOT on the critical path (no downstream dependencies) → move it to Impl-Polish
  - If both are on the critical path → merge into one agent and note in Risk Mitigation

**Constraint check:** If the final agent count for any wave exceeds `agents-per-wave` from `$CONFIG`, either merge more tasks or defer lower-priority tasks to Impl-Polish. Log any such adjustments in Risk Mitigation.

## Step 4: Agent Specification

> **Template Reference:** See `wave-template.md` in this skill directory for the agent specification format, isolation settings, and count tables.

For each wave, define agents using the template format in `wave-template.md`. Apply the agent count table based on session type, capped by `agents-per-wave` from Session Config.

If project intelligence (learnings) suggests different sizing based on historical data, prefer the historical recommendation over the formula.

## Step 5: Issue Updates

Before presenting the plan:

> **VCS Reference:** Use CLI commands per the "Common CLI Commands" section of the gitlab-ops skill.

1. Mark all selected issues as `status:in-progress` (use the issue update/edit command for the detected VCS platform)
2. Add a comment to each issue noting the session and planned wave (use the issue note/comment command for the detected VCS platform)

## Step 6: Present Plan for Approval

If a `/write-executable-plan` artifact exists at `docs/plans/<feature>.md` for any task in this session (see `skills/write-executable-plan/SKILL.md`), include its path in the agent prompts for those tasks and set the "Bite-sized plan" field in the Execution Config accordingly.

Present the plan in this format:

```
## Wave Plan (Session: [type], [N] waves, isolation: [worktree|none])

### Wave 1: Discovery ([N agents], parallel, read-only)
- Agent 1: [task] → [files] → [acceptance criteria] → `subagent_type: Explore`
...
- File scope overlap: none (read-only wave)

### Wave 2: Impl-Core ([N agents], parallel, isolation: [worktree|none])
- Agent 1: [task] → [files] → [acceptance criteria] → `subagent_type: [resolved agent]`
...
- File scope overlap: [none | list conflicting files and which agents]

### Wave 3: Impl-Polish ([N agents], parallel, isolation: [worktree|none])
...
- File scope overlap: [none | list]

### Wave 4: Quality ([N agents], parallel, isolation: [worktree|none])
...

### Wave 5: Finalization ([N agents])
...

### Agent Registry
- [list which agents were discovered and how they map to tasks]
- Example: "database-architect (project) → DB tasks, session-orchestrator:code-implementer (plugin) → API tasks"

### Inter-Wave Checkpoints
- After Discovery: Validate discoveries, adjust Impl-Core scope if needed
- After Impl-Core: Incremental quality checks per quality-gates. **If `pencil` configured: design review.**
- After Impl-Polish: Incremental quality checks + integration verification. **If `pencil` configured: final design-code alignment check.**
- After Quality: Full Gate per quality-gates — if failing, create fix tasks for Finalization
- After Finalization: Final review before session-end

### Project Intelligence Applied
- [list of learnings that influenced this plan, with confidence scores]
- Or: "No project intelligence available yet"

### Risk Mitigation
- [identified risks and how each wave handles them]

### Execution Config
- Waves: [N] | Agents-per-wave cap: [M] | Isolation: [worktree|none|auto]
- Enforcement: [strict|warn|off] | Max turns: [N per session type]
- Persistence: [true|false] | Pencil: [path|none]
- Bite-sized plan: [path if exists, e.g. `docs/plans/2026-05-16-superpowers-cluster.md` | none]
- Parallel dispatch: All agents within each wave execute simultaneously via Agent() tool
- Total agents planned: [sum across all waves]

Ready to execute? Use /go to begin.
```

## Step 7: Handle Plan Changes

If the user requests changes:
- Re-scope affected waves
- Re-assign agents
- Update issue comments if scope changes
- Re-present the modified plan

## Sub-File Reference

| File | Purpose |
|------|---------|
| `wave-template.md` | Step 4 agent specification format and count tables |

## Anti-Patterns

- **DO NOT** create waves with circular dependencies — if wave N depends on wave N+1 output, the plan is broken
- **DO NOT** assign Discovery and Implementation roles to the same wave — read-only and write agents must be separated
- **DO NOT** create agent prompts that reference other agents' work — each agent must be fully self-contained
- **DO NOT** over-split simple tasks into many waves — a 2-file change doesn't need 5 waves
- **DO NOT** plan without reading the actual codebase — plans based on assumptions produce wasted waves

## Critical Rules

- **NEVER put independent tasks in the same agent** — each agent gets ONE focused task
- **ALWAYS order waves by dependency** — never schedule a task before its dependency completes
- **TypeScript check only in Discovery (baseline) and Quality/Finalization roles** — not during implementation roles
- **Build commands only in housekeeping sessions** — never during feature/deep work mid-session
- **Agent prompts must be self-contained** — include ALL context the agent needs (file paths, issue details, acceptance criteria). The agent starts with zero context.
- **If a task is too large for one agent**, split it across multiple agents with clear file-boundary separation
