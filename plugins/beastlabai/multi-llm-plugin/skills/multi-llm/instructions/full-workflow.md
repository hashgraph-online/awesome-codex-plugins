# Full Workflow Mode Instructions

Runs all modes in sequence for complete automation.

## Usage

```bash
/multi-llm:multi-llm --full <plan_path> [model1 model2 ...] [--quick] [--yes]
```

## Process

1. **Phase 1: Review Plan** (with specified models)
2. **Phase 2: Apply Suggestions** (apply validated suggestions to the plan)
3. **Phase 3: Generate Tasks** (automatic task generation)
3b. **Phase 3b: Review Tasks** (optional — review generated tasks with multiple LLMs)
3c. **Phase 3c: Apply Task Suggestions** (auto-apply validated task review findings to tasks)
4. **Phase 4: Implement** (automatic execution)
5. **Phase 5: Review Code** (automatic review)
6. **Phase 6: Apply Code Fixes** (auto-apply validated code-review findings to the code)

`--improve-plan` runs Phases 1–2 on its own, and `--improve-code` runs Phases 5–6.

## How Full Mode Works

Full mode is a **resumable state machine in Python** over the modes above, on the
same `state.json` every standalone invocation writes. This file is the narrative;
the sequencing is not re-implemented by a driving agent.

Three properties follow from that, and they are worth knowing before reading the
per-phase sections:

- **A phase counts as progress only when it recorded itself complete** (or
  skipped). A phase that returns 0 without recording anything — the ordinary case
  when it stopped at a `[…_PENDING]` marker for a host's own subagent tool to
  continue — stops the workflow with exit **3** (row 14), naming that phase's own
  follow-up command *and* the `--resume` re-invocation.
- **Every phase boundary is a resume point.** `--resume` continues from the first
  phase `state.json` does not record as completed or skipped; `--force` re-runs
  phases that are already recorded.
- **A skipped phase is recorded skipped**, never left pending, so `status` and
  rerun logic never show an optional phase as perpetually outstanding.

## Non-Interactive Mode (`--yes` / `--non-interactive`)

By default, full mode still stops to ask you a few questions (model selection, `needs-human-decision` items, whether to review tasks). Passing **`--yes`** (alias **`--non-interactive`**) makes the entire workflow run **fully unattended — zero rendered questions** — by applying these effects to every phase:

| Phase | Default (interactive) | With `--yes` |
|-------|----------------------|--------------|
| uv preflight (shim, once per invocation) | Prints `hosts/uv-missing.txt` and **exits 3** — never installs, never offers | Identical; `--yes` changes nothing (row 1) |
| Model selection (Phase 1 & 5) | Prompts if no models given | Never prompts — uses `--models` if given, else `--quick` if given, else `providers.yaml` `defaults.models`; **exit 3** if nothing resolves (row 2) |
| Partial fan-out results (Phase 1 & 5) | Asks partial / resume / rerun-all | Resumes the missing models once (`--force`), then reaggregates: `[PARTIAL_RESULTS: …]`, `state: "partial"`, exit 0. Zero results → exit 3 (row 3) |
| Consolidation (after Phase 1) | Asks "run consolidation?" | Auto-runs once on `[CONSOLIDATION_RECOMMENDED]` (row 4) |
| Phase 2 Apply Suggestions | Prompts on `needs-human-decision` + no-selection confirmation | Runs with `--agent-decide --no-confirm` (the judge agent decides every item; no confirmation) — rows 10/11 |
| Phase 3 Generate Tasks gate | Asks apply-first / skip / cancel | **Auto-runs the missing apply phase once, then re-checks** — satisfied, not bypassed. Still unmet → exit 3 (rows 5/6, D6a) |
| Phase 3b Review Tasks | Prompts "review the tasks?" | Runs review-tasks **automatically** (no prompt) — row 12 |
| Phase 3c Apply Task Suggestions | `--no-confirm` already | Adds `--agent-decide` (the judge agent decides every item) |
| Phase 4 unapplied task suggestions | Asks "apply them first?" | Skipped, and the phase is *recorded* skipped (row 7) |
| Phase 4 human tasks | Asks which strategy, then pauses per task | Strategy resolves to `skip-dependents`; the per-task pause is unreachable (rows 8/9) |
| Phase 6 Apply Code Fixes | Prompts on `needs-human-decision` + no-selection confirmation | Runs with `--agent-decide --no-confirm` |
| A phase **fails** | Asks retry / run-manually / cancel | **exit 3** naming the failed phase and its `--resume` re-invocation (row 14) |

