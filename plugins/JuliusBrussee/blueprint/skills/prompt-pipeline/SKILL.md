---
name: prompt-pipeline
description: >
  How to design the numbered prompt pipeline that drives Hunt phases in Cavekit.
  Covers greenfield 3-prompt patterns, rewrite 6-9 prompt patterns, shared principles,
  prompt engineering best practices, task templates, and time guards.
  Trigger phrases: "prompt pipeline", "design prompts for SDD", "create Hunt prompts",
  "pipeline prompts", "how many prompts do I need"
---

# Prompt Pipeline Design

The prompt pipeline is the engine of SDD. Each numbered prompt drives one phase of the Hunt lifecycle (Spec, Plan, Implement, Iterate, Monitor). Prompts are structured markdown files that instruct an AI agent to perform a specific phase, with detailed information delegated to specs, plans, and reference materials.

**Core principle:** Prompts should be as lightweight and systemic as possible. They define the *process*, not the *content* -- specs and plans hold the content.

---

## 1. Greenfield Pattern (3-Prompt Pipeline)

For new projects starting from reference materials (PRDs, language specs, design docs, research).

```
Pipeline Flow:
  refs/ ──> [001] ──> specs/ ──> [002] ──> plans/ ──> [003] ──> src/ + tests/
                                   ^                     |
                                   |                     |
                                   +── impl/ <───────────+
                                   (bidirectional flow)
```

| Prompt File | Lifecycle Stage | Reads From | Writes To | Description |
|-------------|----------------|------------|-----------|-------------|
| `001-generate-specs-from-refs.md` | **Spec** | `context/refs/` | `context/kits/` | Reads reference materials, decomposes into domain-specific specs with cross-references and testable acceptance criteria |
| `002-generate-plans-from-specs.md` | **Plan** | `context/kits/` + `context/impl/` | `context/plans/` | Reads specs plus implementation progress, creates framework-specific plans with feature dependencies, test strategies, and acceptance criteria |
| `003-generate-impl-from-plans.md` | **Implement** | `context/plans/` + `context/kits/` | `src/`, `tests/`, `context/impl/` | Implements the highest-priority unblocked work from plans, runs tests, updates implementation tracking |

### Key behaviors

- **Prompt 001** runs once or a few times to stabilize specs. It reads `context/refs/` and produces `context/kits/`.
- **Prompt 002** reads specs and any existing implementation tracking (`context/impl/`). It produces plans that sequence the work.
- **Prompt 003** reads plans and specs, implements code, runs validation gates, and updates `context/impl/` with progress.
- **Prompts 002 and 003 modify each other's files.** This bidirectional flow is expected and healthy -- it is how the system self-corrects.

### Example prompt 001 structure

```markdown
# 001: Generate Specs from Reference Materials

## Runtime Inputs
- Framework: {FRAMEWORK}
- Build command: {BUILD_COMMAND}
- Test command: {TEST_COMMAND}

## Context
Read all files in `context/refs/`. These are the source of truth.

## Task
Decompose the reference materials into domain-specific specifications:
1. Create `context/kits/cavekit-overview.md` as the index file
2. Create one `context/kits/spec-{domain}.md` per domain
3. Each spec must include: Scope, Requirements with Acceptance Criteria, Dependencies, Out of Scope, Cross-References

## Exit Criteria
- [ ] All domains from reference materials have corresponding spec files
- [ ] Every requirement has at least one testable acceptance criterion
- [ ] cavekit-overview.md indexes all spec files with one-line summaries
- [ ] Cross-references link related specs

## Completion Signal
<all-tasks-complete>
```

---

## 2. Rewrite Pattern (6-9 Prompt Pipeline)

For projects that start from existing code that must be reverse-engineered into specs before building a new implementation.

```
Pipeline Flow:
  old-code ──> [001] ──> reference/ ──> [002] ──> specs/ ──> [003] ──> validated specs
                                                                            |
       +────────────────────────────────────────────────────────────────────+
       |
       v
  specs/ ──> [004] ──> plans/ ──> [005] ──> src/ + tests/ ──> [006] ──> updated specs
                                                                            |
       +────────────────────────────────────────────────────────────────────+
       |
       v
  (loop back to 002 for refinement)
```

