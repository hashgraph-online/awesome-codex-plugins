---
name: typescript-dev
description: "TypeScript development. Use for TypeScript, Node.js, Express, Fastify, Zod, vitest, jest. Backend, CLI, libraries only — no frontend frameworks."
user-invocable: true
allowed-tools: Glob, Read, Grep, Bash, Task, Skill, Edit, Write, AskUserQuestion
---

# TypeScript Development

**Announce:** "I'm using the typescript-dev skill. Following the 4-phase workflow."

## MANDATORY: Read and Follow the Shared Workflow

**You MUST read [workflow.md](../../shared/workflow.md) NOW** and follow ALL 4 phases defined there. The sections below provide TypeScript-specific inputs for each phase.

Read [patterns.md](patterns.md) during Phase 1.

**If you lost workflow.md from context:** Re-read `../../shared/workflow.md` NOW before continuing.

---

## TypeScript-Specific Configuration

### Verification Commands (Phase 1 plan + Phase 3 verify)

WORKFLOW STATE Verification line: `tsc --noEmit, <lint-commands>, vitest/jest` (lint failure BLOCKS Phase 3 verify — see Lint Enforcement below).

**Phase 3 Tier A commands:**
- `tsc --noEmit` — type checking
- Lint — see [Lint Enforcement](#lint-enforcement-phase-3) below; failure blocks Phase 3
- `vitest` or `jest` — tests
- Coverage target: 70-80%

**Phase 3 Tier B additional MCP verifications:**
- PostgreSQL MCP → Query DB state before/after

### Lint Enforcement (Phase 3)

**Lint failures BLOCK Phase 3 verification** with the same severity as a failing test. Read [references/lint-enforcement.md](references/lint-enforcement.md) at the start of Phase 3 verification and follow it.

Detection is a union, not a priority ladder:
1. If `package.json` defines `scripts.lint` → run `<PM> run lint` (PM detected per [references/package-manager.md](references/package-manager.md)). Done.
2. Else, run **every** detected standalone linter (biome / eslint / oxlint) — all must pass.
3. Else, record "Lint: skipped (no linter configured)" and do not block.

No `--fix` auto-remediation — agents fix lint errors intentionally.

### Implementation Rules (Phase 3)

- **Schema structure** — Zod CRUD variants per entity (CreateInput/UpdateInput/Output), domain-driven `schemas.ts`, types derived via `z.infer`, composition over deep extends chains
- **Minimize complexity** — Map/Set lookups over array scans
- **Preserve compatibility** — `.transform()` for renamed fields, `.default()` for new fields, preserve exported signatures, re-export moved symbols

### Staff Review Configuration (Phase 4)

- **Patterns file path:** Path to this skill's `patterns.md`

---

## TypeScript-Specific Rules

- Types are erased at runtime — external data needs Zod validation
- Fix type errors during implementation, not after
- No positive claim without running `tsc --noEmit`
- Before emitting any `install` / `run <script>` / `exec <bin>` command, detect the project's package manager — read [references/package-manager.md](references/package-manager.md). Never default to `npm`.
- Lint failures BLOCK Phase 3 verify — same severity as test failures. Skip is allowed only when no linter is configured (no `scripts.lint`, no biome/eslint/oxlint config). See [references/lint-enforcement.md](references/lint-enforcement.md).

---

## Quality Checklist (TypeScript-Specific)

Add these to the shared workflow's verification checklist:

- [ ] Using TypeScript 5.x+ features where appropriate
- [ ] `strict: true` enabled in tsconfig.json
- [ ] No `any` types (or explicitly justified)
- [ ] Proper type guards for runtime checks
- [ ] Zod or similar for external data validation
- [ ] ESM imports with proper extensions
- [ ] `tsc --noEmit` passes (no type errors)
- [ ] Lint passed (or explicitly skipped because no linter is configured)
- [ ] Tests pass (`vitest`/`jest`)
