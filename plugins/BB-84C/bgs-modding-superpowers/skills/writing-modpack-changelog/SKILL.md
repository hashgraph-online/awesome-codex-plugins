---
name: writing-modpack-changelog
description: "Use when cutting a modpack release. Creates <project>/docs/release-changelog.md if absent; appends a new version section with grouped changes. Triggers - 'cut a release', 'release notes', 'changelog', 'v1.2.3 changes', 'what changed since last version'."
---

## Overview

The modpack release changelog is the user-visible record of what changed between releases, grouped by semantic category: Added, Changed, Fixed, Removed, and Compatibility. This skill replaces the deleted `templates/modpack/release-changelog.md` template by creating `<project>/docs/release-changelog.md` at runtime, then inserting a new version section whenever the curator cuts a release.

## When to Use

| Use this skill when... | Result |
| --- | --- |
| The user says "cut a release", "release notes", "changelog", or "what changed since last version" | Create or update the release changelog. |
| A target version is being prepared for Nexus, ModDB, a Discord post, a GitHub release, or another player-facing surface | Produce grouped, readable release notes. |
| The user wants changes since the last tag, version, or release section | Summarize those changes into semantic buckets. |
| The user has finished a modpack milestone | Insert a new version section newest-first. |
| The user asks whether the release is major, minor, or patch | Suggest a version bump based on modpack impact. |

## When NOT to Use

| Do not use this skill when... | Use instead |
| --- | --- |
| The user made a random working change and wants to remember it later | `writing-modpack-devlog` |
| The user wants a single-mod curator note | `writing-modpack-devlog` |
| The user asks for plugin inspection or conflict resolution | `xedit-automation` or `xedit-conflict-audit` first. |
| There is no release boundary, version, tag, or player-facing summary intent | Keep working; do not invent a release. |
| The user needs to set up the modpack project structure first | `setting-up-bgs-modding-environment` |

## Rules

<EXTREMELY-IMPORTANT>
This skill writes release notes for humans. It does not install mods, alter game files, change load order, publish to Nexus, or open a release page. Draft the changelog locally; any public posting or release publication requires explicit user confirmation outside this skill.
</EXTREMELY-IMPORTANT>

1. Detect the modpack project root before writing.
   - If the user provides `<modpack_project_root>`, use it.
   - If the current working directory looks like a modpack directory because it already has `Data/`, `profiles/`, or `docs/`, default to `pwd` and tell the user what default you used.
   - Otherwise ask once: "Which modpack project root should I use? I can default to the current directory if this is the project root."
2. Locate `<project>/docs/release-changelog.md`.
   - If `<project>/docs/` does not exist, create it.
   - If `release-changelog.md` is missing, create it before inserting the version.
3. On first creation, use this header shape:
   - `# <Project Name> Release Changelog`
   - One-line intro: `Player-facing release notes for <Project Name>. Newest releases are listed first.`
   - `## Releases`
4. Determine the target version.
   - If the user provides a version, use it exactly after checking that it is not already present.
   - If the user does not provide a version, read the newest release heading and ask for the new version once.
   - Suggest a semver bump: major for load-order-breaking or save-breaking changes, minor for added mods or compatibility tweaks, patch for fixes only.
5. Use the current local date for the release date unless the user provides a specific release date.
   - Version headings use `## <version> (<release-date>)`.
   - Use `YYYY-MM-DD` for release dates.
6. Each version section must use semantic buckets:
   - `### Added`
   - `### Changed`
   - `### Fixed`
   - `### Removed`
   - `### Compatibility`
7. Omit empty buckets.
   - Do not leave placeholder headings such as `### Removed` with "None" under them unless the user explicitly wants a full template.
8. Insert versions newest-first under `## Releases`.
   - Insert the new version immediately below `## Releases`.
   - If the file already uses oldest-first and the user wants to preserve it, follow the existing convention and note that choice.
9. Optionally consume the dev-log.
   - If `<project>/docs/dev-log.md` exists, offer to summarize entries since the last release into the appropriate buckets.
   - The user must confirm or edit the proposed summary before you write it into the changelog.
   - Do not blindly convert every dev-log entry into player-facing copy; curator noise stays in the dev-log.