| Prompt File | Lifecycle Stage | Reads From | Writes To |
|-------------|----------------|------------|-----------|
| `001-generate-refs-from-code.md` | Pre-Spec | Old application source | `shared-context/reference/` (API docs, data models, UI components) |
| `002-generate-specs.md` | Spec | Feature scope + reference materials | `shared-context/kits/` (implementation-agnostic specs) |
| `003-validate-specs.md` | Spec QA | Reference + specs | Validation report (specs match old behavior) |
| `004-create-plans.md` | Plan | Specs + framework research | `context/plans/` (framework-specific plans) |
| `005-implement.md` | Implement | Plans + specs | `src/` + `tests/` + `context/impl/` |
| `006-backpropagate.md` | Iterate | Working prototype | Updated specs (back-propagates to 002) |

### Rewrite-specific considerations

- **Prompt 001** only runs once -- it extracts reference documentation from the old codebase.
- **Prompt 003** is a validation pass -- it does not produce code, only a report on spec accuracy.
- **Prompt 006** creates a feedback loop: prototype learnings flow back into specs, which then flow forward through 004 and 005 again.
- The rewrite pipeline supports **multi-repo strategies**: shared specs can drive implementations in multiple frameworks simultaneously (e.g., evaluating framework A vs framework B using the same specs).

---

## 3. Shared Principles Across All Pipelines

These principles apply regardless of whether the pipeline is greenfield, rewrite, or hybrid.

| Principle | Detail |
|-----------|--------|
| **One prompt per Hunt phase** | Each prompt maps to exactly one phase. Do not combine phases. |
| **Explicit input/output directories** | Every prompt declares what it reads and what it writes. No implicit side effects. |
| **Git-based continuity** | Agents read git history (`git log`, `git diff`, `git status`) between iterations to understand what was done before. |
| **Explicit done-conditions with termination markers** | Every prompt concludes with a verifiable checklist of conditions and a distinct output token that the iteration loop uses to detect completion. |
| **Bidirectional spec/plan updates** | Plan prompts read impl tracking; implement prompts update plans. This cross-pollination is healthy. |
| **Test generation on changed files** | After modifying source files, run test generation to maintain coverage. |
| **Phase gates between prompts** | Before moving to the next prompt, verify: build passes, tests pass, acceptance criteria met. |

### The bidirectional flow in detail

```
Prompt 002 (Plans):
  READS:  context/kits/     (what to build)
  READS:  context/impl/      (what has been built, what failed)
  WRITES: context/plans/     (how to build it)

Prompt 003 (Implement):
  READS:  context/plans/     (how to build it)
  READS:  context/kits/     (acceptance criteria)
  WRITES: src/, tests/       (the code)
  WRITES: context/impl/      (progress tracking)
  WRITES: context/plans/     (updates to plans based on implementation reality)
```

This means running prompt 002 again after prompt 003 will incorporate implementation learnings into plans. Running prompt 003 again after prompt 002 will implement updated plans. This is exactly the convergence loop at work.

---

## 4. Prompt Engineering Best Practices

### 4.1 Runtime Inputs

Use runtime variables so prompts work across any project without modification:

```markdown
## Runtime Inputs
- Framework: {FRAMEWORK}           # e.g., "React + Vite", "Tauri + Svelte"
- Build command: {BUILD_COMMAND}   # e.g., "npm run build", "cargo build"
- Test command: {TEST_COMMAND}     # e.g., "npm test", "pytest"
- Lint command: {LINT_COMMAND}     # e.g., "npm run lint", "cargo clippy"
- Source dir: {SRC_DIR}            # e.g., "src/", "lib/"
- Test dir: {TEST_DIR}            # e.g., "tests/", "__tests__/"
```

### 4.2 Agent Team Structure (ASCII Trees)

When prompts use agent teams, define the hierarchy explicitly as an ASCII tree:

```
Agent Team Structure:
  Lead (delegate mode -- never writes code directly)
  +-- Teammate A: domain-auth
  |   Owns: src/auth/*, context/impl/impl-auth.md
  |   Dispatch: Agent tool
  +-- Teammate B: domain-data
  |   Owns: src/data/*, context/impl/impl-data.md
  |   Dispatch: Agent tool
  +-- Teammate C: domain-ui
      Owns: src/ui/*, context/impl/impl-ui.md
      Dispatch: Agent tool
```

**Why:** Agents need to understand their role and what they own. Dispatch subagents via the Agent tool. After merging a subagent's branch, the caller must clean up: `git branch -D <branch>`.

### 4.3 Batching Rules

- **Max 3 concurrent teammates** per batch. Prevents resource exhaustion and race conditions.
- **Batch phases:** Spawn batch 1 (3 teammates) -> wait for completion -> shutdown -> spawn batch 2.
- **Max 3 sub-agents per teammate.** Sub-agents handle discrete subtasks (reading docs, running tests) to preserve the teammate's context window.

