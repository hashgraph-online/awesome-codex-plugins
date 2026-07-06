---
name: core-dev
description: "Use when any coding, development, analysis, debugging, or code-related task is detected. Triggers on: implementing features, fixing bugs, refactoring code, reviewing diffs, investigating errors, evaluating approaches, or making architecture decisions."
user-invocable: false
allowed-tools: Glob, Grep, Read, Bash, Skill, AskUserQuestion
---

# Development Workflow Router

Iron Rules: `../../shared/iron-rules.md`.

**Active plan?** `Grep("Status: In Progress", path="docs/plans/", glob="*.md")`. Match → read the plan, resume at its listed phase (skip language detection — the plan specifies it), but still invoke the language skill for implementation rules. No match → continue.

**Brainstorming gate.** Default: invoke `development-skills:brainstorming` with the user's full request as args. Skip ONLY if all three hold: fully reversible with low effort; ONE obvious forced approach (not *"I think this is right"*); WHY doesn't affect HOW. User bypass (*"skip brainstorming"*, *"just code it"*, *"I already know the approach"*) → respect it; *"Fast"* is NOT a bypass.

Don't rationalize skipping it: *"user said exactly what to do"* — WHAT ≠ HOW, multiple approaches → brainstorm; *"I already have a good approach"* — first ≠ best; *"just analysis/investigation"* — analysis IS development.

Specialized routes: bug fix with error / stack trace → `development-skills:debugging`; test creation / strategy / coverage → `development-skills:create-test`.

**Language.** After brainstorming returns (or a skip-decision), detect and invoke the matching skill before writing code:

- `next.config.*`, `app/{layout,page}.tsx`, `@raycast/api`, `vite.config.*` + react, `*.tsx` + react dep → `frontend-dev`
- `*.py`, `requirements*.txt`, `pyproject.toml` → `python-dev`
- `*.ts`, `tsconfig.json` (no frontend signals) → `typescript-dev`
- `*.java`, `pom.xml`, `build.gradle`, `*.kt` → `java-dev`
- `*.swift`, `Package.swift` → `swift-dev`

Frontend signals trump pure TypeScript.
