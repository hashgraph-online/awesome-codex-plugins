# Changelog as a Research Artifact

> A changelog is not marketing copy and not a diff dump — it is an orientation layer for the next agent (or human) who has to navigate the project's history. This reference describes how to produce a changelog that survives that role. Read alongside [`release-notes.md`](release-notes.md), which covers the user-facing notes file separately.

The `$release` skill produces two distinct artifacts per release: `CHANGELOG.md` (the durable history) and `docs/releases/YYYY-MM-DD-v<version>-notes.md` (the curated GitHub Release body). They have different audiences, different shapes, and different lifetimes.

---

## Two artifacts, two audiences

| Artifact | Audience | Lifetime | Optimised for |
|---|---|---|---|
| `CHANGELOG.md` | Future agents, contributors, archaeology | Permanent, append-only | Coverage, evidence links, navigability |
| `docs/releases/*-notes.md` | GitHub feed readers, casual users | Per-release | Plain-English impact, scannable in 15 seconds |

The single biggest mistake is to copy one into the other. The release notes are a curated, jargon-stripped distillation; the changelog is the durable record of what shipped. The `$release` skill enforces this by writing two files in two steps — never duplicate the bullets between them.

---

## What the changelog has to answer

A useful changelog lets another agent answer four questions without reading the diff:

1. What materially changed in this version?
2. When did it ship (release vs plain tag)?
3. Why did it change (which workstream / issue drove it)?
4. Which commits are the right entry points for deeper inspection?

If a section in your changelog cannot answer any of these, it is padding.

---

## Structured sections

A changelog entry per version follows the [Keep a Changelog](https://keepachangelog.com/) shape (Added / Changed / Fixed / Removed / Deprecated / Security). The section names are non-negotiable for tooling; the content style adapts to the project.

For larger releases, layer a thematic structure on top:

```markdown
## [1.7.0] - 2026-05-03

### Added
- <capability-level entries with workstream links>

### Changed
- <capability-level entries>

### Fixed
- <each fix with the issue ID it closed>
```

For a release that lands a multi-week epic, prefer a short narrative paragraph above the Added/Changed sections that names the capability wave. Without that paragraph, the bullets read as a flat diff dump and lose the reason the changes belong together.

---

## Breaking-change callouts

Breaking changes need a structural callout, not just a `BREAKING:` prefix buried in a bullet. Two patterns work:

**Inline callout block** — a bold lead-in inside the section, with the migration step as a sub-bullet:

```markdown
### Changed
- **BREAKING:** `ao goals init` now requires `--mode {yaml,md}`. Existing
  invocations without `--mode` will fail.
  - Migration: pass `--mode md` to retain the previous default.
```

**Dedicated section** — for releases with multiple breaking changes, a `### Breaking Changes` block above Added with a numbered list of "what broke / how to migrate" pairs.

Either pattern surfaces the change to a downstream consumer who is grepping the file for "BREAKING" before upgrading. Burying breaking changes inside narrative is the most common reason a major-version bump silently breaks a downstream agent.

---

## Release vs tag distinction

A git tag and a published GitHub Release are not the same artifact. The changelog must be honest about this:

- A tag with no Release page is a tag. Mark it as such.
- A draft Release is not a published Release. Do not link to it as if it were.
- A published Release exists when `gh release view <tag>` returns a status of `published`.

For the `$release` skill, the in-repo state is the tag plus the curated notes file. CI is what publishes the Release. If a release run failed and never published, the tag still exists — the changelog should not pretend a Release page exists at that tag.

---

## Agent-readable formatting

The changelog is consumed by tooling more often than people. A few formatting rules pay back disproportionately:

- **Live commit URLs**, not bare hashes. `[`abc1234`](https://github.com/<org>/<repo>/commit/abc1234567...)` lets an agent (or human) jump to the commit page in one click.
- **Issue tracker links scoped to the record**, not to a search. Link to `.beads/issues.jsonl#L<line>` or to the specific issue page, not to a repo-wide query.
- **Stable section anchors.** Keep the `## [X.Y.Z]` heading shape exact so downstream tooling (`extract-release-notes.sh`, archaeology scripts) can grep reliably.
- **No bare dates in bullets.** A bullet that says "fixed last Tuesday" loses meaning the moment the next release ships. Either omit the date or use ISO-8601.
- **No author names.** They are noise inside the changelog; git blame retains them where they belong.

---

## Anti-patterns to refuse

| Don't | Do |
|---|---|
| Copy CHANGELOG bullets into the release notes | Curate plain-English bullets for the notes; keep the changelog as the durable record |
| Pretend every tag is a published release | Distinguish tags from Releases explicitly when both exist |
| Drop a breaking change into a generic "Changed" bullet | Use a callout block with a migration step |
| Link bare commit hashes | Link the commit URL so navigation is one click |
| Wait until release day to write the entry | Maintain `## [Unreleased]` continuously so the entry is mostly written by tag time |

---

## Validation

A changelog entry is good enough to ship when:

- [ ] Section headings exactly match Keep a Changelog (`Added`, `Changed`, `Fixed`, `Removed`, `Deprecated`, `Security`)
- [ ] No empty sections (omit a section rather than leaving it blank)
- [ ] Every breaking change has a callout block with migration guidance
- [ ] At least one workstream / issue link per major bullet for releases that closed an epic
- [ ] No author names, no bare commit hashes, no relative dates
- [ ] The corresponding `docs/releases/YYYY-MM-DD-v<version>-notes.md` is curated separately, not copy-pasted

The `$release` skill's Step 8 (user review) is the place to apply this checklist — once the entry is written and the user has confirmed, mutating it post-tag breaks the tagged-tree contract.

---

> Pattern adopted from `changelog-md-workmanship` (ACFS skill corpus). Methodology only — no verbatim text.
