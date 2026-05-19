---
name: write-executable-plan
description: Use when you have a PRD or design spec and need a bite-sized, executable implementation plan that any agent can follow without re-deriving structure. Produces `docs/plans/YYYY-MM-DD-<feature>.md` with per-task Files block, complete code per step (no placeholders), and exact verification commands. Rejects "TBD", "TODO", "add error handling", "similar to Task N".
model: inherit
color: green
tools: Read, Grep, Glob, Bash, Write
---

# Write Executable Plan

> Bite-sized plans for parallel agents. No placeholders. No vague steps.

## When to use

- A PRD from `/plan feature` exists but you need a step-by-step implementation plan
- A `/brainstorm` design is approved and you want to skip the PRD layer
- Multiple agents will execute the plan in parallel and need conflict-free task boundaries
- The work is complex enough that describing it to an agent loses fidelity

## When NOT to use

- Trivial 1-file changes (just do them; no plan needed)
- Pure exploration (use `/brainstorm` instead)
- Bug investigation (use `/debug` instead)
- The source PRD is vague or unapproved (get PRD approval before planning execution)

## Phase 0: Bootstrap Gate

Read `skills/_shared/bootstrap-gate.md` and execute the gate check. If the gate is CLOSED, invoke `skills/bootstrap/SKILL.md` and wait for completion before proceeding. If the gate is OPEN, continue to Phase 1.

<HARD-GATE>
Do NOT proceed past Phase 0 if GATE_CLOSED. There is no bypass. Refer to `skills/_shared/bootstrap-gate.md` for the full HARD-GATE constraints.
</HARD-GATE>

## Phase 1: Source Selection

Accept ONE of the following inputs (in order of preference):

1. **PRD path** — `docs/prd/YYYY-MM-DD-<feature>.md` produced by `/plan feature`
2. **Design spec path** — `docs/specs/YYYY-MM-DD-<slug>-design.md` produced by `/brainstorm`
3. **Inline description** — user provides a free-text description; prompt for elaboration via AUQ before proceeding

If no source is provided and `$ARGUMENTS` is empty, ask via AUQ:

```
AskUserQuestion({
  questions: [{
    question: "Which source should this plan be based on?",
    header: "Plan Source",
    options: [
      { label: "Existing PRD (Recommended)", description: "Point me to docs/prd/YYYY-MM-DD-<feature>.md — most precise decomposition." },
      { label: "Design spec from /brainstorm", description: "Point me to docs/specs/YYYY-MM-DD-<slug>-design.md — skips formal PRD." },
      { label: "Describe inline", description: "Paste or describe the feature — I will ask follow-up questions before planning." }
    ],
    multiSelect: false
  }]
})
```

Read the source file and extract:
- **Feature title** (for filename slug and plan header)
- **Acceptance criteria** or equivalent (drives Task decomposition)
- **Explicit out-of-scope items** (excludes from plan)
- **File inventory** if present (seeds the whole-plan Files block)

## Phase 2: Decomposition

Break the source into Tasks. Each Task MUST satisfy all of these constraints:

- **Single owner** — one agent role (e.g., `code-implementer`, `test-writer`), not "the team"
- **Bounded file set** — lists every file it creates, modifies, or tests; no file appears in two Tasks
- **Independently testable** — after Step 4 the task stands on its own; no cross-task dependencies in the test command
- **2-5 minute wall-clock estimate** — if the estimate exceeds 5 minutes, split the Task; if two Tasks share a file, merge or re-scope

Before writing Tasks, output a brief decomposition plan in plain text:

```
## Decomposition (draft)
- Task 1: <title> — <owner> — ~<N> min — Files: <list>
- Task 2: <title> — <owner> — ~<N> min — Files: <list>
...
```

If any task's file set overlaps another, surface the conflict and resolve it before writing Steps.

## Phase 3: Step Authoring (per Task)

Each Task gets exactly 5 steps in this order. All 5 steps are mandatory.

### Step 1: Write the failing test

Provide:
- Exact file path (absolute from project root)
- Complete, runnable test code — no `// ...`, no placeholders, no `// implement later`
- One sentence explaining why this test verifies the intended behavior

The test MUST fail before Step 3 is applied. If the behavior already exists and cannot fail, pick a harder assertion or a new edge case.

### Step 2: Run the test to confirm it fails

Provide:
- Exact command (e.g., `npm test -- tests/unit/my-module.test.mjs`)
- Expected terminal output — the specific assertion failure line that proves the test exercises missing code (not a generic "FAIL" — copy the actual error shape)

### Step 3: Implement the minimal code

Provide:
- Exact file paths labeled `Create:` or `Modify:`
- Complete code — every function, every import, every export. No `// add appropriate logic`, no `// similar to above`, no `...`
- DRY constraint: reuse existing utilities; do not duplicate logic that already exists in the codebase
- YAGNI constraint: implement exactly what makes Step 2's test pass; no speculative features

### Step 4: Run the test to verify it passes

