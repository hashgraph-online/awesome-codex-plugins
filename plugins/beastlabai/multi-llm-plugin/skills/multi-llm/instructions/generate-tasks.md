# Generate Tasks Mode Instructions

Generates detailed implementation tasks from a high-level plan. A **task-generation
subagent** analyzes the plan *and the repository* and returns a structured task
document; the orchestrator validates it and writes it into the plan.

## Usage

```bash
/multi-llm:multi-llm --generate-tasks <plan_path>
```

## Process (the `generate-tasks` mode drives these steps)

The sequencing lives in Python — this section is the narrative, not a script a
driving agent re-implements.

1. **Check the prerequisite gate** — unapplied plan-review suggestions are never
   silently ignored (D6a rows 5/6; details under Step-by-Step Execution below).

2. **Materialize one `task_generation` task.** The prompt embeds the plan text,
   names exactly one path (the pinned repository root) and carries the
   task-authoring rules below verbatim. It is the one materialized kind whose
   context is the **repository**, so it is `context_mode: workspace-read` and
   requires a runner that can both read the workspace and run under the read-only
   profile — a runner with neither is refused *before dispatch* with exit 3, because
   a non-agentic runner does not fail on this prompt, it invents a task list from
   the plan's prose.

3. **Dispatch it, either way.** With `--exec-subagents` the executor runs it and
   persists the reply. On a host with its own subagent tool, run the task as a
   subagent — have it read the file at `task.prompt_path` (exactly the bytes of
   `task.prompt`, `task_generation.prompt.txt` in the phase dir) in full, through
   line `task.prompt_lines`, and follow it; pass `task.prompt` only when the task
   has no `prompt_path` or the file is absent — write the JSON it returns to the task's `output_path`
   (`task_generation_result.json` under the phase dir) and re-invoke the mode with
   `--reaggregate` — the one follow-up command the orchestrator prints. The
   subagent **only prints**; the invoker persists. There is no temp file, no
   agent-side file write and no second git-root resolution anywhere in this flow.

4. **Validation happens before anything touches the plan**: the document is checked
   against `schemas/generated_tasks.schema.json` plus the semantic rules
   (unique `T###` ids, `depends_on` naming only declared ids, acyclic, at least one
   dependency-free task). A failure is `schema_invalid` and nothing is written.
   With `--exec-subagents` the executor checks both before it persists the reply
   and re-asks the same runner **once** with the validator's errors; a second
   failure is exit 3. On the native path, `--reaggregate` only consumes the reply
   on disk and re-asks nothing: it exits 3 naming the errors. Re-ask the subagent
   once with them and write its reply over the file, then `--reaggregate` again —
   or re-invoke the mode without `--reaggregate`. A result file that fails
   validation is never resumed: a plain re-invoke archives it and dispatches the
   task again.

5. **The plan is updated in-process**, then the *outcome* is verified rather than
   the subagent's claim: a fresh `<!-- TASKS_FILE: … -->` marker, a rendered tasks
   file that exists and parses, and a task count matching the document. If any of
   those is missing, the plan and `state.json` are restored to their pre-run bytes
   and the run exits 3.

## Task JSON Schema

```json
{
  "plan_preamble": "3-5 sentences summarizing the overall goal, key architectural decisions, technology choices, and global conventions",
  "tasks": [
    {
      "id": "T001",
      "title": "Short title (5-10 words)",
      "description": "Detailed description covering: (1) What to implement, (2) How — approach, patterns/helpers to reuse, (3) Interface contracts — what this task produces/consumes for other tasks",
      "depends_on": [],
      "files_to_modify": ["path/to/file.ts"],
      "files_to_create": ["path/to/new-file.ts"],
      "acceptance_criteria": ["Criterion 1", "Criterion 2"],
      "estimated_complexity": "low|medium|high",
      "executor_role": "agent|human"
    }
  ]
}
```

`depends_on`, `files_to_create` and `files_to_modify` are always present — `[]`
when a task has none. A reply that leaves one of them out is completed with `[]`
before validation (on either invoker); a key present with the wrong type, or any
other missing field, is still `schema_invalid`.

