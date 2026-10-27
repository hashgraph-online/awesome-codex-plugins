---
name: auto-pilot
description: Intake-first autonomous project execution for Codex. Use when the user wants a short project request turned into a long-running build workflow with minimal interruptions, or explicitly mentions 오토파일럿/autopilot.
summary: Ask once, lock spec, save state, keep shipping.
metadata:
  priority: 8
  promptSignals:
    phrases:
      - "오토파일럿"
      - "autopilot"
      - "auto-pilot"
      - "24시간 계속"
      - "with ap"
      - "using ap"
    allOf:
      - [ap, build]
      - [build, ap]
      - [ap, make]
      - [make, ap]
      - [ap, create]
      - [create, ap]
      - [ap, app]
      - [app, ap]
      - [ap, 만들어줘]
      - [만들어줘, ap]
    anyOf:
      - "오토파일럿"
      - "autopilot"
      - "auto-pilot"
    minScore: 7
retrieval:
  aliases:
    - 오토파일럿
    - autopilot mode
    - auto-pilot mode
    - with ap
    - intake first execution
    - continuous project execution
  intents:
    - start an autopilot project
    - run intake and keep building
    - continue a project with minimal interruptions
  entities:
    - spec
    - progress
    - blockers
    - state
---

# Auto Pilot

Use this skill as the umbrella workflow for long-running project execution.
Treat it as the **manager** role for the whole system.

## Goal

Turn a short product request into a resumable execution loop that:

- gathers the minimum required inputs once
- locks a written spec and definition of done
- keeps implementing the next highest-priority work
- escalates only for true human-only blockers

## Operating Model

### If state does not exist yet

1. Route to the intake workflow first.
2. Ask only for high-impact decisions.
3. Infer safe defaults for the rest.
4. After intake, detect whether the selected auth or managed services require upfront integration env values.
5. If env values are already present, write:
   - `docs/spec.md`
   - `docs/design.md` for user-facing projects
   - `docs/progress.md`
   - `docs/next.md`
   - `autopilot/state.json`
   - `autopilot/blockers.json`
   - `autopilot/secrets-status.json`
6. If env values are still missing, treat the project as being in the normal `setup-secrets` phase and write:
   - `docs/next.md`
   - `autopilot/state.json`
   - `autopilot/blockers.json`
   - `autopilot/secrets-status.json`
   - request the consolidated env payload
7. Start implementation immediately only after the required env values are ready.

### If state already exists

1. Read `autopilot/state.json`, `autopilot/blockers.json`, and `autopilot/secrets-status.json` if it exists.
2. If `setupStatus` is `pending` or `autopilot/secrets-status.json` is still pending, treat the project as an existing project waiting on setup continuation.
3. In that setup continuation path, collect only the missing env payload and do not assume `docs/spec.md` or `docs/progress.md` already exist.
4. Otherwise read `docs/spec.md`, `docs/progress.md`, `docs/next.md`, and `docs/design.md` when relevant.
5. Read `executionMode`, `teamRoles`, `currentOwner`, `qualityGates`, and `lastReviewerVerdict` from runtime state.
6. Confirm whether there is an active `human-required` blocker.
7. If not blocked, continue with the top unfinished task.
8. Save results back to the same files after each loop.

## Manager Runtime Contract

The manager owns the real orchestration loop.
Do not treat `executionMode`, `teamRoles`, or `qualityGates` as decorative metadata.
Use them to decide which specialist runs next and when a slice can advance.

Before the first specialist step:

1. Read the saved `executionMode`.
2. Check whether Codex native sub-agents are actually available in the current runtime.
3. If the saved mode is `team-product` or `team-lite` but native sub-agents are unavailable, downgrade to `serial-fallback`.
4. Immediately update:
   - `autopilot/state.json`
   - `docs/progress.md`
   - `docs/next.md`
   so the recorded execution mode matches the real runtime path.

## Intake Rules

Ask for only the minimum complete project contract:

- product summary
- target user
- core features
- non-goals for this version
- stack preference or default stack permission
- architecture preset
- auth requirement
- payment requirement
- admin requirement
- deploy target
- data store
- theme preset
- visual vibe
- design direction refinement
- definition of done

Keep the intake compact, but ask exactly one question at a time.
Treat one-question-at-a-time intake as the default behavior, not an optional preference.
For the exact interaction format, follow `../autopilot-intake/SKILL.md`.

