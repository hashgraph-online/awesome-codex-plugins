---
name: release
description: Use when the user asks to release, version, tag, or publish.
---
# Release

Use only when the user asks to release.

1. Confirm version/bump.
2. Start from green tests and clean tree.
3. Update version files.
4. Move CHANGELOG `Unreleased` to `version - date`; create new `Unreleased`.

`<gate>` Steps 5-7 touch shared or irreversible state. Get explicit user approval before **each** step — never chain them on one confirmation. `</gate>`

5. Commit release edits.
6. Create annotated tag.
7. Push commit/tag, or publish.
