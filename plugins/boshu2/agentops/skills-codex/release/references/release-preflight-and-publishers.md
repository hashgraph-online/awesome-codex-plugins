# Release Preflight And Publishers

Use this reference when a release spans more than a local tag: package registries, deploy hosts, multi-repo sync, or hosted platform publishing.

## Separation Of Duties

| Surface | Owns | Should not own |
|---|---|---|
| Local release skill | Readiness, changelog, version bump, tag | Remote publish mutation. |
| CI release workflow | Build, sign, attach assets, publish | Rewriting source docs after tag. |
| Package registry | Distribution metadata | Source-of-truth version decisions. |
| Deployment host | Runtime rollout | Changelog generation. |

## Preflight

Before bumping versions:

1. Confirm the previous release and current unreleased commits.
2. Run the local release gate named by the repo.
3. Verify credentials are present without printing secrets.
4. Confirm package names, registry owners, and deploy targets.
5. Capture rollback path and previous artifact list.

## Multi-Repo Release

When multiple repositories must move together:

- Commit dirty repos before syncing.
- Pull/rebase all repos before version decisions.
- Release dependency repos before consumers.
- Record each repo SHA in the release note or audit trail.
- Stop if one repo cannot prove readiness.

## Publisher Notes

- Rust crates: publish workspace crates in dependency order and verify crates.io metadata.
- Vercel or hosted web deploys: build locally when possible and avoid burning remote build minutes on known failures.
- GitHub CLI: use it for inspection and PR/release metadata, but keep irreversible publish steps in CI unless the repo explicitly says otherwise.

---

**Source:** Adapted from an external skill corpus / `release-preparations`, `rust-crates-publishing`, `vercel`, `gh-cli`, `dsr`, and `ru-multi-repo-workflow`. Pattern-only, no verbatim text.
