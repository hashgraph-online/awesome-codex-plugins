# Release Cut and Version Bumps

Operational addendum to `SKILL.md`. Covers two cases the main flow does not address directly:

1. Cutting a release at a non-HEAD commit (skipping post-boundary work).
2. AgentOps-specific version-bump targets that the generic Step 7 detection does not catch.

## Cutting at a Non-HEAD Commit

The skill's main flow assumes `HEAD` is the release boundary. When the next release should not include the most recent commits on `main` — for example, when a new architectural epic has started landing but belongs in the next major — check out a release branch at the desired boundary SHA *before* invoking `/release`:

```bash
git checkout -b release/v<version> <boundary-sha>
/release <version>
```

The skill operates on `HEAD` of the current branch, so this makes `<boundary-sha>` the effective range endpoint without any flag changes. Step 2's range computation (`<last-tag>..HEAD`) yields `<last-tag>..<boundary-sha>` because `HEAD` now points at the boundary.

What lands where:

- The release commit from Step 12 lands on `release/v<version>`.
- The annotated tag from Step 13 points to that release commit.
- `main` is untouched. The post-boundary commits remain there and become the starting range for the next release.

After tagging, the user decides whether to:

- **Merge `release/v<version>` back into `main`** — the release commit (CHANGELOG entry, version bumps, curated notes, audit) becomes part of mainline history. Use a no-fast-forward merge so the release commit is preserved as a distinct node.
- **Leave the branch parallel** — the tag is permanent and CI can still build from it regardless of the branch's life. The next release on `main` will simply not include the release-commit artifacts; they live only on the tag's tree.
- **Delete the branch after tagging** — equivalent to "leave parallel," since the tag pins the SHA. Reduces branch clutter.

### When to use which path

- If the boundary work and the post-boundary work will both land in production reasonably soon, merge back so `CHANGELOG.md` and version files stay in lock-step with mainline.
- If the post-boundary work will be heavily reworked or split before the next release, leave parallel and re-author the CHANGELOG entry as part of the next release commit on the new mainline.

## AgentOps-Specific Version-Bump Targets

The generic Step 7 detection (`package.json`, `pyproject.toml`, `Cargo.toml`, `*.go`, `version.txt`, `VERSION`, `.goreleaser.yml`) does not cover the manifests and docs that AgentOps releases must keep in lock-step. The v2.39.0 audit (`docs/releases/2026-04-27-v2.39.0-audit.md`) is the canonical list of files touched. As of v2.39.0:

| File | Field / Pattern | Notes |
|------|-----------------|-------|
| `CHANGELOG.md` | New `## [X.Y.Z] - YYYY-MM-DD` block under `## [Unreleased]` | Already handled by Step 9, listed here for completeness. |
| `docs/CHANGELOG.md` | Mirror of the new `## [X.Y.Z]` block | The docs site reads this copy. Keep identical to the root `CHANGELOG.md` entry. |
| `.claude-plugin/plugin.json` | Top-level `"version": "X.Y.Z"` | AgentOps plugin manifest consumed by the Claude Code marketplace. |
| `.claude-plugin/marketplace.json` | `metadata.version` | Manifest-level marketplace version. |
| `.claude-plugin/marketplace.json` | `plugins[0].version` | Per-plugin version inside the same file. Both fields must move together. |
| `docs/comparisons/vs-gsd.md` | `latest AgentOps version vX.Y.Z` | Comparison page references the current shipped version. |
| `docs/comparisons/vs-compound-engineer.md` | `latest AgentOps version vX.Y.Z` | Same pattern. |
| `docs/comparisons/vs-claude-flow.md` | `latest AgentOps version vX.Y.Z` | Same pattern. |

When new comparison docs or manifests are added, extend this list. Audit by comparing against the most recent `docs/releases/YYYY-MM-DD-v<version>-audit.md`.

### Verification

Before the release commit, grep for the old version to catch missed spots:

```bash
git grep -nE 'v?2\.39\.0' -- \
  '.claude-plugin/*.json' 'docs/comparisons/vs-*.md' 'CHANGELOG.md' 'docs/CHANGELOG.md'
```

Any remaining hit that is *not* a historical reference (e.g., a CHANGELOG row dated to a prior release) is a missed bump.
