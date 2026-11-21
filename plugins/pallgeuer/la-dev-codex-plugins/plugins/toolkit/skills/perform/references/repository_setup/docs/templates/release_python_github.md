# Python/GitHub release template

For a versioned Python package hosted on GitHub, use this template to create root `RELEASE.md` for manual GitHub releases with one wheel, one source distribution, and a checksum manifest. The two explicit approval checkpoints are mandatory. No release workflow, PyPI publisher, or protected environment is required for this model. If the user instead chooses notes/tag only, multiple packages, a prerelease policy, or automated publication, agree on and adapt that model explicitly before finalizing the runbook.

Replace every project placeholder before saving the repository's RELEASE.md:

- `YOUR-ORG/YOUR-REPOSITORY`: the actual GitHub owner/repository.
- `YOUR_DEFAULT_BRANCH`: the actual release/default branch.
- `YOUR_IMPORT_PACKAGE`: the import package and its source-directory component.
- `YOUR-DISTRIBUTION-NAME`: the package-metadata distribution name, which may differ from the import package.
- `YOUR_CHECK_WORKFLOW.yml`: the filename of the actual branch-check workflow. Verify its triggers and matrix; do not invent a workflow_dispatch preflight.
- `YOUR_ARCHIVE_VALIDATION_COMMAND`: a real, complete command that checks wheel/sdist metadata and boundaries and independently installs/smoke-tests each archive outside the checkout. Implement/validate the repository-only helper or concrete equivalent before finalizing this runbook; `uv build` and `twine check` alone are insufficient. This command must require exactly one wheel and one source archive and verify their versions against the installed package. The remaining template prose's "helper" refers to that validation implementation.

The template assumes the Python guide's dev dependency group, Hatchling version source at `src/YOUR_IMPORT_PACKAGE/_version.py`, an exported `__version__`, uv tooling, and `docs/devel/plans/` ignore rules. Adapt any explicitly different project layout or tools and the exact staging list. Version values, release SHAs, and CI run IDs are facts selected or discovered during each future release, not setup-time values to hardcode. Use ordinary Bash variable binding for the exact user-approved release_version; never treat an example version as approval. Do not execute tag/push/create commands while adopting or checking the template.

Copy the following complete runbook after replacing those values:

````markdown
# Release procedure

Run `$toolkit:perform publish-release` in Default mode to follow this runbook. Creating this document does not authorize a release. Stop for explicit confirmation of the exact version before editing release metadata, then stop again for explicit publication approval after preparation, CI, tagging, and preflight. End the turn at each approval checkpoint; an unanswered question is not consent.

Run commands from the repository root in Bash. Stop on any failed check. Keep the release variables across sections; after a session restart, reconstruct and verify their values from the approved version, tag, and commit rather than guessing.

## 1. Release model and sources of truth

This repository publishes manual GitHub releases at `YOUR-ORG/YOUR-REPOSITORY` from `YOUR_DEFAULT_BRANCH`. Each release has an annotated `vX.Y.Z` tag, curated changelog notes, one wheel, one source distribution, and `SHA256SUMS`. GitHub also supplies source snapshots. There is no PyPI publication or release/deployment workflow; `.github/workflows/YOUR_CHECK_WORKFLOW.yml` validates branch commits.

`src/YOUR_IMPORT_PACKAGE/_version.py` is the single version source. `pyproject.toml` configures Hatchling's dynamic version, dependencies, and distributions; `uv.lock` records the resolved environment. `CHANGELOG.md` supplies the release date, outcomes, and comparison links. `YOUR_ARCHIVE_VALIDATION_COMMAND` inspects and independently installs both archives. This runbook is repository-only and is not needed inside a distribution.

Use ordinary GitHub releases for `X.Y.Z` versions, including `0.x` versions. A prerelease requires a separately agreed version format and GitHub status; do not silently invent that policy. Never automatically increment a version after publishing.

## 2. Prerequisites

Require Git, uv, authenticated GitHub CLI with write access to this repository, and the standard `sha256sum`, `cmp`, and `mktemp` commands. Use uv's normal cache; follow the README's host-specific build prerequisites if syncing requires them. Ignored plans/reports must remain local.

```bash
git status --short
git branch --show-current
git remote get-url origin
git fetch origin --tags
git rev-parse HEAD origin/YOUR_DEFAULT_BRANCH
gh auth status --hostname github.com
gh release list --repo YOUR-ORG/YOUR-REPOSITORY
git tag --list 'v*' --sort=-version:refname
```

Proceed only on `YOUR_DEFAULT_BRANCH`, with a clean worktree and identical HEAD/origin/YOUR_DEFAULT_BRANCH commits. Review any unexpected files or remote changes; do not discard work, force-push, or switch branches automatically. Check remote tags as well as local tags before deciding that a version is available.

