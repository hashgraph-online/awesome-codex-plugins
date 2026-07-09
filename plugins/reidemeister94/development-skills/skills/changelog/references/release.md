# changelog · release

Move `[Unreleased]` into a versioned section, reset `[Unreleased]`, maintain compare-link footers if present, print suggested git commands. Load `writing-guidelines.md` (SemVer table). Pre-flight: `SKILL.md` Step 2 (missing/empty file stops there). Edits `CHANGELOG.md` only.

## 1 — Validate & detect

- `[Unreleased]` must have ≥1 entry, else STOP (suggest `add` / `from-commits`).
- **Previous version** = topmost `## [X.Y.Z]` heading (the changelog is the source of truth — NOT git tags, NOT the SemVer max). None → `0.0.0`.
- Note whether the file has `[X.Y.Z]: <url>` compare-link footers.

## 2 — Bump

Apply the SemVer table in `writing-guidelines.md`; compute the next version.

## 3 — Confirm

`AskUserQuestion` (include free-text "Other"): recommend the inferred bump (state why — breaking / feat-class / fix-only) and offer Patch/Minor/Major. Pre-1.0 with a BREAKING entry → also offer non-recommended `Promote to 1.0.0`.

## 4 — Apply (`Edit`)

- Rename `## [Unreleased]` → `## [X.Y.Z] - <date>` (`date +%Y-%m-%d`); insert a fresh empty `## [Unreleased]` above it. Don't touch released entries.
- **Footers — only if the file already has them:** build the new line by mimicking an existing `[<prev>]: <url>` line's structure (it already encodes this host's correct shape — operand order, dot count, path), substituting versions; repoint the `[Unreleased]` footer from the new version. No footers → add none.

## 5 — Suggested commands

If version files exist (package.json, pyproject.toml, plugin.json, Cargo.toml, …), tell the user to bump them to `X.Y.Z` first — this skill doesn't, and a CHANGELOG-only commit leaves versions inconsistent. Then print (state the skill ran none):

```
git add CHANGELOG.md   # + any version-file edits
# author the release commit via /commit
git tag vX.Y.Z
git push && git push origin vX.Y.Z   # specific tag — avoid `git push --tags`
```
