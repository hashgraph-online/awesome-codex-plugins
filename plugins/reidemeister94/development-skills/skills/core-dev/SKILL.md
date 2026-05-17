---
name: core-dev
description: "Use when any coding, development, analysis, debugging, or code-related task is detected. Triggers on: implementing features, fixing bugs, refactoring code, reviewing diffs, investigating errors, evaluating approaches, or making architecture decisions."
user-invocable: false
allowed-tools: Glob, Grep, Read, Bash, Skill, AskUserQuestion
---

# Development Workflow Router

Triage (PASS_THROUGH/LIGHT/FULL) is upstream in `using-development-skills`. If you're here, you're FULL. Iron Rules: `../../shared/iron-rules.md`.

## 1. Active plan?

`Grep("Status: In Progress", path="docs/plans/", glob="*.md")`. Match → read the plan file, resume at the phase listed (skip language detection — plan already specifies). Still invoke the language skill for implementation rules. No match → step 2.

## 2. Brainstorming gate

**Default: invoke `development-skills:brainstorming`** with the user's full request as args.

**Skip ONLY if all three hold:**

- Fully reversible in < 1 hour
- ONE obvious approach (forced shape, not *"I think this is right"*)
- WHY doesn't affect HOW

**Specialized routes:**

- Bug fix with error / stack trace → `development-skills:debugging`
- Test creation / strategy / coverage analysis → `development-skills:create-test`

**User bypass:** *"skip brainstorming"*, *"just code it"*, *"I already know the approach"* → respect it. *"Fast"* is NOT a bypass.

### Anti-rationalization

| Your thought | Reality |
|---|---|
| *"User said exactly what to do"* | WHAT ≠ HOW. Multiple approaches → brainstorm. |
| *"I already have a good approach"* | First approach ≠ best. Brainstorming costs nothing. |
| *"Just analysis / investigation"* | Analysis IS development. Brainstorm. |
| *"User confirmed, so my analysis was correct"* | Confirmation validates the decision, not the analysis. |

## 3. Language

After brainstorming returns (or after a skip-decision), detect language:

| Signal | Skill |
|---|---|
| `next.config.*`, `app/{layout,page}.tsx`, `@raycast/api`, `vite.config.*` + react, `*.tsx` + react dep | `frontend-dev` |
| `*.py`, `requirements*.txt`, `pyproject.toml` | `python-dev` |
| `*.ts`, `tsconfig.json` (no frontend signals) | `typescript-dev` |
| `*.java`, `pom.xml`, `build.gradle`, `*.kt` | `java-dev` |
| `*.swift`, `Package.swift` | `swift-dev` |

Frontend signals trump pure TypeScript. Invoke the matching skill before writing any code.
