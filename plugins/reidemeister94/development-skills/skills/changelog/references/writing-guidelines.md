# Changelog writing rules

This file is the policy shared by all `/changelog` actions.

## Entries

- Use an imperative description of at most 15 words. Match existing capitalization, punctuation, and issue/PR-reference style.
- Record user-visible features, breaking changes, meaningful bug or security fixes, API or behavior changes, and significant dependency, architecture, infrastructure, or CI changes.
- Skip formatting, lint, merges, WIP, typos, comments, small refactors, patch dependency bumps, internal doc tweaks, and reverts of unshipped work.
- Aggregate one macro change into one entry; a large feature may need two or three.

## Conventional Commits

| Prefix | Category |
|---|---|
| `feat:` | Added |
| `fix:` | Fixed |
| `perf:` or architectural `refactor:` | Changed |
| `revert:` of a shipped feature | Changed |
| `chore:` `style:` `test:` `docs:` `ci:` `build:` | Skip by default |
| `BREAKING CHANGE:` or `<type>!:` | Its normal category, prefixed `**BREAKING**` |

## Release bump

| `[Unreleased]` content | 1.0.0 or later | pre-1.0 |
|---|---|---|
| `**BREAKING**`, or public API under `Removed` | Major | Minor by default |
| `Added` or `Changed`, without breaking entries | Minor | Minor |
| Only `Fixed`, `Security`, or `Deprecated` | Patch | Patch |

SemVer permits incompatible changes before 1.0. Default those to Minor; offer `1.0.0` only when the user deliberately declares the API stable.

Never remove an `[Unreleased]` entry, change a released section, or date `[Unreleased]`.
