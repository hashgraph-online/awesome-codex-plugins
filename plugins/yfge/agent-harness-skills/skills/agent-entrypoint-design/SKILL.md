---
name: agent-entrypoint-design
description: Use when designing or refactoring AGENTS.md, CLAUDE.md, GEMINI.md, Cursor rules, GitHub instructions, source-of-truth navigation, or agent onboarding entrypoints.
---

# Agent Entrypoint Design

## Overview

Create a small, stable entrypoint that tells agents where truth lives, what rules apply, and which checks gate changes.

The entrypoint should be navigation plus hard rules, not a long project encyclopedia. For shared harness terms, see `../../references/harness-patterns.md`; when entrypoint files are absent, use `references/build-when-missing.md`. For mirror casing and drift rules, see `references/mirror-policy.md`.

## When To Use

- The user wants to create or refactor `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursorrules`, or GitHub instructions.
- Multiple agent instruction files duplicate content, drift, or contradict each other.
- A new project needs to define what an agent reads first, what it can change, and what it must run afterward.

## Inputs Needed

- Repository root and main app/module boundaries.
- Existing agent instruction files and docs entrypoints.
- Whether mirrors, symlinks, generation scripts, or CI drift checks are expected.

## Execution Order

- First: Read existing entrypoint files and identify which file should be the source of truth.
- Then: Design the root entrypoint, subtree entrypoints, mirror strategy, and validation commands.
- Finally: Output the entrypoint structure and sync/drift-prevention checks.

## Step-by-Step Process

1. Search for `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursor`, and `.github/instructions`.
2. Identify repeated rules, oversized rules, stale paths, or chat-only facts.
3. If no usable entrypoint exists, create the minimum source-of-truth entrypoint from `references/build-when-missing.md`.
4. Choose one primary entrypoint; other agent-specific files should mirror, symlink, or explicitly reference it.
5. Keep the root entrypoint to scope, source-of-truth docs, do/avoid rules, commands, tests, and relevant skills.
6. If a subtree has special rules, put a closer `AGENTS.md` in that subtree instead of overloading the root.
7. Define drift prevention through a generation script, check script, CI job, or explicit manual checklist.

## Checks

- Entrypoint: an agent can learn what to read first, where it may edit, and the minimum validation command within 60 seconds.
- Consistency: mirrored files cannot silently drift, or they carry a generation note or symlink constraint.
- Source of truth: rules point to versioned docs/scripts, not conversation memory.
- Scope: root rules are not too detailed, and subtree rules are not missing.
- Executability: every key rule maps to a command, file, or clear decision standard.

## Output Format

```markdown
# Agent Entrypoint Design

## Detected Mapping
- entrypoint:
- mirrors:
- validation:

## Source Of Truth
- Primary entrypoint:
- Mirrors:
- Subtree overrides:

## Root Entrypoint Sections
-

## Sync / Drift Prevention
-

## Minimum Commands
-

## Follow-up Files
-
```

## Common Mistakes

- Copying large rule blocks into every agent file, which creates drift.
- Turning the entrypoint into a project encyclopedia that still leaves agents unsure what to do first.
- Putting concrete product requirements into general agent rules.
- Failing to document instruction precedence.

## Example Prompts

- "Design AGENTS.md and mirror rules for this repository."
- "This repo has multiple agent instruction files. Make them source-of-truth safe."
- "Shrink the agent entrypoint into high-signal navigation."
