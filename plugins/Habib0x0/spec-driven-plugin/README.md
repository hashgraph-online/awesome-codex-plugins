# Spec-Driven Development Plugin

A structured workflow plugin for Claude Code & Codex that transforms feature ideas into formal specifications before implementation.

## Overview

This plugin guides you through three phases:

1. **Requirements** - User stories with EARS notation and acceptance criteria
2. **Design** - Technical architecture, sequence diagrams, implementation considerations
3. **Tasks** - Discrete, trackable implementation items that mirror to Claude Code's todo system

## Commands

Commands use `/` prefix in Claude Code and `$` prefix in Codex.

### Core Workflow
| Claude Code | Codex | Description |
|-------------|-------|-------------|
| `/spec-brainstorm` | `$spec-brainstorm` | Brainstorm a feature idea before spec creation |
| `/spec <name>` | `$spec <name>` | Start a new feature spec with interactive 3-phase workflow |
| `/spec-bugfix <name>` | `$spec-bugfix <name>` | Start a new bugfix spec with defect analysis and regression prevention |
| `/spec-refine` | `$spec-refine` | Refine requirements/design for current spec |
| `/spec-tasks` | `$spec-tasks` | Regenerate tasks from updated spec |
| `/spec-status` | `$spec-status` | Show spec progress, task completion, and dependency status |
| `/spec-validate` | `$spec-validate` | Validate spec completeness and consistency |

### Research & Navigation
| Claude Code | Codex | Description |
|-------------|-------|-------------|
| `/research` | `$research` | Deep parallel research before planning — searches docs, web, and codebase |
| `/zoom-out` | `$zoom-out` | Map modules, interfaces, and callers for unfamiliar code |
| `/ubiquitous-language` | `$ubiquitous-language` | Extract domain terms into a canonical glossary with flagged ambiguities |

### Implementation
| Claude Code | Codex | Description |
|-------------|-------|-------------|
| `/spec-exec` | `$spec-exec` | Run one autonomous implementation iteration |
| `/spec-loop` | `$spec-loop` | Loop implementation until all tasks complete |

### Post-Completion (Optional)
| Claude Code | Codex | Description |
|-------------|-------|-------------|
| `/spec-accept` | `$spec-accept` | Run user acceptance testing for formal sign-off |
| `/spec-docs` | `$spec-docs` | Generate documentation from spec and implementation |
| `/spec-release` | `$spec-release` | Generate release notes and deployment checklist |
| `/spec-verify` | `$spec-verify` | Run post-deployment smoke tests |
| `/spec-retro` | `$spec-retro` | Run a retrospective on a completed spec |
| `/spec-complete` | `$spec-complete` | Run full post-completion pipeline (accept → docs → release → retro) |

## Usage

### Starting a New Spec

**Claude Code:**
```
/spec user-authentication
```

**Codex:**
```
$spec user-authentication
```

This will:
1. Create `.claude/specs/user-authentication/` directory
2. Gather requirements interactively (2-3 rounds of questions)
3. Guide you through Design phase (architecture docs)
4. Generate Tasks with explicit status, wiring, verification, and dependencies

### Spec Files Location

Specs are stored in `.claude/specs/<feature-name>/` by default. Existing `.codex/specs/<feature-name>/` directories are supported as a migration fallback, or set `SPEC_ROOT` explicitly:

```
.claude/specs/user-authentication/
├── requirements.md   # User stories with acceptance criteria
├── design.md         # Architecture and implementation plan
└── tasks.md          # Trackable implementation tasks
```

### Cross-Spec Dependencies

Specs can declare dependencies on other specs via a `## Depends On` section in requirements.md:

```markdown
## Depends On

- auth-system
- database-migrations
```

Execution scripts check dependencies before running. A dependency is considered complete when all its tasks are verified. `/spec-status` shows dependency status.

## Implementation

After creating a spec, run autonomous implementation:

```bash
# single task
bash scripts/spec-exec.sh --spec-name user-authentication

# loop until all tasks complete
bash scripts/spec-loop.sh --spec-name user-authentication --max-iterations 20
```

Scripts live in the plugin's `scripts/` directory. If only one spec exists, `--spec-name` is auto-detected.

### Post-Completion (Optional)