10. Write for players, not for internal tooling.
    - Keep entries concrete and readable.
    - Avoid private debugging details, raw conflict jargon, and internal agent process notes.
    - Mention mod names when they help users understand compatibility or upgrade risk.
11. Do not duplicate an existing version.
    - If the target version heading already exists, ask whether to amend that section or choose a new version.
    - Do not insert a second `## <version>` heading.
12. After writing, report the file path, version, release date, buckets included, and whether dev-log entries were consumed.

## Quick Reference

| Field | Canonical shape | Example |
| --- | --- | --- |
| File | `<project>/docs/release-changelog.md` | `docs/release-changelog.md` |
| Version heading | `## <version> (<release-date>)` | `## v1.4.0 (2026-06-01)` |
| Bucket heading | `### Added`, `### Changed`, `### Fixed`, `### Removed`, `### Compatibility` | `### Compatibility` |
| Entry style | Short player-facing bullet | `- Added a patch for Example Weather and Example Lighting.` |
| Ordering | Newest release first under `## Releases` | `v1.4.0` above `v1.3.2` |

Canonical version shape:

```markdown
## v1.4.0 (2026-06-01)

### Added

- Added Example Weather Overhaul and its modpack patch.

### Changed

- Rebalanced the early-game survival settings for slower hunger and thirst gain.

### Fixed

- Fixed missing workshop keywords in the settlement compatibility patch.

### Compatibility

- Added compatibility notes for Example Lighting Overhaul users upgrading from v1.3.x.
```

## Examples

### Bad

```markdown
Changed a bunch of stuff:
- new weather
- fixed bugs
- removed old patch
```

This has no version, no release date, no grouping, and no signal about compatibility risk.

### Good

```markdown
## v1.4.0 (2026-06-01)

### Added

- Added Example Weather Overhaul with a curated modpack patch.

### Changed

- Updated settlement lighting balance in the downtown cells.

### Fixed

- Fixed missing workshop keywords caused by the lighting compatibility patch.

### Removed

- Removed the obsolete Example Weather Hotfix; its changes are now included upstream.

### Compatibility

- Save-compatible for existing v1.3.x users, but users with custom lighting patches should rebuild their conflict patch.
```

This section gives players the version, date, grouped changes, and upgrade risk in one place.

## Common Mistakes

- Using the changelog for rough working notes that belong in the dev-log.
- Forgetting the version or release date.
- Dumping ungrouped bullets under one heading.
- Leaving empty bucket headings in the final changelog.
- Copying raw dev-log text without translating it for players.
- Hiding compatibility or save-risk information because it sounds negative.
- Creating duplicate version headings.
- Asking repeated version questions instead of suggesting a semver bump.
- Publishing release notes directly instead of drafting them for user review.
- Overstating changes with marketing language instead of concrete release facts.

## Rationalizations

| Excuse | Reality |
| --- | --- |
| "The dev-log already says what changed." | The dev-log is curator history. The changelog is player-facing release communication. They need different detail and tone. |
| "A single bullet list is faster." | Grouped buckets let users scan for added content, fixes, removals, and compatibility risk. |
| "Empty headings show that we considered every category." | Empty headings are noise in release notes. Omit empty buckets unless the user asked for a full template. |
| "I do not know the version, so I will invent one." | Ask once and suggest a bump. Version numbers are release authority, not filler text. |
| "The conflict details are important, so I will paste them all." | Players need the effect and upgrade risk. Keep raw conflict evidence in the dev-log or artifacts. |
| "This is just a patch release, so no changelog is needed." | Patch releases still need a record of what was fixed and whether users should update. |
| "Compatibility notes make the release look risky." | Hidden risk is worse. Clear compatibility notes reduce support burden. |
| "The user said release notes, so I can post them." | This skill drafts local changelog text. Public posting is a separate confirmed action. |

## See also

- `writing-modpack-devlog` - use for curator-facing chronological work records.
- `setting-up-bgs-modding-environment` - use when the modpack project root or docs structure must be established first.
