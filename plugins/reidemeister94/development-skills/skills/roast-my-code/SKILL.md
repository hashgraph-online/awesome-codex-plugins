---
name: roast-my-code
description: "Use when user wants a brutally honest code roast, quality critique, or AI-readiness audit. Use when user says roast, roast my code, critique my code, tear apart my code, review quality, or AI-readiness check. Supports --fix flag to auto-fix CRITICAL and HIGH issues via core-dev workflow."
user-invocable: true
allowed-tools: Glob, Grep, Read, Bash, Agent, AskUserQuestion
effort: max
---

# Roast My Code — Brutally Honest Code Critique + AI-Readiness Audit

**Announce:** "Using the roast-my-code skill. Preparing to roast your code without mercy."

## Target Resolution

Parse `$ARGUMENTS` for the `--fix` flag. If present, enable fix mode. The target scope is everything in `$ARGUMENTS` except `--fix`.

Determine the scope from the remaining arguments:

1. **Empty** (no target after removing `--fix`): Roast the entire repository from the current working directory.
2. **Directory**: if target is a directory path, roast all code files in that directory (recursive).
3. **File**: if target is a single file path, roast that file and its interactions with the rest of the codebase.

## Step 1 — Reconnaissance

Before roasting, understand the terrain:

1. **Detect project type**: Glob for config files (`pyproject.toml`, `package.json`, `pom.xml`, `build.gradle`, `Cargo.toml`, `go.mod`, `Package.swift`, `Makefile`, etc.). Read the main config to understand language, framework, dependencies.
2. **Map the codebase**: Glob for source files in the target scope. Get a count of files by extension. Identify the main directories.
3. **Read key files**: Read entry points, main modules, and any architecture docs. For single-file targets, also read the files that import/use the target.
4. **Check for AI-agent context files**: Look for `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `README.md`, `.cursorrules`, `.github/copilot-instructions.md`, `ARCHITECTURE.md`, or similar files that help AI agents understand the codebase.
5. **Architectural lens (when relevant)**: if the roast targets architecture, depth, testability, or refactor opportunities, read `references/architectural-depth.md` for the glossary (module / interface / depth / seam / adapter / locality), the deletion test, and friction signals. Use this vocabulary in the roast — don't drift into "component" / "service" / "boundary".

## Step 2 — Staff Review (Code Quality Roast)

Dispatch the `development-skills:staff-reviewer` subagent via the `Agent` tool with `subagent_type: "development-skills:staff-reviewer"`. On Codex, follow the named-agent dispatch recipe in `../using-development-skills/references/codex-tools.md`.

Build the target description based on scope:
- **Entire repo:** `"Standalone review. Target: the entire repository at <cwd>. Read the project structure, then systematically review all source files."`
- **Directory:** `"Standalone review. Target: all source files in <directory> and subdirectories. Also check interactions with the rest of the repo."`
- **File:** `"Standalone review. Target: the file <filepath>. Also read files that import or are imported by it."`

The staff-reviewer will detect standalone mode from the absence of task/plan/diff inputs and skip spec compliance (Stage 1), going straight to code quality (Stage 2) with its full checklist.

Collect the staff-reviewer's output.

## Step 3 — AI-Readiness Audit

After the staff review completes, perform the AI-readiness audit yourself. This evaluates how well an AI agent (Claude Code, Copilot, Cursor, Aider, etc.) can work with this codebase.

### AI-Readiness Checklist

Score each dimension 0-3:
- **0** = Missing entirely
- **1** = Exists but inadequate
- **2** = Decent, some gaps
- **3** = Excellent

| Dimension | What to check | Score |
|-----------|--------------|-------|
| **Context files** | Does `CLAUDE.md`, `AGENTS.md`, or equivalent exist? Does it explain project structure, conventions, build commands, and gotchas? | |
| **README quality** | Does README explain what the project does, how to set it up, and how to run it? Or is it a placeholder? | |
| **Architecture docs** | Is there a high-level architecture description? Can an agent understand the system without reading every file? | |
| **Build reproducibility** | Can an agent run `make`, the project's package-manager install + test commands (npm/pnpm/yarn/bun, etc.), or equivalent and get a working build? Are deps pinned? | |
| **Test suite** | Are there tests? Can an agent run them? Do they pass? Is failure output clear enough for an agent to diagnose? | |
| **Code organization** | Is the project structure conventional for its language/framework? Can an agent predict where things live? | |
| **Naming conventions** | Are files, functions, and variables named consistently and descriptively? Can an agent grep for concepts? | |
| **Type safety** | Are types explicit (TypeScript, type hints, schemas)? Or does the agent need to trace runtime behavior to understand data shapes? | |
| **Error messages** | Do errors include enough context for an agent to diagnose the root cause? Or just "something went wrong"? | |
| **Modularity** | Are components independent enough that an agent can modify one without understanding all? Or is everything coupled? | |
| **Configuration** | Are magic numbers, env vars, and settings documented? Or scattered and undiscoverable? | |
| **Commit history** | Are commits atomic and well-described? Can an agent use `git log` and `git blame` to understand why code exists? | |

### Scoring

Compute: `total = sum of scores`, `max = 36`, `percentage = (total / max) * 100`

| Range | Grade | Verdict |
|-------|-------|---------|
| 90-100% | A | AI agents will love working here |
| 75-89% | B | Solid — minor gaps to fill |
| 60-74% | C | Workable but agents will struggle in spots |
| 40-59% | D | Significant friction for AI agents |
| 0-39% | F | AI agents will hallucinate and break things constantly |

## Step 4 — Deliver the Roast

Combine both outputs into a single roast report. Use this format:

```markdown
# Code Roast: {target}

