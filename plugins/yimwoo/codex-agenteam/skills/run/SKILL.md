---
name: run
description: Run a full pipeline for a task. Orchestrates roles through stages (standalone or HOTL-integrated).
---

# AgenTeam Run

Orchestrate a full team pipeline for a task. This is the main entry point
for collaborative AI-assisted development. You are the lead; AgenTeam
dispatches your specialists.

## Process

### 1. Auto-Init Guard

Check for `.agenteam/config.yaml`, `.agenteam.team/config.yaml`, or legacy
`agenteam.yaml` in the project root. If all are missing:
- Create config dir: `mkdir -p .agenteam`
- Copy the template: `cp <plugin-dir>/templates/agenteam.yaml.template .agenteam/config.yaml`
- Set the team name to the project directory name
- Generate agents: `python3 <runtime>/agenteam_rt.py generate`
- Tell the user: "AgenTeam auto-initialized with default roles. Edit `.agenteam/config.yaml` to customize."
- Then continue with the requested run in the same turn. Auto-init is a prerequisite, not the end of the workflow.

### 2. Accept Task

Get the task description from the user. If not provided, ask:
"What task should the team work on?"

### 2b. Select Profile

If the project config defines pipeline profiles, select one before init:

1. Read `pipeline.profiles` from config (check if `pipeline` key is a dict
   with a `profiles` sub-key). If no profiles defined, skip this step.
2. If the user already specified `--profile <name>` in their request, use
   it directly and skip classification.
3. If profiles are defined:
   - Read each profile's `hints` list (advisory examples of task shape)
   - Select the best-fit profile using judgment over the task description
     and hints. Do not keyword-match — use hints as examples of the kind
     of task each profile is designed for.
   - Announce: "Using profile **quick** (one-line fix). Override with
     `--profile standard` if needed."
   - Do not pause for confirmation unless confidence is low or the profile
     materially shortens the pipeline (e.g., skipping 5 of 7 stages).
4. If uncertain which profile fits, default to `full` (all stages).
   Misclassification fails safe.
5. Pass `--profile <name>` to the init command in step 3.3:
   ```bash
   python3 <runtime>/agenteam_rt.py init --task "<task>" --profile <name>
   ```

### 2b2. Inject Run History

Before starting the pipeline, check for relevant context from past runs:

1. Call `python3 <runtime>/agenteam_rt.py history list --last 10`
2. If the result is empty (no past runs), skip this step.
3. Filter for relevance using LLM judgment:
   - Prefer runs with similar task descriptions
   - Prefer runs that touched similar artifact paths or stages
   - Prefer runs with lessons (verify failures, rework edges) — these
     are more informative than clean runs
   - Prefer recent runs over older ones
4. Select 0-3 most relevant summaries. If nothing is clearly relevant,
   inject nothing — nothing is better than noisy context.
5. Format as "Prior Run Context" and append to the task description
   for the first stage's dispatch:

```
## Prior Run Context

### Run: "add user authentication" (2026-03-30, standard profile)
- Status: completed (5/5 stages)
- Implement stage needed 3 verify attempts (test failures in auth middleware)
- Cross-stage rework: test → implement (auth session handling)
- Final verification: passed

### Run: "fix login redirect bug" (2026-03-29, quick profile)
- Status: completed (2/2 stages)
- Clean run, no rework
```

**Rules:**
- Conservative: inject 0-3 summaries, never more
- Selective: nothing is better than noisy/irrelevant context
- Non-blocking: if `history list` fails, skip silently and continue
- No accumulation: each run gets fresh context, not a growing blob

### 2c. Collaborative Discovery Mode

If multiple discovery-phase stages can run in parallel, switch to
collaborative discovery mode. This gives users faster results and a
structured handoff to implementation.

**Trigger — collaborative mode activates when either:**

1. **Profile-based**: The selected profile's front stages all have roles
   with `parallel_safe: true` and disjoint `write_scope` patterns.
2. **Intent-based**: The user explicitly mentions multiple discovery
   roles: "@architect @pm @researcher build X"

When not triggered (0 or 1 qualifying stages, or user didn't request
multi-role work), skip this section entirely — the run skill behaves
as normal serial execution.

**Detection logic:**