`--yes` is the umbrella switch; the narrower flags (`--quick`, `--agent-decide`, `--no-confirm`) keep their individual meanings and can still be passed on their own. Throughout the steps below, **"if `--yes` was specified"** means apply the row above for that phase. If `--yes` is NOT set, follow the interactive behavior as written.

**`--yes` never implies `--skip-prerequisites`.** Consent to run unattended is not
consent to stale input: the prerequisite gates are *satisfied* (by auto-running
the missing apply phase) or they fail closed. `--skip-prerequisites` is a separate
flag the user types, and every use of it is recorded in `state.json`.

Two rows never appear in this workflow, and the table says so rather than
leaving it inferred: **row 13** (`review-tasks` against a plan with no task list)
is structurally unreachable here, because phase order guarantees tasks exist
before Phase 3b; and **row 15** (a decision flag that arrives empty or
unrecognized — `--models ""`, `--human-task <id>=`, an unknown
`--force-strategy`) is rejected at parse time with exit 3 before any phase starts,
so no phase ever sees a half-answered gate.

**Unattended is a flag, never a detected condition** (D6b). Nothing in this
workflow inspects whether it has a TTY, whether `CI` is set, or whether the host
passed `--print`: the same argv produces the same phases in a terminal and in a
pipe. `--interactive` is the only way to get a gate rendered, and `--yes`
together with `--interactive` is exit 3 at parse time — never a precedence rule.

---

## Loading a phase's core

Each phase below says "load the `<mode>` core". That means exactly one command —
the dispatcher serves the phase's instruction file with every skill-dir
placeholder already substituted, so nothing is left for you to resolve:

```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util instructions <mode>
```

`<mode>` is the phase's mode word (`review-plan`, `apply-suggestions`,
`review-tasks`, `apply-task-suggestions`, `implement`, `review-code`,
`apply-code-fixes`). Reading `instructions/<mode>.md` out of the skill directory
is the documented fallback, not the primary path: the served text is
pre-substituted and the file on disk is not.

---

## Step-by-Step Execution

### 1. Handle Model Selection (same as review-plan mode)

- If models provided in args: use those directly
- If `--yes` (or `--non-interactive`) was specified: **never prompt.** Resolve models without asking — use `--models` if given, else pass `--quick` if given, else pass no model flag at all (the orchestrator falls back to `providers.yaml` defaults). Skip the question below entirely.
- If NO models provided (and NOT `--yes`): **ask the user** to select models
  - Present available models from `providers.yaml` (multi-select)

### 2. Execute Phase 1: Review Plan

Load the `review-plan` core and execute it. **The core owns the launch** — its
"Run the orchestrator (DETACHED)" step runs the orchestrator detached, makes the
one non-waiting roster call and then polls — so there is no command to compose
here. Pass the models resolved in step 1 as `--models <selected>`, or `--quick`
instead of `--models` if `--quick` was given, to the command that step builds.

Phase 1 is done when that core's poll loop ends; then proceed to Phase 2.

### 2b. Conditional Consolidation (Between Phase 1 and Phase 2)

After Phase 1 completes (including any validation and reaggregation), check the orchestrator output for the `[CONSOLIDATION_RECOMMENDED]` marker.

**When present** — auto-run consolidation (NO user prompt in full workflow mode):

1. Run the consolidation orchestrator:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" review-plan --plan-file "$PLAN_PATH" --consolidate
   ```

2. Handle subagent batches using the same Strategy A/B logic from review-plan instructions:
   - `[CONSOLIDATION_PENDING]`: single batch — spawn one subagent
   - `[CONSOLIDATION_BATCHES_PENDING]`: multiple batches — Strategy A (≤ 4: parallel direct) or Strategy B (> 4: wave-based spawning in waves of 4, last wave absorbs remainder)
   - Load `consolidation_tasks.json` from `{plan}/review-plan/`
   - Every task in that file already carries a complete `prompt` (the filled
     consolidation template plus that batch's group records), so there is no
     template to open and no prompt to assemble, and its `prompt_path` file
     holds the same bytes: hand the subagent that file to read in full, or
     `task.prompt` when the task has no `prompt_path` or the file is absent
   - Before step 3, confirm every task's `output_path` exists and is not empty,
     and re-dispatch any batch whose file is missing. Do not end your turn with a
     batch still outstanding: **you** write these files, and a host that runs one
     headless turn has no second turn in which to write them

3. Run reaggregation:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" review-plan --plan-file "$PLAN_PATH" --reaggregate-consolidation
   ```

