---
name: changelog
description: 'Record shipped work in the monthly changelog (append-only). Use when something ships or when asked "what changed", "add to changelog", "release notes", or "what shipped this month".'
---

# changelog

The memory of the knowledge base. Every month gets one file; history is **append-only**. This is what the SessionStart hook surfaces so the agent starts each session knowing recent work. Pairs with [`author`](../author/SKILL.md) and [`router`](../router/SKILL.md).

> Golden rule: **never delete or rewrite shipped history.** Reversals get a *new* entry, not an edit.

## Writing style (enforce)
Direct, tech + business. No filler. Outcome first.
- Each entry = a small table (Outcome / Delivered / Business impact / Commits). No narrative paragraphs.
- Summary = 4 bullets max: release type, biggest business change, biggest technical change, prod risk/action.
- Concrete only: feature names, paths, hashes, numbers. Cut adjectives.

---

## 1 — One file per month

`changelog/(mmm-yy).md` — lowercase 3-letter month + 2-digit year: `(apr-26).md`, `(may-26).md`.
`changelog/README.md` is the index: a table of `| Month | Highlights |`, newest first.

Link to a month file (parens need angle brackets): `[may-26](<(may-26).md>)`.

---

## 2 — Anatomy of a month file

```markdown
# Month YEAR — <release / period title>

> Window: `<base>` (`hash`, date) → `<head>` (`hash`, date). Scope: `N` commits.

## Summary
- Release type: patch | feature | architectural
- Biggest business change: <one line>
- Biggest technical change: <one line>
- Risk / action for prod: <one line>

## What Changed

### 1. <Feature / theme>
| | |
|---|---|
| Outcome | <one line> |
| Delivered | <bullet; bullet> |
| Business impact | <one line> |
| Commits | `<hash>` <desc>; `<hash>` <desc> |

### 2. <next theme>
```

A reader skimming the `Outcome` rows alone should understand the release.

---

## 3 — The shipping flow (where changelog fits)

The roadmap (`plans/upcoming/`) and the changelog are two ends of one pipe:

```
plans/upcoming/{critical,now,next,later}.md   ── ships ──►   changelog/(mmm-yy).md
        (what's coming)                                        (what landed)
```

When something ships:
1. **Move** the line out of the `plans/upcoming/*` horizon — don't let shipped work linger there (it kills the roadmap's signal).
2. **Add / update** the entry in the current `changelog/(mmm-yy).md`.
3. **Cross-link**: the feature plan's `## What shipped` table references the changelog month; the ADR/spec stay linked from the plan.
4. If a known bug got fixed, move it from `reviews/bugs/open.md` to `reviews/bugs/fixed.md` with the commit ref.

`plans/upcoming/README.md` keeps a short "Recently shipped" pointer list to the last few months — **pointers only, no restating**.

---

## 4 — Generating an entry from git

To build a month/release entry, diff the two refs and group commits by theme:

```bash
# commits in head not yet in base, newest first
git log --no-merges --pretty='%h %ad %s' --date=short BASE..HEAD
# count for the scope line
git rev-list --count --no-merges BASE..HEAD
```

Then: cluster commits into 3–8 themes → write a `### N. Theme` block each → fill outcome / delivered / why / commits → write the Executive Summary last (it summarizes the blocks).

---

## 5 — Why append-only matters

The changelog is the project's long-term memory. An agent (or a new teammate) that reads the newest one or two month files gets the recent trajectory: what was built, why it mattered, which commits. Editing or pruning old months erases that trail. Superseded decisions are recorded as *new* lines that reference the old — the history of the change is itself information.
