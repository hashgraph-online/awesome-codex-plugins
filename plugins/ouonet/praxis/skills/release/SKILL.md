---
name: release
description: Use when the user asks to release, version, tag, or publish.
---
# Release

Use only when the user asks to release.

If `topology=multi-module` (triage announcement or coordinator spec/plan declaration), read `../references/multi-module.md`. Release only the exact coordinator revision set that passed integration. Determine version and dependency order per repository, and keep the existing approval gates for each repository's commit, tag, push, or publish. A completed change set does not itself authorize a release.

1. Confirm version/bump.
2. Start from green tests and clean tree.
3. Update version files.
4. Move CHANGELOG `Unreleased` to `version - date`; create new `Unreleased`.

`<gate>` Steps 5-7 touch shared or irreversible state. Get explicit user approval before **each** step — never chain them on one confirmation. `</gate>`

5. Commit release edits.
6. Create annotated tag.
7. Push commit/tag, or publish.