## 3. Inspect changes and choose the version

Select the previous published version using the actual release/tag history, not merely the lexically largest tag. Review its complete diff through HEAD, current documentation, and `Unreleased`. For the first release, review the initial commit, subsequent history, and current tracked contents; a diff from the first commit alone omits the foundation it introduced.

Propose the exact semantic version and explain it. An initial package version such as `0.1.0` need not be incremented merely because it is being released for the first time. **Stop and obtain explicit approval of that exact version before editing metadata.** Set `release_version` to that approved value, without a `v` prefix, then initialize:

```bash
release_repo=YOUR-ORG/YOUR-REPOSITORY
release_tag="v${release_version:?Set release_version to the exact user-approved version}"
```

Confirm that neither the local/remote tag nor the GitHub release already exists. If either does exist, inspect it and use the recovery section instead of overwriting it.

## 4. Prepare release metadata

Update `_version.py` only if the approved version differs. Run `uv lock`, inspect its diff, and sync the locked environment after version/dependency metadata changes. Review compatibility and usage documentation; change claims only when supported by the release.

Rewrite and compact `Unreleased` into concise user-facing outcomes. Consolidate overlapping entries, retain material features, fixes, compatibility changes, and migrations, and omit intermediate churn, test-only work, and stale descriptions of removed code. Review the result against the complete release diff and explicitly verify its accuracy before continuing to checks, commits, tags, or publication.

Move the verified entries into `## X.Y.Z (YYYY-MM-DD)` using the approved version and actual release-preparation date. Retain `## Unreleased` with `None.` and retain horizontal rules between the introduction, `Release diffs`, Unreleased, and every released version. Omit empty change categories; keep the existing change-type/category structure for real entries.

Replace the initial `Release diffs` TODO and example fence during first-release preparation. Use real repository/version values: Unreleased links to `compare/vX.Y.Z...HEAD`; the first version links to `releases/tag/vX.Y.Z`; each later version links to `compare/vPREVIOUS...vCURRENT`. Keep previous entries newest first. Prepare these links in the release commit before creating its tag: the new tag and release URLs become resolvable at the later tagging/publication steps. Do not leave example versions in a released changelog.

Extract only the finalized version's entries for GitHub notes, excluding Unreleased, the comparison index, and other versions:

```bash
release_notes_path=docs/devel/plans/release-notes.md
mkdir -p docs/devel/plans
git check-ignore "$release_notes_path"
awk -v heading="## ${release_version} (" '
  index($0, heading) == 1 { active = 1; next }
  active && /^## / { exit }
  active && $0 != "---" { print }
' CHANGELOG.md > "$release_notes_path"
test -s "$release_notes_path"
```

Read the extracted notes and confirm they contain the complete approved release entry. Keep the notes file ignored; never stage the plans directory.

## 5. Run checks and build artifacts

Run this validation block now and repeat it during the tagged preflight in section 8. `uv build --clear` replaces generated build output; retain no stale artifacts as release candidates.

```bash
uv sync --locked --no-default-groups --group dev
uv lock --check
uv run --no-sync python -c 'import importlib.metadata, sys, YOUR_IMPORT_PACKAGE; assert YOUR_IMPORT_PACKAGE.__version__ == importlib.metadata.version("YOUR-DISTRIBUTION-NAME") == sys.argv[1]' "$release_version"
uv run --no-sync pre-commit run --all-files --hook-stage manual --show-diff-on-failure
git diff --check
uv build --clear
uv run --no-sync twine check dist/*.whl dist/*.tar.gz
YOUR_ARCHIVE_VALIDATION_COMMAND
uv run --no-sync la-dev-release-checksums --output dist/SHA256SUMS dist/*.whl dist/*.tar.gz
(cd dist && sha256sum --check SHA256SUMS)
```

Require exactly one wheel and one source archive, matching the approved version; the helper checks archive boundaries, installed identity, and licensing. Inspect filenames and metadata as well as command success. Generate checksums only after validation, in wheel-then-sdist order. On checksum generation failure, stop; never restore an old manifest as if it described new artifacts.

## 6. Commit, push, and wait for CI

Review the release diff and stage only its intended source/metadata/documentation files. Commit and push `YOUR_DEFAULT_BRANCH` without bypassing hooks. If hooks modify files, inspect and validate those changes before completing the commit.

```bash
git status --short
git add src/YOUR_IMPORT_PACKAGE/_version.py uv.lock CHANGELOG.md README.md
git diff --cached --check
git commit -m "release: prepare ${release_tag}"
git push origin YOUR_DEFAULT_BRANCH
release_commit=$(git rev-parse HEAD)
gh run list --repo "$release_repo" --workflow YOUR_CHECK_WORKFLOW.yml --commit "$release_commit"
```

