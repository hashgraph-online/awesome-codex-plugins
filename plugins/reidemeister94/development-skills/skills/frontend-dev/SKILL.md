---
name: frontend-dev
description: "Frontend development. Use for React, Next.js, Raycast extensions, Vite-based frontend projects."
user-invocable: true
allowed-tools: Glob, Read, Grep, Bash, Task, Skill, Edit, Write, AskUserQuestion
---

# Frontend Development

**Announce:** "I'm using the frontend-dev skill. Following the 4-phase workflow."

---

## PRE-STEP A: PACKAGE MANAGER DETECTION — GATE

**Before any command suggestion, you MUST detect the project's package manager.** Do NOT default to `npm` without checking.

Read [../../shared/package-manager.md](../../shared/package-manager.md) and apply its detection algorithm: `packageManager` field in `package.json` wins; otherwise the lockfile (`bun.lock`/`bun.lockb` → bun, `pnpm-lock.yaml` → pnpm, `yarn.lock` → yarn, `package-lock.json` → npm). No signal → ask the user.

State the result before proceeding: *"Detected **[pm]** (via `[signal]`). Will use [pm] commands."*

**Record durably.** In-context memory is volatile (compaction, subagent dispatch, `/clear` all wipe it). Add a `Package Manager:` line to the WORKFLOW STATE block of the active plan file:

```
Package Manager: <pm> (via <signal>)
```

If the plan file does not exist yet (Phase 1 will create it), carry the value forward in your immediate working notes and re-state it as the first WORKFLOW STATE field the moment the plan is created. **Phase 3 verify resolves `<PM>` from this recorded line, not from in-context recall** — never substitute from memory.

**Gate:** Package manager detected (or user-confirmed) AND recorded. Then proceed to Pre-Step B.

---

## PRE-STEP B: FRAMEWORK DETECTION — GATE

**Before starting the workflow, you MUST detect the frontend framework.** Do NOT skip this step. Do NOT assume a framework without checking.

### Step 1: Check configuration files and package.json dependencies

Examine the project root for config files and `package.json` dependencies. Match the **first row** that applies.

**ALWAYS read [patterns/typescript.md](patterns/typescript.md) AND [patterns/coding-conventions.md](patterns/coding-conventions.md) as a base** — they apply to every frontend framework.

| Signal | Framework | Pattern Files to Read (+ typescript.md, coding-conventions.md) |
|--------|-----------|----------------------------------------------------------------|
| `next.config.*` or `app/layout.tsx` exists | **Next.js** | [patterns/react.md](patterns/react.md) + [patterns/nextjs.md](patterns/nextjs.md) |
| `@raycast/api` in deps | **Raycast** | [patterns/react.md](patterns/react.md) + [environments/raycast.md](environments/raycast.md) |
| `vite.config.*` + `react` in deps | **React + Vite** | [patterns/react.md](patterns/react.md) + [environments/vite.md](environments/vite.md) |
| `*.tsx`/`*.jsx` + `react` in deps | **React** | [patterns/react.md](patterns/react.md) |
| `vue` in deps or `vite.config.*` + `vue` | **Vue** | (no Vue-specific patterns yet) |
| `svelte` in deps or `svelte.config.*` | **Svelte** | (no Svelte-specific patterns yet) |
| `@angular/core` in deps | **Angular** | (no Angular-specific patterns yet) |

> **Note:** Frameworks without dedicated pattern files use general TypeScript patterns. Consider creating `patterns/[framework].md` for team-specific standards.

### Step 2: State detection result

**State:** "Detected framework: **[Framework Name]**. Reading pattern files: [list of files]."

If no framework matches, ask: "I couldn't auto-detect your frontend framework. Which are you using?"

**Gate:** Framework detected and pattern files identified. **Only after detection**, proceed to the workflow.

---

## MANDATORY: Read and Follow the Shared Workflow

**You MUST read [workflow.md](../../shared/workflow.md) NOW** and follow ALL 4 phases defined there. The sections below provide frontend-specific inputs for each phase.

**Phase 1:** Read [patterns/typescript.md](patterns/typescript.md) AND [patterns/coding-conventions.md](patterns/coding-conventions.md) FIRST (always), then ALL framework-specific pattern files identified in Framework Detection.

**If you lost workflow.md from context:** Re-read `../../shared/workflow.md` NOW before continuing.

---

## Frontend-Specific Configuration

### Verification Commands (Phase 1 plan + Phase 3 verify)

WORKFLOW STATE Verification line: `<PM> run build, <lint-commands>, <PM> test` — resolve `<PM>` from the `Package Manager:` line recorded in WORKFLOW STATE during Pre-Step A (do NOT substitute from in-context recall). Lint failure BLOCKS Phase 3 verify — see Lint Enforcement below.