### Plan Preamble

The `plan_preamble` field provides essential context for subagents implementing tasks. Include:
- **Overall goal/outcome** - What the plan aims to achieve
- **Key architectural decisions** - Major design choices affecting implementation
- **Technology/library choices** - Specific frameworks, tools, or dependencies to use
- **Global conventions** - Patterns or standards to follow across all tasks

Keep it concise: 3-5 sentences, approximately 200 tokens. This context is included in every task prompt.

**executor_role values:**
- `agent`: Default for all implementation tasks — any invoker may dispatch them
- `human`: Manual steps the user must perform (e.g., API key creation, external service config, manual testing). No invoker ever dispatches a `human` task; it routes to the human-task pause. Rendered in `tasks.md` as "**Type**: Manual (user action required)".

## Guidelines for Task Generation

These rules are the **prompt body** the `task_generation` subagent receives, not just documentation: they are rendered from `TASK_AUTHORING_RULES` in `utils/subagent_prompts.py` and inlined verbatim into `task.prompt`, so a runner that cannot open this file still gets them. Edit the constant, never this block — a test fails when the two diverge.

<!-- BEGIN GENERATED: task-authoring-rules — rendered from utils/subagent_prompts.py TASK_AUTHORING_RULES. Edit the constant, not this block. -->

**Task Granularity**
- Produce 5-15 discrete implementation tasks, each completable in 15-60 minutes
- The first task (T001) is setup/foundation and has NO dependencies
- Each task modifies 1-5 files maximum
- Complex features are broken into multiple tasks
- Tasks should be independently testable when possible
- Give a task `executor_role: human` when:
  - The plan explicitly states something must be done manually
  - The task requires access to external services/dashboards an agent cannot reach
  - The task requires physical or manual verification
- Human task descriptions include clear step-by-step instructions, since a person (not an agent) will read them
- Human task acceptance criteria describe how the user can verify completion

**Dependencies**
- Use explicit `depends_on` arrays referencing task ids
- Independent tasks can share the same dependencies (this enables parallel execution)
- Never create circular dependencies
- Tasks with no dependencies can run in parallel

**Codebase Exploration**
- Look for existing patterns to follow (search for similar features)
- Identify integration points with existing code
- Check for related tests that need updates
- Note any shared utilities or components to reuse

**Task Descriptions**

Each description covers three components in 2-5 sentences:

1. **What** to implement — the concrete deliverable
2. **How** — key implementation approach, patterns/functions to reuse, APIs to call
3. **Interface contracts** — if this task produces or consumes interfaces, types, files or data structures other tasks use, state them explicitly

*Weak:* "Add validation to the form component." — this says *what* at a surface level and nothing about *how* or which interfaces are involved, so the implementer must guess the approach, which helpers exist, and whether other tasks depend on its output.

*Strong:* "Add Zod schema validation to UserProfileForm using the existing `validateWithSchema()` helper from `lib/validation.ts`. The schema enforces email format, required fields and max-length constraints matching the DB column limits in `T001`'s migration. Export the `UserProfileSchema` type from this file — `T003` (API handler) imports it for request body validation." — this covers what, how, and the interface contract.

**Acceptance Criteria**

Acceptance criteria are **task-scoped, specific and verifiable**: each one describes an observable outcome checkable with a concrete test, command or inspection. Avoid "works correctly" or "handles errors properly".

**Test scope rule**: a criterion may run a **specific, narrowly-scoped test** (a single test file or test class) related to this task's changes, but must NOT include broad regression tests like "full test suite passes", "all tests pass" or "existing tests still pass". Full regression testing runs once after implementation; individual tasks verify only their own changes.

*Bad:* "Form validation works correctly" / "Errors are handled properly" / "Performance is acceptable" / "Full test suite passes" / "All existing tests still pass".

*Good:* "Submitting the form with an empty email field shows the error message 'Email is required' below the input" / "`validateWithSchema()` returns `{ valid: false, errors: [...] }` when any required field is missing" / "The exported `UserProfileSchema` type is importable from `lib/validation.ts` and matches the column types in the `user_profiles` table migration".