After implementation completes, optionally run:

```bash
# user acceptance testing
bash scripts/spec-accept.sh --spec-name user-authentication

# generate documentation
bash scripts/spec-docs.sh --spec-name user-authentication

# release notes and deployment checklist
bash scripts/spec-release.sh --spec-name user-authentication

# post-deployment smoke tests
bash scripts/spec-verify.sh --spec-name user-authentication --url https://staging.example.com

# retrospective analysis
bash scripts/spec-retro.sh --spec-name user-authentication

# or run all at once
bash scripts/spec-complete.sh --spec-name user-authentication
```

### Checkpoint Recovery

`spec-loop.sh` creates checkpoint commits before each iteration. If the agent crashes or exits non-zero, the branch is rolled back to the last checkpoint automatically.

### CI/CD Integration

The verification script returns exit codes for CI pipelines:
- `spec-verify.sh` exits `0` on PASS, `1` on FAIL (promise markers: `VERIFIED` / `VERIFICATION_FAILED`)
- `spec-accept.sh` outputs `<promise>ACCEPTED</promise>` or `<promise>REJECTED</promise>`
- `spec-loop.sh` outputs `<promise>COMPLETE</promise>` when all tasks are done

Example CI stage:
```bash
bash scripts/spec-verify.sh --spec-name user-authentication --url "$STAGING_URL" --scope quick || exit 1
```

## Spec-Loop Performance

The loop script includes optimizations for long-running specs:
- **Progress tail**: Only the last 20 progress entries are included in the prompt (configurable via `--progress-tail`)
- **Lightweight Step 1**: Iterations 2+ skip full environment checks
- **Spec reference**: Requirements and design are referenced by path (not inlined) after iteration 1
- **Timing**: Each iteration prints elapsed time

## EARS Notation

Requirements use EARS (Easy Approach to Requirements Syntax):

```
WHEN [condition/trigger]
THE SYSTEM SHALL [expected behavior]
```

Example:
```
WHEN a user submits invalid form data
THE SYSTEM SHALL display validation errors inline
```

## Installation

### Claude Code

Add to your `~/.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "spec-driven@spec-driven": true
  },
  "extraKnownMarketplaces": {
    "spec-driven": {
      "source": {
        "source": "url",
        "url": "https://github.com/Habib0x0/spec-driven-plugin.git"
      }
    }
  }
}
```

Then restart Claude Code.

### Codex

This repository includes a Codex plugin manifest at `.codex-plugin/plugin.json`.

Install from GitHub:

```bash
codex plugin marketplace add Habib0x0/spec-driven-plugin
```

Or test the local checkout:

```bash
codex plugin marketplace add /path/to/spec-driven-plugin
```

Override the agent backend:

```bash
export SPEC_ROOT=.codex/specs
export SPEC_AGENT_CMD='codex exec --full-auto -'
bash scripts/spec-exec.sh --spec-name user-authentication
```

#### Usage in Codex

Codex commands use `$` prefix instead of `/`:

```
$spec user-authentication
$spec-status
$spec-exec
```

You can also invoke the skill by typing one of its default prompt phrases:

| Prompt | Action |
| --- | --- |
| `Create a spec for this feature` | Start a new spec workflow |
| `Validate the current spec` | Run validation on the active spec |
| `Break this design into tasks` | Regenerate tasks from the design doc |

Or reference it by display name: `Use Spec Driven to plan user authentication`.

**Plan mode vs build mode:** Works in both. Plan mode generates the spec for review before writing; build mode writes files directly. Implementation scripts (`spec-exec.sh`, `spec-loop.sh`) run from your terminal.

All generated spec files live in `.codex/specs/<feature-name>/` when running under Codex.

## Inspiration

This plugin was inspired by [Kiro](https://kiro.dev)'s spec-driven development functionality. Kiro introduced the concept of structured specification workflows that guide developers through requirements gathering, design, and task breakdown before implementation.

Key concepts borrowed from Kiro:
- **Three-phase workflow**: Requirements → Design → Tasks
- **EARS notation**: Structured acceptance criteria format
- **Spec file organization**: Dedicated spec directories with separate documents for each phase
- **Task traceability**: Linking implementation tasks back to requirements

## License

MIT
