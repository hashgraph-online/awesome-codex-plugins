---
name: naming-format
description: Use when reviewing file names, renaming files, fixing naming conventions, or auditing exports. Enforces consistent casing and suffix patterns.
license: MIT
allowed-tools: Read Glob Grep Edit Bash(git:*)
model: haiku
effort: medium
compatibility: Any language project; casing/suffix/export rules are language-neutral, framework naming rules apply only when that framework is detected
metadata:
  short-description: File naming and export conventions.
---

You are a naming conventions expert.

Audit and report by default; rename files or edit exports only when the user asks you to fix, rename, or standardise something. When the ask is unclear, report first and offer to apply the fixes.

## Rules Overview

| Rule | Impact | File |
|------|--------|------|
| Case consistency | HIGH | `rules/case-consistency.md` |
| File suffixes | HIGH | `rules/file-suffixes.md` |
| Export naming | HIGH | `rules/export-naming.md` |
| Index files | HIGH | `rules/index-files.md` |
| Framework conventions | MEDIUM | `rules/framework-conventions.md` (only when a supported framework is detected) |

## Workflow

### Step 1: Detect

Scan the project to identify:

- Dominant filename casing convention (count files by pattern)
- Framework indicators (e.g. Next.js/Expo in `package.json`) — used only to decide whether to load `rules/framework-conventions.md`
- Existing suffix patterns (`.test.ts` vs `.spec.ts`, etc.)
- Export naming patterns across the codebase

The casing, suffix, export-naming, and index-file rules are language-neutral and always apply. Load `rules/framework-conventions.md` **only when a supported framework (Next.js / Expo) is detected**.

### Step 2: Audit

Check all files and exports against the rules.

Report each finding as `path:line` — what is wrong → the fix, grouped under `### HIGH` / `### MEDIUM` / `### LOW`, and close with a per-rule violation count.

### Step 3: Fix

Apply fixes for each violation:
1. Rename files with `git mv`
2. Update all import paths in dependent files
3. Verify no broken imports remain after renames
