---
name: release
description: 'Run release validation.'
---
# Release Skill

> **Purpose:** Take a project from "code is ready" to "tagged, pushed by the operator, and verified green on the exact tagged SHA."

Pre-flight validation, changelog from git history, version bumps across package files, release commit, annotated tag, curated release notes, and post-push exact-SHA CI verification. Local preparation is reversible. Publishing (including the GitHub Release page) is CI's job.

---

## Quick Start

```bash
$release 1.7.0                # full release: changelog + bump + commit + tag
$release 1.7.0 --dry-run      # show what would happen, change nothing
$release --check               # readiness validation only (GO/NO-GO)
$release                       # suggest version from commit analysis
```

---

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `version` | No | Semver string (e.g., `1.7.0`). If omitted, suggest based on commit analysis |
| `--check` | No | Readiness validation only — don't generate or write anything |
| `--dry-run` | No | Show generated changelog + version bumps without writing |
| `--skip-checks` | No | Skip pre-flight validation (tests, lint) |
| `--changelog-only` | No | Only update CHANGELOG.md — no version bumps, no commit, no tag |

---

## Modes

| Mode | Invocation | Behavior |
|---|---|---|
| **Full Release** | `$release [version]` | Pre-flight → changelog → release notes → version bump → user review → write → release commit → tag → push guidance → exact-SHA CI verification. |
| **Check** | `$release --check` | Pre-flight checks only; reports GO/NO-GO. Composable with `$vibe`. No writes. |
| **Changelog Only** | `$release X.Y.Z --changelog-only` | Updates `CHANGELOG.md` only — no version bumps, no commit, no tag. |

---

## Workflow

**Read [references/release-workflow-detail.md](references/release-workflow-detail.md) for the full per-step procedure** — bash commands, check tables, expected output, audit-record template, and worked examples. The index below is for orientation only; the agent must execute against `release-workflow-detail.md` for correctness.

1. **Pre-flight** — run `scripts/ci-local-release.sh` (blocking) plus version/lint/test/branch/changelog/SBOM/security checks. `--check` mode stops after this step.
2. **Determine range** — `<last-tag>..HEAD`. For non-HEAD cuts, see [references/release-cut-and-bump.md](references/release-cut-and-bump.md).
3. **Read git history** — `git log --oneline --no-merges <range>` plus stats for ambiguity resolution.
4. **Classify and group** — Added / Changed / Fixed / Removed for `CHANGELOG.md`. Notes prose uses the richer 8-label set per [references/release-notes.md](references/release-notes.md).
5. **Suggest version** — major if breaking, minor if features, patch if only fixes. Confirm with the user before proceeding.
6. **Generate changelog entry** — Keep-a-Changelog format, today's date, style-matched to the most recent existing entry.
7. **Detect and offer version bumps** — generic patterns (`package.json`, `pyproject.toml`, etc.) plus AgentOps-specific manifests per [references/release-cut-and-bump.md](references/release-cut-and-bump.md).
8. **User review** — show generated changelog and version diffs; ask the user to proceed. `--dry-run` stops here.
9. **Write changes** — `CHANGELOG.md` update + version file edits.
10. **Generate release notes** — curated `docs/releases/YYYY-MM-DD-v<version>-notes.md` per [references/release-notes.md](references/release-notes.md). MUST be staged before the release commit.
11. **Write audit trail** — `docs/releases/YYYY-MM-DD-v<version>-audit.md` resolved via `scripts/resolve-release-artifacts.sh`. Format in workflow-detail Step 16.
12. **Release commit** — `git commit -m "Release v<version>"` with all release artifacts staged.
13. **Tag** — annotated `git tag -a v<version> -m "Release v<version>"`.
14. **GitHub Release (CI handles this)** — do NOT `gh release create` locally; GoReleaser is sole creator.
15. **Post-push exact-SHA CI verification** — after the operator pushes, run `scripts/verify-release-ci.sh v<version>` and do not declare the release complete until it prints `GO release-ci`.
16. **Post-release guidance** — show push commands and the verification command; do NOT push.
17. **Audit trail format** — see workflow-detail for the markdown template.

---

## Boundaries

### What this skill does

- Pre-flight validation (tests, lint, clean tree, versions, branch)
- Changelog generation from git history
- Semver suggestion from commit classification
- Version string bumps in package files
- Release commit + annotated tag
- Release notes (highlights + changelog) for GitHub Release page
- Curated release notes for CI to publish on GitHub Release page
- Post-release guidance plus exact-SHA CI verification instructions
- Audit trail

### What this skill does NOT do

- **No publishing** — no `npm publish`, `cargo publish`, `twine upload`. CI handles this.
- **No building** — no `go build`, `npm pack`, `docker build`. CI handles this.
- **No pushing** — no `git push`, no `git push --tags`. The user decides when to push.
- **No CI triggering** — the tag push (done by the user) triggers CI.
- **No monorepo multi-version** — one version, one changelog, one tag. Scope for v2.