1. Look at the first N stages in the effective pipeline. For each stage,
   check its roles via `agenteam-rt roles show <role>`.
2. A stage qualifies for the discovery batch if ALL its roles have
   `parallel_safe: true`.
3. Additionally, ALL roles across ALL qualifying stages must have
   disjoint `write_scope` patterns (no scope string appears in more
   than one role's write_scope list).
4. The first stage whose roles include a non-`parallel_safe` writer
   (e.g., dev with `src/**`) marks the start of the "execution" phase.
5. If 0 or 1 stages qualify, fall back to normal serial execution.

**Note:** The built-in discovery roles (researcher, pm, architect) are
all `can_write: true` with `parallel_safe: true` and disjoint scopes
(`docs/research/**`, `docs/strategies/**`, `docs/designs/**`). The
parallelism basis is disjoint scopes, not read-only status.

**When collaborative mode is active, the following phases apply:**

#### Phase 1: Parallel Discovery Dispatch

**Isolation mode constraints:**

| Isolation Mode | Behavior |
|---------------|----------|
| `none` (scoped parallel) | Dispatch all discovery-batch roles as parallel subagents |
| `branch` | Serial fallback — dispatch discovery stages one at a time |
| `worktree` | Serial fallback — dispatch discovery stages one at a time |

In `isolation: none` mode:
- Collect all roles across discovery-batch stages
- Verify all have `parallel_safe: true` and disjoint `write_scope`
- Dispatch all as parallel subagents (single group)
- If scope overlap detected: fall back to serial

In `branch` or `worktree` mode:
- Dispatch each discovery stage serially (existing behavior)
- The convergence summary and handoff gate still apply after all
  complete — the only difference is discovery takes longer

For each discovery stage:
- Transition: `pending → dispatched`
- After actual launch: emit `stage_dispatched` event
- Check HOTL skill eligibility before each dispatch (same as step c0)
- Each role writes to its standard artifact path:
  - Researcher → `docs/research/<date>-<topic>.md`
  - PM → `docs/strategies/<date>-<topic>.md`
  - Architect → `docs/designs/<date>-<topic>.md`

Wait for all discovery roles to complete.

**Dual-use design doc format (Architect):**

The architect's design artifact should include a HOTL-friendly contract
block at the end — human-readable narrative first, execution contracts
second:

```
# Design: <Feature Name>

## Overview
[human-readable design narrative]

## Proposed Approach
[architecture, components, data flow]

## Interfaces / File Targets
[specific files/modules to create or modify]

## Risks
[what could go wrong, migration concerns]

---

## Execution Contracts

### Intent
- objective: [one sentence]
- constraints: [what must not change]
- success_criteria: [how we know it's done]

### Verification
- [test command or check]

### Handoff to Dev
- [ordered list of implementation steps]
- [estimated scope per step]
```

This is HOTL-compatible by shape — HOTL can consume the contracts if
present, dev can plan from them without HOTL.

#### Phase 2: Convergence Summary

After all discovery roles complete, render an inline summary:

```
Discovery complete (3 specialists, ~45s):

Researcher → docs/research/2026-03-30-auth-analysis.md
  - OAuth2 + PKCE is industry standard for this use case
  - Competitor X shipped passkey support last month

Architect → docs/designs/2026-03-30-auth-design.md
  - Proposes middleware pattern in src/auth/
  - Flags: session storage needs migration

PM → docs/strategies/2026-03-30-auth-strategy.md
  - Priority 1: OAuth2 basic flow (2-3 days)
  - Priority 2: Passkey support (stretch goal)

Recommendation: Ready for dev handoff. Review architect artifact
first — migration risk flagged.

Approve handoff to Dev? (yes / review artifacts first / stop)
```

**Format rules:**
- One line per role with artifact path
- 2-4 bullets max per role (outcome-shaped, not raw telemetry)
- One short controller recommendation line
- Then the gate prompt
- No cross-role synthesis — if roles disagree, it shows in their
  individual bullets

**Partial failure:** If one discovery role fails while others succeed,
include successful roles' outputs normally and show the failed role
with an error note: "Researcher: unavailable — [error reason]". Still
present the handoff gate — user decides whether to proceed.

**State transitions at convergence:**
- For each discovery stage: `dispatched → passed`
- If stage has human gate: `passed → gated`
- No `stage_completed` events yet — stages stay in `gated` or `passed`
  until the handoff gate is resolved

#### Phase 3: Handoff Gate

Pause before the first writing stage. Present options:
- **yes** → continue to execution phase
- **review artifacts first** → user reads the full docs, then returns
- **stop** → emit `run_finished` with `status: stopped`

On approval:
- For each discovery stage: transition to `completed`
- Emit `stage_completed` with `result: passed` for each
- Record gate for each stage that had a human gate
- Continue to the first execution stage

On rejection (stop):
- `gated → rejected` for gated stages
- Emit `stage_completed` with `result: failed, reason: handoff rejected`
- Emit `run_finished` with `status: stopped`

**Headless policy (CI=true or no TTY):**
- Auto-approve the handoff gate
- Log the convergence summary to stderr
- Continue to execution immediately

#### Phase 4: Serial Execution with Per-Role Visibility

After handoff approval, continue through remaining stages (implement →
test → review) using the normal serial pipeline flow from step 6.

The addition is **per-role announcements** at each stage:

Start: `Dev is implementing...`
Complete: `Dev completed → added OAuth middleware in src/auth/, login page updated`

Start: `Qa is testing...`
Complete: `Qa completed → 8 tests added (auth flow, session handling), all passing`

Start: `Reviewer is reviewing...`
Complete: `Reviewer completed → PASS, no blocking findings`

**Announcement rules:**
- Outcome-shaped: primary is what changed and whether it passed
- Secondary (if helpful): file counts, test counts
- Never: raw diffs, full test output, or telemetry dumps

These announcements also apply in normal (non-collaborative) serial
mode — per-role visibility is always useful.

---

### 3. Branch Isolation

Before initializing the run, set up branch isolation. This applies to
`standalone` and `dispatch-only` pipeline modes. If `pipeline: hotl`,
skip this step (HOTL owns git lifecycle for pipeline runs).

1. **Preflight:**
   ```bash
   bash <plugin-dir>/scripts/git-isolate.sh preflight
   ```
   - If `not-a-git-repo`: skip isolation
   - If `dirty-worktree` and mode is serial or worktree: **block.** Tell user
     to stash or commit first.
   - If `detached-head`: **block.** Tell user to checkout a branch first.

2. **Capture current branch** (before any git mutation):
   ```bash
   RETURN_BRANCH=$(git rev-parse --abbrev-ref HEAD)
   ```
   Store this for the entire run. Return to it after the final stage.

3. **Initialize the run first** (to get run_id):
   ```bash
   python3 <runtime>/agenteam_rt.py init --task "<task description>" [--profile <name>]
   ```
   Include `--profile` if one was selected in step 2b. Capture the
   `run_id` from the output.

4. **Get branch plan:**
   ```bash
   python3 <runtime>/agenteam_rt.py branch-plan --task "<task>" --run-id "<run_id>"
   ```

5. **Execute the plan:**
   - If `action: create-branch`:
     `bash <plugin-dir>/scripts/git-isolate.sh create-branch <branch>`
   - If `action: create-worktree`:
     `bash <plugin-dir>/scripts/git-isolate.sh create-worktree <path> <branch>`
   - If `action: use-current`: show warning, continue.
   - If `action: none` (hotl-deferred): skip.

6. All pipeline stages run on the created branch/worktree.

7. **After the final stage completes (or on abort):**
   - If `action` was `create-branch`:
     `bash <plugin-dir>/scripts/git-isolate.sh return $RETURN_BRANCH`
     Tell user: "Pipeline work is on branch `<branch>`. Merge or create a PR."
   - If `action` was `create-worktree`:
     `bash <plugin-dir>/scripts/git-isolate.sh cleanup-worktree <path>`
     Tell user: "Pipeline work is on branch `<branch>`."

### 4. Initialize Run

(Run was already initialized in step 3.3 above to obtain the run_id for
branch naming. Capture the run state from that output.)

Capture the run state (run_id, pipeline_mode, stages).

Creating the run state is bookkeeping only. Do not stop after printing
the run ID or stage list. Once you have the run state, continue
immediately into stage dispatch unless blocked by a human gate, an error,
or an explicit user stop request.

**Pipeline start banner (always show):**

After capturing the run state, announce:

```
Pipeline started: "<task description>"
Profile: <profile name or "full"> | Stages: <comma-separated stage names>
```

This gives the user immediate confirmation of what's about to happen.

### 5. Determine Pipeline Mode

Read `pipeline_mode` from the run state:

- **standalone** -> Run the built-in pipeline (step 4)
- **hotl** -> Run the HOTL wrapper pipeline (step 5)
- **dispatch-only** -> Tell the user: "Pipeline is dispatch-only. Use
  `$ateam:assign <role> <task>` to assign tasks to specific roles."
- **auto** -> Check HOTL availability. If available, ask the user:
  "HOTL detected. Run with HOTL integration? (yes/no)". If yes, use HOTL
  mode. If no, use standalone mode.

### 6. Standalone Pipeline

Iterate through each stage from the run state's `stages` in order. Do not
hardcode a shortened list. The default standalone pipeline is:

`research -> strategy -> design -> plan -> implement -> test -> review`

If the project config defines a different stage list, follow the config.

```
For each stage in the ordered stage list:

  a0. Capture stage baseline:
      python3 <runtime>/agenteam_rt.py stage-baseline --run-id <run_id> \
        --stage <stage> --action capture

  a1. Check if stage should be skipped (docs-only pre-dispatch skip):

     After a writing stage completes and before dispatching the next
     stage, check whether the changes warrant the upcoming stage:

     1. Get changed files since baseline:
        ```bash
        git diff --name-only <baseline>
        ```
     2. Classify: **docs-only** if ALL files match `docs/**`, `*.md`,
        `README*`, `CHANGELOG*`, `LICENSE*`, `.gitignore`.
        Otherwise: **code-or-config**.
     3. If next stage is `test` AND change set is docs-only:
        - Transition: `pending → skipped`
          ```bash
          python3 <runtime>/agenteam_rt.py transition --run-id <run_id> \
            --stage <stage> --to skipped
          python3 <runtime>/agenteam_rt.py set-stage-field --run-id <run_id> \
            --stage <stage> --field skip_reason --value "docs_only_change"
          python3 <runtime>/agenteam_rt.py set-stage-field --run-id <run_id> \
            --stage <stage> --field skipped_at --value "<ISO timestamp>"
          python3 <runtime>/agenteam_rt.py event append --run-id <run_id> \
            --type stage_completed --stage <stage> \
            --data '{"result": "skipped", "reason": "docs_only_change"}'
          ```
        - Announce: "⊘ Skipping test stage (docs-only change, no tests needed)"
        - Continue to next stage (review) or completion
     4. Otherwise: dispatch normally (continue to step a below)

     **Rules:**
     - Never skip `implement` or `review` stages
     - Never skip in collaborative discovery mode
     - Only skip `test` stage, only for docs-only changes
     - Config files (*.yaml, *.toml, *.json) are NOT docs-only

  a. Get dispatch plan:
     python3 <runtime>/agenteam_rt.py dispatch <stage> \
       --task "<task>" --run-id <run_id>

  b. Read the dispatch plan (JSON). Two formats:

     **Flat dispatch (isolation: branch or worktree):**
     - dispatch: list of roles to launch serially
     - blocked: roles waiting for write lock
     - gate: human or auto

     **Grouped dispatch (isolation: none / scoped parallel):**
     - groups: list of parallel-safe writer groups
     - read_only: list of read-only roles
     - gate: human or auto

  b2. Transition stage to dispatched:
     ```bash
     python3 <runtime>/agenteam_rt.py transition --run-id <run_id> \
       --stage <stage> --to dispatched
     ```

  b3. Announce stage start to user:

     Format: "[N/total] Assigning @Role to <verb>..."

     Use the stage name to select the verb:
     | Stage     | Verb |
     |-----------|------|
     | research  | "investigate" |
     | strategy  | "define strategy" |
     | design    | "design the solution" |
     | plan      | "write the implementation plan" |
     | implement | "implement the design" |
     | test      | "write tests" |
     | review    | "review the implementation" |

     For custom stage names not in this table, use the stage name as the verb.

     Adjust numbering to the actual stage count (profiles may skip stages).
     Use the stage's assigned role name from the dispatch plan.

     If a human gate is upcoming at this stage, append:
     "(approval required after this stage)"

     Example: "[3/5] Assigning @Dev to implement the design..."

  c0. Check HOTL skill eligibility (before launching any subagent):

     For each role about to be launched:
     ```bash
     python3 <runtime>/agenteam_rt.py hotl-skills \
       --run-id <run_id> --stage <stage> --role <role>
     ```
     - For each entry in the `eligible[]` array: append the `inject`
       text to the subagent's task instructions.
     - If `hotl_available` is false or `eligible` is empty: no injection,
       launch with default role instructions.

  c0.5. Build a role-context block for each launched role:

     Gather the role's static contract:
     ```bash
     python3 <runtime>/agenteam_rt.py roles show <role>
     ```
     Use the returned `handoff_contract` to tell the role what it is expected
     to consume, produce, and who reads its output next.

     Gather the stage's dynamic verification context:
     ```bash
     python3 <runtime>/agenteam_rt.py verify-plan <stage> --run-id <run_id>
     ```
     If a verify command is present, append it to the role context block.
     This is especially important for QA so it writes tests the pipeline can
     actually discover and run.

     Resolve artifact paths for prior-stage artifact discovery:
     ```bash
     python3 <runtime>/agenteam_rt.py artifact-paths
     ```
     Use the returned `paths` map to scan for prior-stage artifacts.
     This auto-detects standalone vs HOTL mode:
     - Standalone: architect → `docs/designs/`, pm → `docs/strategies/`
     - HOTL: architect → `docs/plans/`, dev plans → `./`

     Do NOT hardcode directory paths — always use the runtime-resolved
     paths so the context block is correct in both modes.

     Include the most relevant prior-stage artifacts or summaries already
     collected in step d2. Keep this block short and specific.

  c. Launch agents:

     **If plan has flat "dispatch" key (serial mode):**
     - For each role in dispatch list:
       - If mode is "read": launch as Codex subagent (can run in parallel
         with other readers)
       - If mode is "write": launch as Codex subagent (serial by default)

     **If plan has "groups" key (scoped parallel mode):**
     - Capture baseline: BASELINE=$(git rev-parse HEAD)
     - Launch read_only roles as parallel subagents (alongside any group)
     - For each group in order:
       1. Launch all roles in the group as parallel subagents
          Instruct agents: "Write your changes but do NOT run git add or
          git commit. The controller handles commits."
       2. Wait for all agents in the group to complete
       3. Serialized commit capture (controller does this, NOT agents):
          For each writing role in the group:
            - git add <files matching role's write_scope>
            - git commit -m "[ateam:<role>] <stage>: <summary>" (if staged files exist)
       4. Check for unclaimed files: git status --porcelain
          If any remain -> containment violation
       5. Run scope audit:
          python3 <runtime>/agenteam_rt.py scope-audit \
            --run-id <run_id> --stage <stage> --baseline $BASELINE
       6. If audit fails:
          - Save the complete diff as
            `.agenteam/runs/<run_id>/<stage>/scope-violation.patch` before
            taking any recovery action.
          - Log: "Scope containment violation. Preserved evidence and stopped
            the stage; no checkout content was reset."
          - Do not modify or discard the dirty checkout. A serial replay must
            start in a new clean branch/worktree from `$BASELINE`.
          - Ask before creating that replay because it may duplicate
            non-idempotent role work. Break out of the group loop.
     - The agent file is at the path in the dispatch plan (e.g.,
       .codex/agents/architect.toml)
     - Pass the task description and any outputs from previous stages
       as context to the agent
     - Append the role-context block from step c0.5 to the task prompt so
       static role instructions are paired with run-specific context
     - You must launch actual Codex subagents. Do not keep the work in the
       lead agent and do not simulate what a role "would" say.

  d. Emit stage_dispatched event and progress snapshot:
     ```bash
     python3 <runtime>/agenteam_rt.py event append --run-id <run_id> \
       --type stage_dispatched --stage <stage> \
       --data '{"roles": ["<role1>", ...], "isolation": "<mode>"}'
     python3 <runtime>/agenteam_rt.py status <run_id> --progress
     ```
     Display the progress snapshot to the user so they can see
     pipeline progress during execution.

     **Progress emission rule:** After every stage transition (dispatch,
     verify result, gate decision, completion, skip), emit the progress
     snapshot via `status --progress`. This gives users in-thread
     visibility into pipeline state without requiring a separate
     terminal or polling loop.

  d2. Collect outputs:
     - Gather each role's output
     - Store as context for subsequent stages

  d3. Announce stage completion to user:

     On success:
       "@Role completed <stage> -- <one-line outcome summary>. <forward reference>"

     Examples:
       "@Researcher completed research -- report on auth patterns written to docs/research/. @Pm strategizes next."
       "@Architect completed design -- OAuth2+PKCE recommended, 3 approaches documented. @Dev implements next."
       "@Dev completed implement -- added 4 files in src/auth/, 230 lines. @Qa tests next."
       "@Qa completed test -- 12 tests added, all passing. @Reviewer reviews next."
       "@Reviewer completed review -- PASS, no blocking findings."

     On failure:
       "@Role failed at <stage> -- <one-line failure reason>"

     Rules:
     - One line per stage, outcome-shaped
     - Include artifact paths or counts when available
     - Include forward reference to next stage's role (except for the final stage)
     - Never dump raw output, diffs, or full test logs

  e. Verify stage (if configured):
     - Get verify plan:
       python3 <runtime>/agenteam_rt.py verify-plan <stage> --run-id <run_id>
     - If verify is null: skip to gate check (see transition note below).
     - Transition to verifying:
       python3 <runtime>/agenteam_rt.py transition --run-id <run_id> \
         --stage <stage> --to verifying
     - Execute verification in the isolated workspace:
       bash <plugin-dir>/scripts/verify-stage.sh run "<verify>" --cwd "<cwd>"
     - Record result:
       python3 <runtime>/agenteam_rt.py record-verify --run-id <run_id> \
         --stage <stage> --result pass|fail --output "<output>"
     - If passed:
       python3 <runtime>/agenteam_rt.py transition --run-id <run_id> \
         --stage <stage> --to passed
       Continue to gate check.
     - If failed:
       python3 <runtime>/agenteam_rt.py transition --run-id <run_id> \
         --stage <stage> --to failed
     - If failed and attempts < max_retries:
       Log "Verification failed (attempt N/max). Re-dispatching..."
       Check verify-plan for rework_to:
         * If rework_to is set (cross-stage repair):
           Dispatch rework_roles as REPAIR (no verify/gate on repair action).
           Record: record-verify --rework-stage <rework_to>
           Re-run THIS stage's verify (not the rework stage's).
         * If rework_to is not set (same-stage retry):
           Determine repair role(s):
             - Single-role stage: re-dispatch that role
             - Multi-role stage: match failing files to write_scope
             - All-read-only stage: fail-fast (no repair possible)
           Before re-dispatching, re-run hotl-skills for each repair role:
           ```
           python3 <runtime>/agenteam_rt.py hotl-skills \
             --run-id <run_id> --stage <stage> --role <repair_role>
           ```
           The stage status is now "failed" or "rework", so
           systematic-debugging becomes eligible. Append any eligible
           inject text to the repair subagent's instructions.
           Re-dispatch repair role(s) with failure output as context
       Go back to verify
     - If failed and attempts >= max_retries (or no legal repair role):
       Log "Verification failed after N attempts."
       Offer non-destructive recovery:
         result = agenteam_rt.py stage-baseline --run-id <run_id> \
           --stage <stage> --action rollback
         If result.allowed:
           Show: git diff --stat <baseline>..HEAD
           Save the current diff to
           `.agenteam/runs/<run_id>/<stage>/failed-attempt.patch`.
           Ask: "Create a clean recovery branch/worktree from the baseline?"
           Never discard the current checkout automatically. Recovery runs in
           the new isolated workspace, and the preserved patch remains reviewable.
         If not result.allowed (isolation:none):
           Log: "Rollback not available in scoped parallel mode."
       Show failure output to user. Do NOT advance.

  **Long-running harness invariant:** Treat runtime state as authoritative.
  Persist the active attempt, `thread_id`, last heartbeat, wall/idle budgets,
  retry count, and stop reason. Emit `status --progress` at least once per
  heartbeat interval. After controller interruption, invoke `$ateam:resume`;
  do not silently launch a replacement agent.

  f. Gate criteria check (if stage has criteria):
     result = agenteam_rt.py gate-eval --run-id <run_id> --stage <stage>
     If result.passed: continue to gate.
     If result.failed:
       Log: "Gate criteria failed: <failed_criteria>"
       Escalate to human: "Stage exceeded criteria. Approve anyway? (yes/no)"
       If approved:
         python3 <runtime>/agenteam_rt.py record-gate --run-id <run_id> \
           --stage <stage> --gate-type criteria_override \
           --result approved --criteria-failed "<list>" \
           --override-reason "<user's reason>"
         Continue to gate.
       If rejected: mark stage failed.

  g. Gate check and stage completion transitions:

     **Transition paths (all four cases from default pipeline):**
     - verify + gate (e.g., design): dispatched → verifying → passed → gated → completed
     - verify + no gate (e.g., implement): dispatched → verifying → passed → completed
     - no verify + gate (e.g., strategy, plan): dispatched → passed → gated → completed
     - no verify + no gate (e.g., research): dispatched → completed

     **If verify was null (no verify configured):**
     - If gate is "human" or "reviewer":
       python3 <runtime>/agenteam_rt.py transition --run-id <run_id> \
         --stage <stage> --to passed
     - If gate is "auto" or no gate:
       python3 <runtime>/agenteam_rt.py transition --run-id <run_id> \
         --stage <stage> --to completed
       (skip gate check, stage is done)

     **Gate evaluation (when gate is not "auto"):**
     - python3 <runtime>/agenteam_rt.py transition --run-id <run_id> \
         --stage <stage> --to gated
     - If gate is "human":
       Announce: "Waiting for your approval at the <stage> gate."
       Pause and show the user a summary of the
       stage output. Ask: "Approve this stage? (yes/no/details)"
     - If gate is "reviewer" or "qa": dispatch the gate agent as a
       SEPARATE subagent (never the stage actor). Parse verdict
       (PASS/BLOCK). Record via record-gate. If BLOCK, pause for human.
     - Record gate result:
       python3 <runtime>/agenteam_rt.py record-gate --run-id <run_id> \
         --stage <stage> --gate-type <type> --result approved|rejected

     **After gate approval:**
     - python3 <runtime>/agenteam_rt.py transition --run-id <run_id> \
         --stage <stage> --to completed

     **After gate rejection:**
     - python3 <runtime>/agenteam_rt.py transition --run-id <run_id> \
         --stage <stage> --to rejected

     **On re-dispatch (retry after failure or rejection):**
     - python3 <runtime>/agenteam_rt.py transition --run-id <run_id> \
         --stage <stage> --to dispatched

  f0. Emit stage_completed event (after verify passed + gate approved):
     ```bash
     python3 <runtime>/agenteam_rt.py event append --run-id <run_id> \
       --type stage_completed --stage <stage> \
       --data '{"result": "passed"}'
     ```
     On stage failure (verify exhausted, gate rejected, or no repair):
     ```bash
     python3 <runtime>/agenteam_rt.py event append --run-id <run_id> \
       --type stage_completed --stage <stage> \
       --data '{"result": "failed", "reason": "<failure reason>"}'
     ```

  f. Handoff:
     - Pass the collected outputs as context to the next stage
     - Design output feeds into plan stage
     - Plan output feeds into implement stage
     - Implement output feeds into test stage
     - All outputs feed into review stage
```

Do not mark the run complete after `implement`. Unless the user explicitly
asks to stop early, continue through `test` and `review`, and surface the
reviewer's findings before calling the pipeline done.

### 6b. Final Verification (after the last configured stage)

After all stages complete, run final verification:

```
1. Get final verify plan:
   python3 <runtime>/agenteam_rt.py final-verify-plan --run-id <run_id>

2. If policy is "unverified":
   Print warning: "No final verification commands configured or detected.
   AgenTeam cannot vouch for this run."
   Skip to completion.

3. Run each command in sequence:
   bash <plugin-dir>/scripts/verify-stage.sh run "<command>" --cwd "<cwd>"

4. If all pass: continue to completion.

5. If any fail and retries remain:
   Determine repair role(s) from failure context:
     * Failing test files (tests/**) -> dispatch qa
     * Failing source files (src/**) -> dispatch dev
     * Both -> dispatch dev + qa
     * Unclear -> dispatch dev as fallback
   Re-dispatch repair role(s) with failure output
   Re-run all final_verify commands

6. If still failing:
   block mode: mark run failed, keep branch open, print failure summary
   warn mode: print "TESTS FAILING" warning, complete but do not suggest merge
```

This is non-negotiable. Final verification is the mechanism that lets
AgenTeam vouch for its work. It runs AFTER the review stage, not before.

### 6c. Run Report (always, at completion or failure)

After final verification (or when pipeline stops due to failure):

```
1. Generate report:
   python3 <runtime>/agenteam_rt.py run-report --run-id <run_id>

2. Render the JSON as markdown and write to the report_path
   (typically .agenteam/reports/<run-id>.md)

3. Show report summary to user

4. Log: "Run report saved to <report_path>"
```

Reports are local diagnostics (gitignored). They are never auto-committed.

### 7. HOTL Wrapper Pipeline

When pipeline mode is `hotl`, AgenTeam acts as the outer orchestrator
and composes HOTL skills for each stage:

```
a. DESIGN STAGE:
   - Resolve roles: agenteam-rt dispatch design -> {architect}
   - Invoke HOTL brainstorming skill with architect's system instructions
     injected as context
   - HOTL drives the design conversation
   - Collect design output

b. PLAN STAGE:
   - Resolve roles: agenteam-rt dispatch plan -> {architect}
   - Invoke HOTL writing-plans skill
   - HOTL generates the workflow file
   - Gate: human approval of the plan

c. IMPLEMENT + TEST STAGE:
   - Resolve roles: agenteam-rt dispatch implement -> {dev}
   - Resolve roles: agenteam-rt dispatch test -> {qa}
   - Invoke HOTL loop-execution or subagent-execution
   - HOTL executes workflow steps
   - Implementer and qa agents are the workers
   - Write policy enforced: serial by default

d. REVIEW STAGE:
   - Resolve roles: agenteam-rt dispatch review -> {reviewer}
   - Invoke HOTL code-review skill with reviewer agent
   - Gate: human approval
```

**Key principle:** AgenTeam manages role selection and write policy
between phases. HOTL manages execution within each phase. AgenTeam
never modifies HOTL internals.

### 8. Completion

Only after the final configured stage completes:
- Emit run_finished event:
  ```bash
  python3 <runtime>/agenteam_rt.py event append --run-id <run_id> \
    --type run_finished --data '{"status": "completed"}'
  ```
- Announce pipeline result:
  On success: `Pipeline complete: <N>/<N> stages passed.`
  On failure: `Pipeline stopped at <stage>: <reason>. Completed <N>/<total> stages.`
- Show a summary of what each role produced
- Show the final state: `python3 <runtime>/agenteam_rt.py status`
- Suggest next steps (commit, create PR, etc.)
- Persist run history for future context:
  ```bash
  python3 <runtime>/agenteam_rt.py history append --run-id <run_id>
  ```
  This saves the run summary + lessons learned for injection into future
  runs. Only called on completed or failed runs — not stopped/abandoned.

On unrecoverable pipeline failure:
- Emit run_finished event:
  ```bash
  python3 <runtime>/agenteam_rt.py event append --run-id <run_id> \
    --type run_finished --data '{"status": "failed"}'
  ```
- Persist run history (failures have useful lessons too):
  ```bash
  python3 <runtime>/agenteam_rt.py history append --run-id <run_id>
  ```

## Error Handling

- If a stage fails, stop the pipeline and show the error
- If a role agent fails, report which role failed and at what stage
- If write policy blocks a role, show the block reason and wait
- If HOTL is configured but not available, fall back to standalone
  with a warning

## Runtime Path Resolution

Resolve the AgenTeam runtime:
1. If running from the plugin directory: `./runtime/agenteam_rt.py`
2. If installed as a Codex plugin: `<plugin-install-path>/runtime/agenteam_rt.py`
