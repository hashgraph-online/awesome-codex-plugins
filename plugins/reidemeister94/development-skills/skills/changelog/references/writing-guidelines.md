# Changelog Writing Guidelines

Single source of truth for `/changelog`. This skill's specific rules and policy choices only — not a Keep a Changelog / SemVer primer.

## Entry rules

- ≤15 words. Match the file's existing capitalization/punctuation/ref style — don't add PR/issue refs if the file has none.
- **Macro-level only.** Document features, breaking changes, noticeable bug/security fixes, API/behavior shifts, AND significant technical changes (major dependency upgrades, architecture refactors, infra/CI shifts, removed modules).
- **Skip sub-macro noise:** formatting/lint runs, merges, WIP, comment/typo fixes, micro-refactors, patch-level dep bumps, internal doc tweaks, reverts of unshipped or in-branch work.
- **Aggregate:** commits belonging to one macro change → one entry (a 10–20-commit feature → 1–3 entries).

## Conventional Commits → category (for `from-commits`)

| Prefix | Category |
|---|---|
| `feat:` | Added |
| `fix:` | Fixed |
| `perf:`; `refactor:` (only if architecturally meaningful) | Changed |
| `revert:` (only if reverting a previously-shipped feature) | Changed |
| `chore:` `style:` `test:` `docs:` `ci:` `build:` | skip by default |
| `BREAKING CHANGE:` footer or `<type>!:` | place under its category, prefix the entry `**BREAKING**`, and bump per the table below |

## SemVer bump (for `release`)

| `[Unreleased]` content | ≥1.0.0 | pre-1.0 (0.y.z) |
|---|---|---|
| Any `**BREAKING**`, or `### Removed` of a public API | MAJOR | MINOR (default) |
| Any `### Added`/`### Changed` (no breaking) | MINOR | MINOR |
| Only `### Fixed`/`### Security`/`### Deprecated` | PATCH | PATCH |

**Pre-1.0 (0.y.z):** SemVer 2.0.0 section 4 lets anything change in `0.y.z`, so a BREAKING entry does NOT force a major bump. Default to MINOR; offer `1.0.0` only as a deliberate, non-recommended "API now stable" choice.

Never remove existing `[Unreleased]` entries, modify released sections, or date `[Unreleased]`.