Everything this skill does is local and reversible:
- Bad changelog → edit the file
- Wrong version bump → `git reset HEAD~1`
- Bad tag → `git tag -d v<version>`
- Bad release notes → edit `docs/releases/*-notes.md` before push

---

## Universal Rules

- **Don't invent** — only document what git log shows
- **No commit hashes** in the final output
- **No author names** in the final output
- **Concise** — one sentence per bullet, technical but readable
- **Adapt, don't impose** — match the project's existing style rather than forcing a particular format
- **User confirms** — never write without showing the draft first
- **Local only** — never push, publish, or trigger remote actions
- **Not done at tag** — after the user pushes, verify a green `validate.yml` run for the exact tagged SHA and record the run id plus conclusion in the handoff or release audit notes.
- **Two audiences** — CHANGELOG.md is for contributors (file paths, issue IDs, implementation detail). Release notes are for feed readers (plain English, user-visible impact, no insider jargon). Never copy-paste the changelog into the release notes.

---

## Examples

**User says:** `$release 1.7.0`
Agent runs pre-flight → reads `v1.6.0..HEAD` git history → classifies commits → drafts CHANGELOG.md entry + curated release notes → detects version files (package.json, version.go, plugin manifests) → presents draft for review → on approval, writes files, creates release commit, creates annotated tag, prints push guidance, then after the user pushes verifies `scripts/verify-release-ci.sh v1.7.0` and records the run id/conclusion.

**User says:** `$release --check`
Agent runs all pre-flight checks and outputs a GO/NO-GO summary table. No writes.

**User says:** `$release` (no version)
Agent classifies commits and suggests a version (major if breaking, minor if features, patch if fixes only) with reasoning, then asks the user to confirm or override.

**User says:** `$release 1.7.0 --dry-run`
Agent shows what the changelog entry + version bumps would look like, then stops without writing.

See `references/release-workflow-detail.md` for the full per-step example narration.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| "No commits since last tag" error | Working tree clean, no new commits | Commit pending changes or skip release |
| Version mismatch warning | `package.json` and `go` version disagree | Manually sync before release, or pick one as source of truth |
| Tests fail during pre-flight | Breaking change not caught earlier | Fix tests, or use `--skip-checks` (not recommended) |
| Dirty working tree warning | Uncommitted changes present | Commit or stash before release |
| GitHub Release page body is empty | GoReleaser conflict with existing draft | CI deletes existing releases before GoReleaser runs; do NOT `gh release create` locally |
| `ci-local-release.sh` hangs on agents-hash | `~/.agents/patterns` is large | Set `AGENTS_HUB_OVERRIDE=/tmp/empty-hub` before invocation |

See `references/release-workflow-detail.md` for the full troubleshooting matrix.

## See Also

- [deps](../deps/SKILL.md) — Dependency audit and vulnerability scanning

When wiring or auditing the CI workflow that backs `--check` mode (or the tag-triggered release pipeline that consumes the curated notes), pull the relevant patterns from `references/gh-actions-ci-patterns.md` (general CI) or `references/gh-actions-release-automation.md` (tag-triggered, draft flow, asset upload). When generating the curated release-notes file or auditing CHANGELOG.md drift, treat the changelog as an orientation layer and use `references/changelog-as-research-artifact.md` for the structured-section, breaking-change-callout, and notes-vs-changelog rules.

For release-prep sessions that span package registries, deploy hosts, multi-repo sync, or platform-specific publishers, use `references/release-preflight-and-publishers.md` to separate local readiness from remote publishing and to preserve rollback evidence.

## Reference Documents

- [references/release-workflow-detail.md](references/release-workflow-detail.md) — full per-step procedure
- [references/release-cut-and-bump.md](references/release-cut-and-bump.md) — non-HEAD cut + AgentOps-specific bump targets
- [references/release-notes.md](references/release-notes.md) — curated notes format + product-area taxonomy
- [references/release-preflight-and-publishers.md](references/release-preflight-and-publishers.md)
- [references/release-cadence.md](references/release-cadence.md)
- [references/changelog-as-research-artifact.md](references/changelog-as-research-artifact.md)
- [references/gh-actions-ci-patterns.md](references/gh-actions-ci-patterns.md)
- [references/gh-actions-release-automation.md](references/gh-actions-release-automation.md)

## Local Resources

### references/

- [references/release-cadence.md](references/release-cadence.md)
- [references/release-notes.md](references/release-notes.md)
- [references/release-preflight-and-publishers.md](references/release-preflight-and-publishers.md)
- [references/release-cut-and-bump.md](references/release-cut-and-bump.md)
- [references/release-workflow-detail.md](references/release-workflow-detail.md)
- [references/gh-actions-ci-patterns.md](references/gh-actions-ci-patterns.md)
- [references/gh-actions-release-automation.md](references/gh-actions-release-automation.md)
- [references/changelog-as-research-artifact.md](references/changelog-as-research-artifact.md)

### scripts/

- `scripts/validate.sh`