**Phase 3 Tier A commands** — use the commands appropriate for the detected framework. The `<PM> run <script>` placeholders below resolve via the detected package manager (npm/pnpm/yarn/bun):

| Framework | Type Check | Build | Lint † | Test |
|-----------|-----------|-------|------|------|
| Next.js | (included in build) | `<PM> run build` | `<PM> run lint` | `vitest`/`jest` |
| React + Vite | `tsc --noEmit` | `vite build` | `eslint` | `vitest` |
| Raycast | `ray build` | (included) | `eslint` | — |

† Lint command shown is the conventional default. The skill detects the actual linter(s) per [Lint Enforcement](#lint-enforcement-phase-3) below — failure blocks Phase 3 verify.

### Lint Enforcement (Phase 3)

**Lint failures BLOCK Phase 3 verification** with the same severity as a failing test. Read [../../shared/lint-enforcement.md](../../shared/lint-enforcement.md) at the start of Phase 3 verification and follow it.

Detection is a union, not a priority ladder:
1. If `package.json` defines `scripts.lint` → run `<PM> run lint`. Done.
2. Else, run **every** detected standalone linter (biome / eslint / oxlint) — all must pass.
3. Else, record "Lint: skipped (no linter configured)" and do not block.

No `--fix` auto-remediation — agents fix lint errors intentionally.

### Implementation Rules (Phase 3)

- **Schema structure** — Zod CRUD variants per entity (CreateInput/UpdateInput/Output), domain-driven `schemas.ts`, types derived via `z.infer`, composition over deep extends chains
- **Minimize complexity** — Map/Set lookups over array scans, avoid unnecessary re-renders
- **Preserve compatibility** — `.transform()` for renamed fields, `.default()` for new fields, preserve exported signatures and component props

### Staff Review Configuration (Phase 4)

- **Detected framework:** The framework detected in the pre-step
- **Patterns file paths:** Paths to `patterns/typescript.md`, `patterns/coding-conventions.md`, AND the framework-specific pattern file(s)

---

## External Canonical References

Two upstream sources extend the local pattern files. Both are **opt-in** — never auto-install or auto-fetch.

### Next.js bundled docs (zero install on v16.2+)

If framework = **Next.js**, check whether the project ships version-matched docs:

```bash
test -d node_modules/next/dist/docs && echo "bundled docs present"
```

When present, treat `node_modules/next/dist/docs/` as the authoritative source for routing, data fetching, caching, and API references — it is version-matched to the installed `next`, so it overrides anything conflicting from training data. Index: `node_modules/next/dist/docs/index.mdx`.

If absent, tell the user they can opt in via `npx @next/codemod@latest agents-md` (adds bundled docs + an `AGENTS.md` block). **Do not run it for them.** See [nextjs.org/docs/app/guides/ai-agents](https://nextjs.org/docs/app/guides/ai-agents).

### Vercel `react-best-practices` (separate installable skill)

For React perf work (async waterfalls, bundle bloat, unnecessary re-renders), Vercel publishes 40+ impact-rated rules as a standalone agent skill. If the user wants stronger React performance guidance, suggest:

```bash
npx skills add vercel-labs/agent-skills
```

Source: [vercel.com/blog/introducing-react-best-practices](https://vercel.com/blog/introducing-react-best-practices). Once installed, it loads as its own skill alongside `frontend-dev` — this skill does not invoke or depend on it.

---

## Frontend-Specific Rules

- Always read ALL pattern files specified by the detection table — they contain team-specific standards
- Framework detection MUST be explicit and stated — wrong detection = wrong patterns = wrong code
- Each framework has specific build/type-check commands — check the verification table
- If the framework isn't listed, ASK the user — do not guess
- Complete framework detection BEFORE starting Phase 1
- Package manager detection is mandatory before emitting any `install` / `run <script>` / `exec <bin>` command — never default to `npm`
- Lint failures BLOCK Phase 3 verify — same severity as test failures. Skip is allowed only when no linter is configured (no `scripts.lint`, no biome/eslint/oxlint config). See [../../shared/lint-enforcement.md](../../shared/lint-enforcement.md).

---

## Quality Checklist (Frontend-Specific)

Add these to the shared workflow's verification checklist:

- [ ] Package manager detected and stated
- [ ] Framework detected and stated
- [ ] `typescript.md` and `coding-conventions.md` read (always)
- [ ] Framework-specific pattern files read
- [ ] TypeScript strict mode, no `any` types
- [ ] Framework-specific standards from pattern files followed
- [ ] Lint passed (or explicitly skipped because no linter is configured)