4. Present consolidated report paths to user:
   - `{plan}/review-plan/consolidated.json`
   - `{plan}/review-plan/consolidated-report.md`
   - `{plan}/review-plan/consolidated-report.html`

**When absent** — skip consolidation silently and proceed directly to Phase 2.

### 3. Execute Phase 2: Apply Suggestions

Load the `apply-suggestions` core and execute it.

```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" apply-suggestions --plan-file "$PLAN_PATH"
```

If `--yes` (or `--non-interactive`) was specified, append `--agent-decide --no-confirm` so the phase runs fully unattended (the judge agent decides every `needs-human-decision` item, salvaging partially-valid ones, and the no-selection confirmation is skipped):
```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" apply-suggestions --plan-file "$PLAN_PATH" --agent-decide --no-confirm
```

This phase applies validated suggestions sequentially:
- Load validation results from Phase 1
- Filter to valid suggestions (HIGH/MEDIUM importance)
- Apply each suggestion one at a time by spawning subagents
- Handle needs-human-decision items by asking the user (or, under `--yes`, via the judged/deferred path — rows 10/11: `--yes` sets `--agent-decide` itself, and the no-selection confirmation is bypassed, so no item and no missing selection file can block)
- Generate applied suggestions report

Wait for completion, then proceed to Phase 3.

### 4. Execute Phase 3: Generate Tasks

Phase 3 is the `generate-tasks` mode, run in-process — the same code path
`--generate-tasks` takes standalone, so there is one implementation and one prompt
(see `instructions/generate-tasks.md`). The inlined Task prompt this section used to
carry is gone: the prompt is materialized in Python, the reply is a document the
invoker persists, and the temp-file channel it needed no longer exists.

**Context isolation still holds, and for a better reason than before.** The phase's
extensive repository exploration happens inside a *subagent* whose entire input is
the materialized prompt, so the workflow's own context never sees it — on a host
with a native subagent tool because the host spawns it, and under
`--exec-subagents` because the executor spawns a provider CLI.

**Note**: In full workflow mode, Phase 2 already handled suggestions, so the
generate-tasks prerequisite (Step 0 of generate-tasks) is *satisfied* rather than
skipped — which is why rows 5/6 never render here. If Phase 2 did not run or left
the gate unmet, `--yes` auto-runs the missing apply phase **once** and re-checks; a
still-unmet re-check stops the workflow with exit 3 rather than generating tasks
from unapplied review output. The subagent has no user channel at all, so no
interactive prompt is ever included in its instructions.

**Verification is part of the phase, not of this narrative.** Success means the plan
carries a fresh `<!-- TASKS_FILE: … -->` marker, the rendered tasks file exists and
parses, and its task count matches the validated document — checked in Python, from
the artifacts, under either invoker. Anything else restores the plan and stops.

**Error handling** (D6 row 14): a failed generation stops the workflow with exit
**3**, naming the failed phase and the re-invocation that continues from it —
`<dispatcher> full <plan> --yes --resume`. `--full` never proceeds past a failed
generation: implementing against a plan with no tasks is the error `--implement`'s
auto-detection already reports. There is no "retry, or run generate-tasks in the
main context, or cancel" prompt any more — the middle option was never anything but
"do it by hand in your own session", and silently switching strategy is how a headless
run ends up with a half-populated plan nobody reviewed. Retry *is* the same
re-invocation; cancelling is not re-invoking.

Then Phase 3b follows.

### 4b. Optional Phase 3b: Review Tasks

After task generation completes successfully, determine whether to run the review-tasks phase.

**`--yes` / `--non-interactive` mode** (D6 row 12): Run `review-tasks` **automatically without prompting**, using the same models resolved in Phase 1 (or `--quick` / `providers.yaml` defaults). Load the `review-tasks` core and execute it; as in Phase 1 the core owns the launch, the roster call and the poll loop, and the resolved models go to the command its "Run the Orchestrator (DETACHED)" step builds. Phase 3b is done when that loop ends; then proceed to Phase 3c. (Do NOT skip and do NOT prompt.)

**There is no TTY-sniffing branch, and there is no question.** "Not asked" is
decided by the shim's baked `--yes` plus the user-typed `--review-tasks` opt-in —
never by `isatty()`, `CI` or a `--print` flag (D6b). Row 12 has exactly two
endings, both resolved in Python:

- `--yes` **or** `--review-tasks` → the phase runs, with the models resolved in
  Phase 1 (`instructions/review-tasks.md` is the narrative for what it does).