## Execution Rules

1. The manager owns user-facing communication and final state updates.
2. Do not send work directly to Builder before Planner has defined the current slice.
3. Always choose the smallest shippable slice.
4. Prefer working software over broad scaffolding with no validation.
5. Run relevant verification after each meaningful change.
6. Update progress and next-step files after each loop.
7. Continue automatically after intake unless the run is waiting on the upfront integration setup phase or a true `human-required` blocker is active.
8. Ask the user only when:
   - the upfront integration setup phase needs a consolidated env payload
   - external account setup is required and no existing key can be provided yet
   - payment or production deployment approval is required
   - the product direction is ambiguous in a way that changes the build materially

Treat `setup-secrets` pending as a normal pre-execution phase, not as a blocker entry by itself.

## Team Orchestration

Default orchestration is conditional:

- `team-product`
  - user-facing product
  - or `Scalable` architecture
  - or auth / payments / admin are required
- `team-lite`
  - CLI-only, backend-only, library-only, or simple internal tooling
- `serial-fallback`
  - use the same role order in one loop when specialist sub-agents are unavailable

### Role Activation

- `Planner`: always active at project start and again at milestone transitions
- `Architect`: active only for `Scalable` architecture or cross-cutting structure decisions
- `Builder`: always active
- `Designer`: active only for user-facing projects
- `QA`: always active before a slice can be marked complete

### Specialist Responsibilities

- `Planner`
  - break the spec into milestones and current-slice acceptance criteria
  - draft `docs/next.md` and the initial quality gates
- `Architect`
  - define shared vs feature boundaries and integration seams
  - prevent structure drift, especially under `Scalable`
- `Builder`
  - implement the next smallest shippable slice
  - stay inside the planner/architect contract
- `Designer`
  - strengthen `docs/design.md` into the binding UI brief
  - run one explicit visual review after the first UI pass
- `QA`
  - validate tests, builds, key flows, regressions, and definition-of-done alignment
  - leave a pass/fail verdict before completion

### Codex Native Sub-Agent Policy

Use Codex native sub-agents when they are available:

- `Planner`, `Architect`, `Designer`, `QA`: `default`
- `Builder`: `worker`
- repo analysis or structural inspection: `explorer`

Keep the manager in control of ordering:

1. planner first
2. architect and designer only when needed
3. builder implementation
4. QA review

Designer review is mandatory for user-facing UI slices.
QA pass is mandatory before a slice is treated as complete.

## Actual Execution Sequence

Use this exact sequence on every slice.

### Step 1: Planner

- Always run planner first.
- Use `../autopilot-planner/SKILL.md`.
- Expected planner output:
  - planner checkpoint
  - current slice
  - acceptance criteria
  - risks
  - required follow-on roles
  - QA checks
- Write planner results into:
  - `docs/progress.md`
  - `docs/next.md`
  - `autopilot/state.json`
- Record the handoff with:

```bash
python3 ../../scripts/team_checkpoint.py \
  --workspace <target-workspace> \
  --role planner \
  --summary "<planner summary>" \
  --planner-checkpoint "<planner checkpoint>" \
  --planner-intent "<planner intent>" \
  --builder-target "<builder target>" \
  --qa-check "<qa check 1>" \
  --qa-check "<qa check 2>" \
  --next-owner "<Architect or Builder>" \
  --next-task "<next current task>"
```

### Step 2: Architect if needed

Run architect only when:

- `Scalable` architecture is active, or
- planner identifies cross-cutting structure risk

Use `../autopilot-architect/SKILL.md`.
Architect refines boundaries before builder starts and updates the same state files.
Record the result with:

```bash
python3 ../../scripts/team_checkpoint.py \
  --workspace <target-workspace> \
  --role architect \
  --summary "<architect summary>" \
  --architect-guardrails "<architect guardrails>" \
  --next-owner "Builder" \
  --next-task "<builder task>"
```

### Step 3: Builder

- Builder only runs after planner, and after architect when architect was required.
- If native sub-agents are available, delegate builder work to a `worker` sub-agent.
- If not, execute the builder role directly inside the manager loop.
- Builder must stay inside the planner and architect contract.
- After a meaningful builder step, record progress with:

