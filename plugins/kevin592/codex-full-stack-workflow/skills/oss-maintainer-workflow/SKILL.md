---
name: oss-maintainer-workflow
description: Use when maintaining or releasing a public open-source repository, including issue triage, pull request review, dependency or security remediation, release preparation, and source-linked adoption reporting.
---

# OSS Maintainer Workflow

Run one small, verifiable maintenance cycle for a public repository. The goal is
not activity volume. The goal is a real maintainer outcome backed by public
issues, pull requests, CI, security checks, release notes, and honest adoption
evidence.

## Input Artifacts

- Public repository URL and license
- Current issue and pull request queue
- Latest release and changelog
- CI and dependency/security status
- Real user feedback, external listings, or downstream references when they exist

## Output Artifact

- `docs/oss-maintenance/<cycle>/01-intake-and-signals.md`
- `docs/oss-maintenance/<cycle>/02-maintenance-plan.md`
- `docs/oss-maintenance/<cycle>/03-change-and-review-evidence.md`
- `docs/oss-maintenance/<cycle>/04-release-readiness.md`
- `docs/oss-maintenance/<cycle>/05-adoption-follow-up.md`

## Required MCP Tool

- `plan_oss_maintenance_cycle`
- `review_oss_release_readiness`

## Required Flow

1. Inspect the public repository, open issues, open pull requests, last release,
   CI, dependency audit, and security policy.
2. Call `plan_oss_maintenance_cycle` with source-backed counts. Do not estimate
   stars, downloads, users, or vulnerabilities.
3. Select the smallest meaningful change. Security fixes and maintainer-requested
   review changes outrank speculative features.
4. Record either a real issue link or a concise rationale. Do not manufacture an
   issue solely to make the repository look active.
5. Implement on a reviewable branch and run the repository's relevant tests,
   build, validation, and security audit.
6. Open or update a pull request. Link the diff, checks, review findings, and
   rollback path in the maintenance evidence.
7. Update user documentation and `CHANGELOG.md`.
8. Call `review_oss_release_readiness`. Do not tag or publish while it reports
   `blocked`.
9. After the pull request is merged, tag and publish the documented version.
10. Record only real adoption signals in the follow-up artifact.

## Evidence Rules

- Prefer GitHub URLs and reproducible command output over prose claims.
- A directory listing is ecosystem evidence; it is not proof of active users.
- A star is a repository signal; it is not automatically a user or deployment.
- A normal contribution to someone else's project does not make the contributor
  a primary or core maintainer.
- If no user feedback exists, say so and invite real testing. Never fabricate it.

## Hard Stops

- No release with unresolved critical or high security findings.
- No release without fresh passing tests and required build or plugin validation.
- No release without documentation, changelog, and review evidence.
- No invented stars, downloads, users, issues, pull requests, or maintainer roles.
- No large speculative feature when a smaller security, compatibility, or
  maintainer-requested fix is available.

## Pressure Test Responsibility

- Block a cosmetic release whose only purpose is repository activity.
- Block a release supported only by stale CI or an old security scan.
- Block adoption claims that cannot be linked to a public source.
- Block a claim of core-maintainer status without repository permission or
  sustained review and release responsibility.

## Next Gate

- `review_oss_release_readiness.nextAllowedAction`

## Reference

Read `references/maintenance-evidence-contract.md` before preparing the release
gate or reporting ecosystem and adoption signals.