- neither → the phase is **recorded skipped** through the same `--skip --reason`
  state path (`reason: not requested (--review-tasks not passed)`), so `status`
  output and rerun logic never show review-tasks as perpetually pending.

Then Phase 3c follows.

### 4c. Execute Phase 3c: Apply Task Suggestions

After Phase 3b completes (or is skipped), determine whether to run the apply-task-suggestions phase. This phase applies validated findings from the task review to update the tasks file automatically.

**Three-case conditional logic**, decided in Python from the *existing*
prerequisite counter rather than re-derived per host:

**(a) Review-tasks was skipped**: apply-task-suggestions is recorded skipped too
(`reason: Skipped: review-tasks was not executed`), and Phase 4 follows.

**(b) Review-tasks ran but produced zero findings**: the counter over
`{plan}/review-tasks/grouped.json` reports nothing actionable, so the phase is
recorded skipped (`reason: Skipped: skipped (no findings)`), and Phase 4 follows.

**(c) Review-tasks produced findings**: the phase runs —

```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" apply-task-suggestions --plan-file "$PLAN_PATH" --no-confirm
```

If `--yes` (or `--non-interactive`) was specified, also append `--agent-decide` so any `needs-human-decision` task suggestions are decided by the judge agent rather than prompted:
```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" apply-task-suggestions --plan-file "$PLAN_PATH" --no-confirm --agent-decide
```

This phase:
- Loads validated task suggestions from the review-tasks phase
- Filters to valid suggestions (HIGH/MEDIUM importance)
- Applies each suggestion to the tasks file by spawning subagents
- Generates an applied task suggestions report (`{prefix}_applied_task_suggestions.md`)
- Produces `orchestrator_output.json` in `{plan}/apply-task-suggestions/`

Load the `apply-task-suggestions` core and follow it to process batches, generate the summary report, and mark the phase completed. Then proceed to Phase 4.

### 5. Execute Phase 4: Implement

Load the `implement` core and execute it.

```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" implement --plan-file "$PLAN_PATH"
```

Wait for completion, then proceed to Phase 5.

### 6. Execute Phase 5: Review Code

Load the `review-code` core and execute it. **The core owns the launch** — its
"Run the code review orchestrator (DETACHED)" step runs the orchestrator
detached, makes the one non-waiting roster call and then polls — so there is no
command to compose here. Pass `--models <selected>`, or `--quick` instead of
`--models` if `--quick` was given, to the command that step builds.

Use the **same models resolved in Phase 1** (Critical Rule 4). Under `--yes`, resolve models the same non-interactive way as Phase 1 (never prompt). This phase only *reviews* the code and produces `{plan}/code-review/` outputs — the fixes are applied in Phase 6.

Phase 5 is done when that core's poll loop ends; then proceed to Phase 6.

### 6b. Execute Phase 6: Apply Code Fixes

Load the `apply-code-fixes` core and execute it. This phase mirrors Phase 2 (Apply Suggestions), but applies the validated findings from the code review (Phase 5) to the **code** rather than the plan.

**Conditional — skip if there is nothing to apply.** When
`{plan}/code-review/grouped.json` is missing or carries no findings, the phase is
recorded skipped (`reason: Skipped: code review produced zero actionable findings`)
through the same `--skip --reason` state path, and the report follows.

**Otherwise, run the apply-code-fixes orchestrator:**

```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" apply-code-fixes --plan-file "$PLAN_PATH"
```

If `--yes` (or `--non-interactive`) was specified, append `--agent-decide --no-confirm` so the phase runs fully unattended:
```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" apply-code-fixes --plan-file "$PLAN_PATH" --agent-decide --no-confirm
```

This phase:
- Loads validated code-review findings from Phase 5
- Filters to valid findings (HIGH/MEDIUM importance)
- Applies each fix to the code one at a time by spawning subagents
- Handles `needs-human-decision` items by asking the user (or, under `--yes`, via the judged/deferred path — rows 10/11, no prompt and no `confirmation_needed` payload)
- Generates an applied code fixes report and overlays decisions onto `{plan}/code-review/report.html`

Follow the full apply-code-fixes instruction file to process batches, generate the summary report, and mark the phase completed. Wait for completion, then proceed to the report.

### 7. Report Combined Results

After all phases complete, provide a comprehensive summary. The reporting rules
in `references/summary-format.md` apply here too — every path comes from the
run's own output, `MULTI_LLM_RESULT.next` is copied verbatim, and the report ends
with the next step its `### Next Steps` rule gives, copied from
`user_next_step` and never composed:

