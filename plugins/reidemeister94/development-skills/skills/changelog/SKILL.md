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

`$ARGUMENTS` contains `add` / `from-commits` (or `commits`) / `release` → that action; else infer from the request, and `AskUserQuestion` (`add | from-commits | release`) if still ambiguous.

## Step 2 — Pre-flight (all actions)

```bash
root=$(git rev-parse --show-toplevel 2>/dev/null) || root=.
ls "$root/CHANGELOG.md" 2>/dev/null
```

All actions read/edit `$root/CHANGELOG.md` (repo-root, never cwd-relative).

- Exists → `Read` it; note its style (compare-link footers? PR refs? capitalization?).
- Missing + `add`/`from-commits` → write the standard Keep a Changelog 1.1.0 skeleton (title + intro linking keepachangelog.com/en/1.1.0 and semver.org/spec/v2.0.0, then `## [Unreleased]`), then proceed.
- Missing + `release` → STOP: nothing to release; suggest `/changelog add` or `/changelog from-commits`.

## Step 3 — Insert under `[Unreleased]` (add, from-commits)

Via `Edit`, append `- <imperative description>` under the entry's `### <Category>` within `## [Unreleased]`, creating the subsection in Keep a Changelog's canonical order if absent. Obey the contract in `references/writing-guidelines.md` (never modify released sections, never date `[Unreleased]`).

## Step 4 — Run the action

`references/writing-guidelines.md` is the single source of truth for entry rules, the Conventional Commits map, and the SemVer bump table — load it for every action.

- **add** — entry from the user's text; else `AskUserQuestion` for category (the six Keep a Changelog categories) + a ≤15-word description. Tighten wording per writing-guidelines, then insert (Step 3).
- **from-commits** — see below.
- **release** — follow `references/release.md`.

### from-commits

The changelog, not git tags, is the source of truth for what shipped — derive entries, don't mirror the log.

1. **Range.** `git tag --sort=-version:refname | head -5`: ≥1 tag → `<latest-tag>..HEAD`. No tag but a prior `## [X.Y.Z]` section → `git log --grep="release.*X\.Y\.Z" -iE -1 --format=%H` for the lower bound. No baseline → `git rev-list --count HEAD`, print N, `AskUserQuestion` (`all N | last 30 | last 100 | other`). Never silently default to all commits.
2. **Gather.** `git log --oneline <range>`, then `git log --pretty=format:"%h %s%n%b%n---" <range>` (BREAKING footers live in bodies).
3. **Classify → filter → aggregate.** Per writing-guidelines: map prefixes to categories, keep macro-only changes, collapse a 10–20-commit feature into 1–3 entries. De-duplicate against existing `[Unreleased]` entries.
4. **Propose & confirm.** Show entries grouped by category, plus what was skipped/aggregated (one-line reasons). Get approval, then insert per Step 3.