## The Verdict
[1-2 sentences — the overall burn. Be memorable, be honest.]

---

## Part 1: Code Quality Roast

{Staff reviewer output — reformatted if needed for readability}

---

## Part 2: AI-Readiness Audit

**Grade: {letter} ({percentage}%)**

| Dimension | Score | Notes |
|-----------|-------|-------|
| Context files | X/3 | [brief note] |
| README quality | X/3 | [brief note] |
| ... | | |
| **Total** | **X/36** | |

### Top AI-Readiness Improvements
[Ranked list of the 3-5 highest-impact changes to make this repo more AI-agent-friendly. Be specific — "add a CLAUDE.md" is vague; "add a CLAUDE.md with: project structure map, build/test commands, key conventions, and common gotchas" is useful.]

---

## The Roast Score

| Category | Rating |
|----------|--------|
| Code Quality | {X}/10 |
| AI-Readiness | {letter grade} |
| Overall | {witty one-liner} |
```

Display the full report to the user.

## Step 5 — Fix Mode (only if --fix flag present)

If `--fix` was NOT in `$ARGUMENTS`, STOP here. The roast is delivered.

If `--fix` WAS present:

1. **Extract actionable issues** from the roast report. Only CRITICAL and HIGH severity issues are eligible for auto-fix. MEDIUM issues are informational only.
2. **Present the fix list** as numbered items:
   ```
   Fixable issues from the roast:
   1. [file:line] [CRITICAL] Description — Fix: specific action
   2. [file:line] [HIGH] Description — Fix: specific action
   ...

   Which issues should I fix? (all / comma-separated numbers / none)
   ```
3. **STOP. Wait for user selection.**
4. **On user selection:** Invoke `development-skills:core-dev` via Skill tool with task: "Fix the following issues identified by code roast: [selected items with file:line and fix actions]". This triggers the standard development workflow (TDD, staff review), ensuring fixes are properly tested and reviewed by a separate agent.

## Rules

- **No mercy, but be constructive.** Every roast must include a specific fix. "This is bad" without "do this instead" is just venting.
- **Read before roasting.** Never roast code you haven't read. Understand context before judging.
- **File:line references required.** Every issue must point to a specific location. Vague complaints are noise.
- **Don't roast style preferences.** Tabs vs spaces, semicolons, bracket placement — these are not quality issues. Focus on things that affect correctness, maintainability, and comprehension.
- **Scale the roast to the scope.** Single file: deep-dive every function. Directory: focus on module-level patterns and interactions. Whole repo: focus on architecture, cross-cutting concerns, and systemic patterns. Don't try to line-review every file in a large repo.
- **AI-readiness is about the next agent, not the current developer.** Judge the repo from the perspective of an AI agent that has never seen it before and needs to make changes safely.