Inspect the corresponding run with `gh run view RUN_ID --repo "$release_repo"`. Require the Checks workflow to succeed for this exact commit on all configured Python versions, and verify the remote YOUR_DEFAULT_BRANCH branch matches it. Do not reuse an older successful run or tag a commit while its CI is pending.

## 7. Create the immutable tag

Recheck tag/release absence remotely and the clean checkout identity immediately before creating the tag. Create an annotated tag on the verified SHA and push that tag only:

```bash
git tag -a "$release_tag" "$release_commit" -m "Release ${release_tag}"
git push origin "refs/tags/${release_tag}"
git cat-file -t "$release_tag"
git rev-parse "${release_tag}^{commit}"
git ls-remote --tags origin "refs/tags/${release_tag}" "refs/tags/${release_tag}^{}"
```

The local object type must be `tag`; its peeled commit and the remote peeled commit must equal `release_commit`. Treat a pushed tag as immutable. Creating it is not permission to publish the GitHub release yet.

## 8. Run a nonpublishing preflight

Confirm a clean checkout and `HEAD == release_commit == release_tag^{commit}`. Repeat section 5's complete validation block against that identity. Branch CI already validates the release commit; this repository has no tag-triggered release workflow or `workflow_dispatch` publication preflight to invoke.

Retain the exact validated wheel, sdist, and manifest in `dist/`, and the reviewed notes in their ignored file. Verify artifact versions again and record their filenames and hashes. Do not rebuild or change these bytes after publication approval; changes require renewed validation and approval.

## 9. Approve publication

**Stop and end the turn for a second explicit approval.** Present the exact version, annotated tag, full commit SHA, successful CI URL, reviewed notes, artifact names/hashes, repository destination, and the command below. Explain that it creates a GitHub release and uploads the three assets, with no PyPI upload or deployment pipeline. Approval must cover this exact prepared result; it is separate from the version confirmation.

## 10. Publish and handle manual approval

After explicit approval, recheck tag identity, local checksums, reviewed notes, and release absence. Publish the retained artifacts without an implicit tag or autogenerated notes:

```bash
gh release create "$release_tag" dist/*.whl dist/*.tar.gz dist/SHA256SUMS \
  --repo "$release_repo" --verify-tag --title "$release_tag" --notes-file "$release_notes_path"
```

Asset upload and publication use separate API operations and can fail partially. Inspect state before retrying. No protected deployment approval is configured here; if a new/manual gate appears, identify the exact run or deployment, ask for the required action, and end the turn without polling until the user responds.

## 11. Verify every published surface

```bash
gh release view "$release_tag" --repo "$release_repo" --json url,tagName,isDraft,isPrerelease,body,assets
release_verify_dir=$(mktemp -d /tmp/release_verify_XXXXXX)
gh release download "$release_tag" --repo "$release_repo" --dir "$release_verify_dir" \
  --pattern '*.whl' --pattern '*.tar.gz' --pattern SHA256SUMS
cmp dist/SHA256SUMS "$release_verify_dir/SHA256SUMS"
(cd "$release_verify_dir" && sha256sum --check SHA256SUMS)
git status --short
```

Confirm a published, non-prerelease release with the exact tag, curated notes, and three expected uploaded assets; automatically generated source snapshots are separate. Recheck the remote tag SHA, released version/date, and all changelog comparison/release links. The downloaded manifest must match the retained manifest and verify the downloaded bytes, which were independently installation-tested before upload. These checksums detect byte mismatches; they are not signatures or independent proof of authorship.

Report the version, tag, commit, CI/release URLs, asset verification, and final branch/worktree state. Keep `Unreleased` available for future work. Do not bump the version again just to mark development as resumed.

## 12. Recover safely

- Before tagging: fix preparation/check failures, review and commit any corrections, push, and require fresh CI for the changed commit.
- After tagging but before publication: retain the tag and validated bytes. Resume only against that exact commit; if source corrections are needed, stop and ask for a new version rather than moving the tag.
- After an interrupted create/upload or a lost response: inspect the existing release, its draft/published status, tag, notes, and asset names/digests before retrying. Do not blindly create a second release or use an overwrite option. A matching unpublished draft may be completed only after confirming the approved bytes and scope; stop for uncertain or changed recovery decisions.
- After publication: do not silently replace published assets or rewrite the tag. A defective release needs an explicitly approved correction/new version. Preserve evidence and validated artifacts until recovery is settled.

Do not delete tags/releases, force-push, publish to another destination, or introduce release automation as an automatic recovery step.
````