**File References**
- Use paths relative to the project root
- Clearly distinguish files to modify from files to create
- Only reference files that actually need changes
- A task that only checks something (a syntax gate, a smoke run) and must not change any file lists none. A task that may fix what it checks lists those files under `files_to_modify`: implement stops a task that changes a file it never declared

**Plan Preamble**

`plan_preamble` is 3-5 sentences (roughly 200 tokens) of shared context injected into every task prompt: the overall goal/outcome, key architectural decisions, technology/library choices and global conventions.

<!-- END GENERATED: task-authoring-rules -->

## Output Format

Tasks are stored in a **separate file in a phase subdirectory** to keep the plan lean. The plan gets a reference:

**Plan file** (`my-plan.md`):
```markdown
# My Plan

... plan content ...

## Implementation Tasks

See [my-plan/tasks/tasks.md](my-plan/tasks/tasks.md) for the detailed task breakdown.

<!-- TASKS_FILE: my-plan/tasks/tasks.md -->
```

**Tasks file** (`my-plan/tasks/tasks.md`):
```markdown
# Implementation Tasks for my-plan.md

*Generated: 2026-01-08 12:00:00*

**Parent Plan**: [my-plan.md](../my-plan.md)

---

## Implementation Tasks

### Task T001: Create base configuration
**Dependencies**: None
**Files to create**: src/config.ts
**Complexity**: low

Description of the task...

**Acceptance Criteria**:
- [ ] Criterion 1
- [ ] Criterion 2

---
```

This approach keeps the plan file small so LLMs don't bloat their context with task details when editing the plan. All generated files for a plan are centralized in the plan's subfolder.

## Auto-Detection in Implement Mode

When running `--implement`, the orchestrator checks if the plan has tasks:
- If task file reference exists (`<!-- TASKS_FILE: ... -->`): proceeds with implementation
- If embedded tasks exist (legacy `## Task N:` format): proceeds with implementation
- If no tasks found: prints error directing user to run `--generate-tasks` first

---

## Step-by-Step Execution

### 0. The Prerequisite Gate

The orchestrator's first step is the shared gate
(`check_workflow_prerequisites.ensure_prerequisites`, D6a) — unapplied suggestions
from plan review. Nothing is produced before it: no phase dir, no task file, no
`state.json` mutation.

**This gate is never auto-skipped, and `--yes` alone does not skip it** (D6a).
Tasks generated from a plan whose HIGH-importance review suggestions were never
applied silently poison every downstream phase, and a warning printed into a
headless log nobody reads *is* that failure mode. Nothing has been produced at
this point — no tasks in the plan file, no phase dir, no `state.json` mutation —
so there is no half-generated artifact to clean up.

- **Standalone**: the mode exits **3** with one message naming *both* fixes:

  ```
  [PREREQUISITE_UNMET] generate-tasks: 7 HIGH / 3 MEDIUM suggestions in
  /abs/plans/x/review-plan/validation.json have not been applied.
    1) Apply them first — <dispatcher> apply-suggestions /abs/plans/x.md --yes
       then re-run      — <dispatcher> generate-tasks /abs/plans/x.md --yes
    2) Proceed on unapplied review output (recorded) —
       <dispatcher> generate-tasks /abs/plans/x.md --yes --skip-prerequisites
  ```

  Both endings a question would have rendered are those two flags, so there is no
  third one to ask about: an unmet gate is exit 3 whether or not `--yes` is set.

- **With `--skip-prerequisites`**: loud but non-fatal. The check prints
  `[PREREQUISITE_SKIPPED] generate-tasks: <n> unapplied apply-suggestions
  suggestions (reason: explicit --skip-prerequisites)`, records the skip in
  `state.json` through the same `--skip --reason` path, and exits with this
  mode's normal code. This is the only path on which tasks may be built from
  unapplied review output, and it is always attributable afterwards (`status`,
  the implementation summary and any later review all see it).