```
Execution Timeline:
  Batch 1: [Teammate A] [Teammate B] [Teammate C]
           ─────────────────────────────────────────> complete, shutdown
  Batch 2: [Teammate D] [Teammate E] [Teammate F]
           ─────────────────────────────────────────> complete, shutdown
```

### 4.4 File Ownership Tables

Assign each shared file to exactly one teammate to eliminate merge conflicts:

```markdown
## File Ownership
| File/Pattern | Owner |
|-------------|-------|
| `src/auth/**` | domain-auth |
| `src/data/**` | domain-data |
| `src/ui/**` | domain-ui |
| `src/shared/types.ts` | domain-data |
| `context/impl/impl-auth.md` | domain-auth |
```

**Rule:** If two teammates need to modify the same file, assign ownership to one and have the other request changes through the lead.

### 4.5 Exit Criteria and Completion Signals

Every prompt must end with explicit exit criteria and a completion signal:

```markdown
## Exit Criteria
- [ ] All T- tasks are DONE or documented as BLOCKED
- [ ] {BUILD_COMMAND} passes with zero errors
- [ ] {TEST_COMMAND} passes with zero failures
- [ ] All modified source files have corresponding test coverage
- [ ] context/impl/ updated with current status

## Completion Signal
When ALL exit criteria are met, output exactly:
<all-tasks-complete>

This signal is used by the iteration loop to detect when to stop.
```

### 4.6 Spawn Templates

Teammates are fresh processes with **no inherited history**. Every spawn must include full context:

```markdown
## Spawn Template for Teammate

You are implementing {DOMAIN} for the {PROJECT_NAME} project.

### Your Role
- You own: {FILE_PATTERNS}
- Dispatched via the Agent tool
- Your impl tracking: context/impl/impl-{DOMAIN}.md

### Context to Read First
1. context/kits/spec-{DOMAIN}.md (WHAT to build)
2. context/plans/plan-{DOMAIN}.md (HOW to build it)
3. context/impl/impl-{DOMAIN}.md (what has been done)
4. git log --oneline -20 (recent history)

### Task
{TASK_DESCRIPTION}

### Exit Criteria
- [ ] {CRITERIA}

### Halting Conditions
- Do NOT push to remote unless explicitly asked
- Do NOT modify files outside your ownership
- If blocked for more than 20 minutes, document the blocker and stop
```

### 4.7 Halting Conditions

Explicit halting conditions prevent irreversible or wasteful actions:

```markdown
## Halting Conditions
- Do NOT push to remote unless explicitly asked
- Do NOT modify files outside your file ownership table
- Do NOT delete test files or skip failing tests
- If a task takes more than 20 minutes, document findings and move on
- If you encounter a circular dependency, document it and stop
- Commit frequently to preserve progress
```

### 4.8 Sub-Agent Delegation

Teammates should delegate discrete subtasks to sub-agents to preserve their own context window:

```markdown
## When to Use Sub-Agents
- Reading large documentation files
- Running and parsing test output
- Generating boilerplate code
- Researching framework APIs
- Performing file-by-file migrations

## Sub-Agent Rules
- Max 3 concurrent sub-agents per teammate
- Each sub-agent gets a focused, self-contained task
- Sub-agent results are summarized back to the teammate
- Sub-agents do NOT inherit the teammate's conversation history
```

---

## 5. Task Template Standardization

Use standardized task templates for consistent tracking across prompts:

### Task ID format

```markdown
### T-{DOMAIN}-{NUMBER}: {Task Title}
- **Status:** TODO | IN_PROGRESS | DONE | BLOCKED
- **blockedBy:** T-{OTHER_DOMAIN}-{NUMBER} (if applicable)
- **Files:** {list of files to create or modify}
- **Acceptance criteria:**
  - [ ] {criterion 1}
  - [ ] {criterion 2}
```

### Dependency tracking with blockedBy

```markdown
### T-AUTH-001: Implement login flow
- **Status:** TODO
- **blockedBy:** T-DATA-001 (needs user model)

### T-DATA-001: Create user data model
- **Status:** IN_PROGRESS
- **blockedBy:** none
```

### Conditional and dynamic tasks

```markdown
### T-UI-005: Implement dark mode [CONDITIONAL]
- **Skip if:** {FRAMEWORK} does not support CSS variables
- **Status:** TODO

### T-PERF-001: Optimize hot paths [DYNAMIC]
- **Created when:** Performance gate identifies bottlenecks
- **Status:** not yet created
```

**`[CONDITIONAL]`** tasks include a skip condition -- if the condition is met, the task is skipped without failure.

**`[DYNAMIC]`** tasks are placeholders created at runtime when a specific trigger occurs. They do not exist in the initial plan.

---

## 6. Time Guards

Per-task time budgets prevent agents from spending too long on any single task:

| Category | Budget | Examples |
|----------|--------|----------|
| **Mechanical** | 10 minutes | File creation, boilerplate, simple refactors |
| **Investigation** | 20 minutes | Debugging, researching APIs, understanding existing code |
| **Category budget** | 20 minutes | Total time for all tasks in one category before escalating |

### Time guard rules

1. **Set expectations in the prompt:**
   ```markdown
   ## Time Guards
   - Mechanical tasks (file creation, boilerplate): 10 min max
   - Investigation tasks (debugging, research): 20 min max
   - If you hit a time guard, document your findings and move to the next task
   - Do NOT silently retry -- document the blocker
   ```

2. **Hard stops:** When a time guard is hit, the agent must:
   - Document what was attempted
   - Document what was learned
   - Document the blocker or open question
   - Move to the next unblocked task

3. **Escalation:** If an agent hits time guards on multiple related tasks, this signals a systemic issue (fuzzy spec, missing dependency, architectural problem). Document it as a pattern, not individual failures.

---

## 7. Prompt File Naming Convention

```
context/prompts/
+-- 000-generate-specs-from-code.md    # Brownfield only (bootstrap, runs once)
+-- 001-generate-specs-from-refs.md    # Greenfield spec generation
+-- 002-generate-plans-from-specs.md   # Plan generation
+-- 003-generate-impl-from-plans.md    # Implementation
+-- 004-validate-specs.md              # Spec validation (rewrite pipelines)
+-- 005-backpropagate.md               # Back-propagation (rewrite pipelines)
```

### Naming rules

- **Three-digit prefix** for ordering (000, 001, 002...)
- **Verb-noun format** describing the transformation (generate-specs-from-refs)
- **Lower prompt numbers** are upstream (closer to specs)
- **Higher prompt numbers** are downstream (closer to code)
- **000** is reserved for brownfield bootstrap (runs once, not in the main loop)

---

## 8. Designing Your Pipeline

### Step-by-step process

1. **Identify your project type:** Greenfield (start from refs) or Rewrite (start from old code)?
2. **Start with the minimum pipeline:** Greenfield = 3 prompts. Rewrite = 6 prompts.
3. **Write prompt 001 first:** This is always the spec generation step.
4. **Define your runtime variables:** What framework, build command, test command?
5. **Set exit criteria for each prompt:** What must be true before moving to the next phase?
6. **Add agent teams if needed:** For large projects, add team structure and file ownership.
7. **Run the pipeline with the iteration loop:** Start with a small number of iterations (3-5) and increase as needed.
8. **Watch for convergence:** Exponentially decreasing changes = convergence. Flat or oscillating changes = fix your specs.

### When to add more prompts

- If a single prompt is trying to do too much (reading AND writing specs, for example), split it.
- If you see a phase producing inconsistent results, add a validation prompt between phases.
- If back-propagation is frequent, add an explicit back-propagation prompt (006 in the rewrite pattern).

---

## 9. Iteration Loop Integration

Prompts are designed to run inside an iteration loop that repeats them until convergence:

```bash
# Greenfield: Run implementation prompt with iteration loop
# -n 10: max 10 iterations
# -t 1h: 1 hour timeout per iteration
iteration-loop context/prompts/003-generate-impl-from-plans.md -n 10 -t 1h

# Leader-follower pattern: staggered pipeline
# Terminal 1: Specs (leader)
iteration-loop context/prompts/001-generate-specs-from-refs.md -n 5 -t 2h

# Terminal 2: Plans (follower, 1h delay)
iteration-loop context/prompts/002-generate-plans-from-specs.md -n 5 -t 2h -d 1h

# Terminal 3: Implementation (follower, 2h delay)
iteration-loop context/prompts/003-generate-impl-from-plans.md -n 10 -t 1h -d 2h
```

The iteration loop handles: iteration counting, timeouts, nudging idle agents, detecting completion signals, and graceful stop on convergence.

---

## Cross-References

- **Prompt engineering details:** See `references/prompt-engineering.md` for the complete reference on runtime inputs, spawn templates, task templates, time guards, and file ownership.
- **Agent team patterns:** See `references/agent-team-patterns.md` for coordination patterns, batching, agent isolation, and merge protocol.
- **Convergence monitoring:** See `ck:convergence-monitoring` skill for detecting when the iteration loop should stop.
- **Revision:** See `ck:revision` skill for how prompt 006 traces bugs back to specs.
- **Context architecture:** See `ck:context-architecture` skill for the directory structure that prompts read from and write to.