Provide:
- Same command as Step 2 (copy verbatim)
- Expected terminal output showing the test suite PASS line with the test name visible

### Step 5: Commit

Provide:
- Exact commit message in Conventional Commits format: `type(scope): subject`
- Scope: the primary module or directory affected by this Task
- Subject: imperative mood, max 72 characters, no period
- Files staged: only this Task's files (list them)

## Phase 4: Placeholder Linter

Before writing the plan to disk, scan every Step in every Task for forbidden strings. Any match is a rejection — fix before writing.

**Forbidden strings (case-insensitive):**

| Pattern | Why forbidden |
|---------|---------------|
| `TBD`, `TODO`, `FIXME`, `XXX` | Deferred decisions defeat the plan's purpose |
| `add appropriate error handling` | Vague — specify the exact error type and handling code |
| `add error handling` | Same — write the catch block |
| `similar to Task N`, `same as above`, `like Task N` | Forces the executor to cross-reference; defeats file-disjoint execution |
| `etc.` | Incomplete enumeration — list every item |
| `[fill in]`, `<placeholder>`, `<YOUR_VALUE>` | Template leftovers — fill them in |
| `...` inside a code block | Ellipsis in implementation code means incomplete code |

Prose ellipsis (e.g., "Phase 1... Phase 2...") is acceptable. Only code-block ellipsis is forbidden.

Any hit → surface to user via AUQ:

```
AskUserQuestion({
  questions: [{
    question: "The placeholder linter found forbidden strings in the draft plan:\n\n[list each hit with Task number, Step number, and matched text]\n\nHow do you want to proceed?",
    header: "Placeholder Linter",
    options: [
      { label: "Fix automatically (Recommended)", description: "I will resolve each hit by filling in the missing specifics before writing the plan." },
      { label: "Show me each hit interactively", description: "Walk me through each one so I can provide the missing detail." }
    ],
    multiSelect: false
  }]
})
```

Fix all hits before Phase 5.

## Phase 5: Write Plan

Ensure the target directory exists:

```bash
mkdir -p docs/plans
```

Generate today's date via `date +%Y-%m-%d`. Derive `<feature-slug>` from the feature title (lowercase, hyphens, no special characters, max 40 characters).

Write to: `docs/plans/YYYY-MM-DD-<feature-slug>.md`

Use the template in `plan-template.md` (same directory as this SKILL.md) as the structural guide. Fill every slot. The written plan must:

- Open with `# Plan: <feature title>` and a `Source:` / `Created:` / `Status: draft` header block
- Include a whole-plan `## Files` section listing all Create / Modify / Test paths across all Tasks
- Contain one `## Task N: <title>` section per Task, each with its per-task `### Files` block and Steps 1-5
- Pass the Phase 4 linter with zero hits

## Phase 6: Hand-off

Present the plan path and task count to the user via AUQ:

```
AskUserQuestion({
  questions: [{
    question: "Executable plan written to docs/plans/YYYY-MM-DD-<slug>.md ([N] tasks, ~[total] min estimated).\n\nHow do you want to execute it?",
    header: "Plan Hand-off",
    options: [
      { label: "Dispatch via wave-executor (Recommended)", description: "Parallel agents execute all tasks simultaneously. Fastest for file-disjoint tasks." },
      { label: "Execute coordinator-direct", description: "One task at a time in this session. Safer for tasks with shared state." },
      { label: "Revise the plan first", description: "I have feedback — describe what to change and I will update the plan." },
      { label: "Done for now", description: "Keep the plan as a reference; no immediate execution." }
    ],
    multiSelect: false
  }]
})
```

If the user selects "Revise the plan first", incorporate the feedback, update the plan file, re-run the Phase 4 linter, and re-present Phase 6.

If the user selects "Dispatch via wave-executor", hand off to `skills/wave-executor/SKILL.md` with the plan path as input.

## Anti-Patterns

- **Steps that say "implement the feature"** without exact file paths and complete code — this is the most common failure mode; reject it at Phase 4
- **Tasks with overlapping file scopes** — agents executing in parallel will conflict; the decomposition must be file-disjoint
- **Plans without a per-Task Files block** — forces agents to grep the codebase to discover their scope, which loses the speed advantage of planning
- **Skipping Phase 4** — placeholders in a plan silently cascade into every agent that executes it; one "TBD" can stall an entire wave
- **Estimating tasks at >5 minutes** — if a task is that large, it contains multiple logical changes; split it
- **Vague commit messages in Step 5** — `feat(core): update things` is not acceptable; the scope and subject must be derivable from the Task's file set without reading the diff

## See Also

- `skills/plan/SKILL.md` — produces the PRD this skill consumes
- `skills/brainstorm/SKILL.md` — alternative source (design spec)
- `skills/wave-executor/SKILL.md` — consumes the plan for parallel execution
- `.claude/rules/test-quality.md` — test conventions to follow in Step 1
- `skills/write-executable-plan/plan-template.md` — structural template used in Phase 5