- **Inside `--full` with `--yes`**: the workflow **auto-runs the missing apply
  phase once and re-checks** — the gate is satisfied, not bypassed. If the apply
  phase exits non-zero, or the re-check still reports the prerequisite unmet, the
  workflow stops there with exit **3**; the auto-run is attempted at most once
  per phase per run and never becomes a retry loop.

When the gate is met, task generation proceeds. A prerequisite that was met
*because an earlier phase recorded a skip* surfaces as one
`[PREREQUISITE_SKIPPED_UPSTREAM …]` line quoting the recorded reason; the run
proceeds, because consent was already given explicitly.

---

### 1. Materialize, dispatch, consume

The remaining steps are the orchestrator's, and they are described in Process
above. What a host with a native subagent tool contributes is exactly one thing:

- run the single task in
  `{plan}/generate-tasks/task_generation_tasks.json` as a subagent: hand it
  the file at the task's `prompt_path` to read in full and follow (never paste
  the prompt into the subagent call), or `task.prompt` when the task has no
  `prompt_path` or the file is absent,
- write the JSON object it prints to that task's `output_path`,
- re-invoke the mode with `--reaggregate`.

Do all three in one turn, and do not end that turn with any of them outstanding.
**You** write that file, not the subagent, and a host that runs one headless turn
has no second turn in which to write it — a reply that lands after the turn ends
leaves `output_path` absent and the phase with nothing on disk to reaggregate or
resume from. Confirm the file exists and is not empty before the `--reaggregate`
call; if it is missing, re-dispatch the task rather than reaggregating over an
absent result.

The subagent explores the repository from the one path the prompt names and prints
one JSON document. It writes no file, runs no command, and is never handed an
interactive prompt.

### 2. Reported on success

Report in the shape `references/summary-format.md` defines, carrying:

- Path of the rendered tasks file (`{plan}/tasks/tasks.md`) and the plan's fresh
  `<!-- TASKS_FILE: … -->` marker
- Number of tasks generated and their dependencies
- The next step exactly as that file's `### Next Steps` rule gives it: the
  `user_next_step` command, copied, never composed. The optional task review
  (`review-tasks`), when it is still pending, is listed after that command
  under "Optional, before that:", its command in its own fenced block.

---

## Example JSON Output

```json
{
  "plan_preamble": "Implement a new feature for user data management. Use the existing service layer pattern with TypeScript. All database queries should use Supabase client. Follow the existing error handling conventions in lib/server.",
  "tasks": [
    {
      "id": "T001",
      "title": "Create database schema for feature",
      "description": "Create the user_features table with columns for id (uuid), user_id (FK to auth.users), feature_data (jsonb), and timestamps. Use the existing migration pattern from supabase/schemas/profiles.sql as a template. This table is read by T002's service layer and must have an index on user_id for the list-by-user query.",
      "depends_on": [],
      "files_to_create": ["apps/web/supabase/schemas/feature.sql"],
      "files_to_modify": [],
      "acceptance_criteria": [
        "Schema validates with supabase db lint with zero errors",
        "All foreign keys reference existing tables with ON DELETE CASCADE",
        "Index exists on user_id column for the user_features table"
      ],
      "estimated_complexity": "medium",
      "executor_role": "agent"
    },
    {
      "id": "T002",
      "title": "Implement service layer for feature CRUD",
      "description": "Create getFeature, listFeatures, createFeature, updateFeature, and deleteFeature functions following the pattern in lib/server/profiles/service.ts. Use the Supabase client from lib/supabase.ts and the error wrapper from lib/server/errors.ts. Export the FeatureService type so T003 (API routes) can import and use it.",
      "depends_on": ["T001"],
      "files_to_create": ["apps/web/lib/server/feature/service.ts"],
      "files_to_modify": [],
      "acceptance_criteria": [
        "All five CRUD functions (get, list, create, update, delete) are exported",
        "Each function wraps Supabase calls with handleServiceError() from lib/server/errors.ts",
        "FeatureService type is exported and importable by T003"
      ],
      "estimated_complexity": "medium",
      "executor_role": "agent"
    }
  ]
}
```
