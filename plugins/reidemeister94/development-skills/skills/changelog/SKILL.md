---
name: changelog
description: "Use when the user asks to manage a project's CHANGELOG.md — add an entry, derive entries from git commits, or cut a release — or runs /changelog. Follows Keep a Changelog 1.1.0 and Semantic Versioning 2.0.0. Action selected via argument: add | from-commits | release."
user-invocable: true
allowed-tools: Read, Edit, Write, Bash, AskUserQuestion
---

# changelog

Manage `CHANGELOG.md` per Keep a Changelog 1.1.0 + SemVer 2.0.0. Three actions: **add** (one hand-written entry), **from-commits** (derive from Conventional Commits), **release** (cut a version).

Edits `CHANGELOG.md` ONLY — never version files, never `git tag`/`git commit`. `release` prints suggested commands.

## Step 1 — Resolve the action

Read `$ARGUMENTS`: contains `add` / `from-commits` (or `commits`) / `release` → that action. Empty or unrecognized → infer from the user's request. Still ambiguous → `AskUserQuestion` with `add | from-commits | release`.

## Step 2 — Pre-flight (all actions)

```bash
root=$(git rev-parse --show-toplevel 2>/dev/null) || root=.
ls "$root/CHANGELOG.md" 2>/dev/null
```

All actions read/edit `$root/CHANGELOG.md` (the repo-root file — never a bare cwd-relative path).

- Exists → `Read` it; note its style (compare-link footers? PR refs? capitalization?).
- Missing + action `add`/`from-commits` → write this skeleton, then proceed:

  ```markdown
  # Changelog

  All notable changes to this project will be documented in this file.

  The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
  and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

  ## [Unreleased]
  ```

- Missing + action `release` → STOP: nothing to release; suggest `/changelog add` or `/changelog from-commits`.

## Step 3 — Insert under `[Unreleased]` (add, from-commits)

Via `Edit`: ensure `## [Unreleased]` exists (after the boilerplate, before the first `## [X.Y.Z]`); put the entry under its `### <Category>`, creating the subsection in Keep a Changelog's canonical category order if absent; append `- <imperative description>`. Never modify a released section; never date `[Unreleased]`.

## Step 4 — Run the action

Load the matching reference and follow it: add → `references/add.md` · from-commits → `references/from-commits.md` · release → `references/release.md`.

`references/writing-guidelines.md` is the single source of truth for entry rules, the Conventional Commits map, and the SemVer bump table — load it when an action says to.
