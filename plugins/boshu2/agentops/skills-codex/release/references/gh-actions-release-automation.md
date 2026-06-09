# GitHub Actions Release Automation

> Tag-triggered release patterns adapted for AgentOps. Read this when wiring or auditing the workflow that runs after `git push origin main --tags`. For pre-release validation patterns (matrix shape, caching, secrets), read [`gh-actions-ci-patterns.md`](gh-actions-ci-patterns.md) first.

The boundary between the `$release` skill and CI is sharp. The skill prepares (changelog, version bumps, commit, tag, curated notes). CI publishes (build, sign, upload, draft → publish). This file is about the CI half.

---

## Trigger surface

Release workflows are tag-triggered, never branch-triggered. Filter on the `v*` glob so semver tags fire the workflow and arbitrary internal tags do not.

```yaml
on:
  push:
    tags: ['v*']

permissions:
  contents: write   # required for GitHub Releases
  id-token: write   # required for sigstore / attestations
```

`workflow_dispatch:` is acceptable as a manual escape hatch. If you add it, gate the publish step on `github.event_name == 'push'` so a manual run cannot accidentally re-publish a release.

For the concurrency block, use `cancel-in-progress: false`. A second tag push during a release run must not cancel the in-flight run — the publish steps are not safely cancellable.

---

## Job graph

The minimum useful release graph is three jobs, each with a single concern:

| Job | Owns | Outputs |
|---|---|---|
| `resolve-version` | Strip `v` from `GITHUB_REF`, verify against in-tree version files | `version` |
| `build` | Cross-platform matrix; produces signed artifacts and checksums | uploaded artifacts |
| `publish` | Aggregates artifacts, drafts the release, attaches assets, flips draft → published | release URL |

Wiring `publish` to `needs: build` ensures a build failure on any matrix cell stops the release. Adding `needs: resolve-version` lets the build step see the resolved version without re-parsing `GITHUB_REF`.

---

## Tag-to-version contract

The release workflow must verify that the pushed tag matches the version strings the `$release` skill bumped locally. Drift here is silent and dangerous.

```yaml
- name: extract version
  id: ver
  run: echo "version=${GITHUB_REF#refs/tags/v}" >> "$GITHUB_OUTPUT"

- name: cross-check version files
  run: |
    file_v="$(cat VERSION | tr -d '\r\n')"
    if [[ "$file_v" != "${{ steps.ver.outputs.version }}" ]]; then
      echo "::error::VERSION ($file_v) does not match tag (${{ steps.ver.outputs.version }})"
      exit 1
    fi
```

For projects that use GoReleaser, the `.goreleaser.yml` reads the version from the git tag, so the in-tree files (`package.json`, `pyproject.toml`, `*.go`, `VERSION`) are the only place a mismatch can hide. Make the check explicit.

---

## Build matrix

For multi-platform binaries, the matrix lives only in the release workflow — CI does not need to spend minutes on every platform every push. The matrix shape mirrors the platforms you will actually ship; do not include cells you cannot test.

Native ARM runners (`ubuntu-24.04-arm`, `macos-14`) are mandatory for any project shipping ARM binaries. QEMU emulation is too slow for release-cadence work.

A single `build` job per matrix cell does three things: build the binary, create the archive (`tar -cJf` for Unix, `Compress-Archive` for Windows), generate the per-asset SHA-256 checksum. Upload all three as a named artifact so `publish` can collect them with `merge-multiple: true`.

---

## Asset upload and the GitHub Release

Use `softprops/action-gh-release@<sha>` for the release-creation step. The relevant inputs:

| Input | Purpose |
|---|---|
| `name:` | Display title (e.g., `v1.7.0`) |
| `tag_name:` | Defaults to the pushed ref; usually unset |
| `files:` | Glob of artifacts to attach |
| `body_path:` | Curated notes file (see below) |
| `draft:` | `true` while testing; `false` for the real publish |
| `generate_release_notes:` | `true` only when no curated notes file is committed |

Two patterns that interact badly:

- A local `gh release create --draft` plus GoReleaser in CI conflict — GoReleaser appends to whatever release page already exists at the tag, and the local draft wins on body content. The `$release` skill explicitly avoids the local draft.
- `generate_release_notes: true` together with `body_path:` will discard the curated notes. Pick one: curated body OR auto-generated, never both.

The `$release` skill's contract is that `docs/releases/YYYY-MM-DD-v<version>-notes.md` is committed before the tag, so the tagged tree contains it. CI reads that file and passes it to GoReleaser via `--release-notes` (or to `softprops/action-gh-release` via `body_path`).

---

## Draft-then-publish flow

For higher-stakes releases (Linux distro binaries, signed artifacts, package-manager fan-out), a two-stage flow lowers the risk of a half-finished release page:

1. The first run on the tag drafts the release with all assets attached.
2. A separate `publish` job (still in the same workflow, gated on artifact integrity checks) flips the draft to published.

Practically this looks like a `softprops/action-gh-release@<sha>` step with `draft: true` followed by a later step that calls `gh release edit <tag> --draft=false`. The intermediate state lets CI verify checksums, SBOM presence, and signature validity before the release is visible to consumers.

---

## Semantic version bump conventions

Do not encode version-bump logic in the release workflow. The `$release` skill already classifies commits and proposes a bump (Major / Minor / Patch) based on commit signals (BREAKING, `feat`, `fix`). Letting CI re-derive the version invites disagreement between local and remote signal.

What CI may legitimately do:

- Refuse a release tag that violates strict semver (`vX.Y.Z` with optional pre-release suffix).
- Refuse a release tag that does not strictly increase from the previous published release.
- Compute the previous tag via `git describe --tags --abbrev=0 HEAD^` for changelog-link generation.

What CI must not do:

- Auto-bump versions on a tag that is not present.
- Mutate `CHANGELOG.md` post-tag — the changelog at tag time is the contract.

---

## Notification fan-out

Once the release is published, fan out to package managers via `peter-evans/repository-dispatch@<sha>` so Homebrew taps, Scoop buckets, and similar repositories see the new release without polling. Each downstream gets a typed event (`event-type: formula-update`) plus a small JSON payload with the version. The downstream tap repo runs its own workflow that updates the formula and opens a PR.

This is the right home for SBOM publication and SLSA provenance attachment too — `actions/attest-build-provenance@<sha>` on the artifact set, with the resulting attestations attached to the release.

---

## Anti-patterns to refuse

| Don't | Reason |
|---|---|
| Re-derive the version inside CI | Local and remote will disagree; silent drift. |
| `cancel-in-progress: true` on releases | A second tag push will cancel the publish step mid-flight. |
| Mutating CHANGELOG.md after tag | Tagged tree must be the canonical record. |
| `generate_release_notes: true` with `body_path:` | Curated notes will be discarded. |
| Cross-compile from x64 to ARM via QEMU | Native ARM runners are an order of magnitude faster. |

---

## Validation

Run these locally before pushing a release-workflow change:

```bash
actionlint .github/workflows/release.yml
gh release list --limit 10
gh release view v<previous> --json assets --jq '.assets[].name'
```

The asset list of the previous release is the regression baseline — every name that was there must still be there after a workflow change, plus any new ones the workflow now produces.

---

> Pattern adopted from `gh-actions` (ACFS skill corpus). Methodology only — no verbatim text.