```markdown
## Full Workflow Complete

**Plan**: /path/to/plan.md

### Phase 1: Review Plan
- Models used: [list]
- Suggestions found: N
- Valid suggestions: N
- Invalid (filtered): N

### Phase 2: Apply Suggestions
- Suggestions applied: N
- Human decisions made: N
- Suggestions skipped: N
- Applied suggestions report: {plan}/apply-suggestions/summary.md

### Phase 3: Generate Tasks
- Tasks generated: N
- Tasks file: {plan}_tasks.md

### Phase 3b: Review Tasks *(only if executed, omit if skipped)*
- Issues found: N
- Importance breakdown: HIGH: N, MEDIUM: N, LOW: N
- Report: {plan}/review-tasks/report.html

### Phase 3c: Apply Task Suggestions *(only if executed, omit if skipped)*
- Suggestions applied: N
- Suggestions skipped: N
- Applied task suggestions report: {prefix}_applied_task_suggestions.md
- Orchestrator output: {plan}/apply-task-suggestions/orchestrator_output.json

### Phase 4: Implement
- Tasks completed: N/N
- Files modified: [list]
- Implementation summary: {plan}_implementation_summary.md

### Phase 5: Review Code
- Issues found: N
- Importance breakdown: HIGH: N, MEDIUM: N, LOW: N
- Review report: {plan}/code-review/report.html

### Phase 6: Apply Code Fixes *(only if executed, omit if skipped)*
- Fixes applied: N
- Decided by the judge agent: N (A approved, V salvaged, S skipped) *(under `--yes`)*
- Fixes skipped: N
- Applied code fixes report: {plan}/apply-fixes/summary.md

### All Output Files
- [List all generated files with full paths]
- Include `{prefix}_applied_task_suggestions.md` and `{plan}/apply-task-suggestions/orchestrator_output.json` (if Phase 3c ran)

   Generate combined resource usage:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util metrics report \
     --state-file "$STATE_FILE" --all-phases
   ```
   Include the output (if non-empty) after "### All Output Files".

### Next Steps
- [Exactly what the `### Next Steps` rule in `references/summary-format.md`
  says: `user_next_step.command` in a fenced block, with any optional commands
  after it under "Optional, before that:", each optional command in its own
  fenced block; "Workflow complete." when
  `complete` is true, with each of its `manual_tasks` listed under it, then its
  `manual_tasks_note` (the `[MANUAL_TASK_NOTE]` line) verbatim and its
  `manual_tasks_command` alone in a fenced block (a command
  answer can carry them too: list them after its commands, without "Workflow
  complete.");
  nothing when there is no `user_next_step`, or one line
  quoting a failed lookup]
```

---

## Critical Rules for Full Mode

1. **Sequential Execution**: Each phase MUST complete before the next begins
2. **Error Handling** (D6 row 14): If a phase fails **without `--yes`**, report the error and ask the user whether to continue. **Under `--yes` a hard failure is a terminal condition, not a question**: stop with exit **3**, name the failed phase and print its `--resume` re-invocation. This is the one site where `--yes` used to fall back to "ask whether to continue", i.e. a guaranteed headless hang on exactly the path a headless run is most likely to take. `--resume` is how a human continues; no flag makes a hard failure proceed.
3. **State Preservation**: Each phase's state is preserved for the next phase
4. **Same Models**: Use the same model selection for both review-plan and review-code phases
5. **Apply Sequential**: In Phases 2, 3c, and 6, process items ONE AT A TIME to avoid conflicts
6. **`--yes` is all-or-nothing for prompts**: When `--yes` / `--non-interactive` is set, **no question may be asked anywhere, for any reason** — not for a workflow decision, not for a crash, not for a prerequisite gate. Every decision point has exactly one of three endings: a documented default that is applied *and recorded* (`[AUTO_RESOLVED] <site>: <decision>`), exit **3** with the re-invocation named, or a flag the user typed. "Ask in free text" is not a fourth ending. See the Non-Interactive Mode table above for the per-site resolution.

## Planned Features (Not Yet Implemented)

The following CLI options are planned but not yet available:

- `--task-timeout <seconds>`: Per-task timeout (default: 1200)
- `--continue-on-failure`: Continue with independent tasks after failure
- `--ignore-dependency <task-id>`: Skip dependency check for a task
- `--no-lsp`: Disable LSP-based file discovery
- `--cleanup-state`: Delete state files after completion

These features are documented in the implementation plan and will be added in future releases.
