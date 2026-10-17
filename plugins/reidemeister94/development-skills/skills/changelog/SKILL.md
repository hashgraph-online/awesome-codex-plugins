---
name: changelog
description: "Add CHANGELOG.md entries, derive them from commits, or cut a Keep a Changelog and SemVer release."
user-invocable: true
allowed-tools: Read, Edit, Write, Bash, AskUserQuestion
---

# changelog

Manage `CHANGELOG.md` per Keep a Changelog 1.1.0 and SemVer 2.0.0:

- **add:** one entry;
- **from-commits:** derive entries from Conventional Commits;
- **release:** cut a version.

Edit only `CHANGELOG.md`. Never change version files, commit, or tag; `release` prints suggested commands.

## Step 1 — Resolve the action

Resolve `add`, `from-commits` (`commits`), or `release` from `$ARGUMENTS` or the request; ask if ambiguous.

## Step 2 — Pre-flight (all actions)

```bash
root=$(git rev-parse --show-toplevel 2>/dev/null) || root=.
ls "$root/CHANGELOG.md" 2>/dev/null
```

Always use `$root/CHANGELOG.md`, never a cwd-relative path.

- Existing: read and preserve style.
- Missing for `add`/`from-commits`: create the standard linked title, intro, and `## [Unreleased]` skeleton.
- Missing for `release`: stop and suggest `/changelog add` or `/changelog from-commits`.

## Step 3 — Insert under `[Unreleased]` (add, from-commits)

Append `- <imperative description>` to its category under `[Unreleased]`, creating the category in canonical order. Never edit released sections or date `[Unreleased]`.

## Step 4 — Run the action

Load [writing guidelines](references/writing-guidelines.md) for entry rules, commit mapping, and SemVer bumps.

- **add** — use the user's text or ask for one of the six categories and a ≤15-word description; tighten and insert it.
- **from-commits** — follow the process below.
- **release** — follow `references/release.md`.

### from-commits

The changelog, not git tags, is the source of truth for what shipped — derive entries, don't mirror the log.

1. **Range:** use `<latest-tag>..HEAD`; without tags, find the commit for the latest released section. Without either baseline, show the commit count and ask for all, last 30, last 100, or another range. Never silently choose all.
2. **Gather:** inspect subjects and bodies; breaking footers may be in bodies.
3. **Derive:** map, filter, aggregate, and deduplicate per the guidelines. Collapse a 10–20-commit feature into 1–3 user-facing entries.
4. **Confirm:** show grouped proposals plus skipped or aggregated items with reasons, then insert only after approval.