```bash
python3 ../../scripts/team_checkpoint.py \
  --workspace <target-workspace> \
  --role builder \
  --summary "<builder summary>" \
  --builder-progress "<builder progress>" \
  --next-owner "<Designer or QA>" \
  --next-task "<next current task>"
```

### Step 4: Designer if needed

Run designer only for user-facing slices.

- Use `../autopilot-designer/SKILL.md`.
- Before the first UI slice, designer strengthens `docs/design.md`.
- After the first UI pass, designer performs one explicit visual review.
- Manager must record the design verdict into:
  - `docs/design.md`
  - `docs/progress.md`
  - `autopilot/state.json`
- Record the result with:

```bash
python3 ../../scripts/team_checkpoint.py \
  --workspace <target-workspace> \
  --role designer \
  --summary "<designer summary>" \
  --designer-notes "<designer notes>" \
  --reviewer-verdict "<designer verdict>" \
  --design-review-note "<design review note>" \
  --next-owner "QA" \
  --next-task "<qa task>"
```

### Step 5: QA

- Always run QA before a slice is marked complete.
- Use `../autopilot-qa/SKILL.md`.
- QA must return pass or fail.
- If QA fails:
  - do not mark the slice complete
  - route rework back to builder
  - update `lastReviewerVerdict`
- Record the verdict with:

```bash
python3 ../../scripts/team_checkpoint.py \
  --workspace <target-workspace> \
  --role qa \
  --summary "<qa summary>" \
  --reviewer-verdict "<pass or fail verdict>" \
  --qa-check "<qa check 1>" \
  --qa-check "<qa check 2>" \
  --next-owner "<Manager or Builder>" \
  --next-task "<next current task>"
```

### Step 6: Manager update

After the final specialist for the slice:

- update `currentOwner`
- update `currentTask`
- update `lastPlannerCheckpoint` when planner completes
- update `lastReviewerVerdict` when designer or QA completes
- update `docs/progress.md`
- update `docs/next.md`
- append or resolve blockers in `autopilot/blockers.json`

Use the same checkpoint script to record blockers when needed:

```bash
python3 ../../scripts/team_checkpoint.py \
  --workspace <target-workspace> \
  --role manager \
  --summary "<manager status update>" \
  --blocker-classification "human-required" \
  --blocker-summary "<minimal blocker summary>" \
  --blocker-owner-role "<current owner role>"
```

## Serial Fallback Rule

If native sub-agents are unavailable, run the exact same role order in one manager loop:

1. planner
2. architect if needed
3. builder
4. designer if needed
5. QA

Do not skip roles just because the runtime is serial.
`serial-fallback` changes the backend, not the quality bar.

## Design Execution Rule

For user-facing products, design synthesis is required before the first UI build.

- Create and follow `docs/design.md`
- Use the `frontend-ui-ux` skill as the default design helper
- Prefer Figma references when provided
- Otherwise use curated design inspiration sources rather than broad web search
- Keep the base UI bright: white or light-neutral surfaces, compact readable typography, and restrained chrome
- Choose the navigation shell from the project type: landing pages use top headers, dashboard/admin surfaces use sidebars, and mobile-style products use app-header or bottom-tab shells
- Treat theme and vibe as modulation of accent, contrast, spacing tone, and component shape rather than a full override of the base surface system
- Run one explicit post-build design review after the first UI pass
- Treat `docs/design.md` as the designer-owned binding brief

Treat these as user-facing by default:

- landing pages
- marketing sites
- dashboards
- consumer web or mobile apps
- admin interfaces

Skip dedicated design synthesis only for clearly CLI-only, backend-only, or library-only work.

## Blocker Policy

### `retryable`

- dependency install errors
- failing tests
- build issues
- small runtime bugs

Behavior:

- retry automatically
- try one or more alternative fixes
- only escalate after retry budget is exhausted

### `deferable`

- placeholder copy
- icon selection
- optional polish
- non-critical analytics

Behavior:

- keep moving with a reasonable default
- write the deferred decision into `docs/next.md` when useful

### `human-required`

- API keys or secrets
- OAuth app creation
- payment account setup
- production deployment approval
- ambiguous product direction that changes scope materially

Behavior:

- stop only at the minimum blocking decision
- ask one focused question
- continue immediately after the answer
- write the blocker with `ownerRole` in `autopilot/blockers.json`

Each blocker entry must include:

- `ownerRole`
- `classification`
- `summary`
