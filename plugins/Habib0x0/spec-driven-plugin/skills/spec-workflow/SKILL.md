---
name: spec-workflow
description: This skill should be used when the user asks to "create a spec", "write requirements", "design a feature", "plan implementation", "use EARS notation", "create user stories", "break down tasks", "write a PRD", "technical specification", or mentions "spec-driven development", "feature spec", "requirements phase", "design phase", or "tasks phase". Provides structured 3-phase workflow for feature development.
version: 5.3.3
---

# Spec-Driven Development Workflow

A structured approach to feature development through four phases: Brainstorm, Requirements, Design, and Tasks. This methodology prevents ad-hoc coding by ensuring proper planning before implementation.

## Overview

Spec-driven development transforms vague feature ideas into formal, traceable specifications:

```
Feature Idea → Brainstorm (Conversation) → Requirements (EARS) → Design (Architecture) → Tasks (Trackable)
```

## Phase 0: Brainstorm

Before formalizing requirements, use `/spec-brainstorm` to explore the idea through conversation.

### When to Brainstorm

- You have a vague idea that needs refinement
- You're weighing multiple approaches
- You want to think through feasibility before committing
- The scope isn't clear yet

### Brainstorm Workflow

1. Start with `/spec-brainstorm [idea]`
2. Have a back-and-forth conversation exploring the problem
3. Codex asks probing questions, suggests alternatives, identifies gaps
4. When the idea is solid, Codex outputs a brief
5. Use that brief as input for `/spec <feature-name>`

The brainstorm phase is optional — if you already know exactly what you want, skip straight to `/spec`.

All new spec files are stored in `.claude/specs/<feature-name>/`. Existing `.codex/specs/<feature-name>/` specs remain supported as a migration fallback:
- `requirements.md` - User stories with EARS acceptance criteria
- `design.md` - Architecture, components, data flow
- `tasks.md` - Implementation tasks tracked by status, wiring, verification, and dependencies

## Phase 1: Requirements

Capture WHAT the system should do using EARS (Easy Approach to Requirements Syntax).

### EARS Notation

Structure requirements as testable statements:

```
WHEN [condition/trigger]
THE SYSTEM SHALL [expected behavior]
```

**Examples:**
```
WHEN a user submits a login form with valid credentials
THE SYSTEM SHALL authenticate the user and redirect to dashboard

WHEN a user submits invalid form data
THE SYSTEM SHALL display inline validation errors without page reload

WHEN an API request fails after 3 retries
THE SYSTEM SHALL display a user-friendly error message and log the failure
```

### User Story Format

```markdown
### US-1: [Story Title]

**As a** [user role]
**I want** [goal/desire]
**So that** [benefit/value]

#### Acceptance Criteria (EARS)

1. WHEN [condition]
   THE SYSTEM SHALL [behavior]
```

### Requirements Phase Workflow

1. Ask clarifying questions about the feature scope
2. Identify user roles and their goals
3. Write user stories with EARS acceptance criteria
4. Identify non-functional requirements (performance, security, accessibility)
5. Document out-of-scope items explicitly
6. List open questions for resolution

For detailed EARS patterns and examples, consult `references/ears-notation.md`.

## Phase 2: Design

Define HOW the system will implement the requirements.

### Design Components

1. **Architecture Overview** - High-level component diagram
2. **Data Flow** - How data moves through the system
3. **Component Specifications** - Purpose, responsibilities, interfaces
4. **Data Models** - Schemas, types, relationships
5. **API Design** - Endpoints, request/response formats
6. **Sequence Diagrams** - Key interaction flows

### Design Phase Workflow

1. Review all requirements from Phase 1
2. Identify major components needed
3. Define interfaces between components
4. Design data models and storage
5. Plan API contracts if applicable
6. Document security and performance considerations
7. List alternatives considered with rationale

For detailed design patterns, consult `references/design-patterns.md`.

## Phase 3: Tasks

Break down the design into discrete, trackable implementation tasks.

### Task Structure

```markdown
### T-1: [Task Title]

- **Status**: pending | in_progress | completed
- **Wired**: no | yes | n/a
- **Verified**: no | yes
- **Requirements**: US-1, US-2
- **Description**: [Detailed description]
- **Acceptance**: [How to verify completion]
- **Dependencies**: T-0 | none
```

### Task Breakdown Principles

1. **Single Responsibility** - Each task does one thing
2. **Testable** - Clear acceptance criteria
3. **Traceable** - Links to requirements
4. **Sequenced** - Dependencies explicit
5. **Time-boxed** - Completable in reasonable scope

### Task Phases

Organize tasks into logical phases:

1. **Setup** - Project scaffolding, dependencies, configuration
2. **Core Implementation** - Main feature functionality
3. **Integration** - Connect components, APIs
4. **Testing** - Unit, integration, E2E tests
5. **Polish** - Error handling, edge cases, cleanup

### Tasks Phase Workflow

1. Review design from Phase 2
2. Identify discrete implementation units
3. Sequence tasks based on dependencies
4. Link each task to requirements
5. Define acceptance criteria per task
6. Keep tasks traceable in `tasks.md`; if the active client has a native todo tool, mirror the task list there.

For detailed task breakdown strategies, consult `references/task-breakdown.md`.

## Phase 4: Execution

After planning is complete, execute the spec autonomously using the provided scripts.

### Single Iteration

Run one task at a time:

```bash
${CODEX_PLUGIN_ROOT:-$CLAUDE_PLUGIN_ROOT}/scripts/spec-exec.sh --spec-name <name>
```

Each run picks the highest-priority pending task, implements it, tests it, updates the spec, and commits.

### Loop Until Done

Run all tasks in a loop:

```bash
${CODEX_PLUGIN_ROOT:-$CLAUDE_PLUGIN_ROOT}/scripts/spec-loop.sh --spec-name <name> --max-iterations 50
```

The loop re-reads spec files each iteration, detects completion via `<promise>COMPLETE</promise>`, and stops when all tasks are done.

### Execution Commands

| Command | Description |
|---------|-------------|
| `/spec-exec` | Run one implementation iteration |
| `/spec-loop` | Loop until all tasks complete |

## Spec File Location

Create specs in the project's `.claude/specs/` directory. If an older project already has `.codex/specs/`, the scripts read that location unless `SPEC_ROOT` is set:

```
project/
├── .codex/
│   └── specs/
│       └── user-authentication/
│           ├── requirements.md
│           ├── design.md
│           └── tasks.md
└── src/
```

## Integration with Codex

### Creating Specs

Use the `/spec <feature-name>` command to start a new spec with interactive guidance through all three phases.

### Task Synchronization

After completing the Tasks phase, keep `tasks.md` authoritative and mirror to the active client's todo system when available:

```
For each task in tasks.md:
  Create or update a todo with subject, description, and dependencies
```

### Auto-Context

When implementing features, include relevant spec files as context. This ensures implementation stays aligned with requirements.

### Refinement

Use `/spec-refine` to update requirements or design. Changes cascade:
- Updated requirements → Review design
- Updated design → Regenerate tasks

## Templates

Templates are available at `${CODEX_PLUGIN_ROOT:-$CLAUDE_PLUGIN_ROOT}/templates/`:
- `requirements.md` - Requirements template with EARS format
- `design.md` - Design document template
- `tasks.md` - Task tracking template

## Quick Reference

| Phase | Focus | Output | Key Question |
|-------|-------|--------|--------------|
| Requirements | WHAT | User stories + EARS | What should it do? |
| Design | HOW | Architecture docs | How will it work? |
| Tasks | WHEN | Task list + todos | What's the sequence? |

## Additional Resources

### Reference Files

For detailed guidance on each phase:
- **`references/ears-notation.md`** - Complete EARS patterns and examples
- **`references/design-patterns.md`** - Architecture documentation patterns
- **`references/task-breakdown.md`** - Task decomposition strategies

### Commands

- `/spec <name>` - Start new spec
- `/spec-refine` - Update existing spec
- `/spec-tasks` - Regenerate tasks
- `/spec-status` - View progress
- `/spec-validate` - Validate completeness
